#!/usr/bin/env python
"""Dose-volume histograms for the clinician plan vs. the two GA plans, as a PDF.

Solves each beam set at FULL resolution (same treatment as scripts/clinical_compare.py,
so the curves and that script's criteria table describe the same plans), extracts a DVH
curve per structure, and writes a three-page PDF:

    page 1  conventional overlay - clinician solid vs. GA B dashed, all structures
    page 2  one panel per structure, all three plans, each annotated with that
            structure's protocol metrics
    page 3  the full clinical-criteria table, all 16 Lung_2Gy_30Fx criteria

Pages 2 and 3 read their numbers from scripts/clinical_compare.py's JSON rather than
recomputing them, so the figure and the reported table cannot drift apart. That file
also fixes the resolution the numbers were measured at: the curves and the criteria
must come from the same treatment, or the comparison is not apples-to-apples, so
--criteria is cross-checked against the cached curves before anything is drawn.

Solving is the expensive part (~40 s per plan at full resolution, plus the influence
matrix load), so the curves are cached to an .npz. Re-plotting is free:

    python scripts/plot_dvh.py                      # solve, cache, plot
    python scripts/plot_dvh.py --from-cache         # re-plot only
    python scripts/plot_dvh.py --downsample         # fast sanity check, NOT clinical
"""
import argparse
import json
import textwrap
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

import portpy.photon as pp

PROTOCOL = "Lung_2Gy_30Fx"

STRUCTS = ["PTV", "HEART", "LUNGS_NOT_GTV", "ESOPHAGUS", "CORD"]
# Page 1 puts every curve on one axes, so its colours must be separable pairwise.
# These four clear the all-pairs CVD and normal-vision gates; adding a fifth does not
# (esophagus vs heart collide), so esophagus appears only in the faceted page 2, where
# each panel is titled and colour carries no discrimination load.
OVERLAY_STRUCTS = ["PTV", "HEART", "LUNGS_NOT_GTV", "CORD"]
COLORS = {"PTV": "#2a78d6", "HEART": "#eb6834", "LUNGS_NOT_GTV": "#1baf7a",
          "CORD": "#4a3aa7", "ESOPHAGUS": "#e34948"}
NICE = {"PTV": "PTV (target)", "HEART": "Heart", "LUNGS_NOT_GTV": "Lungs (minus GTV)",
        "ESOPHAGUS": "Esophagus", "CORD": "Spinal cord"}

PLANS = ["expert", "GA_A_with180", "GA_B_no180"]
PLAN_LABEL = {"expert": "Clinician", "GA_A_with180": "GA run A (180° allowed)",
              "GA_B_no180": "GA run B (180° removed)"}
PLAN_STYLE = {"expert": "solid", "GA_A_with180": "dashdot", "GA_B_no180": "dashed"}

INK, MUTED, GRID = "#0d1216", "#5a656d", "#dfe4e7"
OVER_LIMIT, MISSED_GOAL = "#c0392b", "#a86711"
# Short column heads for the in-panel metric blocks, where the full plan labels do not fit.
PLAN_ABBR = {"expert": "Clin", "GA_A_with180": "GA A", "GA_B_no180": "GA B"}

# Two criteria differing by less than this are the same number for reporting purposes:
# used both to fold the protocol's duplicate rows together and to grey out rows where
# all three plans land in the same place.
TIE_TOL = 0.01


def solve_set(data_dir, patient, beams, downsample):
    data = pp.DataExplorer(data_dir=data_dir)
    data.patient_id = patient
    ct = pp.CT(data)
    structs = pp.Structures(data)
    cc = pp.ClinicalCriteria(data, protocol_name=PROTOCOL)
    opt_params = data.load_config_opt_params(protocol_name=PROTOCOL)
    structs.create_opt_structures(opt_params=opt_params, clinical_criteria=cc)

    bm = pp.Beams(data, beam_ids=list(beams))
    inf = pp.InfluenceMatrix(ct=ct, structs=structs, beams=bm)
    if downsample:
        opt_vox = [r * f for r, f in zip(ct.get_ct_res_xyz_mm(), (6, 6, 1))]
        inf = inf.create_down_sample(
            beamlet_width_mm=bm.get_finest_beamlet_width() * 4,
            beamlet_height_mm=bm.get_finest_beamlet_height() * 4,
            opt_vox_xyz_res_mm=opt_vox)
    plan = pp.Plan(ct=ct, structs=structs, beams=bm, inf_matrix=inf, clinical_criteria=cc)

    opt = pp.Optimization(plan, opt_params=opt_params, clinical_criteria=cc)
    opt.create_cvxpy_problem()
    sol, prob = opt.solve(solver="MOSEK", verbose=False, return_cvxpy_prob=True)
    dose_1d = sol["inf_matrix"].A @ (sol["optimal_intensity"] * plan.get_num_of_fractions())
    return plan, sol, dose_1d, float(prob.value)


def collect(data_dir, patient, downsample, cache_path):
    planner = json.loads((Path(data_dir) / patient / "PlannerBeams.json").read_text())["IDs"]
    beam_sets = {"expert": planner,
                 "GA_A_with180": [6, 33, 36, 39, 51, 57, 66],
                 "GA_B_no180": [9, 33, 39, 51, 57, 60, 66]}

    out = {}
    for name in PLANS:
        beams = beam_sets[name]
        print(f"\n=== {name}: beams {beams} ({[b * 5 for b in beams]} deg) ===", flush=True)
        t0 = time.time()
        plan, sol, dose_1d, obj = solve_set(data_dir, patient, beams, downsample)
        for s in STRUCTS:
            x, y = pp.Evaluation.get_dvh(sol, struct=s, dose_1d=dose_1d)
            out[f"{name}|{s}|x"] = np.asarray(x, dtype=float)
            out[f"{name}|{s}|y"] = np.asarray(y, dtype=float) * 100.0
        out[f"{name}|beams"] = np.asarray(beams)
        out[f"{name}|objective"] = np.asarray([obj])
        print(f"objective {obj:.4f} | {time.time() - t0:.0f}s", flush=True)

    out["downsampled"] = np.asarray([1 if downsample else 0])
    np.savez_compressed(cache_path, **out)
    print(f"\ncurves cached -> {cache_path}")
    return out


def _tied(a, b):
    return a is not None and b is not None and abs(a - b) <= TIE_TOL


def load_criteria(path):
    """Read clinical_compare.py's JSON into one row per distinct measurement.

    The protocol lists some metrics twice — HEART V30Gy appears once carrying the 50%
    limit and once carrying the 48% goal — which would print as two identical table
    rows. Rows that share a label and agree on all three plans are folded into one
    carrying both thresholds.
    """
    raw = json.loads(Path(path).read_text())
    missing = [p for p in PLANS if p not in raw]
    if missing:
        raise SystemExit(f"{path}: no entry for {missing}. Re-run scripts/clinical_compare.py.")

    ref = raw[PLANS[0]]["criteria"]
    for p in PLANS[1:]:
        if [r["label"] for r in raw[p]["criteria"]] != [r["label"] for r in ref]:
            raise SystemExit(f"{path}: criteria rows differ between {PLANS[0]} and {p}; "
                             "the file is not a single comparison run.")

    rows, by_label = [], {}
    for i, r in enumerate(ref):
        values = {p: raw[p]["criteria"][i].get("value") for p in PLANS}
        prev = by_label.get(r["label"])
        if prev is not None and all(_tied(values[p], prev["values"][p]) for p in PLANS):
            for key in ("limit", "goal"):
                if prev[key] is None:
                    prev[key] = r.get(key)
            continue
        row = {"label": r["label"], "unit": r.get("unit"),
               "limit": r.get("limit"), "goal": r.get("goal"), "values": values}
        by_label[r["label"]] = row
        rows.append(row)
    return raw, rows


def check_provenance(C, raw, criteria_path):
    """Refuse to caption curves with numbers measured on a different plan or resolution.

    Jordan's correctness point from meeting 6: scoring GA angles on a down-sampled dose
    matrix while the clinician baseline is at full resolution invalidates the comparison.
    The same applies between the curves and the table printed beside them.
    """
    for name in PLANS:
        curve_beams = [int(b) for b in C[f"{name}|beams"]]
        table_beams = [int(b) for b in raw[name]["beams"]]
        if curve_beams != table_beams:
            raise SystemExit(
                f"{name}: cached curves use beams {curve_beams} but {criteria_path} "
                f"reports {table_beams}. Re-run both, or pass --criteria for this run.")

    recorded = {raw[n].get("downsampled") for n in PLANS}
    if len(recorded) != 1:
        raise SystemExit(f"{criteria_path}: plans disagree on resolution ({recorded}).")
    table_ds = recorded.pop()
    if table_ds is None:                       # written before the flag existed
        return None
    if bool(table_ds) != bool(C["downsampled"][0]):
        raise SystemExit(
            f"resolution mismatch: curves are "
            f"{'down-sampled' if C['downsampled'][0] else 'full resolution'} but "
            f"{criteria_path} is {'down-sampled' if table_ds else 'full resolution'}. "
            "Down-sampling does not preserve per-organ metrics, so the table would not "
            "describe the plotted curves.")
    return bool(table_ds)


def struct_rows(criteria, struct):
    """Protocol rows belonging to one structure, e.g. LUNGS_NOT_GTV max/mean/V20Gy."""
    return [r for r in criteria if r["label"].startswith(struct + " ")]


def best_plans(row):
    """Plans tied for the lowest value, or an empty set when all three are tied.

    Every Lung_2Gy_30Fx criterion is a ceiling (max dose, mean dose, or volume above a
    dose), so lower is better without exception. Structures that abut the target — heart
    max, lung max — sit at 66 Gy for all three plans; those rows carry no signal and are
    deliberately left unmarked. Marking every plan within TIE_TOL of the winner rather
    than the single argmin keeps two plans printing 66.00 from being typeset as if one
    beat the other.
    """
    vals = [v for v in row["values"].values() if v is not None]
    if len(vals) < len(PLANS) or max(vals) - min(vals) <= TIE_TOL:
        return set()
    lo = min(vals)
    return {p for p, v in row["values"].items() if v - lo <= TIE_TOL}


def value_color(row, plan):
    v = row["values"][plan]
    if v is None:
        return MUTED
    if row["limit"] is not None and v > row["limit"]:
        return OVER_LIMIT
    if row["goal"] is not None and v > row["goal"]:
        return MISSED_GOAL
    return INK


def style_axes(ax, xmax):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 100.5)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)


def page_overlay(pdf, C, xmax, patient, downsampled):
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    for s in OVERLAY_STRUCTS:
        for name in ("expert", "GA_B_no180"):
            ax.plot(C[f"{name}|{s}|x"], C[f"{name}|{s}|y"],
                    color=COLORS[s], linestyle=PLAN_STYLE[name],
                    linewidth=1.9, solid_capstyle="round")
    style_axes(ax, xmax)
    ax.set_xlabel("Dose (Gy)", fontsize=9.5, color=INK)
    ax.set_ylabel("Fractional volume (%)", fontsize=9.5, color=INK)

    struct_keys = [Line2D([], [], color=COLORS[s], lw=2.2, label=NICE[s])
                   for s in OVERLAY_STRUCTS]
    plan_keys = [Line2D([], [], color=MUTED, lw=2.2, linestyle=PLAN_STYLE[n],
                        label=PLAN_LABEL[n]) for n in ("expert", "GA_B_no180")]
    # both legends outside the axes: inside, they collide with the PTV shoulder
    first = ax.legend(handles=struct_keys, loc="upper left", bbox_to_anchor=(1.015, 1.0),
                      frameon=False, fontsize=9, labelcolor=INK, title="Structure")
    ax.add_artist(first)
    second = ax.legend(handles=plan_keys, loc="upper left", bbox_to_anchor=(1.015, 0.62),
                       frameon=False, fontsize=9, labelcolor=INK, title="Plan")
    for lg in (first, second):
        lg.get_title().set_fontsize(9)
        lg.get_title().set_color(MUTED)
        lg._legend_box.align = "left"

    fig.suptitle(f"Dose-volume histogram — {patient}", x=0.125, y=0.965,
                 ha="left", fontsize=14, fontweight="bold", color=INK)
    ax.set_title("Clinician plan vs. GA run B. A curve further left and lower means less "
                 "dose to that structure.",
                 loc="left", fontsize=9, color=MUTED, pad=10)
    note = ("Curves further left are better for organs; the PTV curve should stay high, then "
            "drop sharply.\nBoth plans deliver the same target coverage — the GA trades cord "
            "dose for heart sparing. Esophagus is on page 2.")
    if downsampled:
        note = "DOWN-SAMPLED — illustrative shape only, not clinically valid.\n" + note
    fig.text(0.075, 0.015, note, fontsize=8, color=MUTED, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 0.78, 0.93))
    pdf.savefig(fig)
    plt.close(fig)


def annotate_panel(ax, criteria, raw, struct):
    """Print this structure's protocol metrics for all three plans inside its panel.

    A DVH answers "which plan is lower" but not "by how much, and against what limit";
    the numbers are what a planner actually reads. Placement dodges the curves: an organ
    curve hugs the top-left and vacates the upper right, whereas the PTV curve sits at
    100% until it falls off a cliff, leaving the lower left free.
    """
    rows = struct_rows(criteria, struct)
    if struct == "PTV":
        # D95 is the coverage number the plans are matched on; not a protocol criterion,
        # so clinical_compare.py stores it outside the criteria list.
        rows = rows + [{"label": "PTV D95", "unit": "Gy", "limit": None, "goal": None,
                        "values": {p: raw[p].get("PTV_D95_Gy") for p in PLANS}}]
    if not rows:
        return

    x0, y_top = (0.055, 0.40) if struct == "PTV" else (0.335, 0.95)
    col_x = [x0 + 0.215, x0 + 0.435, x0 + 0.645]
    step = 0.078

    for x, name in zip(col_x, PLANS):
        ax.text(x, y_top, PLAN_ABBR[name], transform=ax.transAxes, ha="right", va="top",
                fontsize=6.4, color=MUTED, family="monospace")

    for i, row in enumerate(rows, start=1):
        y = y_top - i * step
        metric = row["label"][len(struct) + 1:]
        unit = "%" if row["unit"] == "%" else "Gy"
        ax.text(x0, y, f"{metric} {unit}", transform=ax.transAxes, ha="left", va="top",
                fontsize=6.4, color=MUTED, family="monospace")
        best = best_plans(row)
        for x, name in zip(col_x, PLANS):
            v = row["values"][name]
            ax.text(x, y, "n/a" if v is None else f"{v:.2f}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=6.4,
                    family="monospace",
                    color=MUTED if not best else value_color(row, name),
                    fontweight="bold" if name in best else "normal")


def page_panels(pdf, C, xmax, patient, downsampled, criteria, raw):
    fig, axes = plt.subplots(2, 3, figsize=(11, 7.2), sharex=True, sharey=True)
    flat = axes.ravel()
    for ax, s in zip(flat, STRUCTS):
        for name in PLANS:
            ax.plot(C[f"{name}|{s}|x"], C[f"{name}|{s}|y"],
                    color=COLORS[s], linestyle=PLAN_STYLE[name], linewidth=1.8)
        style_axes(ax, xmax)
        ax.set_title(NICE[s], loc="left", fontsize=10, color=INK, fontweight="bold", pad=6)
        annotate_panel(ax, criteria, raw, s)

    legend_ax = flat[len(STRUCTS)]
    legend_ax.axis("off")
    keys = [Line2D([], [], color=MUTED, lw=2.2, linestyle=PLAN_STYLE[n], label=PLAN_LABEL[n])
            for n in PLANS]
    legend_ax.legend(handles=keys, loc="center left", frameon=False, fontsize=9,
                     labelcolor=INK, title="Plan")

    for ax in axes[:, 0]:
        ax.set_ylabel("Fractional volume (%)", fontsize=9, color=INK)
    # sharex hides tick labels on the top row, but the legend occupies the slot under the
    # last top-row panel — so that panel has to carry its own axis
    ncol = axes.shape[1]
    exposed = [flat[i] for i in range(len(STRUCTS)) if i + ncol >= len(STRUCTS)]
    for ax in exposed:
        ax.set_xlabel("Dose (Gy)", fontsize=9, color=INK)
        ax.tick_params(labelbottom=True)

    fig.suptitle(f"DVH by structure — {patient}", x=0.06, y=0.97,
                 ha="left", fontsize=14, fontweight="bold", color=INK)
    note = ("Same curves, one structure per panel, all three plans, each annotated with "
            "that structure's protocol metrics.\nBold = best of the three; grey = the "
            "three plans are within 0.01 of each other, so the row carries no signal. "
            "Amber misses a goal, red exceeds a limit.")
    if downsampled:
        note = "DOWN-SAMPLED — illustrative shape only, not clinically valid. " + note
    fig.text(0.06, 0.935, note, fontsize=8.5, color=MUTED, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    pdf.savefig(fig)
    plt.close(fig)


def page_table(pdf, criteria, raw, patient, downsampled, criteria_path):
    """The reference paper's table: every protocol criterion, all three plans."""
    fig = plt.figure(figsize=(11, 8.5))

    label_x = 0.055
    thresh_x = (0.435, 0.505)                       # limit, goal (right-aligned)
    plan_x = (0.665, 0.795, 0.925)                  # clinician, GA A, GA B

    y, step = 0.855, 0.0345

    # Two-line plan headings: the full labels are far wider than a 0.13 column, so the
    # qualifier drops to its own line rather than colliding with the neighbour.
    HEAD = {"expert": ("Clinician", ""), "GA_A_with180": ("GA run A", "180° allowed"),
            "GA_B_no180": ("GA run B", "180° removed")}
    fig.text(label_x, y, "Criterion", fontsize=8.5, color=MUTED, va="bottom")
    for x, head in zip(thresh_x, ("Limit", "Goal")):
        fig.text(x, y, head, fontsize=8.5, color=MUTED, va="bottom", ha="right")
    for x, name in zip(plan_x, PLANS):
        top, sub = HEAD[name]
        fig.text(x, y, top, fontsize=8.5, color=INK, va="bottom", ha="right")
        fig.text(x, y - 0.019, sub, fontsize=7.5, color=MUTED, va="bottom", ha="right")
    rule_y = y - 0.030
    fig.add_artist(plt.Line2D([label_x, 0.945], [rule_y, rule_y],
                              color=MUTED, linewidth=0.9))

    def cell(x, yy, text, color=INK, weight="normal", size=8.5):
        fig.text(x, yy, text, fontsize=size, color=color, ha="right", va="center",
                 family="monospace", fontweight=weight)

    y = rule_y - 0.012
    for row in criteria:
        y -= step
        best = best_plans(row)
        fig.text(label_x, y, row["label"], fontsize=8.5, va="center",
                 color=INK if best else MUTED)
        for x, key in zip(thresh_x, ("limit", "goal")):
            t = "—" if row[key] is None else f"{row[key]:g}"
            cell(x, y, t, MUTED)
        for x, name in zip(plan_x, PLANS):
            v = row["values"][name]
            cell(x, y, "n/a" if v is None else f"{v:.2f}",
                 value_color(row, name) if best else MUTED,
                 "bold" if name in best else "normal")
        fig.text(0.955, y, row["unit"] or "", fontsize=7.5, color=MUTED, va="center")

    # PTV D95 and the objective are not protocol criteria: D95 is the coverage the plans
    # are matched on, and the objective is the GA's search signal, on a scale whose
    # percentages have no clinical meaning. Below the rule, unbolded.
    y -= step * 0.6
    fig.add_artist(plt.Line2D([label_x, 0.945], [y, y], color=GRID, linewidth=0.9))

    for label, get, fmt in (
            ("PTV D95 (target coverage)", lambda n: raw[n].get("PTV_D95_Gy"), "{:.2f}"),
            ("Objective value (search signal)", lambda n: raw[n].get("objective"), "{:.2f}"),
            ("Solve time", lambda n: raw[n].get("solve_time_s"), "{:.0f} s")):
        y -= step
        fig.text(label_x, y, label, fontsize=8.5, color=MUTED, va="center")
        for x, name in zip(plan_x, PLANS):
            v = get(name)
            cell(x, y, "n/a" if v is None else fmt.format(v), MUTED)

    fig.suptitle(f"Clinical criteria — {patient}", x=label_x, y=0.955,
                 ha="left", fontsize=14, fontweight="bold", color=INK)
    sub = ("Lung_2Gy_30Fx protocol. Every criterion is a ceiling, so lower is better; "
           "bold marks the best of the three plans.")
    fig.text(label_x, 0.912, sub, fontsize=9, color=MUTED, va="top")

    # Beam angles as a footnote block, not a table row: seven gantry angles are wider
    # than a column, and this is what identifies each plan, so it belongs with the
    # provenance. Monospace so the three plans' angles line up for comparison.
    head = "Beam angles (gantry°)"
    beams = "\n".join(
        f"{head if i == 0 else '':<{len(head)}s}   {HEAD[n][0]:<10s} "
        f"{', '.join(str(int(b) * 5) for b in raw[n]['beams'])}"
        for i, n in enumerate(PLANS))
    fig.text(label_x, 0.135, beams, fontsize=7.5, color=MUTED, va="top",
             linespacing=1.65, family="monospace")

    prose = (
        "Grey rows: the three plans agree within 0.01 — heart, lung and LUNGS_NOT_GTV max "
        "sit at 66 Gy for every plan because those structures abut the target, which is "
        "target dose leaking in rather than a property of the beam angles. "
        "Amber meets the limit but misses the goal; red exceeds the limit.\n"
        f"Source: {criteria_path}, "
        f"{'DOWN-SAMPLED — per-organ metrics NOT clinically valid' if downsampled else 'full resolution'}"
        " — the same solve the curves come from, so figure and table cannot drift apart."
    )
    wrapped = "\n".join(textwrap.fill(line, width=148) for line in prose.split("\n"))
    fig.text(label_x, 0.077, wrapped, fontsize=7.5, color=MUTED, va="top",
             linespacing=1.65)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="../data")
    ap.add_argument("--patient", default="Lung_Patient_2")
    ap.add_argument("--downsample", action="store_true",
                    help="fast sanity check; per-organ metrics are NOT preserved")
    ap.add_argument("--from-cache", action="store_true", help="re-plot without solving")
    ap.add_argument("--cache", default="dvh_curves.npz")
    ap.add_argument("--criteria", default="clinical_compare_full.json",
                    help="scripts/clinical_compare.py output; supplies the numbers on "
                         "pages 2 and 3, and must describe the same solve as the curves")
    ap.add_argument("--out", default="dvh_lung_patient_2.pdf")
    args = ap.parse_args()

    if args.from_cache:
        C = dict(np.load(args.cache))
        print(f"loaded cached curves <- {args.cache}")
    else:
        C = collect(args.data_dir, args.patient, args.downsample, args.cache)

    raw, criteria = load_criteria(args.criteria)
    table_ds = check_provenance(C, raw, args.criteria)
    if table_ds is None:
        print(f"note: {args.criteria} predates the 'downsampled' flag; resolution "
              "could not be cross-checked against the curves.")

    downsampled = bool(C["downsampled"][0])
    xmax = max(float(C[f"{n}|{s}|x"][-1]) for n in PLANS for s in STRUCTS)
    xmax = 5 * np.ceil(xmax / 5)

    with PdfPages(args.out) as pdf:
        page_overlay(pdf, C, xmax, args.patient, downsampled)
        page_panels(pdf, C, xmax, args.patient, downsampled, criteria, raw)
        page_table(pdf, criteria, raw, args.patient, downsampled, args.criteria)
        d = pdf.infodict()
        d["Title"] = f"DVH — {args.patient}: GA vs. clinician beam angles"
        d["Subject"] = "Algoverse / PortPy beam-angle optimization"

    print(f"saved -> {args.out}")


if __name__ == "__main__":
    main()
