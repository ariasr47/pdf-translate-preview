"""Inventory untrusted PDF capabilities without running actions or reading payloads."""
import pikepdf

ACTION_TYPES = {'/JavaScript', '/URI', '/Launch', '/GoToR', '/GoToE',
                '/SubmitForm', '/ImportData', '/Rendition', '/Movie', '/Sound',
                '/Named', '/Hide', '/ResetForm', '/SetOCGState', '/GoTo'}
POLICIES = ('preserve-report', 'refuse-active')


def inventory(path, max_objects=100000, max_depth=128):
    """Bound Python graph work (including leaves), not parser/decompression work.

    Iterator frames avoid eagerly queuing wide arrays. Retained objects prevent
    direct-wrapper ID reuse; indirect objects are expanded only once.
    """
    if max_objects < 1 or max_depth < 1:
        raise ValueError('PDF inventory budgets must be positive')
    with pikepdf.open(path) as pdf:
        acroform = pdf.Root.get('/AcroForm')
        if acroform is not None and not isinstance(acroform, pikepdf.Dictionary):
            raise ValueError('PDF catalog /AcroForm must be a dictionary')
        result = {'actions': [], 'attachments': [],
                  'signatures': [], 'encrypted': pdf.is_encrypted,
                  'permissions': dict(zip(pikepdf.Permissions._fields, map(bool, pdf.allow))),
                  'tagged': '/StructTreeRoot' in pdf.Root,
                  'xfa': acroform is not None and '/XFA' in acroform,
                  'optional_content': '/OCProperties' in pdf.Root}
        pending = [iter([('catalog', pdf.Root, 0)])]
        seen = {}
        work = 0
        reserved = 1
        while pending:
            try:
                where, obj, depth = next(pending[-1])
            except StopIteration:
                pending.pop()
                continue
            work += 1
            if work > max_objects:
                raise ValueError('PDF capability inventory exceeded its work budget')
            if depth > max_depth:
                raise ValueError('PDF capability inventory exceeded its depth budget')
            if not isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream, pikepdf.Array)):
                continue
            key = ('xref', tuple(obj.objgen)) if obj.is_indirect else ('direct', id(obj))
            if key in seen:
                continue
            seen[key] = obj
            # pikepdf dictionary items() materializes a Python dict. Check
            # width before requesting it, and before descending at the limit.
            child_count = len(obj.stream_dict) if isinstance(obj, pikepdf.Stream) else len(obj)
            reserved += child_count
            if reserved > max_objects:
                raise ValueError('PDF capability inventory exceeded its work budget')
            if child_count and depth >= max_depth:
                raise ValueError('PDF capability inventory exceeded its depth budget')
            if isinstance(obj, pikepdf.Array):
                pending.append(_array_children(obj, where, depth))
                continue
            action_type = str(obj.get('/S', ''))
            if action_type in ACTION_TYPES:
                result['actions'].append({'location': where, 'type': action_type})
            if obj.get('/Type') == pikepdf.Name('/Sig') or '/ByteRange' in obj:
                result['signatures'].append({'location': where,
                    'has_byte_range': '/ByteRange' in obj, 'has_contents': '/Contents' in obj})
            pending.append(_dictionary_children(obj, where, depth))
        result['attachments'] = sorted(str(x) for x in pdf.attachments)
        result['actions'].sort(key=lambda x: (x['location'], x['type']))
        return result


def _array_children(obj, where, depth):
    for i, value in enumerate(obj):
        yield f'{where}[{i}]', value, depth + 1


def _dictionary_children(obj, where, depth):
    for name, value in obj.items():
        yield f'{where}{name}', value, depth + 1


def enforce(report, policy):
    if policy not in POLICIES:
        raise ValueError(f'unknown content policy: {policy}')
    active = [a for a in report['actions'] if a['type'] != '/GoTo']
    if policy == 'refuse-active' and (active or report['attachments']):
        raise ValueError('content policy refuses active actions or embedded attachments')
