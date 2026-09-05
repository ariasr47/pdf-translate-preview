#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf-translate final stage: make text TYPED INTO form fields render.

A translated form whose fields still declare a Latin default appearance will
store what a user types and display nothing (or tofu) in most viewers. Values
survive; the rendering is what breaks — easy to miss if you only test with
ASCII, so test with real target-script input.

What this does:
  1. embeds a FULL-coverage target-script font (NOT the translation subset —
     users type arbitrary names containing characters the document never used)
  2. registers it in /AcroForm /DR /Font, creating /DR and /Font if absent
     (many forms ship a /DA referencing /Helv with no /DR at all)
  3. rewrites every text AND choice field's /DA to that font, preserving the
     original size (a combo box renders its selection from /DA the same way a
     text field renders a typed value)
  4. adds /Helv and /ZaDb alongside it: NeedAppearances makes viewers rebuild
     appearance streams, and a rebuilt checkbox draws its tick from ZapfDingbats
  5. sets an AcroForm-level /DA fallback; for choice forms caches validated
     display-label appearances and clears /NeedAppearances so their logical
     export /V is not mistakenly rendered as the visible label

Checkbox /DA entries are deliberately left alone — their appearance streams are
self-contained and carry their own ZapfDingbats resource.

Usage: python3 field_fonts.py IN.pdf FULL_FONT.ttf OUT.pdf [--name TransFF]
"""
import os
import re
import sys
import tempfile
from pathlib import Path
from acroform import Field, iter_fields
from provenance import disjoint_files

import pikepdf
import pymupdf


class ChoiceAppearanceError(ValueError):
    """The renderer could not faithfully cache a choice's display labels."""


def _appearance_text(appearance):
    """Extract the actual normal appearance in isolation from page labels."""
    with pikepdf.new() as probe:
        box = [float(x) for x in appearance.get('/BBox', [0, 0, 1, 1])]
        page = probe.add_blank_page(page_size=(max(1, box[2]-box[0]), max(1, box[3]-box[1])))
        ap = probe.copy_foreign(appearance)
        # Matrix affects annotation placement, not its local text identity.
        ap.Matrix = pikepdf.Array([1, 0, 0, 1, 0, 0])
        page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Ap=ap))
        page.Contents = probe.make_stream(b'/Ap Do')
        import io
        data = io.BytesIO()
        probe.save(data)
        with pymupdf.open(stream=data.getvalue(), filetype='pdf') as doc:
            return doc[0].get_text()


def _cache_choice_appearances(pdf, tmp):
    """Synthesize display-valued widgets in a disposable copy; copy AP only.

    The real field dictionaries, values, exports, indices and chrome are never
    rewritten. MuPDF's raw resynthesis avoids Widget.update's font/DA edits.
    """
    choices = []
    for pno, page in enumerate(pdf.pages):
        for ano, obj in enumerate(page.get('/Annots', [])):
            field = Field(obj)
            if obj.get('/Subtype') != pikepdf.Name('/Widget') or field.get('/FT') != pikepdf.Name('/Ch'):
                continue
            options = field.get('/Opt', [])
            labels = [(str(x[0]), str(x[1])) if isinstance(x, pikepdf.Array)
                      else (str(x), str(x)) for x in options]
            flags = int(field.get('/Ff', 0))
            combo = bool(flags & (1 << 17))
            if not combo and int(field.get('/TI', 0)) != 0:
                raise ChoiceAppearanceError(f'{field.name}: scrolling listbox appearances are not supported')
            value = field.get('/V')
            values = list(value) if isinstance(value, pikepdf.Array) else ([] if value is None else [value])
            displays = [dict(labels).get(str(v), str(v)) for v in values]
            if combo and len(displays) > 1:
                raise ChoiceAppearanceError(f'{field.name}: combo has multiple selected values')
            choices.append((pno, ano, field.name, combo, labels, displays))
    cached_captions = any(
        Field(obj).get('/FT') == pikepdf.Name('/Btn')
        and int(Field(obj).get('/Ff', 0)) & (1 << 16)
        and isinstance(obj.get('/AP', {}).get('/N'), pikepdf.Stream)
        for page in pdf.pages for obj in page.get('/Annots', []))
    if not choices and not cached_captions:
        return
    missing_text = []
    for pno, page in enumerate(pdf.pages):
        for ano, obj in enumerate(page.get('/Annots', [])):
            field = Field(obj)
            if obj.get('/Subtype') == pikepdf.Name('/Widget') and field.get('/FT') == pikepdf.Name('/Tx') and '/AP' not in obj:
                missing_text.append((pno, ano, field.name, str(field.get('/V', ''))))
    source = str(Path(tmp).with_name('appearance-source.pdf'))
    rendered = str(Path(tmp).with_name('appearance-rendered.pdf'))
    pdf.save(source, encryption=True if pdf.is_encrypted else False)
    with pikepdf.open(source, allow_overwriting_input=True) as staged:
        for pno, ano, name, combo, labels, displays in choices:
            obj = staged.pages[pno].Annots[ano]
            # Flatten effective attributes only in the disposable renderer copy:
            # list synthesis does not reliably inherit /Opt through widget kids.
            field = Field(obj)
            for key in ('/FT', '/Ff', '/DA', '/TI', '/I'):
                value = field.get(key)
                if value is not None:
                    obj[key] = value
            if not combo and field.get('/I') is None:
                original = field.get('/V')
                selected = list(original) if isinstance(original, pikepdf.Array) else ([] if original is None else [original])
                obj.I = pikepdf.Array([i for i, (export, _) in enumerate(labels)
                                      if export in {str(v) for v in selected}])
            obj.Opt = pikepdf.Array([pikepdf.String(label) for _, label in labels])
            if displays:
                obj.V = pikepdf.String(displays[0]) if combo or len(displays) == 1 else pikepdf.Array(displays)
            if '/AP' in obj:
                del obj.AP
        staged.save(source, encryption=True if staged.is_encrypted else False)
    with pymupdf.open(source) as doc:
        for page in doc:
            for widget in page.widgets():
                if widget.field_type in (pymupdf.PDF_WIDGET_TYPE_COMBOBOX, pymupdf.PDF_WIDGET_TYPE_LISTBOX, pymupdf.PDF_WIDGET_TYPE_TEXT):
                    annot = widget._annot.this
                    pymupdf.mupdf.pdf_annot_request_resynthesis(annot)
                    pymupdf.mupdf.pdf_update_annot(annot)
        doc.save(rendered, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    with pikepdf.open(rendered) as staged:
        for pno, ano, name, combo, labels, displays in choices:
            normal = staged.pages[pno].Annots[ano].get('/AP', {}).get('/N')
            if not isinstance(normal, pikepdf.Stream):
                raise ChoiceAppearanceError(f'{name}: renderer did not produce a normal appearance')
            text = ' '.join(_appearance_text(normal).split())
            required = displays if combo else [label for _, label in labels]
            if combo and text != ' '.join(' '.join(label.split()) for label in displays):
                raise ChoiceAppearanceError(f'{name}: cached combo text does not match its display value')
            # Listbox scrolling is supported only if the renderer actually
            # includes every label. Refuse clipped/unsupported caches explicitly.
            for label in required:
                if label.strip() and ' '.join(label.split()) not in text:
                    raise ChoiceAppearanceError(f'{name}: display label cannot be faithfully cached: {label!r}')
            pdf.pages[pno].Annots[ano].AP = pikepdf.Dictionary(N=pdf.copy_foreign(normal))
        for pno, ano, name, value in missing_text:
            normal = staged.pages[pno].Annots[ano].get('/AP', {}).get('/N')
            if not isinstance(normal, pikepdf.Stream):
                raise ChoiceAppearanceError(f'{name}: missing text appearance could not be cached')
            if value.strip() and ' '.join(value.split()) not in ' '.join(_appearance_text(normal).split()):
                raise ChoiceAppearanceError(f'{name}: text value cannot be faithfully cached')
            pdf.pages[pno].Annots[ano].AP = pikepdf.Dictionary(N=pdf.copy_foreign(normal))
    pdf.Root.AcroForm.NeedAppearances = False


def field_fonts(inp, font, out, name='TransFF'):
    """Embed a full-coverage field font and rewrite text-field /DA. Returns 0."""
    if not disjoint_files([inp, font], [out]):
        raise ValueError("field-font output aliases an input")
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        raise ValueError('font resource name must be a simple PDF name')
    with tempfile.TemporaryDirectory(prefix='.field-font-', dir=Path(out).resolve().parent) as staging:
        return _field_fonts(inp, font, out, name, str(Path(staging)/'with-font.pdf'))


def _field_fonts(inp, font, out, name, tmp):
    doc = pymupdf.open(inp)
    try:
        doc[0].insert_font(fontname='TransFieldFont', fontfile=font)
        doc.save(tmp, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    finally:
        doc.close()

    pdf = pikepdf.open(tmp)
    try:
        fobj = pdf.pages[0].Resources.Font.TransFieldFont

        if '/AcroForm' not in pdf.Root:
            print('no /AcroForm — nothing to do (non-form PDF); copying through')
            pdf.save(out, encryption=True if pdf.is_encrypted else False)
            return 0
        af = pdf.Root.AcroForm

        if '/DR' not in af:
            af.DR = pdf.make_indirect(pikepdf.Dictionary())
        if '/Font' not in af.DR:
            af.DR.Font = pdf.make_indirect(pikepdf.Dictionary())

        # register under EXACTLY the name the /DA strings will reference — a
        # mismatch here leaves every /DA pointing at a resource that does not
        # exist, which renders as nothing while every structural check still
        # passes
        af.DR.Font[pikepdf.Name('/' + name)] = fobj

        for nm, base in (('/Helv', '/Helvetica'), ('/ZaDb', '/ZapfDingbats')):
            if pikepdf.Name(nm) not in af.DR.Font:
                extra = ({'Encoding': pikepdf.Name('/WinAnsiEncoding')}
                         if nm == '/Helv' else {})
                af.DR.Font[pikepdf.Name(nm)] = pdf.make_indirect(pikepdf.Dictionary(
                    Type=pikepdf.Name('/Font'), Subtype=pikepdf.Name('/Type1'),
                    BaseFont=pikepdf.Name(base), **extra))

        # Snapshot inherited appearance before changing ancestor dictionaries.
        text_fields = [(f.obj, str(f.get('/DA', ''))) for f in iter_fields(pdf)
                       if f.get('/FT') in (pikepdf.Name('/Tx'), pikepdf.Name('/Ch'))]
        count = len(text_fields)
        for obj, da in text_fields:
            match = re.search(r'/\S+\s+([\d.]+)\s+Tf', da)
            size = match.group(1) if match else '0'
            obj.DA = pikepdf.String(f'/{name} {size} Tf 0 g')

        af.DA = pikepdf.String(f'/{name} 0 Tf 0 g')
        af.NeedAppearances = True
        _cache_choice_appearances(pdf, tmp)
        pdf.save(out, encryption=True if pdf.is_encrypted else False)
    finally:
        pdf.close()

    print(f'registered /{name} in /DR, rewrote /DA on {count} text and '
          f'choice field objects -> {out}')
    if count == 0:
        print('  (no text or choice fields found — checkboxes and buttons '
              'are unaffected by design)')
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    inp, font, out = argv[0], argv[1], argv[2]
    name = (argv[argv.index('--name') + 1]
            if '--name' in argv else 'TransFF')
    return field_fonts(inp, font, out, name=name)


if __name__ == '__main__':
    raise SystemExit(main())
