#!/usr/bin/env python3
"""Generate manuscript-ready tables and a vector cohort figure.

The source is the same full-resolution cohort summary used by
``scripts/analyze_cohort.py``. No plotting package is required.

Usage:
    python3 scripts/generate_paper_assets.py
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import math
from pathlib import Path
from typing import Any

if __package__:
    from .analyze_cohort import load_cohort, summarize
else:
    from analyze_cohort import load_cohort, summarize


TABLE_CRITERIA = (
    ("GTV maximum", "GTV max"),
    ("PTV maximum", "PTV max"),
    ("Esophagus mean", "ESOPHAGUS mean"),
    ("Heart mean", "HEART mean"),
    ("Left-lung maximum", "LUNG_L max"),
    ("Lungs excluding GTV mean", "LUNGS_NOT_GTV mean"),
    ("Lungs excluding GTV V20", "LUNGS_NOT_GTV V20Gy"),
)


def _criterion(summary: dict[str, Any], label: str) -> dict[str, Any]:
    for row in summary["clinical_criteria"]:
        if row["label"] == label:
            return row
    raise ValueError(f"missing cohort criterion: {label}")


def table_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    cohort = summary["cohort"]
    rows = [{
        "metric": "PTV D95",
        "n": cohort["n_patients"],
        "unit": "Gy",
        "clinician": cohort["expert_mean_ptv_d95_gy"],
        "ga": cohort["ga_mean_ptv_d95_gy"],
        "delta": (
            cohort["ga_mean_ptv_d95_gy"] - cohort["expert_mean_ptv_d95_gy"]
        ),
    }]
    for display, label in TABLE_CRITERIA:
        criterion = _criterion(summary, label)
        rows.append({
            "metric": display,
            "n": criterion["n_patients"],
            "unit": criterion["unit"],
            "clinician": criterion["expert_mean"],
            "ga": criterion["ga_mean"],
            "delta": criterion["mean_delta_ga_minus_expert"],
        })
    rows.append({
        "metric": "Protocol-limit violations",
        "n": cohort["n_patients"],
        "unit": "count",
        "clinician": cohort["expert_limit_violations"],
        "ga": cohort["ga_limit_violations"],
        "delta": cohort["ga_limit_violations"] - cohort["expert_limit_violations"],
    })
    return rows


def render_csv(summary: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=("metric", "n", "unit", "clinician", "ga", "delta"),
        lineterminator="\n",
    )
    writer.writeheader()
    for row in table_rows(summary):
        writer.writerow({
            **row,
            "clinician": f"{row['clinician']:.6f}",
            "ga": f"{row['ga']:.6f}",
            "delta": f"{row['delta']:.6f}",
        })
    return output.getvalue()


def _tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in value)


def _table_value(value: float, unit: str, signed: bool = False) -> str:
    if unit == "count":
        return f"{int(value):+d}" if signed else str(int(value))
    suffix = r"\%" if unit == "%" else ""
    number = f"{value:+.2f}" if signed else f"{value:.2f}"
    return number + suffix


def render_latex(summary: dict[str, Any]) -> str:
    cohort = summary["cohort"]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Full-resolution cohort metrics. Values are arithmetic means; "
        rf"the GA had a lower planning objective for {cohort['wins']}/{cohort['n_patients']} "
        rf"patients, with a mean improvement of {cohort['mean_objective_improvement_pct']:.2f}\%. "
        r"The difference column is GA minus clinician.}",
        r"\label{tab:cohort-results}",
        r"\small",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Metric & $n$ & Clinician & GA & Difference \\",
        r"\midrule",
    ]
    for row in table_rows(summary):
        unit = row["unit"]
        metric = _tex_escape(row["metric"])
        if unit not in {"", "count"}:
            metric += rf" ({_tex_escape(unit)})"
        lines.append(
            f"{metric} & {row['n']} & {_table_value(row['clinician'], unit)} & "
            f"{_table_value(row['ga'], unit)} & "
            f"{_table_value(row['delta'], unit, signed=True)} \\\\"
        )
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ])
    return "\n".join(lines)


def _nice_axis(values: list[float]) -> tuple[float, float, list[float]]:
    low = min(-5.0, math.floor(min(values) / 5.0) * 5.0)
    high = max(10.0, math.ceil(max(values) / 10.0) * 10.0)
    ticks = [low] if low < 0 else []
    ticks.extend(float(value) for value in range(0, int(high) + 1, 10))
    return low, high, ticks


def render_svg(summary: dict[str, Any]) -> str:
    patients = summary["patients"]
    cohort = summary["cohort"]
    values = [row["objective_improvement_pct"] for row in patients]
    axis_low, axis_high, ticks = _nice_axis(values)
    width, height = 900, 650
    left, right, top, bottom = 92, 72, 78, 62
    plot_width = width - left - right
    plot_height = height - top - bottom
    row_step = plot_height / len(patients)
    bar_height = min(19.0, row_step * 0.66)

    def x(value: float) -> float:
        return left + (value - axis_low) / (axis_high - axis_low) * plot_width

    zero_x = x(0.0)
    mean_value = summary["cohort"]["mean_objective_improvement_pct"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="title description">',
        '<title id="title">Per-patient full-resolution objective improvement</title>',
        '<desc id="description">Horizontal bars show the percentage objective '
        f'improvement for {cohort["n_patients"]} lung patients. Positive values favor '
        f'the genetic algorithm. {cohort["wins"]} values are positive and '
        f'{cohort["losses"]} are negative.</desc>',
        '<style>',
        'text{font-family:Arial,Helvetica,sans-serif;fill:#222}',
        '.tick{font-size:12px}.patient{font-size:13px}.value{font-size:12px;font-weight:600}',
        '.axis-label{font-size:14px}.legend{font-size:12px}.outlier{font-weight:700}',
        '.grid{stroke:#d9d9d9;stroke-width:1}.zero{stroke:#222;stroke-width:1.4}',
        '.mean{stroke:#555;stroke-width:1.4;stroke-dasharray:6 4}',
        '.win{fill:#0072B2}.loss{fill:#D55E00}',
        '</style>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        'fill="#fff" stroke="#777" stroke-width="1"/>',
    ]
    for tick in ticks:
        tick_x = x(tick)
        cls = "zero" if tick == 0 else "grid"
        parts.append(
            f'<line class="{cls}" x1="{tick_x:.2f}" y1="{top}" '
            f'x2="{tick_x:.2f}" y2="{height-bottom}"/>'
        )
        parts.append(
            f'<text class="tick" x="{tick_x:.2f}" y="{height-bottom+20}" '
            f'text-anchor="middle">{tick:g}</text>'
        )
    mean_x = x(mean_value)
    parts.append(
        f'<line class="mean" x1="{mean_x:.2f}" y1="{top}" '
        f'x2="{mean_x:.2f}" y2="{height-bottom}"/>'
    )

    for index, row in enumerate(patients):
        value = row["objective_improvement_pct"]
        center_y = top + row_step * (index + 0.5)
        value_x = x(value)
        start_x = min(zero_x, value_x)
        bar_width = max(abs(value_x - zero_x), 1.5)
        patient = row["patient"].replace("Lung_Patient_", "P")
        patient_class = "patient outlier" if patient in {"P14", "P17"} else "patient"
        outcome_class = "win" if value >= 0 else "loss"
        parts.append(
            f'<text class="{patient_class}" x="{left-10}" y="{center_y+4:.2f}" '
            f'text-anchor="end">{html.escape(patient)}</text>'
        )
        parts.append(
            f'<rect class="{outcome_class}" x="{start_x:.2f}" '
            f'y="{center_y-bar_height/2:.2f}" width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}"/>'
        )
        # Negative bars are narrow on the full cohort scale because P14 and P17 are
        # large positive outliers. Put their signed labels just right of zero so the
        # values do not collide with the patient labels in the left margin.
        label_x = value_x + 6 if value >= 0 else zero_x + 6
        anchor = "start"
        parts.append(
            f'<text class="value" x="{label_x:.2f}" y="{center_y+4:.2f}" '
            f'text-anchor="{anchor}">{value:+.2f}%</text>'
        )

    parts.extend([
        f'<text class="axis-label" x="{left + plot_width/2:.2f}" y="{height-14}" '
        'text-anchor="middle">Full-resolution objective improvement (%)</text>',
        f'<rect class="win" x="{left}" y="24" width="14" height="14"/>',
        f'<text class="legend" x="{left+20}" y="36">GA lower objective</text>',
        f'<rect class="loss" x="{left+170}" y="24" width="14" height="14"/>',
        f'<text class="legend" x="{left+190}" y="36">GA higher objective</text>',
        f'<line class="mean" x1="{left+355}" y1="31" x2="{left+385}" y2="31"/>',
        f'<text class="legend" x="{left+393}" y="36">Mean {mean_value:.2f}%</text>',
        f'<text class="legend" x="{width-right}" y="36" text-anchor="end">'
        'Positive favors GA</text>',
        '</svg>',
        '',
    ])
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/paper"))
    args = parser.parse_args()

    summary = summarize(load_cohort(args.results_dir))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "cohort_summary_table.csv": render_csv(summary),
        "cohort_summary_table.tex": render_latex(summary),
        "objective_improvement.svg": render_svg(summary),
    }
    for name, contents in outputs.items():
        path = args.out_dir / name
        path.write_text(contents, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
