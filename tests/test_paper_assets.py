import csv
import io
import unittest
from pathlib import Path

from scripts.analyze_cohort import load_cohort, summarize
from scripts.generate_paper_assets import render_csv, render_latex, render_svg


ROOT = Path(__file__).resolve().parents[1]


class PaperAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = summarize(load_cohort(ROOT / "results"))

    def test_table_uses_verified_mean_values(self):
        rows = list(csv.DictReader(io.StringIO(render_csv(self.summary))))
        left_lung = next(row for row in rows if row["metric"] == "Left-lung maximum")
        self.assertAlmostEqual(float(left_lung["delta"]), 9.012878, places=6)
        self.assertNotIn("median", render_latex(self.summary).lower())
        self.assertIn("12/17", render_latex(self.summary))
        self.assertIn("10.14\\%", render_latex(self.summary))

    def test_svg_contains_every_patient_and_outlier_labels(self):
        svg = render_svg(self.summary)
        self.assertEqual(svg.count('<rect class="win"'), 13)  # 12 bars + legend
        self.assertEqual(svg.count('<rect class="loss"'), 6)  # 5 bars + legend
        self.assertIn(">P14</text>", svg)
        self.assertIn(">P17</text>", svg)
        self.assertIn("Mean 10.14%", svg)


if __name__ == "__main__":
    unittest.main()
