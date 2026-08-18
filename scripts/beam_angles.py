#!/usr/bin/env python3
"""Resolve PortPy beam IDs to real gantry angles.

WHY THIS EXISTS
---------------
The pipeline used to assume `beam_id * 5 == gantry_angle`, and built the candidate
pool as `range(0, 72, 3)` with beam 36 removed as "180 degrees". That assumption
holds for Lung_Patient_2 through Lung_Patient_10 and is FALSE from
Lung_Patient_11 onward: those patients store the clinician's beams first and the
angle grid after them, so the IDs no longer encode the angle at all.

    Lung_Patient_3   beam 9 -> 45 deg,  beam 36 -> 180 deg   (id * 5 holds)
    Lung_Patient_15  beam 9 -> 10 deg,  beam 36 -> 145 deg
    Lung_Patient_16  beam 9 -> 245 deg, beam 36 -> 0 deg

Running the old code on those patients silently searched a pool that was not the
intended 15-degree grid, failed to exclude the 180-degree beam it meant to
exclude, and reported wrong angles in every README and figure. Nothing raised an
error. So every angle decision now goes through this module, which reads each
beam's actual `gantry_angle` from its MetaData.json instead of doing arithmetic
on the ID.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ID = "PortPy-Project/PortPy_Dataset"
GRID_STEP_DEG = 15.0
EXCLUDED_DEG = (180.0,)
_TOL = 1e-6


def _beam_id(path: Path) -> int:
    return int(path.name.split("_")[1])


def local_angle_map(patient: str, data_dir) -> dict[int, float]:
    """beam_id -> gantry angle, from metadata already on disk."""
    beams = Path(data_dir) / patient / "Beams"
    angles: dict[int, float] = {}
    for path in beams.glob("Beam_*_MetaData.json"):
        try:
            angle = json.loads(path.read_text()).get("gantry_angle")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if angle is not None:
            angles[_beam_id(path)] = float(angle)
    return angles


def fetch_angle_map(patient: str, data_dir, token=None) -> dict[int, float]:
    """beam_id -> gantry angle, fetching the metadata if it is not on disk yet.

    Only the small *_MetaData.json files are pulled, never the multi-gigabyte
    Beam_*_Data.h5 payloads, so the pool can be chosen before committing to a
    large download. The fetch always runs rather than trusting whatever metadata
    is already on disk: a partial download leaves a partial map, and a partial
    map silently yields a partial pool.
    """
    from huggingface_hub import snapshot_download

    out = Path(data_dir).parent
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        allow_patterns=[
            f"data/{patient}/Beams/Beam_*_MetaData.json",
            f"data/{patient}/PlannerBeams.json",
        ],
        local_dir=str(out),
        max_workers=1,
        token=token,
    )
    return local_angle_map(patient, data_dir)


def _is_multiple(angle: float, step: float) -> bool:
    remainder = angle % step
    return remainder < _TOL or step - remainder < _TOL


def grid_pool(angles: dict[int, float], step_deg: float = GRID_STEP_DEG,
              excluded_deg=EXCLUDED_DEG) -> list[int]:
    """Beam IDs forming the candidate grid, one ID per distinct angle.

    Angles are matched on the value itself, so this returns the intended grid on
    every patient regardless of how the IDs happen to be ordered. Where several
    IDs share an angle (patients above 10 duplicate the clinician's angles into
    the grid) the lowest ID wins, which keeps the choice deterministic.
    """
    excluded = {float(value) for value in excluded_deg}
    best: dict[float, int] = {}
    for beam_id, angle in angles.items():
        normalized = angle % 360.0
        if any(abs(normalized - value) < _TOL for value in excluded):
            continue
        if not _is_multiple(normalized, step_deg):
            continue
        if normalized not in best or beam_id < best[normalized]:
            best[normalized] = beam_id
    return sorted(best.values())


def excluded_ids(angles: dict[int, float], excluded_deg=EXCLUDED_DEG) -> set[int]:
    """Every beam ID sitting on an excluded angle, whatever its ID happens to be."""
    excluded = {float(value) for value in excluded_deg}
    return {
        beam_id for beam_id, angle in angles.items()
        if any(abs(angle % 360.0 - value) < _TOL for value in excluded)
    }


def angles_for(angles: dict[int, float], beam_ids) -> list[float]:
    return [angles[int(beam_id)] for beam_id in beam_ids]


def format_angles(angles: dict[int, float], beam_ids) -> str:
    """Render real gantry angles, never `beam_id * 5`."""
    parts = []
    for beam_id in beam_ids:
        angle = angles.get(int(beam_id))
        parts.append("?" if angle is None else f"{angle:g}°")
    return ", ".join(parts)
