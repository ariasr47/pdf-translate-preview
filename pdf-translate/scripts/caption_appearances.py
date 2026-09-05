"""Bounded, cached text-only pushbutton captions; never rely on viewer synthesis.

Only ordinary upright N/D/R streams with simple vector chrome are edited.
Source objects/resources are never modified. Unsupported named-state/icon buttons
fail before an output is saved. Geometry and the original font size are fixed.
"""
import io
import math
import os
import tempfile
import unicodedata
from pathlib import Path

import pikepdf
import pymupdf
from acroform import Field

SOURCE = '/PdfTranslateCaptionSource'
SHOW = {'Tj', 'TJ', "'", '"'}
SAFE = set('q Q cm w J j M d ri m l c v y h re S s f F f* B B* b b* n W W* BT ET Tc Tw Tz TL Tf Tr Ts Td TD Tm T* Tj TJ G g RG rg K k'.split()) | {"'", '"'}
MAX_FORMS = 64
MAX_OPERATIONS = 10000
MAX_STREAM_BYTES = 1_000_000
MAX_TOTAL_BYTES = 2_000_000
MAX_RASTER_PIXELS = 8_000_000
PROBE_PAD = 100
PROBE_SCALE = 4


class CaptionAppearanceError(ValueError):
    pass


def _authored_caption(text):
    """Only single ASCII spaces and explicit LF breaks have supported semantics.

    In particular, do not convert NBSP into a break opportunity, tabs into spaces,
    or authored runs of spaces into one space. Refuse before staging any change.
    """
    if any(c.isspace() and c not in (' ', '\n') for c in text):
        raise CaptionAppearanceError('unsupported caption whitespace (only ASCII space and LF are supported)')
    if text and any(not line or line.startswith(' ') or line.endswith(' ') or '  ' in line for line in text.split('\n')):
        raise CaptionAppearanceError('unsupported caption whitespace (blank lines, edge or repeated spaces)')
    return text


def _geometry(stream, raster=False):
    box = [float(v) for v in stream.get('/BBox', [])]
    if len(box) != 4 or not all(math.isfinite(v) and abs(v) <= 14400 for v in box):
        raise CaptionAppearanceError('caption geometry exceeds supported bounds')
    w, h = box[2]-box[0], box[3]-box[1]
    if w <= 0 or h <= 0:
        raise CaptionAppearanceError('caption geometry must have positive dimensions')
    if raster and math.ceil((w+2*PROBE_PAD)*PROBE_SCALE)*math.ceil((h+2*PROBE_PAD)*PROBE_SCALE) > MAX_RASTER_PIXELS:
        raise CaptionAppearanceError('caption raster budget exceeded')
    return box


def _appearance_graph(normal):
    """Check reachable Do calls once per Form, including expanded render cost.

    Memoization bounds shared DAG traversal; the separate expanded cost prevents
    a small DAG from asking the renderer to execute exponentially many calls.
    Unused XObject resources do not contribute and are not traversed.
    """
    nodes, active, costs = {}, set(), {}
    total_bytes = 0
    def visit(stream, depth=0):
        nonlocal total_bytes
        key = stream.objgen
        if key in active:
            raise CaptionAppearanceError('cyclic caption appearance resources are unsupported')
        if key in costs: return costs[key]
        if depth > 16 or len(nodes) >= MAX_FORMS:
            raise CaptionAppearanceError('caption appearance graph budget exceeded')
        _geometry(stream)
        size = len(stream.read_bytes())
        total_bytes += size
        if size > MAX_STREAM_BYTES or total_bytes > MAX_TOTAL_BYTES:
            raise CaptionAppearanceError('caption appearance stream budget exceeded')
        ops = list(pikepdf.parse_content_stream(stream))
        if len(ops) > MAX_OPERATIONS:
            raise CaptionAppearanceError('caption appearance operation budget exceeded')
        nodes[key] = ops
        active.add(key)
        cost = len(ops)
        for args, op in ops:
            if str(op) != 'Do': continue
            child = stream.get('/Resources', {}).get('/XObject', {}).get(args[0])
            if not isinstance(child, pikepdf.Stream) or child.get('/Subtype') != pikepdf.Name('/Form'):
                raise CaptionAppearanceError('non-Form caption XObject is unsupported')
            cost += visit(child, depth+1)
            if cost > MAX_OPERATIONS:
                raise CaptionAppearanceError('caption expanded rendering budget exceeded')
        active.remove(key); costs[key] = cost
        return cost
    _geometry(normal, raster=True)
    visit(normal)
    return nodes


def _normal(obj):
    ap = obj.get('/AP', {})
    normal = ap.get('/N')
    if not isinstance(normal, pikepdf.Stream):
        raise CaptionAppearanceError('missing ordinary normal caption appearance')
    return normal


def _simple(obj, normal):
    mk = obj.get('/MK', {})
    if any(k in mk for k in ('/I', '/RI', '/IX', '/RC', '/AC')) or int(mk.get('/R', 0)):
        raise CaptionAppearanceError('icons, alternate captions or rotation are unsupported')
    if any(k not in ('/N','/D','/R') or not isinstance(v, pikepdf.Stream) for k,v in obj.get('/AP', {}).items()):
        raise CaptionAppearanceError('named/dictionary appearance states are unsupported')
    if list(normal.get('/Matrix', [1, 0, 0, 1, 0, 0])) != [1, 0, 0, 1, 0, 0]:
        raise CaptionAppearanceError('transformed caption appearance is unsupported')
    if '/BBox' not in normal or len(normal.BBox) != 4:
        raise CaptionAppearanceError('caption appearance lacks a valid bounding box')
    box = _geometry(normal, raster=True)
    rect = [float(v) for v in obj.Rect]
    if box[:2] != [0, 0] or abs(box[2] - (rect[2]-rect[0])) > .01 or abs(box[3] - (rect[3]-rect[1])) > .01:
        raise CaptionAppearanceError('appearance and widget geometry differ')
    for args, op in _appearance_graph(normal)[normal.objgen]:
        if str(op) not in SAFE or (str(op) == 'Tr' and int(args[0]) != 0):
            raise CaptionAppearanceError(f'complex caption operation {op} is unsupported')
        if str(op) == 'Tz' and float(args[0]) != 100:
            raise CaptionAppearanceError('nondefault caption horizontal text scaling is unsupported')
        if str(op) in ('cm', 'Tm'):
            a,b,c,d,e,f = (float(v) for v in args)
            if not all(math.isfinite(v) for v in (a,b,c,d,e,f)) or a <= 0 or a != d or b != 0 or c != 0:
                raise CaptionAppearanceError('anisotropic or rotated caption text matrices are unsupported')


def stage_caption(pdf, obj, caption):
    """Preserve source AP for later font-aware repair, copying /MK before editing."""
    _authored_caption(caption)
    old = str(obj.get('/MK', {}).get('/CA', ''))
    if old == caption:
        return False
    normal = _normal(obj)
    for state in obj.AP.values():
        _simple(obj, state)
    obj[SOURCE] = pikepdf.Dictionary(obj.AP)
    obj.MK = pikepdf.Dictionary(obj.get('/MK', {}))
    obj.MK.CA = pikepdf.String(caption)
    del obj.AP
    return True


def _probe(normal, text_only=False, remove_clip=True):
    """Expose the unclipped local AP on a padded page for text and ink checks."""
    _appearance_graph(normal)
    pdf = pikepdf.new()
    box = [float(x) for x in normal.BBox]
    w, h = box[2]-box[0], box[3]-box[1]
    pad = PROBE_PAD
    page = pdf.add_blank_page(page_size=(w+2*pad, h+2*pad))
    ap = pdf.copy_foreign(normal)
    visited = set()
    def unclipped(stream):
        key = stream.objgen
        if key in visited: return
        visited.add(key)
        if remove_clip:
            stream.BBox = pikepdf.Array([-pad, -pad, w+pad, h+pad])
        ops = []
        used = set()
        for args, op in pikepdf.parse_content_stream(stream):
            name = str(op)
            if name == 'Do': used.add(args[0])
            if remove_clip and name in ('W', 'W*'):
                continue
            if text_only and name in ('S','s','f','F','f*','B','B*','b','b*'):
                ops.append(([], pikepdf.Operator('n')))
            else:
                ops.append((args, op))
        stream.write(pikepdf.unparse_content_stream(ops))
        resources = pikepdf.Dictionary(stream.get('/Resources', {}))
        xobjects = resources.get('/XObject', {})
        resources.XObject = pikepdf.Dictionary({str(name):xobjects[name] for name in used})
        stream.Resources = resources
        for child in resources.XObject.values():
            unclipped(child)
    unclipped(ap)
    ap.Matrix = pikepdf.Array([1, 0, 0, 1, 0, 0])
    page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Ap=ap))
    page.Contents = pdf.make_stream(f'1 0 0 1 {pad-box[0]} {pad-box[1]} cm /Ap Do'.encode())
    data = io.BytesIO(); pdf.save(data); pdf.close()
    return pymupdf.open(stream=data.getvalue(), filetype='pdf'), w, h, pad


def appearance_issue(obj):
    """Validate AP identity, actual advances and ink, including text hidden by clipping."""
    cap = str(obj.get('/MK', {}).get('/CA', ''))
    if not cap:
        return None
    try:
        _authored_caption(cap)
        normal = _normal(obj)
        if any(key not in ('/N','/D','/R') or not isinstance(state,pikepdf.Stream) for key,state in obj.AP.items()):
            return 'unsupported named/dictionary caption appearance states'
        if SOURCE in obj:
            return 'caption appearance is pending repair'
        box = [float(v) for v in normal.BBox]
        rect = [float(v) for v in obj.Rect]
        if list(normal.get('/Matrix', [1,0,0,1,0,0])) != [1,0,0,1,0,0] or box[:2] != [0,0] or abs(box[2]-(rect[2]-rect[0])) > .01 or abs(box[3]-(rect[3]-rect[1])) > .01:
            return 'appearance and widget geometry differ'
        doc, w, h, pad = _probe(normal, text_only=True)
        try:
            page = doc[0]
            # LF is the only supported wrapping normalization. All other
            # whitespace remains significant, including extractor-added spaces.
            if page.get_text().rstrip('\n').replace('\n', ' ') != cap.replace('\n', ' '):
                return 'cached caption text does not match /MK /CA'
            for span in page.get_texttrace():
                if span['dir'] != (1., 0.) or span['type'] != 0 or span['opacity'] != 1:
                    return 'unsupported caption text transform/rendering'
                for code, glyph, origin, box in span['chars']:
                    if glyph == 0 and not chr(code).isspace():
                        return 'caption contains a missing glyph'
                    if box[0] < pad-.01 or box[2] > pad+w+.01:
                        return 'caption advance exceeds widget width'
            # The font's em box includes unused ascender/descender space. Raster
            # actual ink instead, without the AP's clipping path or BBox.
            scale = PROBE_SCALE
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=True)
            ink = [i for i, alpha in enumerate(pix.samples[pix.n-1::pix.n]) if alpha > 16]
            # One raster pixel tolerance is antialiasing, never layout padding.
            if any(i % pix.width < pad*scale-1 or i % pix.width > (pad+w)*scale+1 or i // pix.width < pad*scale-1 or i // pix.width > (pad+h)*scale+1 for i in ink):
                return 'caption ink exceeds widget rectangle'
            clipped, _, _, _ = _probe(normal, text_only=True, remove_clip=False)
            try:
                visible = clipped[0].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=True)
                if any(a-b > 32 for a,b in zip(pix.samples[pix.n-1::pix.n], visible.samples[visible.n-1::visible.n])):
                    return 'caption ink is hidden by appearance clipping'
            finally:
                clipped.close()
        finally:
            doc.close()
        for key, state in obj.AP.items():
            if key != '/N':
                candidate = pikepdf.Dictionary(obj); candidate.AP = pikepdf.Dictionary(N=state)
                issue = appearance_issue(candidate)
                if issue: return f'{key}: {issue}'
    except (ValueError, pikepdf.PdfError, RuntimeError, AttributeError, TypeError) as exc:
        return str(exc)
    return None


def _make_caption(pdf, obj, fonts, source):
    # Restore the source temporarily in a separate dictionary for support checks.
    check = pikepdf.Dictionary(obj); check.AP = pikepdf.Dictionary(N=source)
    _simple(check, source)
    probe, w, h, pad = _probe(source)
    try:
        spans = probe[0].get_texttrace()
    finally:
        probe.close()
    if not spans or len({(round(s['size'], 3), s['font'], s['color'], s['dir']) for s in spans}) != 1:
        raise CaptionAppearanceError('mixed or absent source caption style is unsupported')
    style = spans[0]
    if style['dir'] != (1., 0.) or style['type'] != 0 or style['opacity'] != 1:
        raise CaptionAppearanceError('transformed source text is unsupported')
    role = 'bold' if 'bold' in style['font'].lower() else 'regular'
    if 'italic' in style['font'].lower() or 'oblique' in style['font'].lower():
        role = 'bold_italic' if role == 'bold' else 'italic'
    font = pymupdf.Font(fontfile=fonts[role])
    text = _authored_caption(str(obj.MK.CA))
    if any(unicodedata.combining(c) or unicodedata.bidirectional(c) in ('R','AL','AN') for c in text):
        raise CaptionAppearanceError('caption shaping is unsupported')
    for c in text:
        if not c.isspace() and not font.has_glyph(ord(c), fallback=False):
            raise CaptionAppearanceError(f'target caption font lacks U+{ord(c):04X}')
    fs = style['size']
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            if font.text_length(word, fontsize=fs) > w+.01:
                raise CaptionAppearanceError('caption word exceeds widget width at source font size')
            candidate = line+' '+word if line else word
            if line and font.text_length(candidate, fontsize=fs) > w+.01:
                lines.append(line); line = word
            else:
                line = candidate
        lines.append(line)
    # Fit actual glyph ink vertically; never reduce the authored source size.
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    bounds = []
    with TTFont(fonts[role]) as tt:
        cmap, glyphs = tt.getBestCmap(), tt.getGlyphSet()
        unit = fs / tt['head'].unitsPerEm
        for c in text:
            if c.isspace(): continue
            if ord(c) not in cmap:
                raise CaptionAppearanceError(f'target caption font lacks U+{ord(c):04X}')
            pen = BoundsPen(glyphs); glyphs[cmap[ord(c)]].draw(pen)
            if pen.bounds: bounds.append(pen.bounds)
    top = min((-b[3]*unit for b in bounds), default=0)
    bottom = max((-b[1]*unit for b in bounds), default=0)
    leading = fs*1.2
    ink_height = bottom-top+(len(lines)-1)*leading
    if ink_height > h+.01:
        raise CaptionAppearanceError('caption lines exceed widget height at source font size')
    baseline = (h-ink_height)/2-top
    target = pymupdf.open(); page = target.new_page(width=w, height=h)
    writer = pymupdf.TextWriter(page.rect)
    left = min(c[2][0]-pad for s in spans for c in s['chars']) < .1
    for i, line in enumerate(lines):
        x = 0 if left else (w-font.text_length(line, fontsize=fs))/2
        writer.append((x, baseline+i*leading), line, font=font, fontsize=fs)
    writer.write_text(page, color=style['color'])
    data = target.tobytes(); target.close()
    with pikepdf.open(io.BytesIO(data)) as rendered:
        # MuPDF's reverse cmap may choose soft hyphen for the hyphen glyph.
        # Map precisely the authored characters before validating extraction.
        mapping = {}
        for c in text:
            if c in '\r\n': continue
            gid = font.has_glyph(ord(c), fallback=False)
            if gid in mapping and mapping[gid] != c:
                raise CaptionAppearanceError('caption characters share an ambiguous glyph mapping')
            mapping[gid] = c
        from retypeset import _override_block
        for resource in rendered.pages[0].Resources.Font.values():
            tu = resource.get('/ToUnicode')
            if tu is not None:
                cmap = tu.read_bytes(); end = cmap.rfind(b'endcmap')
                resource.ToUnicode = rendered.make_stream(cmap[:end] + _override_block(mapping) + cmap[end:])
        caption = pdf.copy_foreign(rendered.pages[0].as_form_xobject())
    chrome = pdf.make_stream(pikepdf.unparse_content_stream([(a,o) for a,o in pikepdf.parse_content_stream(source) if str(o) not in SHOW]))
    for key in ('/Type','/Subtype','/BBox','/Matrix','/Resources','/FormType'):
        if key in source: chrome[key] = source[key]
    composite = pdf.make_stream(b'q /Chrome Do Q q /Caption Do Q')
    composite.Type = pikepdf.Name('/XObject'); composite.Subtype = pikepdf.Name('/Form')
    composite.BBox = pikepdf.Array([0,0,w,h])
    composite.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Chrome=chrome, Caption=caption))
    candidate = pikepdf.Dictionary(obj); del candidate[SOURCE]
    candidate.AP = pikepdf.Dictionary(N=composite)
    issue = appearance_issue(candidate)
    if issue: raise CaptionAppearanceError(issue)
    return composite


def repair_captions(path, fonts):
    """Atomically install every staged caption or leave the input untouched."""
    with pikepdf.open(path) as pdf:
        pending = []
        for page in pdf.pages:
            for obj in page.get('/Annots', []):
                if SOURCE in obj:
                    try:
                        states = {key: _make_caption(pdf, obj, fonts, source) for key, source in obj[SOURCE].items()}
                        pending.append((obj, pikepdf.Dictionary(states)))
                    except Exception as exc:
                        # Any unsupported font/parser/rendering failure is a
                        # refusal. No partially repaired PDF reaches the caller.
                        raise CaptionAppearanceError(f'{Field(obj).name}: {exc}') from exc
        if not pending: return 0
        for obj, states in pending:
            obj.AP = states; del obj[SOURCE]
        with tempfile.TemporaryDirectory(dir=Path(path).resolve().parent, prefix='.captions-') as tmp:
            staged = Path(tmp)/'captions.pdf'
            pdf.save(staged, encryption=True if pdf.is_encrypted else False)
            pdf.close()
            os.replace(staged, path)
    return len(pending)
