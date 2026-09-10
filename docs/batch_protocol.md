# Batch protocol

How the primary cohort was run, and how to extend it without breaking comparability.

## Frozen protocol

Every patient in the primary cohort uses the protocol in `scripts/experiment_protocol.py`:

- 7 beams
- population 20
- 40 generations
- mutation rate 0.15
- seed 0
- real-angle 15-degree candidate grid with 180 degrees excluded
- search downsampling factors `(6, 6, 1)` for voxels and `4` for beamlets
- full-resolution rescoring of the GA winner and the clinician plan

The recorded environment was Python 3.11.16, PortPy 1.1.4, NumPy 2.4.6, CVXPY 1.7.5, and
MOSEK 11.2.2.

Changing the scientific pipeline means the pilot below no longer validates the exact
implementation, so run a new one-patient pilot before scaling. Do not add seeds, change the
GA budget, or select the best of several seeds for the primary cohort; a repeat-seed study is
a separate experiment with separate outputs.

## Protocol-lock pilot

Patient 21 was run alone first, as batch `lung-seed0-pilot-20260826-v2`, to validate the whole
pipeline before the extension. (The earlier batch ID without `-v2` failed before any download
because it was launched with the system interpreter; it is an environment record, not a
result.)

- 40 GA generations and 713 unique solves completed in 9,673.4 seconds.
- The winning beam IDs were `7, 23, 35, 41, 47, 65, 77`, at gantry angles
  `210, 75, 135, 165, 195, 285, 345` degrees.
- At search resolution the GA objective was 337.3321 against the clinician's 341.3699, 1.18%
  better.
- At full resolution the GA objective was 179.8351 against the clinician's 172.4336, 4.29%
  worse. PTV D95 was 59.43 Gy for the GA and 59.50 Gy for the clinician.
- The validated repository source bundle SHA-256 was
  `49b7cdce7cf00e626022b69d913693a85923f0f9d23022af2b9b5e8c8c3ea769`.

The resolution reversal is a result, not a pipeline error. Cohort conclusions use the
full-resolution comparison.

## Launching a batch

Predeclare the complete patient list, and the rule used to choose it, in the first command.
Do not include any patient that already has a completed bundle. From the repository root:

```bash
../portpy-venv/bin/python scripts/run_patient_batch.py \
  --batch-id <new-stable-batch-id> \
  <exact-predeclared-patient-list>
```

The runner processes patients sequentially. For each one it downloads data, runs the GA,
performs both comparisons, generates the PDF and README, validates the bundle, marks the
patient complete, and deletes the raw data. Re-run the same command and batch ID only to
resume an interruption with the same patient list and unchanged source code.

## Completion check

A batch is complete only when all of these are true:

1. `results/batches/<batch-id>.json` has `completed` status for every patient and a
   `completed_at_utc` value.
2. Every patient has a 40-generation GA result and matching standalone manifest.
3. Every patient has downsampled and full-resolution comparison JSONs.
4. Every patient has a DVH PDF and README.
5. The terminal prints `validated result bundle` for every patient and ends with
   `Batch complete.`
