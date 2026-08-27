# Experiment results

Results are grouped by PortPy patient so the numbers and the figure made from them stay
together:

```text
results/
└── Lung_Patient_N/
    ├── ga_runs/
    │   └── Lung_Patient_N_ga_downsampled_seed_0.json
    ├── clinical_comparison/
    │   ├── Lung_Patient_N_clinical_metrics_downsampled.json
    │   └── Lung_Patient_N_clinical_metrics_full_resolution.json
    ├── figures/
    │   └── Lung_Patient_N_DVH_clinical_metrics.pdf
    ├── cache/                  # derived/resumable files; ignored by Git
    └── README.md
```

The GA searches on down-sampled data. Its winning angles and the clinician's angles must
then be re-solved at the same resolution for comparison. Organ-specific clinical claims
come only from the patient-named `clinical_metrics_full_resolution.json` file in
`clinical_comparison/` and the
matching PDF in `figures/`.

The PDF is a dose-volume histogram, not a conventional frequency histogram. The updated
version has three pages: an overlay, per-structure curves annotated with protocol metrics,
and the complete clinical-criteria table.

## Cohort

The intended cohort is `Lung_Patient_2` through `Lung_Patient_41` **except
`Lung_Patient_12`, `Lung_Patient_13` and `Lung_Patient_35`**, giving 37 patients. Every
committed bundle is a seed-0 run at population 20 / 40 generations with the candidate pool
resolved from each beam's real gantry angle, so all of them are directly comparable.

It was built in two stages: Patients 2-21 sequentially, then Patients 22-41 as three
disjoint predeclared batches (`lung-seed0-ext-a-20260826`, `lung-seed0-ext-b2-20260827`,
`lung-seed0-ext-c-20260826`) run concurrently on one machine. Of the 20 predeclared
extension patients, 19 completed and one was excluded for the data defect below. Because
the three batches ran at the same time, their `wall_time_s` and `solve_time_s` are not
comparable with the sequentially-run Patients 2-21; cohort timing statistics stay on the
sequential runs and the extension patients are reported for objectives only.

All three exclusions are defects in the released data, not choices about method, and none
can be worked around from this repository. `Lung_Patient_35` is the same defect as
`Lung_Patient_13`: its structures reference voxel indices beyond its influence matrix, at
full resolution and with the clinician's own `PlannerBeams`, so no plan can be built for it
and no clinician baseline exists to compare against.

Regenerate the cohort-level JSON and paper-ready Markdown summary from the authoritative
full-resolution comparisons with:

```bash
python3 scripts/analyze_cohort.py
```

This writes `results/cohort_analysis.json` and `results/cohort_analysis.md`. All aggregate
statistics use arithmetic means; per-patient values and timing tails remain visible for
outlier review.

Generate the manuscript table and vector cohort figure from that same source with:

```bash
python3 scripts/generate_paper_assets.py
```

The generated files and their suggested caption are documented in `results/paper/README.md`.

**`Lung_Patient_12` is excluded, and cannot be run as published.** PortPy ships
`MetaData.json` for 80 of its beams but a dose-influence matrix (`Beam_*_Data.h5`) for only
63. The 17 beams with metadata and no dose data are 8, 9, 61, and 66-79, and three of them
(68, 74, 77) fall inside the 15-degree candidate grid. The pool is built from metadata, so
it legitimately asks for beams whose dose matrices were never released, and the download can
never complete. Running it would mean a 20-beam pool against 23-30 for every other patient, which
is why it is dropped rather than run reduced. Its beam files are all present and correct;
the gap is that the dose matrices for part of the grid were never published.

**`Lung_Patient_13` is excluded, and cannot be optimized at all.** Its structures reference
voxels that its influence matrix does not contain, so building the CVXPY problem raises
`IndexError: index (578994) out of range` inside PortPy's `create_cvxpy_problem`. This is not
a property of our candidate pool: it fails identically with the clinician's own
`PlannerBeams`, and at full resolution as well as down-sampled, so no beam set and no
resolution avoids it. **Not even the delivered clinical plan can be re-solved for this
patient**, which is what rules out any workaround here - the comparison needs a clinician
baseline, and this patient cannot produce one. Its `CT_Data.h5`, `StructureSet_Data.h5` and
`OptimizationVoxels_Data.h5` are byte-identical to the published files, so the inconsistency
is upstream rather than a bad download.

Patients 2 and 3 also retain clearly named legacy GA runs for historical
context; those legacy files are not comparative evidence. The current seed-0 result,
full-resolution comparison, and matching PDF are the authoritative artifacts in each folder.

The committed PDFs were generated before the 2026-08-12 target-ranking correction. Their
numeric values and curves remain valid, but PTV bold emphasis must be regenerated from the
ignored curve caches after this fix reaches the machine that produced them.
