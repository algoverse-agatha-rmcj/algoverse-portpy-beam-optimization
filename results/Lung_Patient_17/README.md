# Lung_Patient_17 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+41.27% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 152°, 20°, 0°, 318°, 236°, 208°, 185° |
| GA | 1, 2, 4, 22, 31, 40, 67 | 20°, 0°, 236°, 75°, 120°, 165°, 300° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 823.9658 | 483.9087 |
| Full-resolution objective | 413.0923 | 275.5722 |
| Full-resolution PTV D95 | 57.90 Gy | 59.36 Gy |
| Full-resolution pipeline time (setup + solve) | 47.5 s | 40.5 s |

GA search: best fitness 472.1457, 698 unique solves,
63.5 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_17_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_17_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_17_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_17_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
