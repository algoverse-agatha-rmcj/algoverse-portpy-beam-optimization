#!/usr/bin/env python3
"""Live, dependency-free monitor for a lung-patient BAO batch.

The dashboard is deliberately read-only and stateless: it reconstructs progress
from running command lines, PortPy data files, and the normal result artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT.parent / "data"
RESULTS_ROOT = REPO_ROOT / "results"
DEFAULT_PATIENTS = tuple(f"Lung_Patient_{number}" for number in range(15, 21))
GA_GRID = frozenset(beam for beam in range(0, 72, 3) if beam != 36)

RESET = "\033[0m"
COLORS = {
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}


def read_json(path: Path):
    """Return parsed JSON, or None while a producer is replacing the file."""
    try:
        return json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def directory_bytes(path: Path) -> int:
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


def parse_etime(value: str) -> int | None:
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
    """Return [(elapsed_seconds, command), ...] and whether ps was available."""
    try:
        proc = subprocess.run(
            ["ps", "-axo", "etime=,command="],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
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


def beam_progress(patient: str):
    patient_dir = DATA_ROOT / patient
    beam_dir = patient_dir / "Beams"
    actual_ids = set()
    try:
        for path in beam_dir.glob("Beam_*_Data.h5"):
            match = re.fullmatch(r"Beam_(\d+)_Data\.h5", path.name)
            if match:
                actual_ids.add(int(match.group(1)))
    except OSError:
        pass

    expected_ids = None
    planner = read_json(patient_dir / "PlannerBeams.json")
    if isinstance(planner, dict) and isinstance(planner.get("IDs"), list):
        try:
            expected_ids = GA_GRID | (set(map(int, planner["IDs"])) - {36})
        except (TypeError, ValueError):
            expected_ids = None
    return len(actual_ids), (len(expected_ids) if expected_ids is not None else None)


def comparison_progress(path: Path) -> int:
    payload = read_json(path)
    if not isinstance(payload, dict):
        return 0
    return min(2, sum(name in payload for name in ("expert", "GA")))


def artifact_snapshot(patient: str):
    patient_results = RESULTS_ROOT / patient
    ga_path = patient_results / "ga_runs" / f"{patient}_ga_downsampled_seed_0.json"
    compare_dir = patient_results / "clinical_comparison"
    down_path = compare_dir / f"{patient}_clinical_metrics_downsampled.json"
    full_path = compare_dir / f"{patient}_clinical_metrics_full_resolution.json"
    pdf_path = patient_results / "figures" / f"{patient}_DVH_clinical_metrics.pdf"
    data_dir = DATA_ROOT / patient

    ga = read_json(ga_path)
    ga = ga if isinstance(ga, dict) and ga.get("patient") == patient else None
    history = ga.get("history", []) if ga else []
    history = history if isinstance(history, list) else []
    gens = int(ga.get("gens", 40)) if ga else 40
    generation = 0
    if history and isinstance(history[-1], dict):
        generation = int(history[-1].get("gen", -1)) + 1

    actual, expected = beam_progress(patient)
    data_exists = data_dir.is_dir()
    data_bytes = directory_bytes(data_dir) if data_exists else 0
    down = comparison_progress(down_path)
    full = comparison_progress(full_path)
    pdf = pdf_path.is_file() and pdf_path.stat().st_size > 0
    download_complete = expected is not None and actual >= expected

    def age_seconds(path: Path):
        try:
            return max(0.0, time.time() - path.stat().st_mtime)
        except OSError:
            return None

    return {
        "ga": ga,
        "generation": generation,
        "gens": gens,
        "actual": actual,
        "expected": expected,
        "data_exists": data_exists,
        "data_bytes": data_bytes,
        "download_complete": download_complete,
        "down": down,
        "full": full,
        "pdf": pdf,
        "ga_age": age_seconds(ga_path),
        "down_age": age_seconds(down_path),
        "full_age": age_seconds(full_path),
    }


def active_stages(processes, snapshots, patients):
    """Map patients to (stage, elapsed), resolving multi-patient downloads."""
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
    if active:
        return active[0], active[1]
    # Process inspection can be denied by a sandbox. GA generations can each take
    # more than a minute, so a recent, unfinished checkpoint is also a useful live
    # signal. A stopped job naturally changes to "GA paused" after five minutes.
    if (snapshot["ga"] and snapshot["generation"] < snapshot["gens"]
            and snapshot["ga_age"] is not None and snapshot["ga_age"] < 300):
        return "GA running", None
    if (snapshot["full"] == 1 and snapshot["full_age"] is not None
            and snapshot["full_age"] < 300):
        return "Compare full", None
    if (snapshot["down"] == 1 and snapshot["down_age"] is not None
            and snapshot["down_age"] < 300):
        return "Compare DS", None
    if snapshot["pdf"] and not snapshot["data_exists"]:
        return "Complete", None
    if snapshot["pdf"]:
        return "Ready cleanup", None
    if snapshot["full"] == 2:
        return "Ready for DVH", None
    if snapshot["down"] == 2:
        return "Ready for full", None
    if snapshot["generation"] >= snapshot["gens"]:
        return "Ready for DS", None
    if snapshot["ga"]:
        return "GA paused", None
    if snapshot["download_complete"]:
        return "Ready for GA", None
    if snapshot["data_exists"]:
        return "Download paused", None
    return "Queued", None


def comparison_cell(snapshot) -> str:
    def mark(count):
        return "✓" if count == 2 else (f"{count}/2" if count else "—")

    return f"D{mark(snapshot['down'])} F{mark(snapshot['full'])}"


def colorize(value: str, color: str, enabled: bool) -> str:
    return f"{COLORS[color]}{value}{RESET}" if enabled else value


def render(snapshots, active, patients, ps_available: bool, use_color: bool) -> str:
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    numbers = [patient.rsplit("_", 1)[1] for patient in patients]
    span = f"{numbers[0]}–{numbers[-1]}" if len(numbers) > 1 else numbers[0]
    title = f"Algoverse BAO batch · patients {span} · {now}"
    lines = [colorize(title, "bold", use_color), ""]
    widths = (11, 14, 14, 6, 8, 6, 7, 10, 4, 10)
    headers = ("Patient", "Stage", "Beams · GB", "Gen", "Best", "Solves", "GA wall",
               "Compare", "DVH", "Raw data")

    def row(values):
        return " │ ".join(str(value)[:width].ljust(width) for value, width in zip(values, widths))

    lines.append(colorize(row(headers), "dim", use_color))
    lines.append("─┼─".join("─" * width for width in widths))
    for patient in patients:
        number = patient.rsplit("_", 1)[1]
        snapshot = snapshots[patient]
        stage, process_elapsed = inferred_stage(snapshot, active.get(patient))
        expected = snapshot["expected"]
        beam_text = f"{snapshot['actual']}/{expected if expected is not None else '?'}"
        if snapshot["data_exists"]:
            beam_text += f" · {format_gb(snapshot['data_bytes'])}"

        ga = snapshot["ga"] or {}
        gen_text = f"{snapshot['generation']}/{snapshot['gens']}" if ga else "—"
        if stage == "GA running" and not ga:
            gen_text = "setup"
        best = ga.get("best_fitness")
        best_text = f"{float(best):.2f}" if isinstance(best, (int, float)) else "—"
        solves = ga.get("unique_solves", "—")
        wall = format_duration(ga.get("wall_time_s")) if ga else "—"
        if not ga and process_elapsed is not None:
            wall = f"~{format_duration(process_elapsed)}"

        if not snapshot["data_exists"]:
            raw = "cleaned" if snapshot["pdf"] else "absent"
        elif snapshot["pdf"]:
            raw = "pending"
        else:
            raw = "kept"
        dvh = "✓" if snapshot["pdf"] else "—"
        live_stage = (patient in active or stage in {
            "Downloading", "GA running", "Compare DS", "Compare full", "Rendering DVH"
        })
        stage_color = "green" if stage == "Complete" else ("cyan" if live_stage else "yellow")
        values = (f"Patient {number}", colorize(stage.ljust(widths[1]), stage_color, use_color),
                  beam_text, gen_text, best_text, solves, wall,
                  comparison_cell(snapshot), dvh, raw)
        # Stage is pre-padded before ANSI codes, so render this row separately.
        if use_color:
            cells = []
            for index, (value, width) in enumerate(zip(values, widths)):
                if index == 1:
                    cells.append(value)
                else:
                    cells.append(str(value)[:width].ljust(width))
            lines.append(" │ ".join(cells))
        else:
            lines.append(row(values))

    lines.extend([
        "",
        "Beams = selected Beam_*_Data.h5 / expected no-180 pool; GB = raw patient data.",
        "Compare = downsampled/full plans completed (clinician + GA = 2/2).",
        "GA wall comes from the patient-named checkpoint JSON. Ctrl-C to quit.",
    ])
    if not ps_available:
        lines.append(colorize("Process list unavailable; stages use artifacts only.", "yellow", use_color))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a lung-patient BAO batch.")
    parser.add_argument("patients", nargs="*", default=list(DEFAULT_PATIENTS),
                        help="patients to watch (default: Lung_Patient_15..20)")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument("--interval", type=float, default=5.0, help="refresh seconds (default: 5)")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    patients = args.patients or list(DEFAULT_PATIENTS)

    use_color = sys.stdout.isatty()
    try:
        if not args.once and use_color:
            sys.stdout.write("\033[?25l")
        while True:
            snapshots = {patient: artifact_snapshot(patient) for patient in patients}
            processes, ps_available = process_snapshot()
            active = active_stages(processes, snapshots, patients)
            output = render(snapshots, active, patients, ps_available, use_color)
            if not args.once and use_color:
                sys.stdout.write("\033[2J\033[H")
            print(output, flush=True)
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
