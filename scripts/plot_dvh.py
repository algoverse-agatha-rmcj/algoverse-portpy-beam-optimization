#!/usr/bin/env python
"""Dose-volume histograms for the clinician plan vs. the two GA plans, as a PDF.

Solves each beam set at FULL resolution (same treatment as scripts/clinical_compare.py,
so the curves and that script's criteria table describe the same plans), extracts a DVH
curve per structure, and writes a two-page PDF:

    page 1  conventional overlay - clinician solid vs. GA B dashed, all structures
    page 2  one panel per structure, all three plans

Solving is the expensive part (~40 s per plan at full resolution, plus the influence
matrix load), so the curves are cached to an .npz. Re-plotting is free:

    python scripts/plot_dvh.py                      # solve, cache, plot
    python scripts/plot_dvh.py --from-cache         # re-plot only
    python scripts/plot_dvh.py --downsample         # fast sanity check, NOT clinical
"""
import argparse
import json
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


def page_panels(pdf, C, xmax, patient, downsampled):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.6), sharex=True, sharey=True)
    flat = axes.ravel()
    for ax, s in zip(flat, STRUCTS):
        for name in PLANS:
            ax.plot(C[f"{name}|{s}|x"], C[f"{name}|{s}|y"],
                    color=COLORS[s], linestyle=PLAN_STYLE[name], linewidth=1.8)
        style_axes(ax, xmax)
        ax.set_title(NICE[s], loc="left", fontsize=10, color=INK, fontweight="bold", pad=6)

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
    note = "Same curves, one structure per panel, all three plans."
    if downsampled:
        note = "DOWN-SAMPLED — illustrative shape only, not clinically valid. " + note
    fig.text(0.06, 0.925, note, fontsize=9, color=MUTED, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
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
    ap.add_argument("--out", default="dvh_lung_patient_2.pdf")
    args = ap.parse_args()

    if args.from_cache:
        C = dict(np.load(args.cache))
        print(f"loaded cached curves <- {args.cache}")
    else:
        C = collect(args.data_dir, args.patient, args.downsample, args.cache)

    downsampled = bool(C["downsampled"][0])
    xmax = max(float(C[f"{n}|{s}|x"][-1]) for n in PLANS for s in STRUCTS)
    xmax = 5 * np.ceil(xmax / 5)

    with PdfPages(args.out) as pdf:
        page_overlay(pdf, C, xmax, args.patient, downsampled)
        page_panels(pdf, C, xmax, args.patient, downsampled)
        d = pdf.infodict()
        d["Title"] = f"DVH — {args.patient}: GA vs. clinician beam angles"
        d["Subject"] = "Algoverse / PortPy beam-angle optimization"

    print(f"saved -> {args.out}")


if __name__ == "__main__":
    main()
