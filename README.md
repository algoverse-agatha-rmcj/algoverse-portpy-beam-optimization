# Algoverse: Beam-Angle Optimization on PortPy

Algoverse AI Research Fellowship project. We're extending prior linear-programming-based
radiotherapy beam-angle optimization by testing a genetic algorithm on open-source
[PortPy](https://github.com/PortPy-Project/PortPy) lung-cancer benchmark cases.

## Results

Experiment outputs are organized by patient under [`results/`](results/). Each completed
patient bundle keeps the GA result JSON, clinician comparison metrics, and its
dose-volume histogram (DVH) together. The matched primary cohort contains 18
seed-0 patients: Patients 2-11 and 14-21. Patients 12 and 13 are excluded because
their upstream PortPy data cannot produce comparable complete results.

## Frozen primary cohort and safe batching

The primary cohort protocol is frozen in
[`scripts/experiment_protocol.py`](scripts/experiment_protocol.py): 7 beams,
population 20, 40 generations, mutation rate 0.15, seed 0, a real-angle 15-degree
candidate grid with 180 degrees excluded, the existing `(6, 6, 1)` / `4`
downsampling recipe, and full-resolution rescoring of both plans.

The safeguards are passive: manifests, hashes, and validation do not expose the GA
to more patient data, evaluations, seeds, or search time. New results may record
corrected solver timing and objective-term detail, but combined old-plus-new cohort
analysis must use only the fields shared by both generations of artifacts. Never run
several seeds and select the best one for the primary cohort.

Launch a cohort extension through the batch runner with a stable, descriptive ID:

```bash
../portpy-venv/bin/python scripts/run_patient_batch.py \
  --batch-id lung-seed0-extension-20260826 \
  Lung_Patient_22 Lung_Patient_23 Lung_Patient_24
```

Before the first download, the runner writes `results/batches/<batch-id>.json` with
the exact predeclared patient list, frozen protocol, code hashes, and per-patient
status. Future GA results embed patient/configuration/data/code provenance. GA caches
are named by that identity and are rejected if any identity field differs; older
unidentified caches are never silently reused. A repeat-seed study is a separate
experiment and must use separate output files and analysis.

The completed one-patient integration test is the **Algoverse Patient 21 protocol-lock
pilot**, batch ID `lung-seed0-pilot-20260826-v2`. Read
[`docs/large_batch_handoff.md`](docs/large_batch_handoff.md) before launching the next
extension.

## Beam IDs do not encode gantry angles

**Read this before touching anything that selects, excludes, or reports beams.**

A PortPy beam ID is an index into that patient's beam list, not an encoding of its angle.
The relationship happens to be `beam_id * 5 == gantry_angle` for `Lung_Patient_2` through
`Lung_Patient_10`, and it is **false from `Lung_Patient_11` onward**, where each patient
stores the clinician's beams first and the angle grid after them:

| patient | beam 9 | beam 36 | 180° lives at |
|---|---|---|---|
| `Lung_Patient_3` | 45° | 180° | id 36 |
| `Lung_Patient_15` | 10° | 145° | id 43 |
| `Lung_Patient_16` | 245° | 0° | id 78 |

Assuming the arithmetic does three things at once, none of which raises an error:

1. **The candidate pool stops being the intended 15° grid.** On `Lung_Patient_15`,
   `range(0, 72, 3)` selects 19 of 27 beams wrongly.
2. **The 180° exclusion removes the wrong beam.** The project excludes 180° because PortPy
   does not model the treatment couch. On `Lung_Patient_15` the old rule deleted beam 36,
   which is 145°, and left the real 180° beam at id 43 in the catalogue.
3. **Every reported angle is wrong**, because READMEs and figures printed `beam_id * 5`.

So all angle decisions go through [`scripts/beam_angles.py`](scripts/beam_angles.py), which
reads each beam's real `gantry_angle` from its `MetaData.json`. `grid_pool()` returns the
15° grid by matching angle values, and `excluded_ids()` finds the 180° beam whatever its ID.
Only the small metadata files are fetched, so the pool is chosen before committing to a
multi-gigabyte download. GA result JSONs now also record `pool_gantry_deg` and
`best_gantry_deg`; new runs additionally embed the exact pool in their protocol manifest.

Never reintroduce `range(0, 72, 3)`, a literal beam `36`, or `beam_id * 5`.
`tests/test_beam_angles.py` guards this, including a regression case built from the real
`Lung_Patient_15` layout.

The committed `Lung_Patient_2`-`6` results are **unaffected**: all five were verified
against beam metadata and follow the legacy convention exactly.

## Project status

The current implementation and research backlog are tracked in
[`docs/project_status.md`](docs/project_status.md). Simulated annealing and other heuristic
extensions are deferred until the GA implementation, repeat-seed study, and compute
comparison are complete.

## Contributing

Use a branch and pull request for every change; do not commit raw PortPy patient data or
derived caches. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the lightweight checks.
