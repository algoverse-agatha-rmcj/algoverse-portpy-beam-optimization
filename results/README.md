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

Complete, comparable bundles are committed for `Lung_Patient_2` through
`Lung_Patient_6`. Patients 2 and 3 also retain clearly named legacy GA runs for historical
context; those legacy files are not comparative evidence. The current seed-0 result,
full-resolution comparison, and matching PDF are the authoritative artifacts in each folder.

The committed PDFs were generated before the 2026-08-12 target-ranking correction. Their
numeric values and curves remain valid, but PTV bold emphasis must be regenerated from the
ignored curve caches after this fix reaches the machine that produced them.
