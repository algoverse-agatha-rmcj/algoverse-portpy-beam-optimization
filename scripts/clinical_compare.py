#!/usr/bin/env python
"""Re-solve beam sets at FULL resolution and score them against the protocol's clinical criteria.

The GA searches on down-sampled data, so its objective values are not a defensible
clinical claim. This re-solves each candidate plan at native resolution and reports the
16 Lung_2Gy_30Fx criteria (limit = must not exceed, goal = would like to meet).

Each set is solved with a pool equal to the set itself: at full resolution there is no
pool-dependent discretization, so this is equivalent to deactivating unused beams and
is far cheaper in memory.

    python scripts/clinical_compare.py
    python scripts/clinical_compare.py --downsample     # sanity check, much faster
"""
import argparse
import json
import time
from pathlib import Path

import portpy.photon as pp

PROTOCOL = "Lung_2Gy_30Fx"


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
    return plan, cc, sol, float(prob.value), inf.A.shape


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
    ap.add_argument("--patient", default="Lung_Patient_2")
    ap.add_argument("--downsample", action="store_true",
                    help="down-sample (fast sanity check); default is full resolution")
    ap.add_argument("--out", default="clinical_compare.json")
    args = ap.parse_args()

    planner = json.loads(
        (Path(args.data_dir) / args.patient / "PlannerBeams.json").read_text())["IDs"]
    plans = {
        "expert": planner,
        "GA_A_with180": [6, 33, 36, 39, 51, 57, 66],
        "GA_B_no180": [9, 33, 39, 51, 57, 60, 66],
    }

    results = {}
    for name, beams in plans.items():
        print(f"\n=== {name}: beams {beams}  ({[b*5 for b in beams]} deg) ===", flush=True)
        t0 = time.time()
        plan, cc, sol, obj, shape = solve_set(args.data_dir, args.patient, beams, args.downsample)
        # sol has no 'dose_1d'; criteria are whole-course Gy, so scale by fractions.
        dose_1d = sol["inf_matrix"].A @ (sol["optimal_intensity"] * plan.get_num_of_fractions())
        rows = criteria_table(cc, sol, dose_1d)
        ptv_d95 = float(pp.Evaluation.get_dose(sol, struct="PTV", volume_per=95,
                                               dose_1d=dose_1d))
        results[name] = {"beams": beams, "objective": obj, "A_shape": list(shape),
                         "PTV_D95_Gy": ptv_d95, "criteria": rows,
                         "solve_time_s": round(time.time() - t0, 1)}
        print(f"objective {obj:.4f} | PTV D95 {ptv_d95:.2f} Gy | "
              f"A {shape} | {time.time()-t0:.0f}s", flush=True)
        Path(args.out).write_text(json.dumps(results, indent=2))

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
