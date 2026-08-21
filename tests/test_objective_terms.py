import unittest

from scripts.objective_terms import (
    active_objective_specs,
    serialize_objective_terms,
)


class ObjectiveTermTests(unittest.TestCase):
    def test_matches_portpy_term_order_and_skips_missing_structures(self):
        configured = [
            {
                "type": "quadratic-underdose",
                "structure_name": "PTV",
                "dose_gy": 60,
                "weight": 100,
            },
            {
                "type": "quadratic",
                "structure_name": "HEART",
                "weight": 2,
            },
            {"type": "smoothness-quadratic", "weight": 0.1},
            {"type": "future-portpy-type", "weight": 9},
        ]
        active = active_objective_specs(
            configured,
            structure_names={"PTV", "HEART"},
            nonempty_structures={"PTV"},
        )

        self.assertEqual([row["config_index"] for row in active], [0, 2])
        rows = serialize_objective_terms(active, [4.5, 0.25])
        self.assertEqual(rows[0]["structure_name"], "PTV")
        self.assertEqual(rows[0]["dose_gy"], 60)
        self.assertEqual(rows[1]["type"], "smoothness-quadratic")
        self.assertEqual(sum(row["value"] for row in rows), 4.75)

    def test_rejects_term_count_mismatch(self):
        with self.assertRaisesRegex(ValueError, "metadata has 1 terms"):
            serialize_objective_terms(
                [{"config_index": 0, "type": "quadratic"}], []
            )


if __name__ == "__main__":
    unittest.main()
