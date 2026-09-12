#!/usr/bin/env python
"""
Patch PortPy's down-sampler for the current dataset format.

WHY
---
On the current HuggingFace data format, PortPy v1.1.4's
`InfluenceMatrix.down_sample_2d_grid` crashes with:

    TypeError: only 0-dimensional arrays can be converted to Python scalars

because the beamlet arrays are shape (1, N, 1) but the code assumes (1, N),
so indexing `width_mm[0][right_ind]` returns a length-1 array instead of a
scalar. The GA searches on down-sampled matrices, so this blocks the whole
experiment.

FIX
---
`np.ravel(...)` the position/width/height arrays to 1-D so indexing yields a
scalar. Mathematically identical; just fixes the shape assumption.

USAGE
-----
Run ONCE, in the activated `portpy` conda env, after installing PortPy:

    python scripts/patch_portpy_downsampler.py

Idempotent: safe to run repeatedly. Makes a `.orig_backup` the first time.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# The exact buggy block in PortPy v1.1.4 (site-packages/portpy/photon/influence_matrix.py)
ORIGINAL = """        x_positions = beamlets['position_x_mm'][0] - beamlets['width_mm'][0] / 2
        y_positions = beamlets['position_y_mm'][0] + beamlets['height_mm'][0] / 2
        right_ind = np.argmax(x_positions)
        bottom_ind = np.argmin(y_positions)
        # w_all = np.column_stack((x_positions, y_positions))  # top left corners of all beamlets
        x_coord = np.arange(np.min(x_positions), np.max(x_positions) + beamlets['width_mm'][0][right_ind], 2.5)
        y_coord = np.arange(np.max(y_positions), np.min(y_positions) - beamlets['height_mm'][0][bottom_ind], -2.5)"""

PATCHED = """        # PATCH: data arrays are shape (1, N, 1); ravel to 1-D so [right_ind] yields a scalar
        width_1d = np.ravel(beamlets['width_mm'][0])
        height_1d = np.ravel(beamlets['height_mm'][0])
        x_positions = np.ravel(beamlets['position_x_mm'][0]) - width_1d / 2
        y_positions = np.ravel(beamlets['position_y_mm'][0]) + height_1d / 2
        right_ind = np.argmax(x_positions)
        bottom_ind = np.argmin(y_positions)
        # w_all = np.column_stack((x_positions, y_positions))  # top left corners of all beamlets
        x_coord = np.arange(np.min(x_positions), np.max(x_positions) + width_1d[right_ind], 2.5)
        y_coord = np.arange(np.max(y_positions), np.min(y_positions) - height_1d[bottom_ind], -2.5)"""

MARKER = "PATCH: data arrays are shape (1, N, 1)"


def main() -> None:
    try:
        import portpy.photon.influence_matrix as im
    except Exception as exc:  # noqa: BLE001
        print("ERROR: could not import portpy. Activate the `portpy` env first.")
        print(f"       ({type(exc).__name__}: {exc})")
        sys.exit(1)

    target = Path(im.__file__)
    text = target.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"Already patched -> {target}")
        return

    if ORIGINAL not in text:
        print("WARNING: expected original code not found in")
        print(f"         {target}")
        print("Your PortPy version may differ from v1.1.4. No changes made.")
        sys.exit(2)

    backup = target.with_suffix(".py.orig_backup")
    if not backup.exists():
        shutil.copy2(target, backup)

    target.write_text(text.replace(ORIGINAL, PATCHED), encoding="utf-8")
    print("PortPy down-sampler patched successfully.")
    print(f"  file:   {target}")
    print(f"  backup: {backup}")


if __name__ == "__main__":
    main()
