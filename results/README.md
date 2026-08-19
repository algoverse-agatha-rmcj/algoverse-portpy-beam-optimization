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

The intended cohort is `Lung_Patient_2` through `Lung_Patient_20` **except
`Lung_Patient_12`**, giving 18 patients. Every committed bundle is a seed-0 run at
population 20 / 40 generations with the candidate pool resolved from each beam's real
gantry angle, so all of them are directly comparable.

**`Lung_Patient_12` is excluded, and cannot be run as published.** PortPy ships
`MetaData.json` for 80 of its beams but a dose-influence matrix (`Beam_*_Data.h5`) for only
63. The 17 beams with metadata and no dose data are 8, 9, 61, and 66-79, and three of them
(68, 74, 77) fall inside the 15-degree candidate grid. The pool is built from metadata, so
it legitimately asks for beams whose dose matrices were never released, and the download can
never complete. `Lung_Patient_13`, checked as a control, has 79 metadata files and 79 dose
files with no gaps, so this is specific to Patient 12 rather than a problem with the
pipeline. Running it would mean a 20-beam pool against 23-30 for every other patient, which
is why it is dropped rather than run reduced.

Patients 2 and 3 also retain clearly named legacy GA runs for historical
context; those legacy files are not comparative evidence. The current seed-0 result,
full-resolution comparison, and matching PDF are the authoritative artifacts in each folder.

The committed PDFs were generated before the 2026-08-12 target-ranking correction. Their
numeric values and curves remain valid, but PTV bold emphasis must be regenerated from the
ignored curve caches after this fix reaches the machine that produced them.
