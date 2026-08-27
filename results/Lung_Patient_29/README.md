# Lung_Patient_29 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+43.71% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 165°, 0°, 330°, 300°, 235°, 210°, 185° |
| GA | 0, 13, 22, 46, 61, 64, 70 | 165°, 30°, 75°, 195°, 270°, 285°, 315° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 141.0599 | 79.4079 |
| Full-resolution objective | 65.8138 | 47.4049 |
| Full-resolution PTV D95 | 59.54 Gy | 59.76 Gy |
| Full-resolution MOSEK solve time | 21.6 s | 23.0 s |

GA search: best fitness 71.5671, 713 unique solves,
61.5 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_29_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_29_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_29_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_29_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_29_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
