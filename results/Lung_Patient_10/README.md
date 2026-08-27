# Lung_Patient_10 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+3.21% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 37, 42, 48, 54, 60, 66 | 0°, 185°, 210°, 240°, 270°, 300°, 330° |
| GA | 6, 12, 33, 37, 54, 57, 63 | 30°, 60°, 165°, 185°, 270°, 285°, 315° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 96.3204 | 93.2254 |
| Full-resolution objective | 68.8108 | 69.8454 |
| Full-resolution PTV D95 | 59.69 Gy | 59.68 Gy |
| Full-resolution pipeline time (setup + solve) | 29.2 s | 35.8 s |

GA search: best fitness 87.4765, 696 unique solves,
57.4 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_10_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_10_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_10_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_10_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
