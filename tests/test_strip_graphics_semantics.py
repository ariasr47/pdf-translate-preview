"""Text removal must preserve subsequent vector painting, or refuse the PDF."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pikepdf
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pdf-translate' / 'scripts'))
import strip_text


def make_source(path, content, depth=0, split=False):
    with pikepdf.new() as pdf:
        page = pdf.add_blank_page(page_size=(300, 200))
        resources = pikepdf.Dictionary(
            Font=pikepdf.Dictionary(F1=pikepdf.Dictionary(
                Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1,
                BaseFont=pikepdf.Name.Helvetica)),
            ExtGState=pikepdf.Dictionary(GS=pikepdf.Dictionary(
                Type=pikepdf.Name.ExtGState, ca=0.6, CA=0.7)))
        for _ in range(depth):
            form = pdf.make_stream(content)
            form.Type = pikepdf.Name.XObject
            form.Subtype = pikepdf.Name.Form
            form.BBox = pikepdf.Array([0, 0, 300, 200])
            form.Resources = resources
            resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Form=form))
            content = b'/Form Do'
        page.Resources = resources
        if split:
            left, right = content.split(b'(Contact form)', 1)
            page.Contents = pikepdf.Array([
                pdf.make_stream(left), pdf.make_stream(b'(Contact form)' + right)])
        else:
            page.Contents = pdf.make_stream(content)
        pdf.save(path)


class StripGraphicsSemanticsTests(unittest.TestCase):
    def test_later_paint_keeps_colors_width_dash_and_opacity(self):
        # Deleting state-setting operators inside BT makes these vectors change.
        cases = [
            b'0 0 0 rg 0 0 0 RG',
            b'0.3 g 0.6 G',
            b'0 1 1 0 k 1 0 0 0 K',
            b'/DeviceRGB cs 0.2 0.4 0.6 sc /DeviceRGB CS 0.7 0.1 0.2 SC',
            b'0 0 0 rg 0 0 0 RG 5 w 1 J 2 j [4 2] 0 d /GS gs',
        ]
        for depth in (0, 2):
            for state in cases:
                with self.subTest(depth=depth, state=state), tempfile.TemporaryDirectory() as tmp:
                    src, dst = Path(tmp) / 'source.pdf', Path(tmp) / 'stripped.pdf'
                    make_source(src, b'q 1 1 1 rg 1 1 1 RG BT /F1 16 Tf '
                                + state + b' 40 160 Td (Contact form) Tj ET '
                                b'40 80 12 12 re f 70 80 m 110 100 l 150 80 l S Q', depth)
                    strip_text.strip_text(str(src), str(dst))
                    with pymupdf.open(src) as before, pymupdf.open(dst) as after:
                        self.assertIn('Contact form', before[0].get_text())
                        self.assertEqual(after[0].get_text(), '')
                        clip = pymupdf.Rect(30, 95, 160, 130)
                        a = before[0].get_pixmap(clip=clip, alpha=False)
                        b = after[0].get_pixmap(clip=clip, alpha=False)
                        self.assertTrue(any(x < 240 for x in a.samples))
                        self.assertEqual(a.samples, b.samples)

    def test_text_object_can_span_page_content_streams(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / 'source.pdf', Path(tmp) / 'stripped.pdf'
            make_source(src, b'BT /F1 16 Tf 0.2 g 40 160 Td (Contact form) Tj ET '
                        b'40 80 12 12 re f', split=True)
            strip_text.strip_text(str(src), str(dst))
            with pymupdf.open(dst) as doc:
                self.assertEqual(doc[0].get_text(), '')
                self.assertAlmostEqual(doc[0].get_drawings()[0]['fill'][0], 0.2, places=5)

    def test_refuses_clipping_modes_in_pages_and_nested_forms_without_output(self):
        for depth in (0, 2):
            for mode in (4, 5, 6, 7):
                with self.subTest(depth=depth, mode=mode), tempfile.TemporaryDirectory() as tmp:
                    src, dst = Path(tmp) / 'source.pdf', Path(tmp) / 'stripped.pdf'
                    make_source(src, b'BT /F1 16 Tf ' + str(mode).encode()
                                + b' Tr 40 160 Td (Contact form) Tj ET 0 0 300 200 re f', depth)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        rc = strip_text.main([str(src), str(dst)])
                    self.assertNotEqual(rc, 0, output.getvalue())
                    self.assertIn('clipping', output.getvalue().lower())
                    self.assertFalse(dst.exists())

    def test_refuses_malformed_text_structure_and_render_modes(self):
        for content in (b'BT BT ET ET', b'ET', b'BT', b'(orphan) Tj',
                        b'BT 9 Tr ET', b'BT 1.5 Tr ET', b'BT /Bad Tr ET',
                        b'BT Tr ET'):
            with self.subTest(content=content), pikepdf.new() as pdf:
                with self.assertRaises(ValueError):
                    strip_text.strip_ops(pdf.make_stream(content), pdf)

    def test_all_show_operators_removed_and_nonclipping_modes_supported(self):
        for mode in (0, 1, 2, 3):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                src, dst = Path(tmp) / 'source.pdf', Path(tmp) / 'stripped.pdf'
                make_source(src, b'BT /F1 16 Tf 20 TL 40 180 Td '
                            + str(mode).encode() + b' Tr (one) Tj [(two) 20] TJ '
                            b"(three) ' 1 2 (four) \" ET")
                strip_text.strip_text(str(src), str(dst))
                with pymupdf.open(dst) as doc:
                    self.assertEqual(doc[0].get_text(), '')


if __name__ == '__main__':
    unittest.main()
