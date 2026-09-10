# Genetic-Algorithm Beam-Angle Optimization on PortPy

A genetic algorithm that chooses radiotherapy beam angles for lung-cancer patients in the
open-source [PortPy](https://github.com/PortPy-Project/PortPy) benchmark, compared against the
clinician-selected angles shipped with each case. Built during the Algoverse AI Research
Fellowship.

For each patient, the GA searches 7-beam subsets of a 15-degree candidate grid. It scores each
subset by the lowest PortPy fluence-optimization objective reachable with those beams, solved
with MOSEK on a down-sampled influence matrix. The winning angles and the clinician's angles
are then re-solved at full resolution with the same optimizer, and only that matched
full-resolution comparison is reported.

## Results

Across 37 lung patients, the GA reached a lower full-resolution planning objective than the
clinician-selected angles for **30 of 37**, with an arithmetic mean improvement of **12.14%**
(9.46% with the two largest gains excluded). Lower PTV underdose and overdose penalties supply
83% of the mean objective difference. Mean PTV D95 was 59.68 Gy for the GA and 59.54 Gy for
the clinician, against a 60 Gy prescription.

Organ doses moved in both directions: mean heart and esophagus dose fell, while dose to the
lungs rose. A lower objective is therefore not a uniformly better plan. Both arms are
re-optimized in PortPy, so this compares beam geometries under a shared optimizer; it is not a
comparison against the delivered clinical plans.

- [`results/cohort_analysis.md`](results/cohort_analysis.md) has the full cohort report,
  including every loss case and the largest gains.
- [`results/paper/`](results/paper/) has the manuscript table and per-patient figure.
- Each `results/Lung_Patient_N/` folder holds that patient's GA run, both clinician
  comparisons, and a three-page DVH report.

### Cohort

The cohort is `Lung_Patient_2` through `Lung_Patient_41`, run in patient-ID order, except
three cases excluded for defects in the released data:

- **Patient 12** is missing dose-influence matrices for 17 beams, three of them on the
  candidate grid.
- **Patients 13 and 35** have structures that index voxels beyond their influence matrices, so
  not even the clinician's own beams can be re-solved.

Details are in [`results/README.md`](results/README.md). The 37 patients are a sequential
subset of the 201 lung cases PortPy publishes, not the full catalogue.

### Limitations

- One seed per patient, so there is no measure of run-to-run variability or convergence.
- No exact MILP or other global-optimum baseline, so no optimality gap is reported.
- No speedup claim: timing was not recorded under uniform hardware conditions, and the later
  patients ran in three concurrent batches.
- Tumor laterality is not available, which limits interpretation of left- versus right-lung
  dose.

## Setup

Requirements: Python 3.11, PortPy 1.1.4, and a MOSEK license (free for academic use). Full
step-by-step instructions, including known dependency traps, are in
[`TEAM_SETUP.md`](TEAM_SETUP.md).

```bash
python3.11 -m venv ../portpy-venv
../portpy-venv/bin/pip install "portpy[mosek,data]" patchify
../portpy-venv/bin/pip install "numpy==2.4.6"          # patchify downgrades numpy, which breaks cvxpy
../portpy-venv/bin/python scripts/patch_portpy_downsampler.py
# MOSEK license at ~/mosek/mosek.lic
```

`scripts/patch_portpy_downsampler.py` fixes a `TypeError` in PortPy 1.1.4's down-sampler on
the current dataset format. Re-run it after any PortPy reinstall. The batch runner expects the
virtual environment at `../portpy-venv`, a sibling of this repository, and patient data is
downloaded to `../data`, so it is never tracked here.

## Reproducing

Run a new patient end to end (download, GA, both comparisons, DVH, validation, cleanup).
Any of `Lung_Patient_2` through `Lung_Patient_202` is accepted; completed stages are skipped,
so use a patient without a committed bundle:

```bash
../portpy-venv/bin/python scripts/run_patient_batch.py \
  --batch-id <stable-batch-id> Lung_Patient_42
```

Or run the same stages individually:

```bash
../portpy-venv/bin/python scripts/download_patient_data.py Lung_Patient_42 --beam-mode ga
../portpy-venv/bin/python ga_bao.py --patient Lung_Patient_42
../portpy-venv/bin/python scripts/clinical_compare.py --patient Lung_Patient_42 --downsample --require-primary-protocol
../portpy-venv/bin/python scripts/clinical_compare.py --patient Lung_Patient_42 --require-primary-protocol
../portpy-venv/bin/python scripts/plot_dvh.py --patient Lung_Patient_42
```

A full patient takes roughly one to three hours, dominated by the MOSEK solves.

Regenerating the cohort report and paper assets from the committed results needs no solver
or data:

```bash
python3 scripts/analyze_cohort.py
python3 scripts/generate_paper_assets.py
python3 -m unittest discover -s tests
```

The primary protocol is frozen in
[`scripts/experiment_protocol.py`](scripts/experiment_protocol.py): 7 beams, population 20,
40 generations, mutation rate 0.15, seed 0, 180 degrees excluded, `(6, 6, 1)` voxel and `4`
beamlet down-sampling. Results embed patient, configuration, data, and code provenance, and
caches are rejected if any of it differs. See [`docs/batch_protocol.md`](docs/batch_protocol.md)
before extending the cohort.

Further reading: [`docs/ga_bao_walkthrough.md`](docs/ga_bao_walkthrough.md) walks through
`ga_bao.py` section by section, and [`docs/fitness_function.md`](docs/fitness_function.md)
explains the objective.

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
2. **The 180° exclusion removes the wrong beam.** The 180° beam is excluded because PortPy
   does not model the treatment couch. On `Lung_Patient_15` the old rule deleted beam 36,
   which is 145°, and left the real 180° beam at id 43 in the catalogue.
3. **Every reported angle is wrong.**

So all angle decisions go through [`scripts/beam_angles.py`](scripts/beam_angles.py), which
reads each beam's real `gantry_angle` from its `MetaData.json`. `grid_pool()` returns the
15° grid by matching angle values, and `excluded_ids()` finds the 180° beam whatever its ID.
Only the small metadata files are fetched, so the pool is chosen before committing to a
multi-gigabyte download. GA result JSONs record `pool_gantry_deg` and `best_gantry_deg`.

Never reintroduce `range(0, 72, 3)`, a literal beam `36`, or `beam_id * 5`.
`tests/test_beam_angles.py` guards this, including a regression case built from the real
`Lung_Patient_15` layout.

## License and data

- **Code:** the source code is released under the [MIT license](LICENSE).
- **Results:** everything under `results/` is derived from the PortPy dataset and is released
  under **CC BY-NC 4.0**, the dataset's own license. See [`results/LICENSE.md`](results/LICENSE.md).
- **Data:** patient data comes from the PortPy dataset on Hugging Face
  ([`PortPy-Project/PortPy_Dataset`](https://huggingface.co/datasets/PortPy-Project/PortPy_Dataset)),
  derived from the TCIA NSCLC-Radiomics collection. No raw patient data is stored here.
- **PortPy:** the library this code depends on is distributed under Apache 2.0 with the
  Commons Clause, for non-commercial academic use. Using this code therefore also means
  following PortPy's terms.

If you use this work, please also cite PortPy as its maintainers request in the
[PortPy README](https://github.com/PortPy-Project/PortPy#license).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Keep raw PortPy data and resumable caches out of Git.
