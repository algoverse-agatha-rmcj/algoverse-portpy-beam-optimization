import json
import tempfile
import unittest
from pathlib import Path

from scripts.analyze_cohort import load_cohort, render_markdown, summarize


ROOT = Path(__file__).resolve().parents[1]


def write_patient(root, number, expert_objective, ga_objective, expert_d95, ga_d95):
    patient = f"Lung_Patient_{number}"
    patient_root = root / patient
    comparison_root = patient_root / "clinical_comparison"
    ga_root = patient_root / "ga_runs"
    comparison_root.mkdir(parents=True)
    ga_root.mkdir(parents=True)
    criterion = {
        "label": "LUNG_L max",
        "value": 10.0,
        "unit": "Gy",
        "pass_limit": True,
    }
    payload = {
        "expert": {
            "objective": expert_objective,
            "PTV_D95_Gy": expert_d95,
            "criteria": [criterion, {**criterion, "goal": 20}],
        },
        "GA": {
            "objective": ga_objective,
            "PTV_D95_Gy": ga_d95,
            "criteria": [{**criterion, "value": 12.0}],
        },
    }
    comparison_path = (
        comparison_root / f"{patient}_clinical_metrics_full_resolution.json"
    )
    comparison_path.write_text(json.dumps(payload))
    (ga_root / f"{patient}_ga_downsampled_seed_0.json").write_text(json.dumps({
        "pop": 20,
        "wall_time_s": 100.0,
        "history": [{"gen": 0, "unique_solves": 20}],
        "solve_time_s": {
            "measured_solves": 10,
            "mean_s": 9.0,
            "p95_s": 11.0,
            "max_s": 12.0,
            "total_s": 90.0,
        },
    }))


class CohortAnalysisTests(unittest.TestCase):
    def test_uses_arithmetic_mean_and_collapses_duplicate_criteria(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_patient(root, 2, 100.0, 90.0, 59.0, 59.5)
            write_patient(root, 3, 100.0, 110.0, 60.0, 59.5)
            summary = summarize(load_cohort(root))

            self.assertEqual(summary["cohort"]["n_patients"], 2)
            self.assertEqual(summary["cohort"]["wins"], 1)
            self.assertEqual(summary["cohort"]["losses"], 1)
            self.assertEqual(summary["cohort"]["mean_objective_improvement_pct"], 0.0)
            self.assertEqual(len(summary["clinical_criteria"]), 1)
            self.assertEqual(
                summary["clinical_criteria"][0]["mean_delta_ga_minus_expert"], 2.0
            )
            self.assertEqual(summary["timing"]["pooled_mean_s"], 9.0)
            self.assertEqual(
                summary["timing"]["patients_with_full_run_wall_time"], 2
            )
            self.assertNotIn("median", json.dumps(summary).lower())

    def test_current_committed_cohort_is_complete(self):
        summary = summarize(load_cohort(ROOT / "results"))
        self.assertEqual(summary["cohort"]["n_patients"], 17)
        self.assertEqual(summary["cohort"]["wins"], 12)
        self.assertEqual(summary["cohort"]["losses"], 5)
        self.assertAlmostEqual(
            summary["cohort"]["mean_objective_improvement_pct"], 10.13778, places=6
        )
        self.assertAlmostEqual(
            summary["cohort"][
                "mean_objective_improvement_excluding_two_largest_gains_pct"
            ],
            4.881758,
            places=6,
        )
        self.assertEqual(
            len(summary["review_priorities"]["focused_patients"]), 7
        )
        self.assertEqual(
            summary["timing"]["resumed_wall_time_patients"],
            ["Lung_Patient_11"],
        )
        self.assertEqual(
            summary["timing"]["patients_with_full_run_wall_time"], 16
        )
        markdown = render_markdown(summary)
        self.assertIn("All aggregate values are arithmetic means", markdown)
        self.assertIn("Focused loss and outlier analysis", markdown)
        self.assertIn("P14", markdown)
        self.assertIn("P17", markdown)


if __name__ == "__main__":
    unittest.main()
