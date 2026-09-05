"""Portable regressions for the public source preview.

The fixture is generated in a temporary directory. No PDF or font bytes live
in the repository.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1] if (HERE.parents[1] / "pdf-translate").is_dir() else HERE.parents[3]
SCRIPTS = ROOT / "pdf-translate" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import acroform  # noqa: E402


def load_generator():
    path = HERE.with_name("make_regression_fixture.py")
    spec = importlib.util.spec_from_file_location("public_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.source = self.work / "simple-form.pdf"
        load_generator().build(self.source)

    def test_field_exports_and_occurrences_are_stable(self):
        rows = acroform.field_records(self.source)
        choice = next(row for row in rows if row["name"] == "contact_method")
        self.assertEqual(choice["exports"], [("string", "456d61696c"), ("string", "50686f6e65")])
        repeated = [row for row in rows if row["name"] == "applicant_name" and row["widget"]]
        self.assertEqual([row["pages"] for row in repeated], [[0], [1]])
        self.assertEqual(acroform.structural_misses(self.source, self.source), [])

    def test_extraction_maps_repeated_labels_and_document_strings(self):
        out = self.work / "extract"
        command = [sys.executable, str(SCRIPTS / "extract_segments.py"),
                   str(self.source), "--outdir", str(out)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        translation = json.loads((out / "to_translate.json").read_text(encoding="utf-8"))
        labels = [row for row in translation["occurrences"] if row["source"] == "Applicant name:"]
        self.assertEqual([row["occurrence_id"] for row in labels], ["p0:s1", "p1:s0"])
        self.assertEqual([row["page"] for row in labels], [0, 1])
        cores = {row["text"] for row in translation["cores"]}
        self.assertIn("Public regression form", cores)
        self.assertIn("Application", cores)


if __name__ == "__main__":
    unittest.main()
