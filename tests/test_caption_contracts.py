"""Caption regressions with an invented test font; no font/PDF assets distributed.

The rectangle glyphs exercise mechanics, not typography or linguistic quality.
"""
from pathlib import Path
import sys
import tempfile
import unittest
import pikepdf
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1] if (HERE.parents[1]/'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0,str(ROOT/'pdf-translate/scripts'))
import caption_appearances as captions


def toy_font(path):
    codepoints=list(range(32,127))+[241]
    names=['.notdef']+[f'u{n:04X}' for n in codepoints]
    builder=FontBuilder(1000,isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap({n:f'u{n:04X}' for n in codepoints})
    glyphs={}
    for name in names:
        pen=TTGlyphPen(None)
        if name!='u0020':
            pen.moveTo((50,0));pen.lineTo((450,0));pen.lineTo((450,700));pen.lineTo((50,700));pen.closePath()
        glyphs[name]=pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name:(500,0) for name in names})
    builder.setupHorizontalHeader(ascent=800,descent=-200)
    builder.setupNameTable({'familyName':'Invented Regression','styleName':'Regular','uniqueFontIdentifier':'InventedRegression-Regular','fullName':'Invented Regression Regular','psName':'InventedRegression-Regular'})
    builder.setupOS2(sTypoAscender=800,sTypoDescender=-200,usWinAscent=800,usWinDescent=200)
    builder.setupPost();builder.save(path)


def staged(path, target):
    with pikepdf.new() as pdf:
        page=pdf.add_blank_page(page_size=(300,200))
        font=pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Font'),Subtype=pikepdf.Name('/Type1'),BaseFont=pikepdf.Name('/Helvetica')))
        normal=pdf.make_stream(b'BT /F 9 Tf 5 8 Td (Print) Tj ET')
        normal.Type=pikepdf.Name('/XObject');normal.Subtype=pikepdf.Name('/Form');normal.BBox=[0,0,100,22]
        normal.Resources=pikepdf.Dictionary(Font=pikepdf.Dictionary(F=font))
        obj=pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Annot'),Subtype=pikepdf.Name('/Widget'),FT=pikepdf.Name('/Btn'),Ff=65536,T=pikepdf.String('PrintButton'),Rect=[20,20,120,42],MK=pikepdf.Dictionary(CA=pikepdf.String('Print')),AP=pikepdf.Dictionary(N=normal),A=pikepdf.Dictionary(S=pikepdf.Name('/URI'),URI=pikepdf.String('https://example.org/'))))
        page.Annots=[obj];pdf.Root.AcroForm=pikepdf.Dictionary(Fields=[obj])
        captions.stage_caption(pdf,obj,target);pdf.save(path)


class CaptionContracts(unittest.TestCase):
    def test_cached_unicode_caption_and_action_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);font=base/'toy.ttf';toy_font(font)
            pdf=base/'staged.pdf';staged(pdf,'Español')
            self.assertEqual(captions.repair_captions(pdf,{role:str(font) for role in ('regular','bold','italic','bold_italic')}),1)
            with pikepdf.open(pdf) as doc:
                obj=doc.pages[0].Annots[0]
                self.assertIsNone(captions.appearance_issue(obj))
                self.assertEqual(str(obj.MK.CA),'Español')
                self.assertEqual(str(obj.A.URI),'https://example.org/')
                self.assertEqual(list(obj.Rect),[20,20,120,42])

    def test_expansion_refusal_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);font=base/'toy.ttf';toy_font(font)
            pdf=base/'staged.pdf';staged(pdf,'W'*100);before=pdf.read_bytes()
            with self.assertRaises(captions.CaptionAppearanceError):
                captions.repair_captions(pdf,{role:str(font) for role in ('regular','bold','italic','bold_italic')})
            self.assertEqual(pdf.read_bytes(),before)

if __name__=='__main__':unittest.main()
