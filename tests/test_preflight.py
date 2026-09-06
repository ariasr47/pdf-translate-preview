import io,json,sys,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
import pikepdf,pymupdf
HERE=Path(__file__).resolve()
ROOT=HERE.parents[1] if (HERE.parents[1]/'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0,str(ROOT/'pdf-translate/scripts'))
import input_policy,font_audit,pipeline

class PreflightTests(unittest.TestCase):
    def make_pdf(self, path, change):
        with pikepdf.new() as pdf:
            pdf.add_blank_page();change(pdf);pdf.save(path)

    def test_malformed_acroform_and_init_concise_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            for n,value in enumerate((42,pikepdf.Array([1]))):
                path=Path(tmp)/f'{n}.pdf'
                self.make_pdf(path,lambda p:setattr(p.Root,'AcroForm',value))
                with self.assertRaisesRegex(ValueError,'AcroForm must be a dictionary'):
                    input_policy.inventory(path)
                log=io.StringIO()
                with redirect_stdout(log):
                    rc=pipeline.cmd_init([str(path),'--work',str(Path(tmp)/f'job{n}')])
                self.assertEqual(rc,2);self.assertNotIn('Traceback',log.getvalue())
                self.assertFalse((Path(tmp)/f'job{n}'/'stripped.pdf').exists())
                self.assertFalse((Path(tmp)/f'job{n}'/'preflight.json').exists())

    def test_wide_primitive_array_hits_work_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'wide.pdf'
            self.make_pdf(path,lambda p:setattr(p.Root,'Wide',pikepdf.Array(range(10000))))
            with self.assertRaisesRegex(ValueError,'work budget'):
                input_policy.inventory(path,max_objects=50)

    def test_wide_dictionary_refused_before_items_materialization(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'wide-dict.pdf'
            self.make_pdf(path,lambda p:setattr(p.Root,'Wide',pikepdf.Dictionary({f'/K{i}':i for i in range(1000)})))
            original=input_policy._dictionary_children
            def guarded(obj,where,depth):
                self.assertLess(len(obj.stream_dict) if isinstance(obj,pikepdf.Stream) else len(obj),1000)
                return original(obj,where,depth)
            with patch.object(input_policy,'_dictionary_children',side_effect=guarded):
                with self.assertRaisesRegex(ValueError,'work budget'):
                    input_policy.inventory(path,max_objects=50)

    def test_depth_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'deep.pdf'
            def change(pdf):
                node=pdf.Root
                for _ in range(30):
                    child=pdf.make_indirect(pikepdf.Dictionary());node.Next=child;node=child
            self.make_pdf(path,change)
            with self.assertRaisesRegex(ValueError,'depth budget'):
                input_policy.inventory(path,max_depth=10)

    def test_cycles_shared_nodes_and_action_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cycle.pdf'
            def change(pdf):
                action=pdf.make_indirect(pikepdf.Dictionary(S=pikepdf.Name('/JavaScript')))
                action.Next=action;pdf.Root.OpenAction=action
                pdf.Root.Shared=pikepdf.Array([action]*20)
            self.make_pdf(path,change)
            report=input_policy.inventory(path,max_objects=100)
            self.assertEqual([a['type'] for a in report['actions']],['/JavaScript'])

    def job(self,tmp):
        path=Path(tmp)
        (path/'face.ttf').write_bytes(pymupdf.Font('helv').buffer)
        conf={'fonts':{'regular':'face.ttf'},'translations':{'Name':'Nombre'},
              'segment_targets':{'1':'気'},'notices':[{'text':'Hello','page':0}]}
        (path/'translations.json').write_text(json.dumps(conf),encoding='utf-8')
        (path/'segments.json').write_text(json.dumps({'segments':[{'id':1,'page':0,'core':'Name','text':'Name'}]}))
        return path,conf

    def test_effective_targets_context_and_mapping_relative_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,_=self.job(tmp);report,_=font_audit.audit(path)
            self.assertEqual(report['status'],'coverage_gaps')
            self.assertEqual(report['faces'][0]['missing'],[{'channel':'segment','segment_id':1,'page':0,'codepoints':['U+6C17']}])
            self.assertTrue(report['advisory']);self.assertEqual(report['delivery_decision'],'unchanged')
            with redirect_stdout(io.StringIO()):self.assertEqual(font_audit.main(['--work',tmp]),1)

    def test_merge_override_skip_and_notice_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,conf=self.job(tmp)
            segments=[{'id':i,'page':0,'core':str(i),'text':str(i)} for i in range(1,4)]
            conf.update(translations={'1':'気','2':'気','3':'気'},segment_targets={},
                        merges=[{'page':0,'lines':['1'],'html':'Hello'}],
                        overrides=[{'page':0,'contains':'2','parts':[{'text':'気'}]}],
                        skip=['3'],notices=[{'page':0,'text':'気'}])
            (path/'translations.json').write_text(json.dumps(conf))
            (path/'segments.json').write_text(json.dumps({'segments':segments}))
            report,_=font_audit.audit(path)
            self.assertEqual([r['channel'] for r in report['faces'][0]['missing']],['override','notice'])

    def test_missing_and_corrupt_fonts_are_input_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,conf=self.job(tmp)
            (path/'corrupt.ttf').write_bytes(b'not a font')
            for filename in ('missing.ttf','corrupt.ttf'):
                with self.subTest(font=filename):
                    conf['fonts']['regular']=filename
                    (path/'translations.json').write_text(json.dumps(conf))
                    output=path/'new-report.json';log=io.StringIO()
                    with redirect_stdout(log):
                        rc=font_audit.main(['--work',tmp,'--output',str(output)])
                    self.assertEqual(rc,2)
                    self.assertIn('FAIL advisory font audit: Cannot load font role regular',log.getvalue())
                    self.assertNotIn('Traceback',log.getvalue())
                    self.assertFalse(output.exists())

    def test_malformed_json_roots_and_containers_are_input_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,conf=self.job(tmp)
            cases=[([],[]), (None,[]), (conf,{}), (conf,None),
                   (conf,[None]), (conf,[{'id':1,'page':0,'core':[], 'text':'x'}]),
                   ({**conf,'translations':[]},[]),
                   ({**conf,'merges':['invalid']},[]),
                   ({**conf,'overrides':[{'page':0,'contains':'x','parts':['invalid']}]},[]),
                   ({**conf,'notices':'invalid'},[])]
            for mapping,segments in cases:
                with self.subTest(mapping=mapping,segments=segments):
                    (path/'translations.json').write_text(json.dumps(mapping))
                    (path/'segments.json').write_text(json.dumps(segments))
                    output=path/'new-report.json';log=io.StringIO()
                    with redirect_stdout(log):
                        rc=font_audit.main(['--work',tmp,'--output',str(output)])
                    self.assertEqual(rc,2)
                    self.assertIn('FAIL advisory font audit:',log.getvalue())
                    self.assertNotIn('Traceback',log.getvalue())
                    self.assertFalse(output.exists())

    def test_clean_coverage_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,conf=self.job(tmp);conf['segment_targets']={}
            mapping=path/'translations.json';mapping.write_text(json.dumps(conf))
            before=mapping.read_bytes()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(font_audit.main(['--work',tmp,'--output',str(path/'report.json')]),0)
                self.assertEqual(font_audit.main(['--work',tmp,'--output',str(mapping)]),2)
                self.assertEqual(font_audit.main(['--work',tmp,'--output',str(path/'report.json')]),2)
            self.assertEqual(mapping.read_bytes(),before)

if __name__=='__main__':unittest.main()
