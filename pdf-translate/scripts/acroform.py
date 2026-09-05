"""AcroForm field-tree resolution and occurrence-preserving structural checks.

Objects returned by iter_fields belong to its open pikepdf document. Names are
fully qualified; unnamed widget kids inherit their terminal field's name.
"""
from collections import Counter

import pikepdf
import pymupdf

INHERITED = ('/FT', '/Ff', '/DA', '/Opt', '/V', '/DV', '/TU')


def object_id(obj):
    return tuple(obj.objgen) if obj.is_indirect else id(obj)


class Field:
    def __init__(self, obj, acroform=None):
        self.obj = obj
        self.acroform = acroform
        self.chain = []
        seen = set()
        while obj is not None and object_id(obj) not in seen:
            seen.add(object_id(obj))
            self.chain.append(obj)
            obj = obj.get('/Parent')
        self.name = '.'.join(str(a['/T']) for a in reversed(self.chain) if '/T' in a)

    def get(self, key, default=None):
        for obj in self.chain:
            if key in obj:
                return obj[key]
        if key == '/DA' and self.acroform is not None:
            return self.acroform.get(key, default)
        return default

    def owner(self, key):
        """Mutation target: the logical field, never a shared value ancestor.

        An unnamed widget belongs to the nearest named field. Materializing
        inherited values there keeps sibling fields independent and all of
        this field's repeated widget occurrences synchronized.
        """
        return next((obj for obj in self.chain if '/T' in obj), self.obj)


def iter_fields(pdf):
    """Yield each field-tree node and orphan page widget once, resolving parents."""
    seen = set()
    acroform = pdf.Root.get('/AcroForm')

    def walk(obj):
        key = object_id(obj)
        if key in seen:
            return
        seen.add(key)
        yield Field(obj, acroform=acroform)
        for child in obj.get('/Kids', []):
            yield from walk(child)

    for root in pdf.Root.get('/AcroForm', {}).get('/Fields', []):
        yield from walk(root)
    for page in pdf.pages:
        for obj in page.get('/Annots', []):
            if obj.get('/Subtype') == pikepdf.Name('/Widget'):
                yield from walk(obj)


def value_token(obj):
    if obj is None:
        return None
    if isinstance(obj, pikepdf.String):
        return ('string', bytes(obj).hex())
    if isinstance(obj, pikepdf.Array):
        return tuple(value_token(x) for x in obj)
    return str(obj)


def field_records(path):
    """Return serializable resolved records, including widget multiplicity."""
    records = []
    with pikepdf.open(path) as pdf:
        occurrences = {}
        for i, page in enumerate(pdf.pages):
            for obj in page.get('/Annots', []):
                if obj.get('/Subtype') == pikepdf.Name('/Widget'):
                    occurrences.setdefault(object_id(obj), []).append(i)
        for f in iter_fields(pdf):
            is_widget = f.obj.get('/Subtype') == pikepdf.Name('/Widget')
            if f.get('/FT') is None and not is_widget:
                continue
            opt = f.get('/Opt')
            records.append(dict(name=f.name, type=str(f.get('/FT')),
                flags=int(f.get('/Ff', 0)), annotation_flags=int(f.obj.get('/F', 0)),
                pages=occurrences.get(object_id(f.obj), []),
                widget=is_widget,
                da=str(f.get('/DA', '')),
                rect=[float(x) for x in f.obj.get('/Rect', [])],
                exports=None if opt is None else [value_token(x[0] if isinstance(x, pikepdf.Array) else x) for x in opt],
                value=value_token(f.get('/V')), default=value_token(f.get('/DV'))))
    return records


def structural_misses(orig, trans, mirror=False, allow_extra_prefix=None):
    """Strict pages/field occurrences; mirror uses the engine's page-space flip."""
    misses = []
    with pymupdf.open(orig) as o, pymupdf.open(trans) as j:
        if len(o) != len(j):
            misses.append(f'page count: {len(o)} -> {len(j)}')
        for i in range(min(len(o), len(j))):
            for key in ('mediabox', 'cropbox', 'bleedbox', 'trimbox', 'artbox', 'rotation'):
                if getattr(o[i], key) != getattr(j[i], key):
                    misses.append(f'page {i+1} {key} changed')
        source = field_records(orig)
        target = field_records(trans)
        source_names = {r['name'] for r in source}
        if allow_extra_prefix:
            target = [r for r in target if r['name'] in source_names or not r['name'].startswith(allow_extra_prefix)]

        def fields(rows):
            # Internal nodes without /T merely repeat inherited values. A set
            # records logical state; the counter below records every widget.
            return {(r['name'], r['type'], r['flags'], repr(r['exports']),
                     repr(r['value']) if r['type'] == '/Ch' else None,
                     repr(r['default']) if r['type'] == '/Ch' else None) for r in rows}

        if fields(source) != fields(target):
            misses.append('logical field type/flags or choice export/value/default changed')

        def widgets(rows, transform=False):
            result = Counter()
            for r in rows:
                if not r['widget']:
                    continue
                for pno in r['pages'] or [None]:
                    rect = r['rect']
                    if transform and pno is not None and len(rect) == 4:
                        page = o[pno]
                        pr = pymupdf.Rect(rect) * page.transformation_matrix
                        pr = pymupdf.Rect(page.rect.width-pr.x1, pr.y0, page.rect.width-pr.x0, pr.y1)
                        rect = list(pr * ~page.transformation_matrix)
                    result[(r['name'], r['type'], r['flags'], r['annotation_flags'], pno,
                            tuple(round(x, 3) for x in rect))] += 1
            return result
        if widgets(source, mirror) != widgets(target):
            misses.append('widget occurrence/page/rectangle/type/flags changed')
    return misses
