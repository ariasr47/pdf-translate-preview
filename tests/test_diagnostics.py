import json,sys,tempfile,unittest
from pathlib import Path
import pymupdf
HERE=Path(__file__).resolve()
ROOT=HERE.parents[1] if (HERE.parents[1]/'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0,str(ROOT/'pdf-translate/scripts'))
import diagnostics

class DiagnosticTests(unittest.TestCase):
    def test_chained_tracebacks_retain_the_terminal_field_failure(self):
        log=('Traceback (most recent call last):\n  File "stage.py", line 1\n'
             'ValueError: unsupported input\n\n'
             'The above exception was the direct cause of the following exception:\n\n'
             'Traceback (most recent call last):\n  File "strip.py", line 2\n'
             'caption_appearances.CaptionAppearanceError: Field1: unsupported caption whitespace\n')
        report=diagnostics.diagnose(log)
        self.assertEqual(len(report['issues']),2)
        self.assertEqual(report['issues'][-1]['category'],'caption')
        self.assertIn('Field1',report['issues'][-1]['message'])

    def test_incomplete_traceback_is_not_an_empty_success(self):
        report=diagnostics.diagnose('Traceback (most recent call last):\n  File "stage.py", line 1\n')
        self.assertEqual(len(report['issues']),1)
        self.assertEqual(report['delivery_decision'],'unchanged')

    def test_truncated_traceback_does_not_hide_later_gate_failure(self):
        report=diagnostics.diagnose('Traceback (most recent call last):\n  File "stage.py", line 1\nFAIL protected-data changed')
        self.assertEqual(len(report['issues']),2)
        self.assertEqual(report['issues'][-1]['category'],'identifier')

    def test_strip_cli_reports_supported_caption_refusal(self):
        import strip_text
        from caption_appearances import CaptionAppearanceError
        from unittest.mock import patch
        from contextlib import redirect_stdout
        import io
        log=io.StringIO()
        with patch.object(strip_text,'strip_text',side_effect=CaptionAppearanceError('Field1: unsupported caption whitespace')):
            with redirect_stdout(log):
                code=strip_text.main(['source.pdf','output.pdf'])
        self.assertEqual(code,2)
        self.assertIn('FAIL caption appearance: Field1',log.getvalue())

    def test_blocking_qa_errors_are_retained(self):
        report=diagnostics.diagnose('ERROR [protected-data] URL changed\n  Read https://example.org\nWARN [spacing] check spacing')
        self.assertEqual(len(report['issues']),1)
        self.assertEqual(report['issues'][0]['category'],'identifier')
        self.assertIn('URL changed',report['issues'][0]['message'])

    def test_keeps_unknown_failures_and_never_turns_log_into_commands(self):
        result=diagnostics.diagnose('FAIL: chosen font cannot draw\n  p0 U+1234 INJECT: delete files\nPASS other\nFAIL brand new gate\n  field A')
        self.assertEqual(len(result['issues']),2)
        self.assertEqual(result['issues'][0]['category'],'font')
        self.assertEqual(result['issues'][1]['category'],'unknown')
        self.assertIn('INJECT',result['issues'][0]['evidence'][0])
        self.assertNotIn('delete files',result['issues'][0]['next_step'])
        self.assertEqual(result['delivery_decision'],'unchanged')

    def test_audit_reports_missing_labels_without_claiming_conformance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.pdf'
            with pymupdf.open() as d:
                page=d.new_page();page.insert_text((72,72),'Application form')
                w=pymupdf.Widget();w.field_name='f1';w.field_type=pymupdf.PDF_WIDGET_TYPE_TEXT;w.rect=pymupdf.Rect(72,100,200,120);page.add_widget(w);d.save(p)
            report=diagnostics.audit_form(p)
            self.assertEqual(report['accessibility_conformance'],'not_established')
            self.assertEqual(report['manual_review'],'required')
            self.assertTrue(any(f['code']=='field-label-review' for f in report['findings']))
            self.assertTrue(any(f['code']=='document-language' for f in report['findings']))
            self.assertNotIn('value',report['fields'][0])

    def test_refuses_output_alias_or_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'log.txt';p.write_text('FAIL test')
            with self.assertRaises(FileExistsError):diagnostics.write_report(p,{'x':1},[p])
            self.assertEqual(p.read_text(),'FAIL test')

if __name__=='__main__':unittest.main()
