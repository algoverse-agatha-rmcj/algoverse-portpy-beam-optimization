#!/usr/bin/env python
"""
Resilient PortPy patient-data downloader.

Downloads one or more PortPy patients from Hugging Face into a `data/` folder
that sits NEXT TO the repo (i.e. <repo_parent>/data). That is exactly where the
example notebooks expect it (they use `data_dir = '../../data'`), and it keeps
the multi-GB dataset OUT of git.

Why this script instead of a one-line download call:
    The HuggingFace dataset files are served from the `xethub.hf.co` CDN. On
    many campus / corporate / antivirus networks, that CDN RESETS connections
    under parallel load (the default is 8 workers), which shows up as
    `WinError 10054` or `httpx.RemoteProtocolError` and then STALLS FOREVER.
    The fix that reliably works: a SINGLE connection (max_workers=1) plus a
    resume-on-failure retry loop. HuggingFace caches every completed file, so
    each retry makes forward progress.

Usage (run from the repo root, with the `portpy` conda env activated):
    python scripts/download_patient_data.py Lung_Patient_3
    python scripts/download_patient_data.py Lung_Patient_3 Lung_Patient_4
    python scripts/download_patient_data.py --beam-mode ga Lung_Patient_3
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Force the classic HTTP transport (not the Xet chunk protocol). Combined with
# max_workers=1 below, this is the combination proven to get past the resets.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_XET_DISABLE", "1")

# This file lives at <repo>/scripts/download_patient_data.py, so:
#   parents[0] = <repo>/scripts
#   parents[1] = <repo>
#   parents[2] = <repo_parent>   <-- we download here; data lands in <repo_parent>/data
REPO_PARENT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description="Resilient PortPy data downloader.")
    ap.add_argument("patients", nargs="+", help="e.g. Lung_Patient_3 Lung_Patient_4")
    ap.add_argument("--beam-mode", default="planner",
                    choices=["planner", "ga", "all", "none"],
                    help="'planner' = only expert beams (default, smaller); "
                         "'ga' = no-180 GA pool plus clinician beams; "
                         "'all' = every available beam.")
    ap.add_argument("--max-attempts", type=int, default=40)
    args = ap.parse_args()

    import portpy.photon as pp  # imported here so --help works without the env

    dest = REPO_PARENT / "data"
    print(f"Downloading into: {dest}")
    print(f"(the example notebooks read this as data_dir='../../data')\n")

    for patient in args.patients:
        print(f"==== {patient}  (beam_mode={args.beam_mode}) ====")
        for attempt in range(1, args.max_attempts + 1):
            try:
                # NOTE: download_portpy_data creates <out>/data/<patient>,
                # so out=REPO_PARENT gives <repo_parent>/data/<patient>.
                if args.beam_mode == "ga":
                    # Download only the grid the GA can actually select. The first call
                    # also fetches PlannerBeams.json; the second incrementally adds any
                    # off-grid clinician beams so the comparison remains fair.
                    ga_beams = [b for b in range(0, 72, 3) if b != 36]
                    pp.download_portpy_data(
                        patient, out=str(REPO_PARENT), beam_mode="ids",
                        beam_ids=ga_beams, max_workers=1)
                    planner_path = dest / patient / "PlannerBeams.json"
                    planner = json.loads(planner_path.read_text())["IDs"]
                    comparison_beams = sorted(set(ga_beams) | (set(planner) - {36}))
                    if comparison_beams != ga_beams:
                        pp.download_portpy_data(
                            patient, out=str(REPO_PARENT), beam_mode="ids",
                            beam_ids=comparison_beams, max_workers=1)
                    print(f"  GA beam pool: {len(comparison_beams)} beams "
                          f"(180 degrees excluded)")
                else:
                    pp.download_portpy_data(
                        patient,
                        out=str(REPO_PARENT),
                        beam_mode=args.beam_mode,
                        max_workers=1,           # <-- the critical setting
                    )
                print(f"  DONE: {patient}\n")
                break
            except Exception as e:  # noqa: BLE001 - we want to retry on anything
                first_line = str(e).splitlines()[0][:150] if str(e) else ""
                print(f"  attempt {attempt}/{args.max_attempts} failed: "
                      f"{type(e).__name__}: {first_line}")
                time.sleep(min(5 + attempt * 2, 30))  # capped backoff
        else:
            print(f"  GAVE UP on {patient} after {args.max_attempts} attempts.")
            sys.exit(1)

    print("All requested patients downloaded.")


if __name__ == "__main__":
    main()
