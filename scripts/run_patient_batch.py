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
    from .beam_angles import excluded_ids, fetch_angle_map, format_angles, grid_pool
    from .experiment_protocol import (
        BATCH_SCHEMA,
        EXPERIMENT_ID,
        PRIMARY_GENERATIONS,
        PRIMARY_K,
        PRIMARY_MUTATION_RATE,
        PRIMARY_POPULATION,
        PRIMARY_SEED,
        batch_manifest,
        fingerprint,
        primary_config_mismatches,
        primary_scientific_config,
        result_scientific_config,
        utc_now,
    )
    from .json_io import atomic_write_json, read_json
    from .timing import timing_label
else:
    from beam_angles import excluded_ids, fetch_angle_map, format_angles, grid_pool
    from experiment_protocol import (
        BATCH_SCHEMA,
        EXPERIMENT_ID,
        PRIMARY_GENERATIONS,
        PRIMARY_K,
        PRIMARY_MUTATION_RATE,
        PRIMARY_POPULATION,
        PRIMARY_SEED,
        batch_manifest,
        fingerprint,
        primary_config_mismatches,
        primary_scientific_config,
        result_scientific_config,
        utc_now,
    )
    from json_io import atomic_write_json, read_json
    from timing import timing_label


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT.parent / "data"
PYTHON = ROOT.parent / "portpy-venv" / "bin" / "python"
# PortPy's Hugging Face catalogue publishes Lung_Patient_2 through Lung_Patient_202
# contiguously; anything outside that range is a typo, not a patient.
PATIENT_RE = re.compile(r"Lung_Patient_(\d+)\Z")
PATIENT_RANGE = range(2, 203)
KNOWN_UNUSABLE_PATIENTS = {"Lung_Patient_12", "Lung_Patient_13"}
BATCH_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
# A download that exits 0 is not proof it fetched the whole pool.
DOWNLOAD_ATTEMPTS = 3


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
        "ga_manifest": root / "ga_runs" / f"{patient}_ga_downsampled_seed_0.manifest.json",
        "down": root / "clinical_comparison" / f"{patient}_clinical_metrics_downsampled.json",
        "full": root / "clinical_comparison" / f"{patient}_clinical_metrics_full_resolution.json",
        "pdf": root / "figures" / f"{patient}_DVH_clinical_metrics.pdf",
        "readme": root / "README.md",
        "data": DATA_ROOT / patient,
    }


def ga_complete(
    path: Path,
    patient: str,
    dropped: set[int],
    expected_pool: set[int] | None = None,
) -> bool:
    if not path.exists():
        return False
    data = load_json(path)
    if data is None:
        return False
    history = data.get("history")
    pool = data.get("pool")
    best_angles = data.get("best_angles")
    if not (isinstance(pool, list) and isinstance(best_angles, list)):
        return False
    # `dropped` holds the IDs sitting at 180 degrees for this patient; beam 36 is
    # only 180 degrees on patients 2-10, so this can never be a hardcoded ID.
    return (
        data.get("patient") == patient
        and not primary_config_mismatches(data)
        and isinstance(history, list)
        and len(history) == PRIMARY_GENERATIONS
        and not dropped.intersection(pool)
        and not dropped.intersection(best_angles)
        and (expected_pool is None or set(pool) == expected_pool)
    )


def wait_for_external_ga(
    path: Path,
    patient: str,
    dropped: set[int],
    expected_pool: set[int],
) -> bool:
    """Wait for a GA already writing this result; return false if it goes stale."""
    if not path.exists() or time.time() - path.stat().st_mtime > 120:
        return False
    while not ga_complete(path, patient, dropped, expected_pool):
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


def comparison_complete(path: Path, downsampled: bool, ga_result: dict | None = None) -> bool:
    if not path.exists():
        return False
    data = load_json(path)
    if data is None:
        return False
    structurally_complete = (
        set(data) == {"expert", "GA"}
        and all(isinstance(row, dict) for row in data.values())
        and {row.get("downsampled") for row in data.values()} == {downsampled}
        and all(isinstance(row.get("criteria"), list)
                and len(row["criteria"]) >= 10 for row in data.values())
    )
    if not structurally_complete:
        return False
    if ga_result is None or not isinstance(ga_result.get("protocol_manifest"), dict):
        return True
    expected = fingerprint(result_scientific_config(ga_result))
    return {
        row.get("source_protocol_fingerprint")
        for row in data.values()
    } == {expected}


def data_complete(patient: str) -> bool:
    data_dir = DATA_ROOT / patient
    planner_path = data_dir / "PlannerBeams.json"
    if not planner_path.exists():
        return False
    planner_payload = load_json(planner_path)
    if planner_payload is None or not isinstance(planner_payload.get("IDs"), list):
        return False
    planner = {int(x) for x in planner_payload["IDs"]}
    angles = fetch_angle_map(patient, DATA_ROOT)
    dropped = excluded_ids(angles)
    expected = set(grid_pool(angles)) | (planner - dropped)
    present = {
        int(path.name.split("_")[1])
        for path in (data_dir / "Beams").glob("Beam_*_Data.h5")
    }
    return expected <= present


def validate_bundle(
    patient: str,
    p: dict[str, Path],
    dropped: set[int],
    expected_pool: set[int] | None = None,
) -> None:
    ga = load_json(p["ga"])
    if ga is None:
        raise RuntimeError(f"{patient}: missing or unreadable GA result")
    require_keys(ga, {"patient", "best_angles", "pool"}, f"{patient}: GA result")
    if not isinstance(ga["best_angles"], list) or not isinstance(ga["pool"], list):
        raise RuntimeError(f"{patient}: GA angles and pool must be lists")
    if ga.get("patient") != patient:
        raise RuntimeError(f"{patient}: GA result belongs to {ga.get('patient')!r}")
    mismatches = primary_config_mismatches(ga)
    if mismatches:
        raise RuntimeError(
            f"{patient}: GA result is outside the frozen primary protocol: "
            + "; ".join(mismatches)
        )
    if expected_pool is not None and set(ga["pool"]) != expected_pool:
        raise RuntimeError(f"{patient}: GA result uses a different candidate pool")
    if dropped.intersection(ga["best_angles"]) or dropped.intersection(ga["pool"]):
        raise RuntimeError(f"{patient}: GA result includes a 180-degree beam")

    manifest = ga.get("protocol_manifest")
    if isinstance(manifest, dict):
        if manifest.get("patient") != patient:
            raise RuntimeError(f"{patient}: protocol manifest belongs to another patient")
        if manifest.get("experiment_id") != EXPERIMENT_ID:
            raise RuntimeError(f"{patient}: protocol manifest is not in the primary cohort")
        recorded_pool = {
            int(row["beam_id"])
            for row in manifest.get("candidate_pool", [])
            if isinstance(row, dict) and "beam_id" in row
        }
        if recorded_pool != set(ga["pool"]):
            raise RuntimeError(f"{patient}: manifest and GA candidate pools disagree")
        recorded_manifest = load_json(p["ga_manifest"])
        if recorded_manifest is None:
            raise RuntimeError(f"{patient}: missing standalone run manifest")
        if recorded_manifest.get("cache_identity") != manifest.get("cache_identity"):
            raise RuntimeError(f"{patient}: standalone and embedded manifests disagree")

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
        if isinstance(manifest, dict):
            expected_fingerprint = fingerprint(result_scientific_config(ga))
            if {
                row.get("source_protocol_fingerprint")
                for row in comparison.values()
            } != {expected_fingerprint}:
                raise RuntimeError(f"{patient}: {key} comparison protocol mismatch")

    if not p["pdf"].read_bytes().startswith(b"%PDF"):
        raise RuntimeError(f"{patient}: missing or invalid DVH PDF")


def write_readme(patient: str, p: dict[str, Path], angles: dict[int, float]) -> None:
    ga = load_json(p["ga"])
    down = load_json(p["down"])
    full = load_json(p["full"])
    if ga is None or down is None or full is None:
        raise RuntimeError(f"{patient}: cannot write README from incomplete JSON")

    def improvement(data: dict) -> float:
        return 100 * (data["expert"]["objective"] - data["GA"]["objective"]) / data["expert"]["objective"]

    clinician = full["expert"]["beams"]
    winner = ga["best_angles"]
    # A bundle re-run after the 2026-08-26 timing fix reports the solver alone; one carried
    # over from before it reports the whole pipeline. Name whichever this patient has.
    time_label = timing_label(full["expert"], prefix="Full-resolution ")
    text = f"""# {patient} - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
{PRIMARY_POPULATION}, {PRIMARY_GENERATIONS} generations, and seed {PRIMARY_SEED}. Its
objective was **{improvement(down):+.2f}% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | {', '.join(map(str, clinician))} | {format_angles(angles, clinician)} |
| GA | {', '.join(map(str, winner))} | {format_angles(angles, winner)} |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | {down['expert']['objective']:.4f} | {down['GA']['objective']:.4f} |
| Full-resolution objective | {full['expert']['objective']:.4f} | {full['GA']['objective']:.4f} |
| Full-resolution PTV D95 | {full['expert']['PTV_D95_Gy']:.2f} Gy | {full['GA']['PTV_D95_Gy']:.2f} Gy |
| {time_label} | {full['expert']['solve_time_s']:.1f} s | {full['GA']['solve_time_s']:.1f} s |

GA search: best fitness {ga['best_fitness']:.4f}, {ga['unique_solves']} unique solves,
{ga['wall_time_s'] / 60:.1f} minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/{p['ga'].name}` - raw reduced-resolution GA history and winner.
- `ga_runs/{p['ga_manifest'].name}` - protocol, input, environment, and code provenance.
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

    # One angle lookup per patient, reused by every check below.
    angles = fetch_angle_map(patient, DATA_ROOT)
    dropped = excluded_ids(angles)
    planner_payload = load_json(DATA_ROOT / patient / "PlannerBeams.json")
    if planner_payload is None or not isinstance(planner_payload.get("IDs"), list):
        raise RuntimeError(f"{patient}: missing or unreadable PlannerBeams.json")
    planner = {int(value) for value in planner_payload["IDs"]}
    expected_pool = set(grid_pool(angles)) | (planner - dropped)
    ga_result = load_json(p["ga"])

    bundle_complete = (
        ga_complete(p["ga"], patient, dropped, expected_pool)
        and comparison_complete(p["down"], True, ga_result)
        and comparison_complete(p["full"], False, ga_result)
        and p["pdf"].exists()
    )
    if not bundle_complete and not data_complete(patient):
        # The downloader can exit 0 having fetched only part of the pool: Patient 12
        # stopped at beam 65, reported DONE, and the GA then died on the first missing
        # Beam_*_Data.h5 an hour into the batch. data_complete() already knows what the
        # pool requires, so re-ask it after each attempt instead of trusting the exit code.
        for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
            run("scripts/download_patient_data.py", "--beam-mode", "ga", patient)
            if data_complete(patient):
                break
            if attempt == DOWNLOAD_ATTEMPTS:
                raise RuntimeError(
                    f"{patient}: download still incomplete after {DOWNLOAD_ATTEMPTS} "
                    "attempts; the beam pool is missing files on disk"
                )
            print(f"[retry] {patient} download incomplete, "
                  f"attempt {attempt}/{DOWNLOAD_ATTEMPTS}", flush=True)

    if not ga_complete(p["ga"], patient, dropped, expected_pool) and not wait_for_external_ga(
            p["ga"], patient, dropped, expected_pool):
        run(
            "ga_bao.py",
            "--patient", patient,
            "--k", str(PRIMARY_K),
            "--pop", str(PRIMARY_POPULATION),
            "--gens", str(PRIMARY_GENERATIONS),
            "--mutation-rate", str(PRIMARY_MUTATION_RATE),
            "--seed", str(PRIMARY_SEED),
        )
    ga_result = load_json(p["ga"])
    if not comparison_complete(p["down"], True, ga_result):
        run(
            "scripts/clinical_compare.py",
            "--patient", patient,
            "--downsample",
            "--require-primary-protocol",
        )
    if not comparison_complete(p["full"], False, ga_result):
        run(
            "scripts/clinical_compare.py",
            "--patient", patient,
            "--require-primary-protocol",
        )
    if not p["pdf"].exists():
        run("scripts/plot_dvh.py", "--patient", patient)

    validate_bundle(patient, p, dropped, expected_pool)
    write_readme(patient, p, angles)
    print(f"validated result bundle -> {p['root']}", flush=True)
    if not keep_data:
        delete_raw_data(patient, p["data"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("patients", nargs="+", help="e.g. Lung_Patient_15 Lung_Patient_16")
    parser.add_argument("--keep-data", action="store_true")
    parser.add_argument(
        "--batch-id",
        default=time.strftime("seed0-%Y%m%dT%H%M%SZ", time.gmtime()),
        help="stable label for the predeclared batch manifest",
    )
    args = parser.parse_args()

    for patient in args.patients:
        if not valid_patient(patient):
            parser.error(
                f"unsupported patient {patient!r}; expected Lung_Patient_2 "
                f"through Lung_Patient_202"
            )
        if patient in KNOWN_UNUSABLE_PATIENTS:
            parser.error(
                f"{patient} is excluded: its upstream PortPy data cannot produce a "
                "comparable complete result"
            )
    if len(set(args.patients)) != len(args.patients):
        parser.error("patient list contains duplicates")
    if not BATCH_ID_RE.fullmatch(args.batch_id):
        parser.error("--batch-id may contain only letters, numbers, dot, dash, and underscore")
    if not PYTHON.exists():
        parser.error(f"PortPy environment not found: {PYTHON}")

    manifest_path = ROOT / "results" / "batches" / f"{args.batch_id}.json"
    proposed = batch_manifest(batch_id=args.batch_id, patients=args.patients, repo_root=ROOT)
    existing = load_json(manifest_path)
    if existing is not None:
        if existing.get("batch_schema") != BATCH_SCHEMA:
            parser.error(f"{manifest_path}: unsupported batch manifest schema")
        if existing.get("patients_predeclared") != args.patients:
            parser.error(
                f"{manifest_path}: patient list differs from the predeclared batch; "
                "use the original list or a new --batch-id"
            )
        if existing.get("scientific_config") != primary_scientific_config():
            parser.error(f"{manifest_path}: scientific protocol differs from this runner")
        old_source = existing.get("code_provenance", {}).get("source_bundle_sha256")
        new_source = proposed.get("code_provenance", {}).get("source_bundle_sha256")
        if old_source != new_source:
            parser.error(
                f"{manifest_path}: source code changed since this batch started; "
                "use a new --batch-id instead of mixing implementations"
            )
        record = existing
    else:
        record = proposed
        atomic_write_json(manifest_path, record)
    print(f"predeclared batch manifest -> {manifest_path}", flush=True)

    for patient in args.patients:
        record["patients"][patient] = {"status": "running", "updated_at_utc": utc_now()}
        atomic_write_json(manifest_path, record)
        try:
            process(patient, args.keep_data)
        except KeyboardInterrupt:
            record["patients"][patient] = {
                "status": "interrupted",
                "updated_at_utc": utc_now(),
            }
            atomic_write_json(manifest_path, record)
            raise
        except Exception as exc:
            record["patients"][patient] = {
                "status": "failed",
                "updated_at_utc": utc_now(),
                "error": f"{type(exc).__name__}: {exc}",
            }
            atomic_write_json(manifest_path, record)
            raise
        record["patients"][patient] = {
            "status": "completed",
            "updated_at_utc": utc_now(),
        }
        atomic_write_json(manifest_path, record)
    record["completed_at_utc"] = utc_now()
    atomic_write_json(manifest_path, record)
    print("\nBatch complete.", flush=True)


if __name__ == "__main__":
    main()
