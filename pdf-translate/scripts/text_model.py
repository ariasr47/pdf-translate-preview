"""Validated author text channels shared by composition and linguistic QA.
Precedence: merge, skip remaining lines, page override, segment target, core.
IDs refer to the exact segments.json; null occurrence values fall back to core.
"""
from html.parser import HTMLParser
from html import unescape
import re
import math
import unicodedata

def seg_dir(seg):
    """Unit line direction of a segment; (1, 0) when absent or unusable."""
    d = seg.get('dir') or (1.0, 0.0)
    try:
        dx, dy = float(d[0]), float(d[1])
    except (TypeError, ValueError, IndexError, KeyError):
        return 1.0, 0.0
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return 1.0, 0.0
    return dx / n, dy / n


def is_rotated(dx, dy):
    return abs(dx - 1.0) > 1e-6 or abs(dy) > 1e-6


INLINE_TAGS = re.compile(r'</?(?:b|i|em|strong)\s*/?>', re.I)


def has_inline_markup(text):
    return bool(INLINE_TAGS.search(text or ''))


def composition_fragments(value, channel):
    """Raw parser inputs, preserving the renderer's independent boundaries."""
    if channel == 'override':
        return list(value)
    if channel == 'notice' or (channel in {'core', 'segment'} and not has_inline_markup(value)):
        return value.split('‖')
    return [value]


class _Text(HTMLParser):
    tags = {'b','strong','i','em','u','br','p','div','span','sup','sub'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag not in self.tags or attrs:
            raise ValueError(f'unsafe markup: tag {tag!r} or attributes/resources are not allowed')
        if tag in {'br','p','div'}: self.parts.append(' ')
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag,attrs)
    def handle_endtag(self, tag):
        if tag not in self.tags: raise ValueError(f'unsafe markup: {tag}')
        if tag in {'p','div'}: self.parts.append(' ')
    def handle_data(self, data): self.parts.append(data)
    def handle_decl(self, decl): raise ValueError('unsafe markup declaration')
    def handle_pi(self, data): raise ValueError('unsafe markup processing instruction')


class _AuthoredText(HTMLParser):
    """Text characters and authored numeric values, excluding comments."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.characters = []
    def handle_data(self, data):
        match = re.search(r'&#(?:[xX]([0-9a-fA-F]+)|([0-9]+))$', data)
        if not match:
            self.characters.extend(data)
            return
        self.characters.extend(data[:match.start()])
        self.handle_charref(('x' + match.group(1)) if match.group(1)
                            else match.group(2))
    def handle_charref(self, name):
        try:
            value = int(name[1:], 16) if name[:1].lower() == 'x' else int(name)
            if 0 <= value <= 0x10ffff:
                self.characters.append(chr(value))
        except ValueError:
            pass
    def handle_entityref(self, name):
        self.characters.extend(unescape(f'&{name};'))

def plain_text(value, strip=True):
    if not isinstance(value,str): raise ValueError('text target must be a string')
    parser=_Text(); parser.feed(value); parser.close()
    result = ''.join(parser.parts).replace('‖','')
    return result.strip() if strip else result

def segment_target(conf, seg):
    targets = conf.get('segment_targets') or {}
    value = targets.get(seg.get('occurrence_id'))
    if value is None: value = targets.get(str(seg['id']))
    return value if value is not None else (conf.get('translations') or {}).get(seg['core'])

def effective_texts(conf, segments=None, widget_text=None):
    segments=segments or []
    targets=conf.get('segment_targets') or {}
    if not isinstance(targets,dict): raise ValueError('segment_targets must be an object keyed by segment ID')
    ids=[str(s['id']) for s in segments]
    if len(set(ids))!=len(ids): raise ValueError('duplicate segment IDs')
    canonical = [s['occurrence_id'] for s in segments if 'occurrence_id' in s]
    if len(set(canonical)) != len(canonical): raise ValueError('duplicate occurrence IDs')
    valid = set(ids) | set(canonical)
    if set(targets)-valid: raise ValueError('unknown segment target IDs: '+', '.join(sorted(set(targets)-valid)))
    for seg in segments:
        values = [targets[k] for k in (str(seg['id']),seg.get('occurrence_id')) if k in targets and targets[k] is not None]
        if len(values)==2 and values[0]!=values[1]: raise ValueError('conflicting segment aliases')
    # Validate even superseded text: unsafe author markup never reaches an engine.
    for value in list((conf.get('translations') or {}).values())+list(targets.values()):
        if value is not None: plain_text(value)
    rows=[]
    def add(source,target,channel,segment=None,**context):
        if target is not None:
            raw_parts = composition_fragments(target, channel)
            # Rotated inline targets take the renderer's literal TextWriter path.
            literal = channel == 'widget' or (channel == 'segment' and
                has_inline_markup(target) and is_rotated(*seg_dir(segment or {})))
            decoded = raw_parts if literal else [plain_text(part, strip=False) for part in raw_parts]
            joiner = ' ' if channel in {'override', 'notice'} else ''
            authored = joiner.join(decoded)
            rows.append(dict(source=source,target=authored if literal else authored.strip(),
                authored_target=authored, raw_target=joiner.join(raw_parts) if channel == 'override' else target,
                raw_fragments=raw_parts, literal_fragments=literal, channel=channel,
                placement_targets=decoded, **context))
    consumed=set()
    for m in conf.get('merges') or []:
        add(' '.join(m.get('lines') or []),m.get('html'),'merge',page=m.get('page'))
        remaining=list(m.get('lines') or [])
        for s in segments:
            if str(s['id']) not in consumed and remaining and s['page']==m.get('page') and s['text'].strip()==remaining[0].strip():
                consumed.add(str(s['id'])); remaining.pop(0)
    for o in conf.get('overrides') or []:
        for part in o.get('parts') or []: plain_text(part['text'])
    seen=set()
    for s in segments:
        core=s['core']; seen.add(core)
        if str(s['id']) in consumed or s['text'].strip() in (conf.get('skip') or []): continue
        override=next((o for o in conf.get('overrides') or [] if o['page']==s['page'] and o['contains'] in s['text'].strip()),None)
        if override:
            add(s['text'].strip(),[p['text'] for p in override['parts']],'override',segment_id=s['id'],occurrence_id=s.get('occurrence_id'),page=s['page'])
        else: add(core,segment_target(conf,s),'segment',segment=s,segment_id=s['id'],
                  occurrence_id=s.get('occurrence_id'),page=s['page'])
    for core,target in (conf.get('translations') or {}).items():
        if core not in seen and core not in (conf.get('skip') or []): add(core,target,'core')
    if not segments:
        for o in conf.get('overrides') or []:
            add(o['contains'],[p['text'] for p in o['parts']],'override',page=o['page'])
    for n in conf.get('notices') or []:
        add(n.get('source',''),n.get('text'),'notice',page=n.get('page'),source_supplied='source' in n)
    def widgets(node, path=()):
        if isinstance(node,dict):
            if 'source' in node and 'target' in node:
                add(str(node['source']),node['target'],'widget',widget_path='.'.join(path),
                    protected=bool(path and path[-1] in {'value','default','export'}))
            else:
                for key,value in node.items():
                    if key != 'export': widgets(value,path+(str(key),))
        elif isinstance(node,list):
            for index,value in enumerate(node): widgets(value,path+(str(index),))
        elif isinstance(node,str):
            add('',node,'widget',widget_path='.'.join(path),source_supplied=False)
    widgets(widget_text if widget_text is not None else conf.get('widget_text'))
    return rows


def authored_text_diagnostics(rows):
    """Unsupported renderer controls and discretionary soft hyphens by row."""
    findings = []
    for row in rows:
        text = row.get('authored_target', row.get('target', ''))
        fragments = row.get('raw_fragments', [row.get('raw_target', text)])
        for part_index, fragment in enumerate(fragments):
            findings.extend(_fragment_diagnostics(row, fragment, part_index, len(fragments)))
    return findings


def _fragment_diagnostics(row, text, part_index, part_count):
    findings = []
    allowed_controls = {'\t', '\n', '\r'}
    if row.get('literal_fragments', row.get('channel') == 'widget'):
        authored_characters = list(text)
    else:
        parser = _AuthoredText()
        parser.feed(text)
        parser.close()
        authored_characters = parser.characters
    codepoints = []
    for ch in authored_characters:
        if ch == '\u00ad' or (unicodedata.category(ch) == 'Cc'
                              and ch not in allowed_controls):
            if ch not in codepoints:
                codepoints.append(ch)
    for ch in codepoints:
        positions = [index + 1 for index, value in enumerate(authored_characters)
                     if value == ch]
        count = len(positions)
        soft = ch == '\u00ad'
        item = {
            'kind': 'soft-hyphen' if soft else 'unsupported-control',
            'severity': 'warn' if soft else 'error',
            'core': row.get('source', ''),
            'codepoint': f'U+{ord(ch):04X}',
            'occurrence_count': count,
            'positions': positions,
            'detail': (f'U+00AD SOFT HYPHEN occurs {count} time(s); '
                       'review the discretionary break without removing or normalizing it'
                       if soft else
                       f'U+{ord(ch):04X} {unicodedata.name(ch, "CONTROL")} occurs '
                       f'{count} time(s) at decoded character position(s) '
                       f'{positions}; this composer does not support that control'),
        }
        for key in ('channel', 'segment_id', 'occurrence_id', 'page', 'widget_path'):
            if key in row and row[key] is not None:
                item[key] = row[key]
        if part_count > 1:
            item['part_index'] = part_index
        findings.append(item)
    return findings
