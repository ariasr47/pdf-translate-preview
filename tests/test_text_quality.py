"""Portable regressions for authored-text diagnostics and font comparisons."""
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1] if (HERE.parents[1] / 'pdf-translate').is_dir() else HERE.parents[3]
sys.path.insert(0, str(ROOT / 'pdf-translate' / 'scripts'))
import font_audit
import extract_segments
import qa_check
import retypeset
import strip_text


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_font(path, chars):
    glyph_order = ['.notdef'] + [f'u{ord(ch):04X}' for ch in chars]
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)
        if name != '.notdef':
            pen.moveTo((80, 0)); pen.lineTo((80, 700)); pen.lineTo((520, 700))
            pen.lineTo((520, 0)); pen.closePath()
        glyphs[name] = pen.glyph()
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap({ord(ch): f'u{ord(ch):04X}' for ch in chars})
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (600, 0) for name in glyph_order})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({'familyName': 'Synthetic Test', 'styleName': 'Regular'})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200,
                     usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.save(path)


class AuthoredTextDiagnosticTests(unittest.TestCase):
    def mapping(self, root, target, *, notice=False):
        conf = {'fonts': {'regular': 'face.ttf'}, 'translations': {},
                'merges': [], 'overrides': [], 'skip': []}
        segments = []
        if notice:
            conf['notices'] = [{'page': 4, 'text': target}]
        else:
            conf['translations'] = {'Source': target}
            segments = [{'id': 7, 'occurrence_id': 'p2-o3', 'page': 2,
                         'core': 'Source', 'text': 'Source'}]
        tr = root / 'translations.json'
        seg = root / 'segments.json'
        build_font(root / 'face.ttf', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -')
        tr.write_text(json.dumps(conf, ensure_ascii=False), encoding='utf-8')
        seg.write_text(json.dumps({'segments': segments}), encoding='utf-8')
        return tr, seg

    def test_qa_reports_decoded_and_edge_controls_before_source_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, '&#3;&#X03;Notice\u0085', notice=True)
            findings = qa_check.qa_check(tr, seg)
            controls = [f for f in findings if f['kind'] == 'unsupported-control']
            self.assertEqual([f['codepoint'] for f in controls], ['U+0003', 'U+0085'])
            self.assertEqual(controls[0]['occurrence_count'], 2)
            self.assertEqual([(f['channel'], f['page']) for f in controls],
                             [('notice', 4), ('notice', 4)])
            self.assertTrue(any(f['kind'] == 'source-unavailable' for f in findings))

    def test_qa_cli_prints_control_location_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, 'bad\u0003target')
            log = io.StringIO()
            with redirect_stdout(log):
                rc = qa_check.main([str(tr), '--segments', str(seg)])
            self.assertEqual(rc, 1)
            shown = log.getvalue()
            self.assertIn('U+0003', shown)
            self.assertIn('channel=segment', shown)
            self.assertIn('page=2', shown)
            self.assertIn('occurrence_id=p2-o3', shown)

    def test_controls_inside_html_comments_are_not_authored_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, 'Safe<!-- &#3; \u0004 -->text')
            findings = qa_check.qa_check(tr, seg)
            self.assertFalse([f for f in findings
                              if f['kind'] == 'unsupported-control'])

            source = root / 'source.pdf'
            stripped = root / 'stripped.pdf'
            output = root / 'output.pdf'
            with pymupdf.open() as doc:
                page = doc.new_page()
                page.insert_text((72, 72), 'Source')
                doc.save(source)
            extract_segments.extract_segments(str(source), outdir=str(root))
            strip_text.strip_text(str(source), str(stripped))
            with redirect_stdout(io.StringIO()) as log:
                rc = retypeset.retypeset(stripped, root / 'segments.json', tr, output)
            self.assertEqual(rc, 0, msg=log.getvalue())
            self.assertTrue(output.exists())
            with pymupdf.open(output) as doc:
                self.assertIn('Safetext', doc[0].get_text())

    def test_semicolonless_numeric_controls_at_eof_are_diagnosed(self):
        cases = [('Safe&#3', 'U+0003'),
                 ('Safe&#x85', 'U+0085'),
                 ('Safe&#X03', 'U+0003')]
        for target, codepoint in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                tr, seg = self.mapping(root, target)
                controls = [f for f in qa_check.qa_check(tr, seg)
                            if f['kind'] == 'unsupported-control']
                self.assertEqual([f['codepoint'] for f in controls], [codepoint])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, 'Safe&amp;#3')
            self.assertFalse([f for f in qa_check.qa_check(tr, seg)
                              if f['kind'] == 'unsupported-control'])

    def test_qa_preserves_occurrence_context_and_separates_soft_hyphen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, '\u000bZX-2048\u00ad\tjoin\n\r\u200c\u200d\u000b')
            findings = qa_check.qa_check(tr, seg)
            controls = [f for f in findings if f['kind'] == 'unsupported-control']
            self.assertEqual(len(controls), 1)
            self.assertEqual(controls[0]['codepoint'], 'U+000B')
            self.assertEqual(controls[0]['occurrence_count'], 2)
            self.assertEqual(controls[0]['occurrence_id'], 'p2-o3')
            self.assertEqual(controls[0]['page'], 2)
            shy = [f for f in findings if f['kind'] == 'soft-hyphen']
            self.assertEqual(len(shy), 1)
            self.assertEqual(shy[0]['severity'], 'warn')
            self.assertFalse(any(f.get('codepoint') in {'U+200C', 'U+200D'} for f in findings))

    def test_direct_rebuild_refuses_control_before_writing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tr, seg = self.mapping(root, 'unsafe\u0003target')
            out = root / 'out.pdf'
            log = io.StringIO()
            with redirect_stdout(log):
                rc = retypeset.retypeset(root / 'stripped.pdf', seg, tr, out)
            self.assertEqual(rc, 1)
            self.assertIn('U+0003', log.getvalue())
            self.assertIn('p2-o3', log.getvalue())
            self.assertFalse(out.exists())


class FragmentBoundaryTests(unittest.TestCase):
    def conf(self, channel, later):
        target = 'Safe<!-- unfinished' + '‖' + later
        conf = {'translations': {'Source': target}, 'fonts': {'regular': 'face.ttf'}}
        if channel == 'override':
            conf['translations'] = {'Source': None}
            conf['overrides'] = [{'page': 0, 'contains': 'Source',
                'parts': [{'text': 'Safe<!-- unfinished'}, {'text': later}]}]
        elif channel == 'notice':
            conf['translations'] = {'Source': None}
            conf['notices'] = [{'page': 0, 'text': target, 'box': [72, 120, 400, 180]}]
        elif channel == 'occurrence':
            conf['segment_targets'] = {'p0-source': target}
        return conf

    def test_independent_fragments_qa_and_early_refusal(self):
        for channel in ('override', 'segment', 'occurrence', 'notice'):
            for later in ('\u0003text', '&#3;text', '&#x03'):
                with self.subTest(channel=channel, later=later), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    with pymupdf.open() as doc:
                        doc.new_page().insert_text((72,72), 'Source'); doc.save(root/'source.pdf')
                    with redirect_stdout(io.StringIO()):
                        data = extract_segments.extract_segments(str(root/'source.pdf'), outdir=str(root))
                        strip_text.strip_text(str(root/'source.pdf'), str(root/'stripped.pdf'))
                    data['segments'][0]['occurrence_id'] = 'p0-source'
                    (root/'segments.json').write_text(json.dumps(data), encoding='utf-8')
                    build_font(root/'face.ttf', ''.join(dict.fromkeys('Safe textSource')))
                    conf = self.conf(channel, later)
                    tr = root/'translations.json'; tr.write_text(json.dumps(conf), encoding='utf-8')
                    for seg in (root/'segments.json', None) if channel != 'occurrence' else (root/'segments.json',):
                        controls = [f for f in qa_check.qa_check(tr, seg) if f['kind']=='unsupported-control']
                        self.assertEqual(len(controls), 1)
                        self.assertEqual(controls[0]['codepoint'], 'U+0003')
                        self.assertEqual(controls[0]['part_index'], 1)
                        if seg is not None:
                            self.assertEqual(controls[0]['page'], 0)
                            self.assertEqual(controls[0]['channel'], 'segment' if channel == 'occurrence' else channel)
                            if channel != 'notice':
                                self.assertEqual(controls[0]['occurrence_id'], 'p0-source')
                    before = {p: digest(p) for p in (tr, root/'source.pdf', root/'stripped.pdf')}
                    with redirect_stdout(io.StringIO()) as log:
                        rc = retypeset.retypeset(root/'stripped.pdf', root/'segments.json', tr, root/'out.pdf')
                    self.assertEqual(rc, 1, log.getvalue())
                    self.assertIn('part_index=1', log.getvalue())
                    self.assertFalse((root/'out.pdf').exists())
                    self.assertEqual(before, {p: digest(p) for p in before})

    def test_font_coverage_checks_later_fragment(self):
        for channel in ('override', 'segment', 'occurrence', 'notice'):
            with self.subTest(channel=channel), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                build_font(root/'face.ttf', ''.join(dict.fromkeys('Safe textSource')))
                (root/'translations.json').write_text(json.dumps(self.conf(channel, '気')), encoding='utf-8')
                (root/'segments.json').write_text(json.dumps({'segments': [{'id': 0, 'occurrence_id': 'p0-source', 'page':0, 'text':'Source', 'core':'Source'}]}), encoding='utf-8')
                report, _ = font_audit.audit(root, [root/'face.ttf'])
                self.assertEqual(report['candidates'][0]['status'], 'coverage_gaps')
                self.assertEqual(report['candidates'][0]['missing'][0]['codepoints'], ['U+6C17'])
                self.assertEqual(report['candidates'][0]['missing'][0]['part_index'], 1)

    def test_whole_html_and_fragment_comments_remain_comments(self):
        from text_model import effective_texts, authored_text_diagnostics
        for conf in ({'translations': {'Source': '<b>Safe</b><!-- unfinished‖\u0003'}},
                     {'merges': [{'page':0, 'lines':['Source'], 'html':'Safe<!-- unfinished‖&#3;'}]},
                     self.conf('override', 'text<!-- &#3; \u0004 -->'),
                     self.conf('notice', 'text<!-- &#3; \u0004 -->')):
            self.assertEqual(authored_text_diagnostics(effective_texts(conf)), [])
        rows = effective_texts(self.conf('override', ' \ttext\u00ad\n'))
        self.assertEqual(rows[0]['placement_targets'][1], ' \ttext\u00ad\n')
        findings = authored_text_diagnostics(rows)
        self.assertEqual([(f['kind'], f['part_index']) for f in findings], [('soft-hyphen', 1)])

    def test_renderer_precedence_and_rotated_inline_literal_path(self):
        from text_model import effective_texts, authored_text_diagnostics
        seg = {'id': 0, 'occurrence_id': 'p0-source', 'page': 0,
               'core': 'Source', 'text': 'Source', 'dir': [0, 1]}
        conf = {'translations': {'Source': '<b>Safe</b><!--‖\u0003'}}
        rows = effective_texts(conf, [seg])
        self.assertEqual(rows[0]['placement_targets'], [conf['translations']['Source']])
        self.assertEqual(authored_text_diagnostics(rows)[0]['codepoint'], 'U+0003')
        conf['segment_targets'] = {'p0-source': 'Good'}
        self.assertEqual(authored_text_diagnostics(effective_texts(conf, [seg])), [])
        conf['overrides'] = [{'page': 0, 'contains': 'Source', 'parts': [{'text': '\u0004'}]}]
        self.assertEqual(authored_text_diagnostics(effective_texts(conf, [seg]))[0]['codepoint'], 'U+0004')
        conf['skip'] = ['Source']
        self.assertEqual(effective_texts(conf, [seg]), [])
        conf['merges'] = [{'page': 0, 'lines': ['Source'], 'html': 'Good<!--‖\u0003'}]
        rows = effective_texts(conf, [seg])
        self.assertEqual([r['channel'] for r in rows], ['merge'])
        self.assertEqual(authored_text_diagnostics(rows), [])

    def test_candidate_does_not_split_whole_html_comments(self):
        from text_model import effective_texts
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'face.ttf'; build_font(path, 'Safe')
            font = pymupdf.Font(fontfile=str(path))
            for conf in ({'translations': {'Source':'<b>Safe</b><!--‖気'}},
                         {'merges':[{'page':0,'lines':['Source'],'html':'Safe<!--‖気'}]}):
                self.assertEqual(font_audit._coverage(font, effective_texts(conf)), [])


class CandidateFontAuditTests(unittest.TestCase):
    def make_job(self, root):
        configured = root / 'configured.ttf'
        latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -'
        build_font(configured, latin)
        candidate = root / 'candidate.ttf'
        build_font(candidate, latin + '気')
        (root / 'translations.json').write_text(json.dumps({
            'fonts': {'regular': 'configured.ttf'},
            'translations': {'Name': 'ZX-2048 気'},
        }, ensure_ascii=False), encoding='utf-8')
        (root / 'segments.json').write_text(json.dumps({'segments': [{
            'id': 1, 'occurrence_id': 'p0-name', 'page': 0,
            'core': 'Name', 'text': 'Name',
        }]}), encoding='utf-8')
        return configured, candidate

    def test_candidate_compares_full_mixed_script_text_without_changing_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            configured, candidate = self.make_job(root)
            before = {p: digest(p) for p in (configured, candidate,
                                              root / 'translations.json', root / 'segments.json')}
            old = Path.cwd()
            try:
                os.chdir(root)
                report, inputs = font_audit.audit(root, ['candidate.ttf'])
            finally:
                os.chdir(old)
            self.assertEqual(report['status'], 'coverage_gaps')
            self.assertEqual(report['faces'][0]['missing'][0]['codepoints'], ['U+6C17'])
            self.assertEqual(report['candidates'][0]['status'], 'codepoints_covered')
            self.assertEqual(report['candidates'][0]['missing'], [])
            self.assertIn(candidate.resolve(), [Path(p).resolve() for p in inputs])
            self.assertEqual(before, {p: digest(p) for p in before})

    def test_candidate_is_an_input_and_cannot_be_the_report_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, candidate = self.make_job(root)
            before = digest(candidate)
            old = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(io.StringIO()):
                    rc = font_audit.main(['--work', str(root), '--candidate',
                                          'candidate.ttf', '--output', 'candidate.ttf'])
            finally:
                os.chdir(old)
            self.assertEqual(rc, 2)
            self.assertEqual(digest(candidate), before)


if __name__ == '__main__':
    unittest.main()
