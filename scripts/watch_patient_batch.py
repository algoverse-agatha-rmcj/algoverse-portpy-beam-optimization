#!/usr/bin/env python3
"""Live, dependency-free terminal tracker for a lung-patient BAO batch.

The dashboard is read-only: it reconstructs progress from result artifacts, the
PortPy data directory, and (when available) the process list.

DESIGNED AROUND THE WAYS THIS DISPLAY HAS FAILED BEFORE
-------------------------------------------------------
1. `ps` is blocked in some sandboxes. Every stage is therefore inferable from
   artifacts alone; the process list is an enhancement, never a requirement.
2. Hardcoded column widths truncated real values ("Patient 15" rendered as
   "Patient 1"). Widths are now measured from the content being printed.
3. Producers rewrite JSON while the tracker reads it, so a read returns None for
   one tick. Cells used to blank out and counters appeared to run backwards.
   Every value is now sticky: the last good reading is kept and marked stale
   rather than replaced with an empty one.
4. A fixed "is it alive" timeout mislabelled slow patients as paused, because a
   single GA generation can take longer than the timeout. Liveness is now judged
   against each patient's own observed generation cadence.
5. Sizing the data directory walks tens of thousands of files. Doing that every
   refresh made the loop lag behind its own interval, so it is throttled and
   cached independently of the refresh rate.
6. Clearing the whole screen each tick flickered and fought with terminal
   scrollback. Redraw now homes the cursor and clears each line in place.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beam_angles import excluded_ids, grid_pool, local_angle_map


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT.parent / "data"
RESULTS_ROOT = REPO_ROOT / "results"
DEFAULT_PATIENTS = tuple(f"Lung_Patient_{number}" for number in range(15, 21))

# Sizing the data tree is expensive; refresh it far less often than the display.
SIZE_REFRESH_SECONDS = 20.0
# A value older than this is shown dimmed, so a frozen producer is visible.
STALE_AFTER_SECONDS = 90.0
# Fallback liveness window used until a patient has shown two generations.
DEFAULT_LIVE_WINDOW = 420.0

RESET = "\033[0m"
COLORS = {
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "cyan": "\033[36m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}


def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled or color not in COLORS:
        return text
    return f"{COLORS[color]}{text}{RESET}"


def visible_width(text: str) -> int:
    """Length of `text` ignoring ANSI escapes, so padding stays correct."""
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - visible_width(text))


def read_json(path: Path):
    """Return parsed JSON, or None while a producer is replacing the file."""
    try:
        return json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def format_gb(byte_count: int) -> str:
    return f"{byte_count / (1024 ** 3):.1f}G"


def format_duration(seconds) -> str:
    try:
        seconds = max(0, int(float(seconds)))
    except (TypeError, ValueError):
        return "—"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def parse_etime(value: str):
    """Parse ps(1)'s [[days-]hours:]minutes:seconds elapsed format."""
    try:
        days = 0
        if "-" in value:
            day_text, value = value.split("-", 1)
            days = int(day_text)
        parts = [int(part) for part in value.split(":")]
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes, seconds = 0, parts[0], parts[1]
        else:
            return None
        return days * 86400 + hours * 3600 + minutes * 60 + seconds
    except (TypeError, ValueError):
        return None


def process_snapshot():
    """Return [(elapsed_seconds, command), ...] and whether ps was available.

    A sandbox that denies `ps` returns (…, False); the caller must stay useful.
    """
    try:
        proc = subprocess.run(
            ["ps", "-axo", "etime=,command="],
            check=False, capture_output=True, text=True, timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return [], False
    if proc.returncode != 0:
        return [], False
    rows = []
    for line in proc.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2:
            rows.append((parse_etime(fields[0]), fields[1]))
    return rows, True


def directory_bytes(path: Path) -> int:
    """Total bytes under `path`, preferring du(1) and falling back to a walk."""
    try:
        proc = subprocess.run(["du", "-sk", str(path)], check=False,
                              capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            return int(proc.stdout.split()[0]) * 1024
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        pass
    total = 0
    try:
        for root, _, names in os.walk(path):
            for name in names:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def beam_progress(patient: str):
    """(beams on disk, beams expected) — expected is None until it is knowable."""
    patient_dir = DATA_ROOT / patient
    actual_ids = set()
    try:
        for path in (patient_dir / "Beams").glob("Beam_*_Data.h5"):
            match = re.fullmatch(r"Beam_(\d+)_Data\.h5", path.name)
            if match:
                actual_ids.add(int(match.group(1)))
    except OSError:
        pass

    expected = None
    planner = read_json(patient_dir / "PlannerBeams.json")
    if isinstance(planner, dict) and isinstance(planner.get("IDs"), list):
        try:
            angles = local_angle_map(patient, DATA_ROOT)
            if angles:
                dropped = excluded_ids(angles)
                expected = len(set(grid_pool(angles))
                               | (set(map(int, planner["IDs"])) - dropped))
        except (TypeError, ValueError):
            expected = None
    return len(actual_ids), expected


def comparison_progress(path: Path) -> int:
    """Plans present: the clinician plan plus the GA plan, whatever it is named.

    Lung_Patient_2 stores its GA plan as "GA_B_no180", so matching a literal "GA"
    reported a finished comparison as half done.
    """
    payload = read_json(path)
    if not isinstance(payload, dict):
        return 0
    has_expert = "expert" in payload
    has_ga = any(name != "expert" for name in payload)
    return int(has_expert) + int(has_ga)


def age_seconds(path: Path):
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return None


class PatientTracker:
    """Per-patient state that survives a producer rewriting a file mid-read."""

    def __init__(self, patient: str):
        self.patient = patient
        results = RESULTS_ROOT / patient
        self.ga_path = results / "ga_runs" / f"{patient}_ga_downsampled_seed_0.json"
        compare = results / "clinical_comparison"
        self.down_path = compare / f"{patient}_clinical_metrics_downsampled.json"
        self.full_path = compare / f"{patient}_clinical_metrics_full_resolution.json"
        self.pdf_path = results / "figures" / f"{patient}_DVH_clinical_metrics.pdf"
        self.data_dir = DATA_ROOT / patient

        # Sticky values: a failed read never erases what we already saw.
        self.ga = None
        self.generation = 0
        self.gens = 40
        self.best_fitness = None
        self.solves = None
        self.wall = None
        self.expected = None
        self.actual = 0
        self.data_bytes = 0
        self._sized_at = 0.0
        self._gen_marks: list[tuple[float, int]] = []
        self.last_change = time.time()

    def _note_generation(self, generation: int, now: float) -> None:
        if not self._gen_marks or self._gen_marks[-1][1] != generation:
            self._gen_marks.append((now, generation))
            del self._gen_marks[:-6]

    def seconds_per_generation(self):
        """Observed cadence, or None until two distinct generations are seen."""
        if len(self._gen_marks) < 2:
            return None
        (t0, g0), (t1, g1) = self._gen_marks[0], self._gen_marks[-1]
        if g1 <= g0 or t1 <= t0:
            return None
        return (t1 - t0) / (g1 - g0)

    def live_window(self) -> float:
        """How long a quiet checkpoint may be before the GA is called paused."""
        cadence = self.seconds_per_generation()
        if cadence is None:
            return DEFAULT_LIVE_WINDOW
        # Two missed generations, floored so a fast patient is not called dead
        # during one slow solve.
        return max(DEFAULT_LIVE_WINDOW, cadence * 2.5)

    def refresh(self) -> dict:
        now = time.time()
        changed = False

        payload = read_json(self.ga_path)
        if isinstance(payload, dict) and payload.get("patient") == self.patient:
            self.ga = payload
            history = payload.get("history")
            history = history if isinstance(history, list) else []
            generation = len(history)
            if history and isinstance(history[-1], dict):
                # Trust the recorded index, falling back to the length.
                generation = max(generation, int(history[-1].get("gen", -1)) + 1)
            if generation != self.generation:
                changed = True
            self.generation = max(self.generation, generation)
            self._note_generation(self.generation, now)
            try:
                self.gens = int(payload.get("gens", self.gens))
            except (TypeError, ValueError):
                pass
            for key, attr in (("best_fitness", "best_fitness"),
                              ("unique_solves", "solves"),
                              ("wall_time_s", "wall")):
                value = payload.get(key)
                if isinstance(value, (int, float)):
                    if getattr(self, attr) != value:
                        changed = True
                    setattr(self, attr, value)

        actual, expected = beam_progress(self.patient)
        if actual != self.actual:
            changed = True
        self.actual = max(self.actual, actual) if self.data_dir.is_dir() else actual
        if expected is not None:
            self.expected = expected

        data_exists = self.data_dir.is_dir()
        if not data_exists:
            self.data_bytes = 0
            self.actual = actual
        elif now - self._sized_at >= SIZE_REFRESH_SECONDS:
            size = directory_bytes(self.data_dir)
            if size != self.data_bytes:
                changed = True
            self.data_bytes = size
            self._sized_at = now

        data_age = age_seconds(self.data_dir / "Beams")
        down = comparison_progress(self.down_path)
        full = comparison_progress(self.full_path)
        pdf = self.pdf_path.is_file() and self.pdf_path.stat().st_size > 0
        if changed:
            self.last_change = now

        return {
            "patient": self.patient,
            "ga": self.ga,
            "generation": self.generation,
            "gens": self.gens,
            "best_fitness": self.best_fitness,
            "solves": self.solves,
            "wall": self.wall,
            "actual": self.actual,
            "expected": self.expected,
            "data_exists": data_exists,
            "data_bytes": self.data_bytes,
            "download_complete": self.expected is not None and self.actual >= self.expected,
            "down": down,
            "full": full,
            "pdf": pdf,
            "ga_age": age_seconds(self.ga_path),
            "down_age": age_seconds(self.down_path),
            "full_age": age_seconds(self.full_path),
            "data_age": data_age,
            "quiet_for": now - self.last_change,
            "live_window": self.live_window(),
            "sec_per_gen": self.seconds_per_generation(),
        }


def active_stages(processes, snapshots, patients):
    """Map patients to (stage, elapsed) from the process list, when available."""
    active = {}
    for elapsed, command in processes:
        mentioned = [patient for patient in patients if patient in command]
        if not mentioned:
            continue
        if "download_patient_data.py" in command:
            # The downloader accepts a list but processes it serially. Select the
            # first patient whose requested beam set is not yet on disk.
            patient = next(
                (item for item in mentioned if not snapshots[item]["download_complete"]),
                mentioned[-1],
            )
            active.setdefault(patient, ("Downloading", elapsed))
        elif "ga_bao.py" in command:
            for patient in mentioned:
                active[patient] = ("GA running", elapsed)
        elif "clinical_compare.py" in command:
            stage = "Compare DS" if "--downsample" in command else "Compare full"
            for patient in mentioned:
                active[patient] = (stage, elapsed)
        elif "plot_dvh.py" in command:
            for patient in mentioned:
                active[patient] = ("Rendering DVH", elapsed)
    return active


def inferred_stage(snapshot, active):
    """Stage for one patient. Every branch works without the process list."""
    if active:
        return active[0], active[1]

    window = snapshot["live_window"]
    if (snapshot["ga"] and snapshot["generation"] < snapshot["gens"]
            and snapshot["ga_age"] is not None and snapshot["ga_age"] < window):
        return "GA running", None
    if (snapshot["full"] == 1 and snapshot["full_age"] is not None
            and snapshot["full_age"] < window):
        return "Compare full", None
    if (snapshot["down"] == 1 and snapshot["down_age"] is not None
            and snapshot["down_age"] < window):
        return "Compare DS", None
    if snapshot["pdf"] and not snapshot["data_exists"]:
        return "Complete", None
    if snapshot["pdf"]:
        return "Ready cleanup", None
    if snapshot["full"] == 2:
        return "Ready for DVH", None
    if snapshot["down"] == 2:
        return "Ready for full", None
    if snapshot["generation"] >= snapshot["gens"] and snapshot["ga"]:
        return "Ready for DS", None
    if snapshot["ga"]:
        return "GA paused", None
    if snapshot["download_complete"]:
        return "Ready for GA", None
    if (snapshot["data_exists"] and not snapshot["download_complete"]
            and snapshot["data_age"] is not None and snapshot["data_age"] < window):
        # Beam files are still landing, so this is live even with no process list.
        return "Downloading", None
    if snapshot["data_exists"] and snapshot["actual"] > 0:
        return "Download paused", None
    # The angle lookup writes metadata before any beam is fetched, so a directory
    # with no beams in it means "not started", not "downloading".
    return "Queued", None


LIVE_STAGES = {"Downloading", "GA running", "Compare DS", "Compare full", "Rendering DVH"}


def stage_color(stage: str) -> str:
    if stage == "Complete":
        return "green"
    if stage in LIVE_STAGES:
        return "cyan"
    if stage in {"GA paused", "Download paused"}:
        return "red"
    return "yellow"


def comparison_cell(snapshot) -> str:
    def mark(count):
        return "✓" if count == 2 else (f"{count}/2" if count else "—")
    return f"D{mark(snapshot['down'])} F{mark(snapshot['full'])}"


def overall_eta(snapshots, patients):
    """Rough remaining time: unfinished generations plus untouched patients."""
    cadences = [s["sec_per_gen"] for s in snapshots.values() if s["sec_per_gen"]]
    if not cadences:
        return None
    cadence = sum(cadences) / len(cadences)
    remaining_gens = 0
    untouched = 0
    for patient in patients:
        s = snapshots[patient]
        if s["pdf"]:
            continue
        if s["ga"]:
            remaining_gens += max(0, s["gens"] - s["generation"])
        else:
            untouched += 1
            remaining_gens += s["gens"]
    # Each untouched patient also pays a download and three solve/plot stages;
    # measured at roughly a third of its GA time on this cohort.
    overhead = untouched * cadence * s["gens"] * 0.33 if untouched else 0
    return remaining_gens * cadence + overhead


def render(snapshots, active, patients, ps_available, use_color, width) -> str:
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    numbers = [p.rsplit("_", 1)[1] for p in patients]
    # Span is the numeric range, not the first and last of the argument order: a batch
    # is often ordered by expected runtime, so "7 9 11 14 12 13 8 10" would otherwise
    # advertise itself as "7-10" and hide half the work.
    ordered = sorted(numbers, key=lambda n: int(n) if n.isdigit() else 0)
    if len(ordered) <= 1:
        span = ordered[0] if ordered else "none"
    else:
        contiguous = all(n.isdigit() for n in ordered) and (
            int(ordered[-1]) - int(ordered[0]) + 1 == len(ordered)
        )
        span = f"{ordered[0]}–{ordered[-1]}"
        if not contiguous:
            span += f" ({len(ordered)} patients)"

    headers = ("Patient", "Stage", "Data", "Beams", "Gen", "Best",
               "Solves", "GA wall", "Compare", "DVH", "Raw data")
    rows = []
    for patient in patients:
        s = snapshots[patient]
        stage, elapsed = inferred_stage(s, active.get(patient))

        expected = s["expected"]
        beams = f"{s['actual']}/{expected if expected is not None else '?'}"
        data = format_gb(s["data_bytes"]) if s["data_exists"] else "—"

        gen = f"{s['generation']}/{s['gens']}" if s["ga"] else "—"
        if stage == "GA running" and not s["ga"]:
            gen = "setup"
        best = f"{s['best_fitness']:.2f}" if isinstance(s["best_fitness"], (int, float)) else "—"
        solves = str(s["solves"]) if s["solves"] is not None else "—"
        wall = format_duration(s["wall"]) if s["wall"] is not None else "—"
        stage_cell = stage
        if elapsed is not None and stage in LIVE_STAGES:
            stage_cell = f"{stage} {format_duration(elapsed)}"

        if not s["data_exists"]:
            raw = "cleaned" if s["pdf"] else "absent"
        elif s["pdf"]:
            raw = "pending"
        elif s["actual"] == 0:
            raw = "meta only"
        else:
            raw = "kept"

        stale = s["quiet_for"] > STALE_AFTER_SECONDS and stage in LIVE_STAGES
        rows.append({
            "cells": [f"Patient {patient.rsplit('_', 1)[1]}", stage_cell, data, beams, gen,
                      best, solves, wall, comparison_cell(s), "✓" if s["pdf"] else "—", raw],
            "stage": stage,
            "stale": stale,
            "quiet_for": s["quiet_for"],
        })

    # Widths measured from real content, so nothing is ever silently truncated.
    widths = [
        max(len(headers[i]), max(len(r["cells"][i]) for r in rows))
        for i in range(len(headers))
    ]

    lines = [colorize(f"Algoverse BAO batch · patients {span} · {now}", "bold", use_color), ""]
    lines.append(colorize(" │ ".join(pad(h, w) for h, w in zip(headers, widths)),
                          "dim", use_color))
    lines.append("─┼─".join("─" * w for w in widths))

    for row in rows:
        cells = []
        for index, (value, w) in enumerate(zip(row["cells"], widths)):
            if index == 1:
                cells.append(pad(colorize(value, stage_color(row["stage"]), use_color), w))
            else:
                cells.append(pad(value, w))
        line = " │ ".join(cells)
        if row["stale"]:
            line += colorize(f"  ⚠ quiet {format_duration(row['quiet_for'])}",
                             "red", use_color)
        lines.append(line)

    done = sum(1 for p in patients if snapshots[p]["pdf"])
    eta = overall_eta(snapshots, patients)
    summary = f"{done}/{len(patients)} bundles complete"
    if eta:
        summary += f" · rough ETA {format_duration(eta)}"
    lines += ["", colorize(summary, "bold", use_color)]

    footer = ["Beams = Beam_*_Data.h5 on disk / expected pool (angle-derived; ? until known).",
              "Compare = clinician+GA plans done. Values persist across a partial read;",
              "a ⚠ marks a producer that has gone quiet, not a value that vanished."]
    if not ps_available:
        footer.append("Process list unavailable — stages inferred from artifacts alone.")
    lines += [""] + [colorize(text, "dim", use_color) for text in footer]

    if width:
        lines = [line if visible_width(line) <= width else
                 line[:max(0, width + (len(line) - visible_width(line)))] for line in lines]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a lung-patient BAO batch.")
    parser.add_argument("patients", nargs="*", default=list(DEFAULT_PATIENTS),
                        help="patients to watch (default: Lung_Patient_15..20)")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="refresh seconds (default: 5)")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colour")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    patients = args.patients or list(DEFAULT_PATIENTS)

    trackers = {patient: PatientTracker(patient) for patient in patients}
    use_color = sys.stdout.isatty() and not args.no_color
    previous_lines = 0

    try:
        if not args.once and use_color:
            sys.stdout.write("\033[?25l")
        while True:
            width = shutil.get_terminal_size((0, 0)).columns or None
            snapshots = {p: trackers[p].refresh() for p in patients}
            processes, ps_available = process_snapshot()
            active = active_stages(processes, snapshots, patients)
            output = render(snapshots, active, patients, ps_available, use_color, width)

            if args.once or not use_color:
                print(output, flush=True)
            else:
                # Home the cursor and clear each line in place: no full-screen
                # wipe, so the display does not flicker or fight the scrollback.
                buffer = ["\033[H"]
                for line in output.split("\n"):
                    buffer.append("\033[2K" + line + "\n")
                blank = previous_lines - len(output.split("\n"))
                buffer.extend("\033[2K\n" for _ in range(max(0, blank)))
                buffer.append("\033[J")
                previous_lines = len(output.split("\n"))
                sys.stdout.write("".join(buffer))
                sys.stdout.flush()

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        if not args.once and use_color:
            sys.stdout.write("\033[?25h\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
