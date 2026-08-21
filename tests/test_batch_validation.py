import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_patient_batch import comparison_complete, validate_bundle


class BatchValidationTests(unittest.TestCase):
    def test_comparison_key_order_does_not_matter(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparison.json"
            payload = {
                "GA": {"downsampled": False, "criteria": [{}] * 10},
                "expert": {"downsampled": False, "criteria": [{}] * 10},
            }
            path.write_text(json.dumps(payload))
            self.assertTrue(comparison_complete(path, False))

    def test_incomplete_comparison_is_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparison.json"
            path.write_text('{"expert":')
            self.assertFalse(comparison_complete(path, False))

    def test_validation_reports_missing_ga_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "ga": root / "ga.json",
                "down": root / "down.json",
                "full": root / "full.json",
                "pdf": root / "figure.pdf",
            }
            paths["ga"].write_text(json.dumps({"patient": "Lung_Patient_3"}))
            with self.assertRaisesRegex(RuntimeError, "missing required keys"):
                validate_bundle("Lung_Patient_3", paths)


if __name__ == "__main__":
    unittest.main()
