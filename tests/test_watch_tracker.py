import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from scripts import watch_patient_batch as watcher


class ComparisonProgressTests(unittest.TestCase):
    def test_counts_a_differently_named_ga_plan(self):
        # Lung_Patient_2 stores its GA plan as "GA_B_no180"; matching a literal
        # "GA" reported a finished comparison as half done.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compare.json"
            path.write_text(json.dumps({"expert": {}, "GA_B_no180": {}}))
            self.assertEqual(watcher.comparison_progress(path), 2)

    def test_counts_the_ordinary_ga_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compare.json"
            path.write_text(json.dumps({"expert": {}, "GA": {}}))
            self.assertEqual(watcher.comparison_progress(path), 2)

    def test_partial_and_unreadable_files_do_not_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compare.json"
            path.write_text(json.dumps({"expert": {}}))
            self.assertEqual(watcher.comparison_progress(path), 1)
            path.write_text("{not json")
            self.assertEqual(watcher.comparison_progress(path), 0)


class PaddingTests(unittest.TestCase):
    def test_padding_ignores_ansi_so_columns_stay_aligned(self):
        plain = watcher.pad("Patient 202", 11)
        colored = watcher.pad(watcher.colorize("Patient 202", "green", True), 11)
        self.assertEqual(watcher.visible_width(plain), 11)
        self.assertEqual(watcher.visible_width(colored), 11)

    def test_long_values_are_never_silently_cut(self):
        # The old table used fixed widths and rendered "Patient 15" as "Patient 1".
        self.assertEqual(watcher.pad("Patient 202", 4), "Patient 202")


class StickyValueTests(unittest.TestCase):
    """A producer rewriting JSON mid-read must not blank or rewind the display."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.results = root / "results"
        self.data = root / "data"
        self._saved = (watcher.RESULTS_ROOT, watcher.DATA_ROOT)
        watcher.RESULTS_ROOT = self.results
        watcher.DATA_ROOT = self.data
        self.patient = "Lung_Patient_15"
        self.ga_dir = self.results / self.patient / "ga_runs"
        self.ga_dir.mkdir(parents=True)
        self.ga_path = self.ga_dir / f"{self.patient}_ga_downsampled_seed_0.json"

    def tearDown(self):
        watcher.RESULTS_ROOT, watcher.DATA_ROOT = self._saved
        self.tmp.cleanup()

    def _write(self, generations, best):
        self.ga_path.write_text(json.dumps({
            "patient": self.patient,
            "gens": 40,
            "history": [{"gen": i} for i in range(generations)],
            "best_fitness": best,
            "unique_solves": generations * 18,
            "wall_time_s": generations * 60,
        }))

    def test_partial_read_keeps_the_last_good_values(self):
        tracker = watcher.PatientTracker(self.patient)
        self._write(5, 91.5)
        first = tracker.refresh()
        self.assertEqual(first["generation"], 5)
        self.assertAlmostEqual(first["best_fitness"], 91.5)

        # Simulate catching the file mid-rewrite.
        self.ga_path.write_text('{"patient": "Lung_Patient_15", "hist')
        second = tracker.refresh()
        self.assertEqual(second["generation"], 5, "generation must not reset")
        self.assertAlmostEqual(second["best_fitness"], 91.5, msg="value must persist")

        self._write(6, 88.0)
        third = tracker.refresh()
        self.assertEqual(third["generation"], 6)
        self.assertAlmostEqual(third["best_fitness"], 88.0)

    def test_generation_never_runs_backwards(self):
        tracker = watcher.PatientTracker(self.patient)
        self._write(12, 80.0)
        tracker.refresh()
        self._write(3, 80.0)   # a truncated or stale rewrite
        self.assertEqual(tracker.refresh()["generation"], 12)

    def test_generation_falls_back_to_history_length(self):
        # History entries without a "gen" key used to leave the counter at zero.
        self.ga_path.write_text(json.dumps({
            "patient": self.patient, "gens": 40,
            "history": [{}, {}, {}],
        }))
        tracker = watcher.PatientTracker(self.patient)
        self.assertEqual(tracker.refresh()["generation"], 3)


class StageInferenceTests(unittest.TestCase):
    """Every stage must be derivable without the process list."""

    BASE = {
        "ga": None, "generation": 0, "gens": 40, "actual": 0, "expected": 24,
        "data_exists": False, "download_complete": False, "down": 0, "full": 0,
        "pdf": False, "ga_age": None, "down_age": None, "full_age": None,
        "data_age": None, "live_window": watcher.DEFAULT_LIVE_WINDOW,
    }

    def snapshot(self, **overrides):
        data = dict(self.BASE)
        data.update(overrides)
        return data

    def test_recent_beam_writes_read_as_downloading_without_ps(self):
        stage, _ = watcher.inferred_stage(
            self.snapshot(data_exists=True, actual=8, data_age=5.0), None)
        self.assertEqual(stage, "Downloading")

    def test_quiet_partial_download_reads_as_paused(self):
        stage, _ = watcher.inferred_stage(
            self.snapshot(data_exists=True, actual=8, data_age=9999.0), None)
        self.assertEqual(stage, "Download paused")

    def test_metadata_only_directory_is_queued_not_downloading(self):
        # fetch_angle_map writes metadata before any beam, which used to be
        # rendered as an active download.
        stage, _ = watcher.inferred_stage(
            self.snapshot(data_exists=True, actual=0, data_age=9999.0), None)
        self.assertEqual(stage, "Queued")

    def test_running_ga_is_detected_from_a_fresh_checkpoint(self):
        stage, _ = watcher.inferred_stage(
            self.snapshot(ga={"x": 1}, generation=7, ga_age=30.0), None)
        self.assertEqual(stage, "GA running")

    def test_slow_patient_is_not_called_paused_inside_its_own_cadence(self):
        # A single generation can outlast a fixed timeout; the window adapts.
        stage, _ = watcher.inferred_stage(
            self.snapshot(ga={"x": 1}, generation=7, ga_age=600.0,
                          live_window=1500.0), None)
        self.assertEqual(stage, "GA running")

    def test_finished_bundle_reads_complete(self):
        stage, _ = watcher.inferred_stage(
            self.snapshot(pdf=True, down=2, full=2, data_exists=False), None)
        self.assertEqual(stage, "Complete")

    def test_process_list_wins_when_available(self):
        stage, elapsed = watcher.inferred_stage(
            self.snapshot(), ("Rendering DVH", 42))
        self.assertEqual((stage, elapsed), ("Rendering DVH", 42))


class LiveWindowTests(unittest.TestCase):
    def test_window_widens_to_the_observed_cadence(self):
        tracker = watcher.PatientTracker("Lung_Patient_15")
        now = time.time()
        tracker._gen_marks = [(now - 2000, 1), (now, 3)]   # 1000s per generation
        self.assertGreater(tracker.live_window(), 2000)

    def test_window_has_a_floor_before_any_cadence_is_known(self):
        tracker = watcher.PatientTracker("Lung_Patient_15")
        self.assertEqual(tracker.live_window(), watcher.DEFAULT_LIVE_WINDOW)


if __name__ == "__main__":
    unittest.main()
