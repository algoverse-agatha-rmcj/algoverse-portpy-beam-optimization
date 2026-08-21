import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommittedResultTests(unittest.TestCase):
    def test_solve_time_summaries_use_mean_not_median(self):
        ga_paths = ROOT.glob("results/*/ga_runs/*_ga_downsampled_seed_0.json")
        summaries = []
        for ga_path in ga_paths:
            summary = json.loads(ga_path.read_text()).get("solve_time_s")
            if summary is not None:
                summaries.append(summary)
                self.assertIn("mean_s", summary)
                self.assertNotIn("median_s", summary)
        self.assertGreater(len(summaries), 0)

    def test_patients_2_through_6_have_complete_consistent_bundles(self):
        for number in range(2, 7):
            with self.subTest(patient=number):
                patient = f"Lung_Patient_{number}"
                root = ROOT / "results" / patient
                ga_path = root / "ga_runs" / f"{patient}_ga_downsampled_seed_0.json"
                ga = json.loads(ga_path.read_text())

                self.assertEqual(ga["patient"], patient)
                self.assertEqual(len(ga["history"]), ga["gens"])
                self.assertNotIn(36, ga["pool"])
                self.assertNotIn(36, ga["best_angles"])

                current_plan = "GA_B_no180" if number == 2 else "GA"
                for resolution, downsampled in (("downsampled", True),
                                                ("full_resolution", False)):
                    comparison_path = (
                        root / "clinical_comparison"
                        / f"{patient}_clinical_metrics_{resolution}.json"
                    )
                    comparison = json.loads(comparison_path.read_text())
                    self.assertIn("expert", comparison)
                    self.assertIn(current_plan, comparison)
                    self.assertEqual(comparison[current_plan]["beams"], ga["best_angles"])
                    self.assertEqual(
                        {plan["downsampled"] for plan in comparison.values()},
                        {downsampled},
                    )
                    self.assertTrue(all(len(plan["criteria"]) >= 10
                                        for plan in comparison.values()))

                pdf_path = root / "figures" / f"{patient}_DVH_clinical_metrics.pdf"
                self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))
                self.assertTrue((root / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
