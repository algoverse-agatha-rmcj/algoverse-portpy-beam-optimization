#!/usr/bin/env python
"""Score one beam set with the same fitness the GA uses (default: the planner/expert beams).

The pool defaults to the GA's pool so the one-time down-sampling is IDENTICAL to the
GA run -- beamlet width is derived from the finest beam in the pool, so scoring against
a different pool would not be comparable.

    python scripts/score_beam_set.py --patient Lung_Patient_2
    python scripts/score_beam_set.py --patient Lung_Patient_2 --beams 0 9 15 30 33 42 60
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ga_bao import BAOProblem  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data-dir", default="../data")
ap.add_argument("--patient", default="Lung_Patient_2")
ap.add_argument("--beams", type=int, nargs="+", default=None,
                help="beam set to score (default: the planner/expert beams)")
ap.add_argument("--pool", type=int, nargs="+", default=None)
ap.add_argument("--no-downsample", action="store_true")
args = ap.parse_args()

planner = json.loads(
    (Path(args.data_dir) / args.patient / "PlannerBeams.json").read_text())["IDs"]
beams = args.beams or planner
pool = args.pool or sorted(set(range(0, 72, 3)) | set(planner))

print(f"patient : {args.patient}")
print(f"planner : {planner}")
print(f"scoring : {beams}")
print(f"pool    : {len(pool)} beams")

t0 = time.time()
problem = BAOProblem(args.data_dir, args.patient, pool,
                     downsample=not args.no_downsample)
score = problem.evaluate(beams)
print(f"\nfitness = {score:.4f}   ({time.time() - t0:.0f}s)")
