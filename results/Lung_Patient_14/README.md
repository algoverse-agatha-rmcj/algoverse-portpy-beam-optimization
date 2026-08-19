# Lung_Patient_14 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+73.68% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 200°, 175°, 155°, 120°, 32°, 0° |
| GA | 3, 15, 21, 24, 39, 45, 48 | 120°, 45°, 75°, 90°, 165°, 195°, 210° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 356.2398 | 93.7637 |
| Full-resolution objective | 188.4651 | 64.4070 |
| Full-resolution PTV D95 | 58.48 Gy | 59.71 Gy |
| Full-resolution solve time | 33.2 s | 40.2 s |

GA search: best fitness 85.6957, 693 unique solves,
76.3 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_14_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_14_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_14_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_14_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
