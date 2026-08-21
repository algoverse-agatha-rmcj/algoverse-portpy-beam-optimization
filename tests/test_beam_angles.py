import unittest

from scripts.beam_angles import (
    excluded_ids,
    format_angles,
    grid_pool,
)


# Patients 2-10 store beams on a 5-degree grid where beam_id * 5 == gantry angle.
LEGACY = {beam: float(beam * 5) for beam in range(72)}

# From Lung_Patient_11 on, the clinician's beams are stored first and the grid
# follows them, so the ID no longer encodes the angle. This mirrors the real
# Lung_Patient_15 layout: 7 clinician beams, then a 67-beam 5-degree grid.
CLINICIAN_FIRST = {0: 0.0, 1: 330.0, 2: 300.0, 3: 270.0, 4: 240.0, 5: 210.0, 6: 185.0}
CLINICIAN_FIRST.update({7 + step: float(step * 5) for step in range(72)})
# This reproduces the real Lung_Patient_15 offsets: 180 degrees lands on id 43 and
# id 36 - the beam the old code deleted as "180" - is actually 145 degrees.


class GridPoolTests(unittest.TestCase):
    def test_legacy_patients_get_the_documented_pool(self):
        pool = grid_pool(LEGACY)
        self.assertEqual(pool, [b for b in range(0, 72, 3) if b != 36])
        self.assertEqual(len(pool), 23)

    def test_clinician_first_patients_get_the_same_angles(self):
        pool = grid_pool(CLINICIAN_FIRST)
        angles = sorted(CLINICIAN_FIRST[b] for b in pool)
        self.assertEqual(
            angles,
            [float(a) for a in range(0, 360, 15) if a != 180],
        )
        self.assertEqual(len(pool), 23)

    def test_id_arithmetic_would_have_been_wrong(self):
        # The regression this module exists to prevent: on a clinician-first
        # patient the old pool picked angles that are not the 15-degree grid.
        old_pool = [b for b in range(0, 72, 3) if b != 36]
        old_angles = sorted(CLINICIAN_FIRST[b] for b in old_pool if b in CLINICIAN_FIRST)
        self.assertNotEqual(old_angles, [float(a) for a in range(0, 360, 15) if a != 180])

    def test_180_is_excluded_whatever_its_id(self):
        self.assertEqual(excluded_ids(LEGACY), {36})
        # 180 degrees sits at id 43 once seven clinician beams come first.
        self.assertEqual(excluded_ids(CLINICIAN_FIRST), {43})
        self.assertNotIn(43, grid_pool(CLINICIAN_FIRST))

    def test_old_hardcoded_36_would_have_dropped_the_wrong_beam(self):
        self.assertEqual(CLINICIAN_FIRST[36], 145.0)

    def test_duplicate_angles_resolve_to_the_lowest_id(self):
        # 0 degrees exists at both id 0 (clinician) and id 7 (grid).
        self.assertEqual(CLINICIAN_FIRST[0], CLINICIAN_FIRST[7])
        self.assertIn(0, grid_pool(CLINICIAN_FIRST))
        self.assertNotIn(7, grid_pool(CLINICIAN_FIRST))

    def test_off_grid_angles_are_never_in_the_pool(self):
        self.assertNotIn(6, grid_pool(CLINICIAN_FIRST))  # 185 degrees

    def test_wrapping_angles_are_normalized(self):
        self.assertEqual(grid_pool({0: 360.0, 1: 15.0}), [0, 1])
        self.assertEqual(excluded_ids({0: 540.0}), {0})


class FormatAnglesTests(unittest.TestCase):
    def test_renders_real_angles_not_id_arithmetic(self):
        self.assertEqual(format_angles(CLINICIAN_FIRST, [0, 1, 6]), "0°, 330°, 185°")

    def test_unknown_beam_is_marked_rather_than_guessed(self):
        self.assertEqual(format_angles({}, [4]), "?")


if __name__ == "__main__":
    unittest.main()
