#!/usr/bin/env python3
"""Re-solve beam sets at FULL resolution and score them against the protocol's clinical criteria.

The GA searches on down-sampled data, so its objective values are not a defensible
clinical claim. This re-solves each candidate plan at native resolution and reports the
16 Lung_2Gy_30Fx criteria (limit = must not exceed, goal = would like to meet).

Each set is solved with a pool equal to the set itself: at full resolution there is no
pool-dependent discretization, so this is equivalent to deactivating unused beams and
is far cheaper in memory.

    python scripts/clinical_compare.py --patient Lung_Patient_3
    python scripts/clinical_compare.py --patient Lung_Patient_3 --downsample
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beam_angles import excluded_ids, fetch_angle_map, format_angles
from experiment_protocol import (
    PROTOCOL_NAME,
    downsample_dimensions,
    fingerprint,
    primary_config_mismatches,
    result_scientific_config,
)
from objective_terms import active_objective_specs, serialize_objective_terms
from timing import TIMING_SCHEMA

import portpy.photon as pp

if __package__:
    from .json_io import atomic_write_json
else:
    from json_io import atomic_write_json

PROTOCOL = PROTOCOL_NAME


def solve_set(data_dir, patient, beams, downsample):
    setup_t0 = time.perf_counter()
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
        opt_vox, beamlet_width, beamlet_height = downsample_dimensions(
            ct.get_ct_res_xyz_mm(),
            bm.get_finest_beamlet_width(),
            bm.get_finest_beamlet_height(),
        )
        inf = inf.create_down_sample(
            beamlet_width_mm=beamlet_width,
            beamlet_height_mm=beamlet_height,
            opt_vox_xyz_res_mm=opt_vox)
    plan = pp.Plan(ct=ct, structs=structs, beams=bm, inf_matrix=inf, clinical_criteria=cc)

    opt = pp.Optimization(plan, opt_params=opt_params, clinical_criteria=cc)
    opt.create_cvxpy_problem()
    # Everything above is setup — loading the patient, building the influence matrix and,
    # when asked, down-sampling it. Timing it together with the solve made the down-sampled
    # variant pay for its own down-sampling and hid the speedup entirely; bracket MOSEK alone.
    setup_s = time.perf_counter() - setup_t0
    solve_t0 = time.perf_counter()
    sol, prob = opt.solve(solver="MOSEK", verbose=False, return_cvxpy_prob=True)
    solve_s = time.perf_counter() - solve_t0
    timing = {
        "setup_time_s": round(setup_s, 1),
        "solve_time_s": round(solve_s, 1),
        "total_time_s": round(setup_s + solve_s, 1),
    }
    structure_names = set(plan.structures.get_structures())
    nonempty_structures = {
        structure for structure in structure_names
        if len(inf.get_opt_voxels_idx(structure)) > 0
    }
    specs = active_objective_specs(
        opt_params.get("objective_functions", []),
        structure_names,
        nonempty_structures,
    )
    objective_terms = serialize_objective_terms(
        specs, [expression.value for expression in opt.obj]
    )
    if not math.isclose(
        sum(row["value"] for row in objective_terms),
        float(prob.value),
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        raise RuntimeError("serialized objective terms do not sum to total objective")
    return plan, cc, sol, float(prob.value), inf.A.shape, objective_terms, timing


def criteria_table(cc, sol, dose_1d):
    rows = []
    for c in cc.clinical_criteria_dict["criteria"]:
        p, con, t = c["parameters"], c.get("constraints", {}), c["type"]
        s = p["structure_name"]
        try:
            if t == "max_dose":
                val, unit = pp.Evaluation.get_max_dose(sol, struct=s, dose_1d=dose_1d), "Gy"
                label = f"{s} max"
            elif t == "mean_dose":
                val, unit = pp.Evaluation.get_mean_dose(sol, struct=s, dose_1d=dose_1d), "Gy"
                label = f"{s} mean"
            elif t == "dose_volume_V":
                val = pp.Evaluation.get_volume(sol, struct=s, dose_value_gy=p["dose_gy"],
                                               dose_1d=dose_1d)
                unit, label = "%", f"{s} V{p['dose_gy']}Gy"
            else:
                continue
        except Exception as exc:
            rows.append({"label": f"{s} {t}", "value": None, "err": f"{type(exc).__name__}"})
            continue
        limit = con.get("limit_dose_gy", con.get("limit_volume_perc"))
        goal = con.get("goal_dose_gy", con.get("goal_volume_perc"))
        rows.append({"label": label, "value": float(val), "unit": unit,
                     "limit": limit, "goal": goal,
                     "pass_limit": None if limit is None else bool(val <= limit),
                     "pass_goal": None if goal is None else bool(val <= goal)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="../data")
    ap.add_argument("--patient", required=True, help="PortPy patient ID, e.g. Lung_Patient_3")
    ap.add_argument(
        "--ga-result",
        default=None,
        help="GA result JSON (default: the patient's down-sampled seed-0 result)",
    )
    ap.add_argument("--downsample", action="store_true",
                    help="down-sample (fast sanity check); default is full resolution")
    ap.add_argument(
        "--require-primary-protocol",
        action="store_true",
        help="refuse GA results outside the frozen seed-0 20x40 primary cohort",
    )
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.ga_result is None:
        args.ga_result = str(
            Path("results") / args.patient / "ga_runs"
            / f"{args.patient}_ga_downsampled_seed_0.json"
        )

    ga_result_path = Path(args.ga_result)
    ga_result = json.loads(ga_result_path.read_text())
    if ga_result.get("patient") != args.patient:
        raise SystemExit(
            f"{ga_result_path}: patient is {ga_result.get('patient')!r}, "
            f"expected {args.patient!r}"
        )
    mismatches = primary_config_mismatches(ga_result)
    if args.require_primary_protocol and mismatches:
        raise SystemExit(
            f"{ga_result_path}: not compatible with the frozen seed-0 primary cohort:\n  - "
            + "\n  - ".join(mismatches)
        )
    source_config = result_scientific_config(ga_result)
    source_fingerprint = fingerprint(source_config)
    ga_beams = [int(b) for b in ga_result["best_angles"]]
    # Checked by real gantry angle: beam 36 is 180 degrees only on patients 2-10.
    angle_map = fetch_angle_map(args.patient, args.data_dir)
    at_180 = sorted(excluded_ids(angle_map).intersection(ga_beams))
    if at_180:
        raise SystemExit(
            f"{ga_result_path}: GA winner contains beam(s) {at_180} at 180 degrees; "
            "use the no-180 run"
        )

    if args.out is None:
        resolution = "downsampled" if args.downsample else "full_resolution"
        args.out = str(
            Path("results") / args.patient / "clinical_comparison"
            / f"{args.patient}_clinical_metrics_{resolution}.json"
        )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    planner = json.loads(
        (Path(args.data_dir) / args.patient / "PlannerBeams.json").read_text())["IDs"]
    plans = {
        "expert": planner,
        "GA": ga_beams,
    }

    results = {}
    for name, beams in plans.items():
        print(
            f"\n=== {name}: beams {beams}  "
            f"({format_angles(angle_map, beams)}) ===",
            flush=True,
        )
        t0 = time.time()
        plan, cc, sol, obj, shape, objective_terms, timing = solve_set(
            args.data_dir, args.patient, beams, args.downsample
        )
        # sol has no 'dose_1d'; criteria are whole-course Gy, so scale by fractions.
        dose_1d = sol["inf_matrix"].A @ (sol["optimal_intensity"] * plan.get_num_of_fractions())
        rows = criteria_table(cc, sol, dose_1d)
        ptv_d95 = float(pp.Evaluation.get_dose(sol, struct="PTV", volume_per=95,
                                               dose_1d=dose_1d))
        results[name] = {"beams": beams, "objective": obj,
                         "objective_terms": objective_terms, "A_shape": list(shape),
                         "downsampled": bool(args.downsample),
                         "source_protocol_fingerprint": source_fingerprint,
                         "evaluation_resolution": (
                             "downsampled" if args.downsample else "full_resolution"
                         ),
                         "PTV_D95_Gy": ptv_d95, "criteria": rows,
                         "timing_schema": TIMING_SCHEMA,
                         **timing,
                         "scored_time_s": round(time.time() - t0, 1)}
        if name == "GA":
            results[name]["source_ga_result"] = str(ga_result_path)
        print(f"objective {obj:.4f} | PTV D95 {ptv_d95:.2f} Gy | A {shape} | "
              f"setup {timing['setup_time_s']:.0f}s + solve "
              f"{timing['solve_time_s']:.0f}s", flush=True)
        atomic_write_json(args.out, results)

    # summary
    print("\n\n================ CLINICAL CRITERIA ================")
    labels = [r["label"] for r in results["expert"]["criteria"]]
    hdr = f"{'criterion':26s} {'limit':>7s} {'goal':>7s}" + "".join(
        f"{n:>16s}" for n in results)
    print(hdr)
    print("-" * len(hdr))
    for i, lab in enumerate(labels):
        base = results["expert"]["criteria"][i]
        line = f"{lab:26s} {str(base.get('limit','-')):>7s} {str(base.get('goal','-')):>7s}"
        for n in results:
            r = results[n]["criteria"][i]
            v = r.get("value")
            if v is None:
                line += f"{'n/a':>16s}"
            else:
                mark = "" if r.get("pass_limit") in (None, True) else " X"
                line += f"{v:>14.2f}{mark:2s}"
        print(line)
    print("\nobjective / PTV D95:")
    for n in results:
        print(f"  {n:16s} obj {results[n]['objective']:9.4f}   D95 {results[n]['PTV_D95_Gy']:.2f} Gy")
    print(f"\nsaved -> {args.out}")


if __name__ == "__main__":
    main()
