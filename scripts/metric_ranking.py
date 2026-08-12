"""Clinical-metric ranking rules used by the DVH report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def _rank(row: Mapping, value: float) -> tuple[int, float]:
    """Return a sortable rank: lower is better, with target constraints respected."""
    label = str(row.get("label", ""))
    goal = row.get("goal")
    limit = row.get("limit")

    if label.startswith("PTV ") and goal is not None:
        if limit is not None and value > limit:
            return 1, value - limit
        return 0, abs(value - goal)
    return 0, value


def select_best_plans(
    row: Mapping,
    plans: Iterable[str],
    tie_tolerance: float = 0.01,
) -> set[str]:
    """Select report winners, leaving a row unmarked when every plan is tied.

    Organ-at-risk criteria favor the lowest dose. PTV criteria with a goal favor the
    value closest to that goal while first excluding values above the clinical limit.
    """
    plan_names = list(plans)
    values = row.get("values", {})
    if not isinstance(values, Mapping) or any(values.get(name) is None for name in plan_names):
        return set()

    ranks = {name: _rank(row, float(values[name])) for name in plan_names}
    best_tier = min(rank[0] for rank in ranks.values())
    best_distance = min(rank[1] for rank in ranks.values() if rank[0] == best_tier)
    winners = {
        name
        for name, (tier, distance) in ranks.items()
        if tier == best_tier and distance - best_distance <= tie_tolerance
    }
    return set() if len(winners) == len(plan_names) else winners
