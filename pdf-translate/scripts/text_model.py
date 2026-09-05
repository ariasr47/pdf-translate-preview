"""Validated author text channels shared by composition and linguistic QA.
Precedence: merge, skip remaining lines, page override, segment target, core.
IDs refer to the exact segments.json; null occurrence values fall back to core.
"""
from html.parser import HTMLParser

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
    def add(source,target,channel,**context):
        if target is not None:
            text = target if channel == 'widget' else plain_text(target)
            rows.append(dict(source=source,target=text,channel=channel,
                placement_targets=([target] if channel == 'widget' else
                    [plain_text(part, strip=False) for part in target.split('‖')]), **context))
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
            add(s['text'].strip(),' '.join(p['text'] for p in override['parts']),'override',segment_id=s['id'],page=s['page'])
            rows[-1]['placement_targets'] = [plain_text(p['text']) for p in override['parts']]
        else: add(core,segment_target(conf,s),'segment',segment_id=s['id'],page=s['page'])
    for core,target in (conf.get('translations') or {}).items():
        if core not in seen and core not in (conf.get('skip') or []): add(core,target,'core')
    if not segments:
        for o in conf.get('overrides') or []:
            add(o['contains'],' '.join(p['text'] for p in o['parts']),'override',page=o['page'])
            rows[-1]['placement_targets'] = [plain_text(p['text'], strip=False) for p in o['parts']]
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
