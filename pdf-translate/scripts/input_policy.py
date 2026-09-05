"""Inventory untrusted PDF capabilities without running actions or reading payloads."""
import pikepdf

ACTION_TYPES = {'/JavaScript', '/URI', '/Launch', '/GoToR', '/GoToE',
                '/SubmitForm', '/ImportData', '/Rendition', '/Movie', '/Sound',
                '/Named', '/Hide', '/ResetForm', '/SetOCGState', '/GoTo'}
POLICIES = ('preserve-report', 'refuse-active')


def inventory(path, max_objects=100000):
    """Visit reachable dictionaries/arrays with a bounded traversal; no payload execution."""
    with pikepdf.open(path) as pdf:
        result = {'actions': [], 'attachments': sorted(str(x) for x in pdf.attachments),
                  'signatures': [], 'encrypted': pdf.is_encrypted,
                  'permissions': dict(zip(pikepdf.Permissions._fields, map(bool, pdf.allow))),
                  'tagged': '/StructTreeRoot' in pdf.Root,
                  'xfa': '/XFA' in pdf.Root.get('/AcroForm', {}),
                  'optional_content': '/OCProperties' in pdf.Root}
        pending = [('catalog', pdf.Root)]
        seen = {}
        while pending:
            where, obj = pending.pop()
            if not isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream, pikepdf.Array)):
                continue
            key = ('xref', tuple(obj.objgen)) if obj.is_indirect else ('direct', id(obj))
            if key in seen:
                continue
            seen[key] = obj
            if len(seen) > max_objects:
                raise ValueError('PDF capability inventory exceeded its object budget')
            if isinstance(obj, pikepdf.Array):
                pending.extend((f'{where}[{i}]', x) for i, x in enumerate(obj))
                continue
            action_type = str(obj.get('/S', ''))
            if action_type in ACTION_TYPES:
                result['actions'].append({'location': where, 'type': action_type})
            if obj.get('/Type') == pikepdf.Name('/Sig') or '/ByteRange' in obj:
                result['signatures'].append({'location': where,
                    'has_byte_range': '/ByteRange' in obj, 'has_contents': '/Contents' in obj})
            pending.extend((f'{where}{name}', value) for name, value in obj.items())
        result['actions'].sort(key=lambda x: (x['location'], x['type']))
        return result


def enforce(report, policy):
    if policy not in POLICIES:
        raise ValueError(f'unknown content policy: {policy}')
    active = [a for a in report['actions'] if a['type'] != '/GoTo']
    if policy == 'refuse-active' and (active or report['attachments']):
        raise ValueError('content policy refuses active actions or embedded attachments')
