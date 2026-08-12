import unittest

from scripts.metric_ranking import select_best_plans


class MetricRankingTests(unittest.TestCase):
    plans = ["expert", "GA"]

    def test_organ_at_risk_prefers_lower_value(self):
        row = {"label": "HEART mean", "goal": 20, "limit": 27,
               "values": {"expert": 10.92, "GA": 11.78}}
        self.assertEqual(select_best_plans(row, self.plans), {"expert"})

    def test_ptv_prefers_value_closest_to_goal(self):
        row = {"label": "PTV max", "goal": 66, "limit": 69,
               "values": {"expert": 68.08, "GA": 68.00}}
        self.assertEqual(select_best_plans(row, self.plans), {"GA"})

    def test_ptv_rejects_value_above_limit(self):
        row = {"label": "PTV max", "goal": 66, "limit": 69,
               "values": {"expert": 69.01, "GA": 65.0}}
        self.assertEqual(select_best_plans(row, self.plans), {"GA"})

    def test_all_tied_is_left_unmarked(self):
        row = {"label": "CORD max", "goal": 48, "limit": 50,
               "values": {"expert": 28.420, "GA": 28.425}}
        self.assertEqual(select_best_plans(row, self.plans), set())

    def test_missing_value_is_left_unmarked(self):
        row = {"label": "CORD max", "goal": 48, "limit": 50,
               "values": {"expert": 28.42, "GA": None}}
        self.assertEqual(select_best_plans(row, self.plans), set())


if __name__ == "__main__":
    unittest.main()
