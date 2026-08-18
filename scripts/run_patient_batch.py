#!/usr/bin/env python3
"""Run the no-180 GA, clinician comparison, DVH, and cleanup for lung patients.

The pipeline is resumable from artifacts. Re-running it skips completed stages; GA
solves also resume from the ignored per-patient cache written by ga_bao.py.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import time
from pathlib import Path

if __package__:
    from .json_io import read_json
else:
    from json_io import read_json


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT.parent / "data"
PYTHON = ROOT.parent / "portpy-venv" / "bin" / "python"
# PortPy's Hugging Face catalogue publishes Lung_Patient_2 through Lung_Patient_202
# contiguously; anything outside that range is a typo, not a patient.
PATIENT_RE = re.compile(r"Lung_Patient_(\d+)\Z")
PATIENT_RANGE = range(2, 203)


def valid_patient(patient: str) -> bool:
    match = PATIENT_RE.fullmatch(patient)
    return match is not None and int(match.group(1)) in PATIENT_RANGE


def run(*args: str) -> None:
    command = [str(PYTHON), *args]
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def load_json(path: Path) -> dict | None:
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


def require_keys(payload: dict, required: set[str], label: str) -> None:
    missing = required - set(payload)
    if missing:
        raise RuntimeError(f"{label}: missing required keys {sorted(missing)}")


def paths(patient: str) -> dict[str, Path]:
    root = ROOT / "results" / patient
    return {
        "root": root,
        "ga": root / "ga_runs" / f"{patient}_ga_downsampled_seed_0.json",
        "down": root / "clinical_comparison" / f"{patient}_clinical_metrics_downsampled.json",
        "full": root / "clinical_comparison" / f"{patient}_clinical_metrics_full_resolution.json",
        "pdf": root / "figures" / f"{patient}_DVH_clinical_metrics.pdf",
        "readme": root / "README.md",
        "data": DATA_ROOT / patient,
    }


def ga_complete(path: Path, patient: str) -> bool:
    if not path.exists():
        return False
    data = load_json(path)
    if data is None:
        return False
    history = data.get("history")
    pool = data.get("pool")
    best_angles = data.get("best_angles")
    return (
        data.get("patient") == patient
        and data.get("gens") == 40
        and isinstance(history, list)
        and len(history) == 40
        and isinstance(pool, list)
        and 36 not in pool
        and isinstance(best_angles, list)
        and 36 not in best_angles
    )


def wait_for_external_ga(path: Path, patient: str) -> bool:
    """Wait for a GA already writing this result; return false if it goes stale."""
    if not path.exists() or time.time() - path.stat().st_mtime > 120:
        return False
    while not ga_complete(path, patient):
        age = time.time() - path.stat().st_mtime
        if age > 120:
            print(f"GA checkpoint stale for {age:.0f}s; resuming it here", flush=True)
            return False
        data = load_json(path) or {}
        print(
            f"waiting for active GA: generation {len(data.get('history', []))}/40, "
            f"{data.get('unique_solves', 0)} solves",
            flush=True,
        )
        time.sleep(30)
    return True


def comparison_complete(path: Path, downsampled: bool) -> bool:
    if not path.exists():
        return False
    data = load_json(path)
    if data is None:
        return False
    return (
        set(data) == {"expert", "GA"}
        and all(isinstance(row, dict) for row in data.values())
        and {row.get("downsampled") for row in data.values()} == {downsampled}
        and all(isinstance(row.get("criteria"), list)
                and len(row["criteria"]) >= 10 for row in data.values())
    )


def data_complete(patient: str) -> bool:
    data_dir = DATA_ROOT / patient
    planner_path = data_dir / "PlannerBeams.json"
    if not planner_path.exists():
        return False
    planner_payload = load_json(planner_path)
    if planner_payload is None or not isinstance(planner_payload.get("IDs"), list):
        return False
    planner = {int(x) for x in planner_payload["IDs"]}
    expected = ({b for b in range(0, 72, 3) if b != 36} | (planner - {36}))
    present = {
        int(path.name.split("_")[1])
        for path in (data_dir / "Beams").glob("Beam_*_Data.h5")
    }
    return expected <= present


def validate_bundle(patient: str, p: dict[str, Path]) -> None:
    ga = load_json(p["ga"])
    if ga is None:
        raise RuntimeError(f"{patient}: missing or unreadable GA result")
    require_keys(ga, {"patient", "best_angles", "pool"}, f"{patient}: GA result")
    if not isinstance(ga["best_angles"], list) or not isinstance(ga["pool"], list):
        raise RuntimeError(f"{patient}: GA angles and pool must be lists")
    if ga.get("patient") != patient or 36 in ga["best_angles"] or 36 in ga["pool"]:
        raise RuntimeError(f"{patient}: invalid GA patient or 180-degree beam")

    for key, expected_ds in (("down", True), ("full", False)):
        comparison = load_json(p[key])
        if comparison is None:
            raise RuntimeError(f"{patient}: missing or unreadable {key} comparison")
        if set(comparison) != {"expert", "GA"}:
            raise RuntimeError(f"{patient}: {key} comparison does not contain clinician + GA")
        for name in ("expert", "GA"):
            if not isinstance(comparison[name], dict):
                raise RuntimeError(f"{patient}: {key} {name} entry must be an object")
            require_keys(
                comparison[name],
                {"beams", "downsampled", "criteria"},
                f"{patient}: {key} {name}",
            )
        if comparison["GA"]["beams"] != ga["best_angles"]:
            raise RuntimeError(f"{patient}: {key} comparison uses a different GA winner")
        if {row["downsampled"] for row in comparison.values()} != {expected_ds}:
            raise RuntimeError(f"{patient}: {key} comparison resolution mismatch")

    if not p["pdf"].read_bytes().startswith(b"%PDF"):
        raise RuntimeError(f"{patient}: missing or invalid DVH PDF")


def write_readme(patient: str, p: dict[str, Path]) -> None:
    ga = load_json(p["ga"])
    down = load_json(p["down"])
    full = load_json(p["full"])
    if ga is None or down is None or full is None:
        raise RuntimeError(f"{patient}: cannot write README from incomplete JSON")

    def improvement(data: dict) -> float:
        return 100 * (data["expert"]["objective"] - data["GA"]["objective"]) / data["expert"]["objective"]

    clinician = full["expert"]["beams"]
    winner = ga["best_angles"]
    text = f"""# {patient} - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **{improvement(down):+.2f}% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | {', '.join(map(str, clinician))} | {', '.join(str(x * 5) + '°' for x in clinician)} |
| GA | {', '.join(map(str, winner))} | {', '.join(str(x * 5) + '°' for x in winner)} |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | {down['expert']['objective']:.4f} | {down['GA']['objective']:.4f} |
| Full-resolution objective | {full['expert']['objective']:.4f} | {full['GA']['objective']:.4f} |
| Full-resolution PTV D95 | {full['expert']['PTV_D95_Gy']:.2f} Gy | {full['GA']['PTV_D95_Gy']:.2f} Gy |
| Full-resolution solve time | {full['expert']['solve_time_s']:.1f} s | {full['GA']['solve_time_s']:.1f} s |

GA search: best fitness {ga['best_fitness']:.4f}, {ga['unique_solves']} unique solves,
{ga['wall_time_s'] / 60:.1f} minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/{p['ga'].name}` - raw reduced-resolution GA history and winner.
- `clinical_comparison/{p['down'].name}` - clinician vs. GA at search resolution.
- `clinical_comparison/{p['full'].name}` - clinical source of truth at full resolution.
- `figures/{p['pdf'].name}` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
"""
    p["readme"].write_text(text)


def delete_raw_data(patient: str, data_dir: Path) -> None:
    if not valid_patient(patient):
        raise RuntimeError(f"refusing cleanup for unexpected patient name: {patient}")
    if data_dir.parent.resolve() != DATA_ROOT.resolve():
        raise RuntimeError(f"refusing cleanup outside {DATA_ROOT}: {data_dir}")
    if data_dir.exists():
        shutil.rmtree(data_dir)
        print(f"deleted raw data -> {data_dir}", flush=True)


def process(patient: str, keep_data: bool) -> None:
    p = paths(patient)
    print(f"\n{'=' * 72}\n{patient}\n{'=' * 72}", flush=True)

    bundle_complete = (
        ga_complete(p["ga"], patient)
        and comparison_complete(p["down"], True)
        and comparison_complete(p["full"], False)
        and p["pdf"].exists()
    )
    if not bundle_complete and not data_complete(patient):
        run("scripts/download_patient_data.py", "--beam-mode", "ga", patient)

    if not ga_complete(p["ga"], patient) and not wait_for_external_ga(p["ga"], patient):
        run("ga_bao.py", "--patient", patient, "--k", "7", "--pop", "20",
            "--gens", "40", "--seed", "0")
    if not comparison_complete(p["down"], True):
        run("scripts/clinical_compare.py", "--patient", patient, "--downsample")
    if not comparison_complete(p["full"], False):
        run("scripts/clinical_compare.py", "--patient", patient)
    if not p["pdf"].exists():
        run("scripts/plot_dvh.py", "--patient", patient)

    validate_bundle(patient, p)
    write_readme(patient, p)
    print(f"validated result bundle -> {p['root']}", flush=True)
    if not keep_data:
        delete_raw_data(patient, p["data"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("patients", nargs="+", help="e.g. Lung_Patient_15 Lung_Patient_16")
    parser.add_argument("--keep-data", action="store_true")
    args = parser.parse_args()

    for patient in args.patients:
        if not valid_patient(patient):
            parser.error(
                f"unsupported patient {patient!r}; expected Lung_Patient_2 "
                f"through Lung_Patient_202"
            )
    if not PYTHON.exists():
        parser.error(f"PortPy environment not found: {PYTHON}")

    for patient in args.patients:
        process(patient, args.keep_data)
    print("\nBatch complete.", flush=True)


if __name__ == "__main__":
    main()
