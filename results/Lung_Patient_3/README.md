# Lung_Patient_3 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+7.97% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 6, 12, 18, 24, 30, 35 | 0°, 30°, 60°, 90°, 120°, 150°, 175° |
| GA | 0, 9, 15, 30, 33, 42, 60 | 0°, 45°, 75°, 150°, 165°, 210°, 300° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 103.6408 | 95.3831 |
| Full-resolution objective | 53.2239 | 52.5031 |
| Full-resolution PTV D95 | 59.74 Gy | 59.75 Gy |
| Full-resolution solve time | 25.4 s | 22.7 s |

GA search: best fitness 82.8777, 671 unique solves,
41.2 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_3_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_3_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_3_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_3_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
