"""Regression contracts for the experimental simple-form milestone."""
import sys, unittest
from pathlib import Path
import pymupdf
HERE=Path(__file__).resolve()
ROOT=HERE.parents[1] if (HERE.parents[1]/'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0,str(ROOT/'pdf-translate/scripts'))
import verify, qa_check

class MetadataContracts(unittest.TestCase):
    def docs(self, title='Form W-4', outline='Schedule A'):
        src, dst = pymupdf.open(), pymupdf.open()
        self.addCleanup(src.close); self.addCleanup(dst.close)
        for doc in (src,dst):
            doc.new_page(); doc.set_metadata({'title':title}); doc.set_toc([[1,outline,1]])
        return src,dst

    def test_explicit_identity_metadata_is_valid(self):
        src,dst=self.docs()
        self.assertEqual(verify.document_metadata_misses(src,dst,{'translations':{'Form W-4':'Form W-4','Schedule A':'Schedule A'}}),[])

    def test_wrong_target_and_missing_outline_are_rejected(self):
        src,dst=self.docs();dst.set_metadata({'title':'Unrelated title'});dst.set_toc([])
        misses=verify.document_metadata_misses(src,dst,{'translations':{'Form W-4':'Formulario W-4','Schedule A':'Anexo A'}})
        self.assertEqual({kind for kind,_ in misses},{'title','outline'})

    def test_target_also_source_key_is_not_misclassified(self):
        src,dst=self.docs(outline='First');dst.set_toc([[1,'Second',1]])
        self.assertEqual(verify.document_metadata_misses(src,dst,{'translations':{'First':'Second','Second':'Tercero'}}),[])

class DataContracts(unittest.TestCase):
    def test_accented_source_words_are_complete(self):
        words=verify.source_words_from_text('Complete información médica mañana',set())
        self.assertIn('información',words);self.assertNotIn('informaci',words)
        self.assertTrue(verify.scan_leaks('información médica mañana',set(),source_words=words)[0])

    def test_url_sentence_punctuation_is_review_not_data_loss(self):
        findings=qa_check.check_pair('Read https://example.org/help.', 'Consulte https://example.org/help !',set(),'Latin')
        self.assertFalse([f for f in findings if f['kind']=='protected-data' and f['severity']=='error'])
        self.assertTrue([f for f in findings if f['kind']=='url-punctuation' and f['severity']=='warn'])

    def test_changed_url_queries_still_fail(self):
        for source,target in [('https://example.org?a=1.','https://example.org?a=1'),('https://example.org/help','https://evil.org/help')]:
            findings=qa_check.check_pair(source,target,set(),'Latin')
            self.assertTrue([f for f in findings if f['kind']=='protected-data' and f['severity']=='error'])

if __name__=='__main__':unittest.main()
