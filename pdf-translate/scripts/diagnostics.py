"""Read-only failure guidance and basic form accessibility inventory.

Neither command repairs PDFs, runs document actions, nor grants delivery approval.
"""
import argparse
import json
from pathlib import Path
import re

import pikepdf
import pymupdf
from acroform import Field
from provenance import sha256

GUIDANCE = (
    ('font', ('cannot draw', 'glyph', 'font coverage'),
     'Choose a licensed font covering the listed code points; prepare page subsets and retain a full field font. Do not delete or substitute characters to hide missing glyphs.'),
    ('layout', ('scaled below', 'overflow', 'scaled runs'),
     'Inspect the named page and box. Reword only without changing meaning, or author a reviewed paragraph merge. Rebuild; do not lower thresholds globally.'),
    ('caption', ('caption', 'appearance'),
     'Inspect the named widget, target caption and cached appearance. Preserve actions and field geometry. Use supported caption rendering; do not flatten the form or remove the field.'),
    ('metadata', ('metadata', '/title', 'bookmark'),
     'Compare the authored title, locale and bookmark targets against source/output metadata. Preserve identifiers deliberately and retain bookmark destinations.'),
    ('identifier', ('identifier', 'protected-data', 'write/find/say'),
     'Compare the exact protected source and target spans, including numbers and URL query values. Correct unintended edits; document only narrow, reviewed exceptions.'),
    ('mapping', ('target', 'mapping', 'null'),
     'Inspect translations.json and the matching occurrence ID in segments.json. Author missing targets in context, then run qa and rebuild.'),
    ('source-language', ('untranslated', 'source-script'),
     'Review each retained phrase against the source. Translate accidental leftovers; explicitly document genuine names or operational identifiers rather than disabling leak checks.'),
    ('structure', ('structural', 'field parity', 'export parity'),
     'Compare original and output field occurrences, rectangles, flags and export values. Repair the transformation while preserving source field identity.'),
    ('input', ('input policy', 'scanned', 'invisible text', 'ocr'),
     'Recheck whether this input belongs to the supported born-digital route. Stop this route for scans or unsupported active content; use a separately scoped workflow.'),
)


def diagnose(log):
    issues = []
    for line in log.splitlines():
        if line.startswith(('FAIL', '!!', 'ERROR')):
            category, step = 'unknown', 'Inspect this stage and its complete log. Do not discard an unfamiliar failure or treat partial output as final.'
            for name, patterns, action in GUIDANCE:
                if any(pattern in line.lower() for pattern in patterns):
                    category, step = name, action
                    break
            issues.append({'category': category, 'message': line, 'evidence': [], 'next_step': step})
        elif issues and line[:1].isspace():
            issues[-1]['evidence'].append(line.strip())
    return {'schema_version': '1.0', 'status': 'analysis_complete',
            'delivery_decision': 'unchanged', 'issues': issues,
            'evidence_is_untrusted_data': True,
            'page_numbering': 'Retained exactly as emitted by the originating stage.',
            'limitation': 'This parses explicit failure lines; no failures found is not a successful verification receipt.'}


def audit_form(path):
    """Inventory mechanics; descriptive labels/order/usability require a person/viewer."""
    findings, fields, pages = [], [], []
    def add(code, detail, page=None, field=None):
        findings.append({'code': code, 'severity': 'review', 'page': page, 'field': field, 'detail': detail})
    with pikepdf.open(path) as pdf:
        lang = str(pdf.Root.get('/Lang', ''))
        if not lang.strip(): add('document-language', 'No catalog /Lang; determine and set the correct document locale.')
        if '/StructTreeRoot' not in pdf.Root:
            add('untagged-document', 'No structure tree. Reading order and PDF/UA conformance are not established.')
        acro = pdf.Root.get('/AcroForm')
        for number, page in enumerate(pdf.pages, 1):
            tabs = str(page.obj.get('/Tabs', 'unspecified'))
            page_fields = []
            for annot in page.obj.get('/Annots', []):
                if annot.get('/Subtype') != pikepdf.Name('/Widget'): continue
                resolved = Field(annot, acro)
                label = str(resolved.get('/TU', '') or '')
                name = resolved.name
                kind = str(resolved.get('/FT', ''))
                flags = int(resolved.get('/Ff', 0) or 0)
                role = {'/Tx':'text', '/Sig':'signature'}.get(kind, 'unknown')
                if kind == '/Btn':
                    role = 'pushbutton' if flags & (1 << 16) else 'radio' if flags & (1 << 15) else 'checkbox'
                if kind == '/Ch': role = 'combo' if flags & (1 << 17) else 'list'
                caption = str(annot.get('/MK', {}).get('/CA', '') or '')
                accessible_name_candidate = caption if role == 'pushbutton' else label
                if not name: add('field-name', 'Widget has no resolved field name.', number, name)
                if not accessible_name_candidate.strip(): add('field-label-review', 'No alternate label (or pushbutton caption); inspect the accessible name in a screen reader.', number, name)
                if kind not in ('/Tx','/Ch','/Btn','/Sig'): add('field-role', 'Unrecognized or missing field type.', number, name)
                if '/AP' not in annot: add('field-appearance', 'No cached appearance; viewer rendering needs verification.', number, name)
                row = {'page': number, 'name': name, 'alternate_label': label,
                       'pdf_type': kind, 'role': role, 'accessible_name_candidate': accessible_name_candidate,
                       'flags': flags, 'read_only': bool(flags & 1),
                       'required': bool(flags & 2), 'has_value': resolved.get('/V') is not None,
                       'rect': [float(n) for n in annot.get('/Rect', [])]}
                fields.append(row);page_fields.append(name)
            pages.append({'page': number, 'tab_order': tabs, 'annotation_field_order': page_fields})
            if page_fields: add('keyboard-order', f'Tab policy {tabs}; test actual focus order, focus visibility and all controls in a native viewer.', number)
    with pymupdf.open(path) as doc:
        visible_text_pages = sum(bool(page.get_text().strip()) for page in doc)
        rotated = any(page.rotation for page in doc)
    # Screening narrows trials, not qualification. It deliberately makes no pixel/OCR assertion.
    reasons = []
    if not 1 <= len(pages) <= 5: reasons.append('outside 1–5 page trial limit')
    if len(fields) > 50: reasons.append('more than 50 widget occurrences')
    if visible_text_pages != len(pages): reasons.append('one or more pages lack extractable text')
    if rotated: reasons.append('rotated page')
    if any(f['pdf_type'] == '/Sig' for f in fields): reasons.append('signature field')
    return {'schema_version':'1.0', 'source_sha256':sha256(path), 'status':'inventory_complete',
            'accessibility_conformance':'not_established', 'manual_review':'required',
            'document_language':lang, 'fields':fields, 'pages':pages, 'findings':findings,
            'trial_screen': {'status':'outside_proposed_limits' if reasons else 'within_basic_limits',
                             'reasons':reasons, 'qualification':'not_established'},
            'limits':['No screen-reader or native viewer execution.',
                      'Extractable text is not proof of visible born-digital content.',
                      'Labels, reading order, contrast, actions, scripts and translation accuracy need separate checks.',
                      'Current field contents are intentionally not copied into this report.']}


def write_report(path, report, inputs=()):
    path = Path(path)
    if path.exists() or path.is_symlink(): raise FileExistsError('Choose a new report path; existing inputs/evidence are preserved.')
    if any(path.resolve() == Path(item).resolve() for item in inputs):
        raise ValueError('Report aliases an input.')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('diagnose','audit-form'))
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        report=(diagnose(args.input.read_text(encoding='utf-8-sig'))
                if args.mode=='diagnose' else audit_form(args.input))
        if args.mode=='diagnose':report['log_sha256']=sha256(args.input)
        if args.output:write_report(args.output,report,[args.input])
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,pikepdf.PdfError) as exc:
        print(f'FAIL diagnostic inventory: {exc}')
        return 2

if __name__=='__main__':raise SystemExit(main())
