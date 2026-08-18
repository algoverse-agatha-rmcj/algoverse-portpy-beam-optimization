import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_patient_batch import (
    comparison_complete,
    ga_complete,
    valid_patient,
    validate_bundle,
)


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
                validate_bundle("Lung_Patient_3", paths, set())



class PatientSelectionTests(unittest.TestCase):
    def test_catalogue_range_is_accepted(self):
        for patient in ("Lung_Patient_2", "Lung_Patient_15", "Lung_Patient_20",
                        "Lung_Patient_202"):
            with self.subTest(patient=patient):
                self.assertTrue(valid_patient(patient))

    def test_patients_outside_the_catalogue_are_rejected(self):
        for patient in ("Lung_Patient_1", "Lung_Patient_203", "Lung_Patient_",
                        "Prostate_Patient_15", "Lung_Patient_15x", ""):
            with self.subTest(patient=patient):
                self.assertFalse(valid_patient(patient))

    def test_ga_checkpoint_must_belong_to_the_requested_patient(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ga.json"
            payload = {
                "patient": "Lung_Patient_15",
                "gens": 40,
                "history": [0.0] * 40,
                "pool": [0, 3, 6],
                "best_angles": [0, 3, 6],
            }
            path.write_text(json.dumps(payload))
            self.assertTrue(ga_complete(path, "Lung_Patient_15", set()))
            self.assertFalse(ga_complete(path, "Lung_Patient_16", set()))


if __name__ == "__main__":
    unittest.main()
