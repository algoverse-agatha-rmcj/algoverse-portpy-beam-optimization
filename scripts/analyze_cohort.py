#!/usr/bin/env python3
"""Aggregate the committed GA-vs-clinician results into paper-ready evidence.

The full-resolution comparison JSON in each patient bundle is the source of truth.
All cohort aggregates use arithmetic means. The report keeps per-patient values and
tail timing statistics visible so unusually large cases are disclosed, not hidden by
changing the headline statistic.

Usage:
    python3 scripts/analyze_cohort.py
    python3 scripts/analyze_cohort.py --results-dir results
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from statistics import fmean
from typing import Any

if __package__:
    from .json_io import atomic_write_json
else:
    from json_io import atomic_write_json


PATIENT_RE = re.compile(r"Lung_Patient_(\d+)")
ROUND_DIGITS = 6
FOCUS_CRITERIA = (
    "GTV max",
    "PTV max",
    "ESOPHAGUS mean",
    "HEART mean",
    "LUNG_L max",
    "LUNGS_NOT_GTV mean",
    "LUNGS_NOT_GTV V20Gy",
)


class CohortDataError(ValueError):
    """Raised when a committed result cannot be compared safely."""


def _number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CohortDataError(f"{context} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise CohortDataError(f"{context} must be finite")
    return value


def _rounded(value: float) -> float:
    return round(float(value), ROUND_DIGITS)


def _patient_number(patient: str) -> int:
    match = PATIENT_RE.fullmatch(patient)
    if not match:
        raise CohortDataError(f"invalid patient directory name: {patient}")
    return int(match.group(1))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CohortDataError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CohortDataError(f"{path} must contain a JSON object")
    return payload


def _select_ga_plan(comparison: dict[str, Any], path: Path) -> tuple[str, dict[str, Any]]:
    # Patient 2 retains a named legacy-with-180 plan. GA_B_no180 is its authoritative
    # current plan; later bundles use the simpler GA key.
    key = "GA" if "GA" in comparison else "GA_B_no180"
    plan = comparison.get(key)
    if not isinstance(plan, dict):
        raise CohortDataError(f"{path}: missing authoritative GA plan")
    return key, plan


def _criteria_by_label(rows: Any, context: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise CohortDataError(f"{context} criteria must be a list")
    collapsed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("label"), str):
            raise CohortDataError(f"{context} criterion {index} is malformed")
        if row.get("value") is None:
            continue
        label = row["label"]
        value = _number(row["value"], f"{context} {label}")
        unit = row.get("unit", "")
        existing = collapsed.get(label)
        if existing is not None:
            if existing["unit"] != unit or not math.isclose(existing["value"], value):
                raise CohortDataError(f"{context} has conflicting duplicate rows for {label}")
            continue
        collapsed[label] = {"value": value, "unit": unit}
    return collapsed


def _limit_violations(rows: Any) -> int:
    if not isinstance(rows, list):
        return 0
    return sum(isinstance(row, dict) and row.get("pass_limit") is False for row in rows)


def load_patient(path: Path) -> dict[str, Any]:
    patient = path.parents[1].name
    patient_number = _patient_number(patient)
    comparison = _read_json(path)
    expert = comparison.get("expert")
    if not isinstance(expert, dict):
        raise CohortDataError(f"{path}: missing expert plan")
    ga_key, ga = _select_ga_plan(comparison, path)

    expert_objective = _number(expert.get("objective"), f"{patient} expert objective")
    ga_objective = _number(ga.get("objective"), f"{patient} GA objective")
    if expert_objective == 0:
        raise CohortDataError(f"{patient} expert objective cannot be zero")
    improvement = 100.0 * (expert_objective - ga_objective) / expert_objective
    tolerance = 1e-9 * max(1.0, abs(expert_objective), abs(ga_objective))
    if ga_objective < expert_objective - tolerance:
        outcome = "win"
    elif ga_objective > expert_objective + tolerance:
        outcome = "loss"
    else:
        outcome = "tie"

    expert_d95 = _number(expert.get("PTV_D95_Gy"), f"{patient} expert PTV D95")
    ga_d95 = _number(ga.get("PTV_D95_Gy"), f"{patient} GA PTV D95")
    ga_result_path = (
        path.parents[1] / "ga_runs" / f"{patient}_ga_downsampled_seed_0.json"
    )
    ga_result = _read_json(ga_result_path)
    wall_time = ga_result.get("wall_time_s")
    wall_time_s = None if wall_time is None else _number(wall_time, f"{patient} wall time")
    solve_time = ga_result.get("solve_time_s")
    if solve_time is not None and not isinstance(solve_time, dict):
        raise CohortDataError(f"{ga_result_path}: solve_time_s must be an object")
    history = ga_result.get("history")
    population = ga_result.get("pop")
    wall_time_scope = "unknown"
    if (
        isinstance(history, list)
        and history
        and isinstance(history[0], dict)
        and history[0].get("unique_solves") is not None
        and population is not None
    ):
        initial_solves = _number(
            history[0]["unique_solves"], f"{patient} initial unique solves"
        )
        population_size = _number(population, f"{patient} population")
        wall_time_scope = (
            "resumed_segment" if initial_solves > population_size else "full_run"
        )

    return {
        "patient": patient,
        "patient_number": patient_number,
        "ga_plan_key": ga_key,
        "expert_objective": expert_objective,
        "ga_objective": ga_objective,
        "objective_improvement_pct": improvement,
        "outcome": outcome,
        "expert_ptv_d95_gy": expert_d95,
        "ga_ptv_d95_gy": ga_d95,
        "ptv_d95_delta_gy": ga_d95 - expert_d95,
        "expert_criteria": _criteria_by_label(
            expert.get("criteria"), f"{patient} expert"
        ),
        "ga_criteria": _criteria_by_label(ga.get("criteria"), f"{patient} GA"),
        "expert_limit_violations": _limit_violations(expert.get("criteria")),
        "ga_limit_violations": _limit_violations(ga.get("criteria")),
        "wall_time_s": wall_time_s,
        "wall_time_scope": wall_time_scope,
        "solve_time_s": solve_time,
    }


def load_cohort(results_dir: Path) -> list[dict[str, Any]]:
    paths = list(results_dir.glob(
        "Lung_Patient_*/clinical_comparison/"
        "Lung_Patient_*_clinical_metrics_full_resolution.json"
    ))
    if not paths:
        raise CohortDataError(f"no full-resolution comparisons found under {results_dir}")
    patients = [load_patient(path) for path in paths]
    patients.sort(key=lambda row: row["patient_number"])
    numbers = [row["patient_number"] for row in patients]
    if len(numbers) != len(set(numbers)):
        raise CohortDataError("duplicate patient bundles found")
    return patients


def _criterion_summary(patients: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_labels: list[str] = []
    for patient in patients:
        for label in patient["expert_criteria"]:
            if label not in ordered_labels:
                ordered_labels.append(label)
        for label in patient["ga_criteria"]:
            if label not in ordered_labels:
                ordered_labels.append(label)

    summaries = []
    for label in ordered_labels:
        pairs = []
        units = set()
        missing = []
        for patient in patients:
            expert = patient["expert_criteria"].get(label)
            ga = patient["ga_criteria"].get(label)
            if expert is None or ga is None:
                missing.append(patient["patient"])
                continue
            units.update((expert["unit"], ga["unit"]))
            pairs.append((expert["value"], ga["value"]))
        if len(units) > 1:
            raise CohortDataError(f"criterion {label} mixes units: {sorted(units)}")
        if not pairs:
            continue
        deltas = [ga - expert for expert, ga in pairs]
        summaries.append({
            "label": label,
            "unit": next(iter(units), ""),
            "n_patients": len(pairs),
            "missing_patients": missing,
            "expert_mean": _rounded(fmean(expert for expert, _ in pairs)),
            "ga_mean": _rounded(fmean(ga for _, ga in pairs)),
            "mean_delta_ga_minus_expert": _rounded(fmean(deltas)),
            "ga_lower_n": sum(delta < -1e-9 for delta in deltas),
            "ga_higher_n": sum(delta > 1e-9 for delta in deltas),
            "equal_n": sum(abs(delta) <= 1e-9 for delta in deltas),
        })
    return summaries


def _timing_summary(patients: list[dict[str, Any]]) -> dict[str, Any]:
    full_run_wall_times = [
        p["wall_time_s"] for p in patients
        if p["wall_time_s"] is not None and p["wall_time_scope"] == "full_run"
    ]
    resumed_wall_time_patients = [
        p["patient"] for p in patients if p["wall_time_scope"] == "resumed_segment"
    ]
    unknown_wall_time_patients = [
        p["patient"] for p in patients
        if p["wall_time_s"] is not None and p["wall_time_scope"] == "unknown"
    ]
    measured_solves = 0
    measured_total_s = 0.0
    reported_p95 = []
    reported_max = []
    timing_patients = []
    inconsistencies = []
    for patient in patients:
        stats = patient["solve_time_s"]
        if not isinstance(stats, dict):
            continue
        raw_count = _number(stats.get("measured_solves"), "measured_solves")
        if raw_count <= 0 or not raw_count.is_integer():
            raise CohortDataError("measured_solves must be a positive integer")
        count = int(raw_count)
        total = _number(stats.get("total_s"), "total_s")
        mean = _number(stats.get("mean_s"), "mean_s")
        timing_patients.append(patient["patient"])
        measured_solves += count
        measured_total_s += total
        if stats.get("p95_s") is not None:
            reported_p95.append(_number(stats["p95_s"], "p95_s"))
        if stats.get("max_s") is not None:
            reported_max.append(_number(stats["max_s"], "max_s"))
        if not math.isclose(mean, total / count, rel_tol=0.01, abs_tol=0.01):
            inconsistencies.append(
                f"{patient['patient']}: mean_s does not match total_s / measured_solves"
            )
        wall = patient["wall_time_s"]
        if (
            wall is not None
            and patient["wall_time_scope"] == "full_run"
            and total > wall * 1.05
        ):
            inconsistencies.append(
                f"{patient['patient']}: solve total {total:.1f}s exceeds GA wall time "
                f"{wall:.1f}s"
            )
    return {
        "patients_with_full_run_wall_time": len(full_run_wall_times),
        "mean_full_run_ga_wall_time_s": (
            _rounded(fmean(full_run_wall_times)) if full_run_wall_times else None
        ),
        "resumed_wall_time_patients": resumed_wall_time_patients,
        "unknown_wall_time_patients": unknown_wall_time_patients,
        "patients_with_per_solve_timing": len(timing_patients),
        "per_solve_timing_patients": timing_patients,
        "measured_solves": measured_solves,
        "pooled_mean_s": (
            _rounded(measured_total_s / measured_solves) if measured_solves else None
        ),
        "largest_reported_p95_s": max(reported_p95, default=None),
        "largest_reported_max_s": max(reported_max, default=None),
        "inconsistencies": inconsistencies,
    }


def _focused_patient(patient: dict[str, Any], review_reason: str) -> dict[str, Any]:
    criteria = []
    for label in FOCUS_CRITERIA:
        expert = patient["expert_criteria"].get(label)
        ga = patient["ga_criteria"].get(label)
        if expert is None or ga is None:
            criteria.append({"label": label, "missing": True})
            continue
        if expert["unit"] != ga["unit"]:
            raise CohortDataError(
                f"{patient['patient']} criterion {label} mixes units"
            )
        criteria.append({
            "label": label,
            "unit": expert["unit"],
            "expert": _rounded(expert["value"]),
            "ga": _rounded(ga["value"]),
            "delta_ga_minus_expert": _rounded(ga["value"] - expert["value"]),
        })
    return {
        "patient": patient["patient"],
        "review_reason": review_reason,
        "outcome": patient["outcome"],
        "objective_improvement_pct": _rounded(
            patient["objective_improvement_pct"]
        ),
        "ptv_d95_delta_gy": _rounded(patient["ptv_d95_delta_gy"]),
        "clinical_deltas": criteria,
    }


def summarize(patients: list[dict[str, Any]]) -> dict[str, Any]:
    if not patients:
        raise CohortDataError("cohort cannot be empty")
    public_patients = []
    for patient in patients:
        public_patients.append({
            key: (_rounded(value) if isinstance(value, float) else value)
            for key, value in patient.items()
            if key not in {"expert_criteria", "ga_criteria", "solve_time_s"}
        })

    ranked_objective = sorted(
        public_patients,
        key=lambda row: abs(row["objective_improvement_pct"]),
        reverse=True,
    )
    ranked_d95 = sorted(
        public_patients,
        key=lambda row: abs(row["ptv_d95_delta_gy"]),
        reverse=True,
    )
    losses = [row["patient"] for row in public_patients if row["outcome"] == "loss"]
    loss_rows = [patient for patient in patients if patient["outcome"] == "loss"]
    largest_wins = sorted(
        (patient for patient in patients if patient["outcome"] == "win"),
        key=lambda row: row["objective_improvement_pct"],
        reverse=True,
    )[:2]
    focused_patients = [
        _focused_patient(patient, "GA loss") for patient in loss_rows
    ] + [
        _focused_patient(patient, "largest GA gain") for patient in largest_wins
    ]
    objective_improvements = [
        row["objective_improvement_pct"] for row in public_patients
    ]
    without_largest_two = sorted(objective_improvements, reverse=True)[2:]
    return {
        "methodology": {
            "source": "full-resolution GA-vs-clinician comparison JSON",
            "aggregate": "arithmetic mean",
            "objective_improvement_pct": "100 * (expert - GA) / expert; positive favors GA",
            "clinical_delta": "GA - expert; positive means higher dose/volume under GA",
        },
        "cohort": {
            "n_patients": len(public_patients),
            "patients": [row["patient"] for row in public_patients],
            "wins": sum(row["outcome"] == "win" for row in public_patients),
            "losses": sum(row["outcome"] == "loss" for row in public_patients),
            "ties": sum(row["outcome"] == "tie" for row in public_patients),
            "mean_objective_improvement_pct": _rounded(fmean(
                objective_improvements
            )),
            "mean_objective_improvement_excluding_two_largest_gains_pct": (
                _rounded(fmean(without_largest_two))
                if without_largest_two else None
            ),
            "expert_mean_objective": _rounded(fmean(
                row["expert_objective"] for row in public_patients
            )),
            "ga_mean_objective": _rounded(fmean(
                row["ga_objective"] for row in public_patients
            )),
            "expert_mean_ptv_d95_gy": _rounded(fmean(
                row["expert_ptv_d95_gy"] for row in public_patients
            )),
            "ga_mean_ptv_d95_gy": _rounded(fmean(
                row["ga_ptv_d95_gy"] for row in public_patients
            )),
            "expert_limit_violations": sum(
                row["expert_limit_violations"] for row in public_patients
            ),
            "ga_limit_violations": sum(
                row["ga_limit_violations"] for row in public_patients
            ),
        },
        "patients": public_patients,
        "clinical_criteria": _criterion_summary(patients),
        "timing": _timing_summary(patients),
        "review_priorities": {
            "loss_patients": losses,
            "mean_loss_pct": _rounded(fmean(
                row["objective_improvement_pct"]
                for row in public_patients if row["outcome"] == "loss"
            )) if loss_rows else None,
            "focused_patients": focused_patients,
            "largest_absolute_objective_changes": [
                {
                    "patient": row["patient"],
                    "objective_improvement_pct": row["objective_improvement_pct"],
                    "expert_ptv_d95_gy": row["expert_ptv_d95_gy"],
                    "ga_ptv_d95_gy": row["ga_ptv_d95_gy"],
                }
                for row in ranked_objective[:3]
            ],
            "largest_absolute_ptv_d95_changes": [
                {
                    "patient": row["patient"],
                    "ptv_d95_delta_gy": row["ptv_d95_delta_gy"],
                    "objective_improvement_pct": row["objective_improvement_pct"],
                }
                for row in ranked_d95[:3]
            ],
        },
    }


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _focused_delta(row: dict[str, Any], label: str) -> str:
    criterion = next(
        item for item in row["clinical_deltas"] if item["label"] == label
    )
    if criterion.get("missing"):
        return "-"
    return f"{criterion['delta_ga_minus_expert']:+.2f}"


def render_markdown(summary: dict[str, Any]) -> str:
    cohort = summary["cohort"]
    priorities = summary["review_priorities"]
    focused_losses = [
        row for row in priorities["focused_patients"]
        if row["review_reason"] == "GA loss"
    ]
    largest_loss_d95_change = max(
        (abs(row["ptv_d95_delta_gy"]) for row in focused_losses),
        default=0.0,
    )
    lines = [
        "# Cohort analysis",
        "",
        "Generated from the committed full-resolution GA-vs-clinician comparisons. "
        "All aggregate values are arithmetic means.",
        "",
        "## Headline",
        "",
        f"- {cohort['n_patients']} usable lung patients; "
        f"GA wins {cohort['wins']}, loses {cohort['losses']}, and ties {cohort['ties']}.",
        f"- Mean objective improvement: "
        f"{_fmt(cohort['mean_objective_improvement_pct'])}% "
        "(positive favors GA).",
        f"- Sensitivity disclosure: the arithmetic mean is "
        f"{_fmt(cohort['mean_objective_improvement_excluding_two_largest_gains_pct'])}% "
        "when the two largest gains are excluded.",
        f"- Mean PTV D95: expert {_fmt(cohort['expert_mean_ptv_d95_gy'])} Gy; "
        f"GA {_fmt(cohort['ga_mean_ptv_d95_gy'])} Gy.",
        f"- Protocol-limit violations: expert {cohort['expert_limit_violations']}; "
        f"GA {cohort['ga_limit_violations']}.",
        "",
        "## Per-patient objective and target coverage",
        "",
        "| Patient | Expert objective | GA objective | Improvement | Outcome | "
        "Expert PTV D95 | GA PTV D95 | D95 delta |",
        "|---|---:|---:|---:|:---:|---:|---:|---:|",
    ]
    for row in summary["patients"]:
        lines.append(
            f"| {row['patient'].replace('Lung_Patient_', 'P')} "
            f"| {_fmt(row['expert_objective'], 3)} "
            f"| {_fmt(row['ga_objective'], 3)} "
            f"| {row['objective_improvement_pct']:+.2f}% "
            f"| {row['outcome']} "
            f"| {_fmt(row['expert_ptv_d95_gy'])} Gy "
            f"| {_fmt(row['ga_ptv_d95_gy'])} Gy "
            f"| {row['ptv_d95_delta_gy']:+.2f} Gy |"
        )

    lines.extend([
        "",
        "## Mean clinical-criteria values",
        "",
        "The delta is GA minus expert. Positive means the GA plan delivered a higher "
        "dose or volume for that metric; clinical desirability depends on whether the "
        "row is a target or an organ at risk.",
        "",
        "| Criterion | n | Expert mean | GA mean | Mean delta | Missing |",
        "|---|---:|---:|---:|---:|:---|",
    ])
    for row in summary["clinical_criteria"]:
        unit = f" {row['unit']}" if row["unit"] else ""
        missing = ", ".join(p.replace("Lung_Patient_", "P")
                            for p in row["missing_patients"]) or "-"
        lines.append(
            f"| {row['label']} | {row['n_patients']} "
            f"| {_fmt(row['expert_mean'])}{unit} "
            f"| {_fmt(row['ga_mean'])}{unit} "
            f"| {row['mean_delta_ga_minus_expert']:+.2f}{unit} | {missing} |"
        )

    timing = summary["timing"]
    lines.extend([
        "",
        "## Compute timing",
        "",
        f"- Mean full-run GA wall time across "
        f"{timing['patients_with_full_run_wall_time']} patients: "
        f"{_fmt(timing['mean_full_run_ga_wall_time_s'] / 3600)} hours.",
    ])
    if timing["resumed_wall_time_patients"]:
        resumed = ", ".join(
            patient.replace("Lung_Patient_", "P")
            for patient in timing["resumed_wall_time_patients"]
        )
        lines.append(
            f"- {resumed} was resumed from a checkpoint; its wall time covers only "
            "the resumed process segment and is excluded from the full-run mean."
        )
    if timing["pooled_mean_s"] is not None:
        lines.append(
            f"- Pooled arithmetic mean across {timing['measured_solves']} measured "
            f"solves from {timing['patients_with_per_solve_timing']} patients: "
            f"{_fmt(timing['pooled_mean_s'], 3)} seconds per solve."
        )
        lines.append(
            f"- Tail disclosure: largest reported p95 "
            f"{_fmt(timing['largest_reported_p95_s'], 3)} seconds; largest observed "
            f"solve {_fmt(timing['largest_reported_max_s'], 3)} seconds."
        )
    if timing["inconsistencies"]:
        lines.append("- Timing records needing review: " + "; ".join(
            timing["inconsistencies"]
        ) + ".")

    largest = priorities["largest_absolute_objective_changes"]
    lines.extend([
        "",
        "## Review priorities",
        "",
        "- GA losses: " + ", ".join(
            patient.replace("Lung_Patient_", "P")
            for patient in priorities["loss_patients"]
        ) + ".",
        "- Largest absolute objective changes: " + ", ".join(
            f"{row['patient'].replace('Lung_Patient_', 'P')} "
            f"({row['objective_improvement_pct']:+.2f}%, expert/GA PTV D95 "
            f"{row['expert_ptv_d95_gy']:.2f}/{row['ga_ptv_d95_gy']:.2f} Gy)"
            for row in largest
        ) + ".",
        "- GTV target-versus-organ interpretation remains a clinical methodology "
        "decision; this report presents its raw mean delta without declaring a winner.",
        "",
        "## Focused loss and outlier analysis",
        "",
        f"The {len(focused_losses)} losses and the two largest gains are shown together. "
        "Clinical deltas are GA minus expert; units are Gy except V20, which is in "
        "percentage points.",
        "",
        "| Patient | Reason | Objective | D95 | GTV max | PTV max | Eso mean | "
        "Heart mean | Left lung max | Lungs-not-GTV mean | V20 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in priorities["focused_patients"]:
        lines.append(
            f"| {row['patient'].replace('Lung_Patient_', 'P')} "
            f"| {row['review_reason']} "
            f"| {row['objective_improvement_pct']:+.2f}% "
            f"| {row['ptv_d95_delta_gy']:+.2f} "
            f"| {_focused_delta(row, 'GTV max')} "
            f"| {_focused_delta(row, 'PTV max')} "
            f"| {_focused_delta(row, 'ESOPHAGUS mean')} "
            f"| {_focused_delta(row, 'HEART mean')} "
            f"| {_focused_delta(row, 'LUNG_L max')} "
            f"| {_focused_delta(row, 'LUNGS_NOT_GTV mean')} "
            f"| {_focused_delta(row, 'LUNGS_NOT_GTV V20Gy')} |"
        )
    top_gains = [
        row for row in priorities["focused_patients"]
        if row["review_reason"] == "largest GA gain"
    ]
    gain_names = " and ".join(
        row["patient"].replace("Lung_Patient_", "P") for row in top_gains
    )
    gain_d95 = " and ".join(f"{row['ptv_d95_delta_gy']:+.2f} Gy" for row in top_gains)
    lines.extend([
        "",
        f"Across the {len(focused_losses)} loss cases, mean objective improvement is "
        f"{priorities['mean_loss_pct']:+.2f}%. Their largest absolute PTV D95 change is "
        f"{largest_loss_d95_change:.2f} Gy. The two largest gains, {gain_names}, change "
        f"PTV D95 by {gain_d95}, respectively.",
    ])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--json-out", type=Path, default=Path("results/cohort_analysis.json")
    )
    parser.add_argument(
        "--markdown-out", type=Path, default=Path("results/cohort_analysis.md")
    )
    args = parser.parse_args()

    summary = summarize(load_cohort(args.results_dir))
    atomic_write_json(args.json_out, summary)
    markdown = render_markdown(summary)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Wrote {args.json_out} and {args.markdown_out}")


if __name__ == "__main__":
    main()
