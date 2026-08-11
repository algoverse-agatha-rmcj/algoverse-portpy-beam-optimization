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

`Lung_Patient_2` is the first complete bundle. `Lung_Patient_3` currently contains only a
legacy GA run; it predates the corrected candidate pool and has no clinician comparison or
matching DVH, so it must not be used as comparative evidence.
