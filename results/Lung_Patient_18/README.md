# Lung_Patient_18 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+25.99% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 40°, 0°, 330°, 300°, 205°, 185° |
| GA | 0, 1, 2, 45, 54, 60, 63 | 40°, 0°, 330°, 195°, 240°, 270°, 285° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 96.1068 | 71.1239 |
| Full-resolution objective | 47.8948 | 42.2210 |
| Full-resolution PTV D95 | 59.72 Gy | 59.79 Gy |
| Full-resolution solve time | 27.1 s | 27.3 s |

GA search: best fitness 64.4793, 700 unique solves,
41.6 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_18_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_18_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_18_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_18_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
