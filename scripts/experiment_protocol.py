"""Canonical experiment settings and passive provenance for PortPy GA runs.

The primary cohort is intentionally frozen to the settings used by the existing
17-patient seed-0 result.  This module records and validates those settings; it
does not give the optimizer any additional patient data, evaluations, or seeds.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MANIFEST_SCHEMA = 1
CACHE_SCHEMA = 1
BATCH_SCHEMA = 1
EXPERIMENT_ID = "portpy-lung-ga-seed0-primary-v1"
CUSTOM_EXPERIMENT_ID = "custom-not-pooled-with-seed0-primary"

PROTOCOL_NAME = "Lung_2Gy_30Fx"
GRID_STEP_DEG = 15.0
EXCLUDED_GANTRY_DEG = (180.0,)
DOWNSAMPLE_VOXEL_FACTORS = (6, 6, 1)
DOWNSAMPLE_BEAMLET_FACTOR = 4

PRIMARY_K = 7
PRIMARY_POPULATION = 20
PRIMARY_GENERATIONS = 40
PRIMARY_MUTATION_RATE = 0.15
PRIMARY_SEED = 0

GA_SOURCE_FILES = (
    "ga_bao.py",
    "scripts/beam_angles.py",
    "scripts/experiment_protocol.py",
)
PIPELINE_SOURCE_FILES = GA_SOURCE_FILES + (
    "scripts/clinical_compare.py",
    "scripts/objective_terms.py",
    "scripts/plot_dvh.py",
    "scripts/run_patient_batch.py",
    "scripts/timing.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str | None:
    source = Path(path)
    try:
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def downsample_dimensions(
    ct_resolution_xyz_mm: Iterable[float],
    finest_beamlet_width_mm: float,
    finest_beamlet_height_mm: float,
) -> tuple[list[float], float, float]:
    """Apply the cohort's one canonical downsampling recipe."""
    resolution = list(ct_resolution_xyz_mm)
    if len(resolution) != len(DOWNSAMPLE_VOXEL_FACTORS):
        raise ValueError("CT resolution must contain exactly three axes")
    opt_vox = [
        value * factor
        for value, factor in zip(resolution, DOWNSAMPLE_VOXEL_FACTORS)
    ]
    return (
        opt_vox,
        finest_beamlet_width_mm * DOWNSAMPLE_BEAMLET_FACTOR,
        finest_beamlet_height_mm * DOWNSAMPLE_BEAMLET_FACTOR,
    )


def scientific_config(
    *,
    k: int,
    population: int,
    generations: int,
    mutation_rate: float,
    seed: int,
    downsampled: bool,
    protocol_name: str = PROTOCOL_NAME,
) -> dict[str, Any]:
    return {
        "protocol_name": protocol_name,
        "beam_count": int(k),
        "population": int(population),
        "generations": int(generations),
        "mutation_rate": float(mutation_rate),
        "seed": int(seed),
        "candidate_grid_step_deg": GRID_STEP_DEG,
        "excluded_gantry_deg": list(EXCLUDED_GANTRY_DEG),
        "search_resolution": "downsampled" if downsampled else "full_resolution",
        "downsample_voxel_factors": list(DOWNSAMPLE_VOXEL_FACTORS),
        "downsample_beamlet_factor": DOWNSAMPLE_BEAMLET_FACTOR,
        "final_evaluation_resolution": "full_resolution",
    }


def primary_scientific_config() -> dict[str, Any]:
    return scientific_config(
        k=PRIMARY_K,
        population=PRIMARY_POPULATION,
        generations=PRIMARY_GENERATIONS,
        mutation_rate=PRIMARY_MUTATION_RATE,
        seed=PRIMARY_SEED,
        downsampled=True,
    )


def is_primary_config(config: dict[str, Any]) -> bool:
    return config == primary_scientific_config()


def result_scientific_config(result: dict[str, Any]) -> dict[str, Any]:
    """Read a new manifest or reconstruct the common fields from a legacy result."""
    manifest = result.get("protocol_manifest")
    if isinstance(manifest, dict) and isinstance(manifest.get("scientific_config"), dict):
        return manifest["scientific_config"]
    return scientific_config(
        k=result.get("k"),
        population=result.get("pop"),
        generations=result.get("gens"),
        mutation_rate=result.get("mutation_rate"),
        seed=result.get("seed"),
        downsampled=True,
    )


def primary_config_mismatches(result: dict[str, Any]) -> list[str]:
    expected = primary_scientific_config()
    try:
        actual = result_scientific_config(result)
    except (TypeError, ValueError):
        return ["GA result is missing one or more primary protocol fields"]
    return [
        f"{key}: expected {expected[key]!r}, found {actual.get(key)!r}"
        for key in expected
        if actual.get(key) != expected[key]
    ]


def _git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _portpy_source_hashes() -> dict[str, str | None]:
    """Fingerprint the installed PortPy files that define matrices and solves.

    This also captures the locally applied downsampler patch, which a package
    version alone cannot distinguish.
    """
    spec = importlib.util.find_spec("portpy")
    if spec is None or not spec.submodule_search_locations:
        return {}
    package_root = Path(next(iter(spec.submodule_search_locations)))
    files = (
        "photon/influence_matrix.py",
        "photon/optimization.py",
    )
    return {relative: file_sha256(package_root / relative) for relative in files}


def code_provenance(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    source_hashes = {
        relative: file_sha256(root / relative)
        for relative in PIPELINE_SOURCE_FILES
    }
    ga_source_hashes = {
        relative: source_hashes[relative]
        for relative in GA_SOURCE_FILES
    }
    portpy_source_hashes = _portpy_source_hashes()
    return {
        "git_commit": _git_output(root, "rev-parse", "HEAD"),
        "git_dirty": bool(_git_output(root, "status", "--porcelain")),
        "source_files_sha256": source_hashes,
        "source_bundle_sha256": fingerprint(source_hashes),
        "ga_source_bundle_sha256": fingerprint(ga_source_hashes),
        "portpy_source_files_sha256": portpy_source_hashes,
        "portpy_source_bundle_sha256": fingerprint(portpy_source_hashes),
        "python_version": platform.python_version(),
        "packages": {
            name: _package_version(name)
            for name in ("portpy", "numpy", "cvxpy", "mosek")
        },
    }


def build_run_manifest(
    *,
    patient: str,
    candidate_pool: Iterable[int],
    angle_map: dict[int, float],
    clinician_beams: Iterable[int],
    config: dict[str, Any],
    repo_root: str | Path,
    data_dir: str | Path,
) -> dict[str, Any]:
    pool = [int(value) for value in candidate_pool]
    planner = [int(value) for value in clinician_beams]
    provenance = code_provenance(repo_root)
    beam_metadata = {
        str(beam_id): float(angle_map[beam_id])
        for beam_id in sorted(angle_map)
    }
    data_root = Path(data_dir)
    scientific_sha = fingerprint(config)
    manifest = {
        "manifest_schema": MANIFEST_SCHEMA,
        "experiment_id": EXPERIMENT_ID if is_primary_config(config) else CUSTOM_EXPERIMENT_ID,
        "created_at_utc": utc_now(),
        "patient": patient,
        "scientific_config": config,
        "scientific_config_sha256": scientific_sha,
        "candidate_pool": [
            {"beam_id": beam_id, "gantry_deg": float(angle_map[beam_id])}
            for beam_id in pool
        ],
        "candidate_pool_size": len(pool),
        "clinician_beams": [
            {"beam_id": beam_id, "gantry_deg": float(angle_map[beam_id])}
            for beam_id in planner
        ],
        "input_provenance": {
            "dataset": "PortPy-Project/PortPy_Dataset",
            "planner_beams_sha256": file_sha256(data_root / patient / "PlannerBeams.json"),
            "beam_metadata_sha256": fingerprint(beam_metadata),
        },
        "code_provenance": provenance,
        "analysis_policy": {
            "primary_cohort_fields": [
                "objective",
                "clinical_metrics",
                "winning_angles",
                "ga_vs_clinician_improvement",
            ],
            "seed_policy": "one predeclared seed; never select the best of several seeds",
            "new_only_fields": ["objective_terms", "timing_schema_2"],
        },
    }
    manifest["cache_identity"] = {
        "patient": patient,
        "scientific_config_sha256": scientific_sha,
        "candidate_pool_sha256": fingerprint(manifest["candidate_pool"]),
        "clinician_beams_sha256": fingerprint(manifest["clinician_beams"]),
        "beam_metadata_sha256": manifest["input_provenance"]["beam_metadata_sha256"],
        "planner_beams_sha256": manifest["input_provenance"]["planner_beams_sha256"],
        "ga_source_bundle_sha256": provenance["ga_source_bundle_sha256"],
        "portpy_version": provenance["packages"]["portpy"],
        "portpy_source_bundle_sha256": provenance["portpy_source_bundle_sha256"],
    }
    manifest["cache_identity_sha256"] = fingerprint(manifest["cache_identity"])
    return manifest


def cache_payload(identity: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cache_schema": CACHE_SCHEMA,
        "identity": identity,
        "identity_sha256": fingerprint(identity),
        "entries": entries,
    }


def validated_cache_entries(payload: Any, expected_identity: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("cache_schema") != CACHE_SCHEMA:
        raise RuntimeError(
            "legacy or unreadable GA cache has no verifiable protocol identity; "
            "use the automatically fingerprinted checkpoint path or pass a fresh --checkpoint"
        )
    expected_sha = fingerprint(expected_identity)
    if payload.get("identity") != expected_identity or payload.get("identity_sha256") != expected_sha:
        raise RuntimeError(
            "GA cache protocol mismatch; refusing to reuse solves from a different "
            "patient, configuration, dataset, or code version"
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError("GA cache entries are incomplete or unreadable")
    return entries


def batch_manifest(
    *,
    batch_id: str,
    patients: list[str],
    repo_root: str | Path,
) -> dict[str, Any]:
    config = primary_scientific_config()
    return {
        "batch_schema": BATCH_SCHEMA,
        "batch_id": batch_id,
        "created_at_utc": utc_now(),
        "experiment_id": EXPERIMENT_ID,
        "patients_predeclared": list(patients),
        "scientific_config": config,
        "scientific_config_sha256": fingerprint(config),
        "code_provenance": code_provenance(repo_root),
        "patients": {
            patient: {"status": "pending", "updated_at_utc": utc_now()}
            for patient in patients
        },
    }
