"""Portable lifecycle, input-refusal, and ActualText regressions."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pikepdf
import pymupdf

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1] if (HERE.parents[1] / 'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0, str(ROOT / 'pdf-translate' / 'scripts'))
import pipeline
import extract_segments
import strip_text
import verify
from test_caption_contracts import toy_font


def source_pdf(path, rotation=0, inherited=False):
    with pikepdf.new() as pdf:
        page = pdf.add_blank_page(page_size=(300, 200))
        page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(
            F1=pikepdf.Dictionary(Type=pikepdf.Name.Font,
                                  Subtype=pikepdf.Name.Type1,
                                  BaseFont=pikepdf.Name.Helvetica)))
        page.Contents = pdf.make_stream(b'BT /F1 14 Tf 40 150 Td (Hello world) Tj ET')
        if rotation:
            if inherited:
                page.obj.Parent.Rotate = rotation
            else:
                page.Rotate = rotation
        pdf.save(path)


class PublicLifecycleTests(unittest.TestCase):
    def test_init_rebuild_finish_with_generated_font(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.pdf'
            source_pdf(source)
            font = root / 'font.ttf'
            toy_font(font)
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(pipeline.main(['init', str(source), '--work', str(root)]), 0)
                self.assertEqual(pipeline.main(['from-cores', '--work', str(root)]), 0)
            mapping_path = root / 'translations.json'
            mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
            mapping['lang'] = 'es-US'
            mapping['fonts'] = {role: font.name for role in
                                ('regular', 'bold', 'italic', 'bold_italic')}
            mapping['translations']['Hello world'] = 'Hola mundo'
            mapping_path.write_text(json.dumps(mapping), encoding='utf-8')
            intermediate = root / 'intermediate.pdf'
            final = root / 'final.pdf'
            with redirect_stdout(out):
                self.assertEqual(pipeline.main(['rebuild', str(source), str(intermediate),
                                                '--work', str(root)]), 0)
                self.assertEqual(pipeline.main(['finish', str(source), str(intermediate),
                                                str(font), str(final),
                                                str(root / 'comparison.html')]), 0)
            self.assertTrue(final.is_file(), out.getvalue())
            self.assertEqual(json.loads((root / 'delivery.json').read_text())['status'],
                             'review_required')

    def test_arabic_shaping_gate_ignores_actualtext_substitution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'actualtext.pdf'
            with pikepdf.new() as pdf:
                page = pdf.add_blank_page(page_size=(200, 100))
                page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(
                    F1=pikepdf.Dictionary(Type=pikepdf.Name.Font,
                                          Subtype=pikepdf.Name.Type1,
                                          BaseFont=pikepdf.Name.Helvetica)))
                page.Contents = pdf.make_stream(
                    b'/Span << /ActualText ' + pikepdf.String('\ufe89\ufe8f\ufe95').unparse() +
                    b' >> BDC BT /F1 12 Tf 20 60 Td (abc) Tj ET EMC')
                pdf.save(path)
            with pymupdf.open(path) as doc:
                default = ''.join(c['c'] for block in doc[0].get_text(
                    'rawdict', flags=pymupdf.TEXTFLAGS_RAWDICT)['blocks']
                    for line in block.get('lines', []) for span in line['spans']
                    for c in span['chars'])
                ignored = ''.join(c['c'] for block in doc[0].get_text(
                    'rawdict', flags=(pymupdf.TEXTFLAGS_RAWDICT |
                                      pymupdf.TEXT_IGNORE_ACTUALTEXT))['blocks']
                    for line in block.get('lines', []) for span in line['spans']
                    for c in span['chars'])
                self.assertEqual(default, '\ufe89\ufe8f\ufe95')
                self.assertEqual(ignored, 'abc')
                self.assertEqual(verify.unshaped_arabic_pages(doc), ([], False))


class InputRefusalTests(unittest.TestCase):
    def test_rotation_refusal_is_clean_in_extract_and_verify_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_pdf(root / 'source.pdf', 90, True)
            for action in (
                    lambda: extract_segments.main([
                        str(root / 'source.pdf'), '--outdir', str(root / 'extract')]),
                    lambda: verify.verify(str(root / 'source.pdf'),
                                          str(root / 'source.pdf'))):
                output = io.StringIO()
                with redirect_stdout(output):
                    rc = action()
                self.assertNotEqual(rc, 0)
                self.assertIn('rotat', output.getvalue().lower())
                self.assertNotIn('traceback', output.getvalue().lower())
                self.assertNotIn('PASS text layer is visible', output.getvalue())

    def test_quarter_turn_pages_refuse_before_output(self):
        for rotation in (90, 180, 270):
            for inherited in (False, True):
                with self.subTest(rotation=rotation, inherited=inherited), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source, output = root / 'source.pdf', root / 'output.pdf'
                    source_pdf(source, rotation, inherited)
                    with self.assertRaisesRegex(strip_text.StripGraphicsError, 'rotat'):
                        strip_text.strip_text(source, output)
                    self.assertFalse(output.exists())

    def test_password_failure_is_clean_at_cli_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plain, protected = root / 'plain.pdf', root / 'protected.pdf'
            source_pdf(plain)
            with pikepdf.open(plain) as pdf:
                pdf.save(protected, encryption=pikepdf.Encryption(
                    owner='owner-secret', user='user-secret', R=6))
            for argv in ([str(protected), str(root / 'stripped.pdf')],
                         ['init', str(protected), '--work', str(root / 'job')]):
                output = io.StringIO()
                with redirect_stdout(output):
                    rc = strip_text.main(argv) if len(argv) == 2 else pipeline.main(argv)
                self.assertEqual(rc, 2)
                self.assertIn('password', output.getvalue().lower())
                self.assertNotIn('traceback', output.getvalue().lower())


if __name__ == '__main__':
    unittest.main()
