# Large batch handoff

> **Historical, as of 2026-09-09.** The extension this document plans was run and completed:
> the cohort is now 37 patients (2-11, 14-34, 36-41), not the 18 described below. Kept for the
> pilot record and the launch procedure, which are still correct. For current cohort state see
> `README.md` and `docs/project_status.md`.

## Canonical pilot

Refer to the completed test as the **Algoverse Patient 21 protocol-lock pilot**. Its
canonical batch ID is `lung-seed0-pilot-20260826-v2`. The earlier batch ID without
`-v2` failed before any data download or optimization because it was launched with the
system Python interpreter. It is only a failed environment record and is not a scientific
result.

The canonical pilot completed on 2026-08-26 and validated the entire patient pipeline:

- 40 GA generations and 713 unique solves completed in 9,673.4 seconds.
- The winning beam IDs were `7, 23, 35, 41, 47, 65, 77`, corresponding to gantry
  angles `210, 75, 135, 165, 195, 285, 345` degrees.
- The downsampled objective was 337.3321 for the GA and 341.3699 for the clinician.
  The GA was 1.18 percent better at the search resolution.
- The full-resolution objective was 179.8351 for the GA and 172.4336 for the
  clinician. The GA was 4.29 percent worse at the clinical evaluation resolution.
- Full-resolution PTV D95 was 59.43 Gy for the GA and 59.50 Gy for the clinician.
- Both comparison JSONs, the DVH PDF, the patient README, and the protocol manifests
  were generated and passed bundle validation.
- The batch manifest ended with `completed` status, and the runner deleted the raw
  patient data after validation.

The resolution reversal is a result, not a pipeline error. Cohort conclusions must use
the full-resolution comparison as the clinical source of truth.

## Frozen protocol

The pilot used the same primary protocol as Patients 2 through 11 and 14 through 20:

- 7 beams
- population 20
- 40 generations
- mutation rate 0.15
- seed 0
- real-angle 15-degree candidate grid with 180 degrees excluded
- search downsampling factors `(6, 6, 1)` for voxels and `4` for beamlets
- full-resolution rescoring of the GA winner and clinician plan

The recorded environment was Python 3.11.16, PortPy 1.1.4, NumPy 2.4.6, CVXPY
1.7.5, and MOSEK 11.2.2. The validated repository source bundle SHA-256 was
`49b7cdce7cf00e626022b69d913693a85923f0f9d23022af2b9b5e8c8c3ea769`.

Do not edit the scientific pipeline before launching the extension. A source change
means this pilot no longer validates the exact implementation, so run a new one-patient
pilot before scaling.

## Starting the large batch

At the time of this handoff the primary cohort had 18 usable patients: Patients 2 through 11
and 14 through 21, with Patients 12 and 13 excluded for upstream PortPy data defects. That
extension has since completed; the cohort is now 37 patients and Patient 35 joined the
exclusion list. Do not include any completed patient in an extension batch.

Before running, Milen must provide the exact new patient list and the sampling rule used
to choose it. Do not infer a list or describe a sampled subset as the full PortPy lung
cohort. Use one new batch ID and predeclare the entire list in the first command.

Run from the repository root with the project interpreter:

```bash
cd /Users/milen/dev/projects/research/algoverse-portpy-beam-optimization

../portpy-venv/bin/python scripts/run_patient_batch.py \
  --batch-id <new-stable-batch-id> \
  <exact-predeclared-patient-list>
```

The placeholders must be replaced before execution. Do not use the system `python3`.
Do not add extra seeds, change the GA budget, or select the best seed for the primary
cohort.

The runner processes patients sequentially. It downloads data, runs the GA, performs
both comparisons, generates the PDF and README, validates the bundle, marks the patient
complete, and deletes raw data. Reuse the same command and batch ID only to resume an
interruption with the same patient list and unchanged source code.

## Completion check

The batch is complete only when all of these are true:

1. `results/batches/<batch-id>.json` has `completed` status for every patient and a
   `completed_at_utc` value.
2. Every patient has a 40-generation GA result and matching standalone manifest.
3. Every patient has downsampled and full-resolution comparison JSONs.
4. Every patient has a DVH PDF and README.
5. The terminal prints `validated result bundle` for every patient and ends with
   `Batch complete.`

The pilot artifacts are under `results/Lung_Patient_21/`, and its batch manifest is
`results/batches/lung-seed0-pilot-20260826-v2.json`.
