# Lung_Patient_7 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+7.16% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 37, 42, 48, 54, 60, 66 | 0°, 185°, 210°, 240°, 270°, 300°, 330° |
| GA | 3, 9, 33, 37, 51, 57, 63 | 15°, 45°, 165°, 185°, 255°, 285°, 315° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 110.3515 | 102.4498 |
| Full-resolution objective | 66.9234 | 67.8089 |
| Full-resolution PTV D95 | 59.74 Gy | 59.74 Gy |
| Full-resolution pipeline time (setup + solve) | 20.3 s | 20.5 s |

GA search: best fitness 94.8550, 721 unique solves,
52.5 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_7_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_7_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_7_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_7_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
