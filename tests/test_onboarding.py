"""Execute the documented sample with a generated font; no binary assets shipped."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest

import pymupdf
from test_caption_contracts import toy_font

PUBLIC = Path(__file__).resolve().parents[1]


class OnboardingTests(unittest.TestCase):
    def test_documented_translation_and_no_overwrite(self):
        command = re.search(r'```text\n(PY examples/first_translation.py[^\n]+)\n```',
                            (PUBLIC / 'docs/QUICKSTART.md').read_text(encoding='utf-8'))
        self.assertIsNotNone(command, 'Keep the executable tutorial command documented')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            font = root / 'sample font.ttf'
            toy_font(font)
            job = root / 'first Spanish'
            replacements = {'PY': sys.executable, 'FONT': str(font), 'JOB': str(job)}
            argv = [replacements.get(arg, arg) for arg in shlex.split(command[1])]
            result = subprocess.run(argv, cwd=PUBLIC, capture_output=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads((job / 'delivery.json').read_text())['status'], 'review_required')
            with pymupdf.open(job / 'final.pdf') as doc:
                page = doc[0]
                text = page.get_text()
                self.assertIn('Taller comunitario', text)
                self.assertIn('Escriba su nombre completo abajo.', text)
                widget = next(page.widgets())
                self.assertEqual(widget.field_name, 'participant_name')
                self.assertEqual(widget.field_label, 'Nombre completo')
                widget.field_value = 'Sample Name'
                widget.update()
                doc.save(root / 'filled.pdf')
            with pymupdf.open(root / 'filled.pdf') as doc:
                self.assertEqual(next(doc[0].widgets()).field_value, 'Sample Name')
            before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in job.iterdir() if p.is_file()}
            rerun = subprocess.run(argv, cwd=PUBLIC, capture_output=True, encoding='utf-8')
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in job.iterdir() if p.is_file()})

    def test_missing_font_does_not_create_job(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run([sys.executable, str(PUBLIC / 'examples/first_translation.py'),
                                     '--font', str(root / 'missing.ttf'), '--output', str(root / 'job')],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / 'job').exists())

    def test_local_document_links(self):
        spec = importlib.util.spec_from_file_location('check_docs', PUBLIC / 'tools/check_docs.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        # The complete source export mounts runtime and licenses beside templates.
        if (PUBLIC / 'pdf-translate').is_dir():
            self.assertEqual(checker.check(PUBLIC), [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'README.md').write_text('[broken](missing.md)\n', encoding='utf-8')
            self.assertEqual(len(checker.check(root)), 1)
            (root / 'missing.md').write_text('Available\n', encoding='utf-8')
            self.assertEqual(checker.check(root), [])


if __name__ == '__main__':
    unittest.main()
