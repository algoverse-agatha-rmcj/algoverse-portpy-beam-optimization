"""Label and serialize PortPy's solved objective components."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any


VOXEL_OBJECTIVE_TYPES = {
    "quadratic-overdose",
    "quadratic-underdose",
    "quadratic",
}
SUPPORTED_OBJECTIVE_TYPES = VOXEL_OBJECTIVE_TYPES | {"smoothness-quadratic"}


def active_objective_specs(
    objective_functions: Any,
    structure_names: Iterable[str],
    nonempty_structures: Iterable[str],
) -> list[dict[str, Any]]:
    """Return config rows that PortPy adds to ``Optimization.obj``, in order."""
    if not isinstance(objective_functions, list):
        raise ValueError("objective_functions must be a list")
    structures = set(structure_names)
    nonempty = set(nonempty_structures)
    active = []
    for index, spec in enumerate(objective_functions):
        if not isinstance(spec, dict):
            raise ValueError(f"objective function {index} must be an object")
        objective_type = spec.get("type")
        if objective_type not in SUPPORTED_OBJECTIVE_TYPES:
            continue
        if objective_type in VOXEL_OBJECTIVE_TYPES:
            structure = spec.get("structure_name")
            if structure not in structures or structure not in nonempty:
                continue
        active.append({**spec, "config_index": index})
    return active


def serialize_objective_terms(
    specs: Sequence[dict[str, Any]], values: Sequence[Any]
) -> list[dict[str, Any]]:
    """Pair active config rows with solved CVXPY expression values."""
    if len(specs) != len(values):
        raise ValueError(
            f"objective metadata has {len(specs)} terms but PortPy solved {len(values)}"
        )
    rows = []
    for spec, raw_value in zip(specs, values):
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError("objective term has no scalar solved value") from exc
        if not math.isfinite(value):
            raise ValueError("objective term must be finite")
        row = {
            "config_index": spec["config_index"],
            "type": spec["type"],
            "value": value,
        }
        for key in ("structure_name", "weight"):
            if key in spec:
                row[key] = spec[key]
        dose_keys = sorted(key for key in spec if "dose" in key)
        for key in dose_keys:
            row[key] = spec[key]
        rows.append(row)
    return rows
