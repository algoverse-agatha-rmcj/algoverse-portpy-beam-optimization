"""The clinical_compare timing contract: schema 2 times MOSEK, schema 1 timed the pipeline."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from timing import TIMING_SCHEMA, is_true_solve_time, timing_label


class TestTimingSchema(unittest.TestCase):
    def test_legacy_entry_is_not_called_a_solve_time(self):
        legacy = {"solve_time_s": 923.7}
        self.assertFalse(is_true_solve_time(legacy))
        label = timing_label(legacy)
        self.assertIn("Pipeline", label)
        self.assertIn("setup", label)
        self.assertNotIn("MOSEK", label)

    def test_schema_2_entry_is_a_solve_time(self):
        current = {"timing_schema": TIMING_SCHEMA, "solve_time_s": 6.4,
                   "setup_time_s": 21.0, "total_time_s": 27.4}
        self.assertTrue(is_true_solve_time(current))
        self.assertIn("MOSEK", timing_label(current))

    def test_prefix_keeps_the_acronym_intact(self):
        current = {"timing_schema": TIMING_SCHEMA, "solve_time_s": 6.4}
        self.assertEqual(timing_label(current, prefix="Full-resolution "),
                         "Full-resolution MOSEK solve time")

    def test_committed_bundles_declare_their_schema_consistently(self):
        import json
        for path in sorted((ROOT / "results").glob(
                "Lung_Patient_*/clinical_comparison/*_clinical_metrics_*.json")):
            data = json.loads(path.read_text())
            for name, entry in data.items():
                if "solve_time_s" not in entry:
                    continue
                if is_true_solve_time(entry):
                    self.assertLessEqual(
                        entry["solve_time_s"], entry["total_time_s"] + 1e-6,
                        f"{path.name}:{name} solve time exceeds its total")
                    self.assertAlmostEqual(
                        entry["setup_time_s"] + entry["solve_time_s"],
                        entry["total_time_s"], delta=0.151,
                        msg=f"{path.name}:{name} setup + solve != total")


if __name__ == "__main__":
    unittest.main()
