# Lung_Patient_9 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **-2.86% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 10, 20, 28, 35, 44, 52, 62 | 0°, 50°, 100°, 140°, 175°, 220°, 260°, 310° |
| GA | 0, 18, 24, 42, 48, 62, 69 | 0°, 90°, 120°, 210°, 240°, 310°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 117.3092 | 120.6601 |
| Full-resolution objective | 84.7685 | 85.9301 |
| Full-resolution PTV D95 | 59.73 Gy | 59.70 Gy |
| Full-resolution solve time | 35.2 s | 23.5 s |

GA search: best fitness 109.8924, 675 unique solves,
56.6 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_9_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_9_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_9_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_9_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
