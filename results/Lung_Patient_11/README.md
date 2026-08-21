# Lung_Patient_11 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+29.05% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 147°, 355°, 340°, 315°, 235°, 205°, 185° |
| GA | 5, 6, 31, 40, 55, 61, 64 | 205°, 185°, 120°, 165°, 240°, 270°, 285° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 120.5819 | 85.5534 |
| Full-resolution objective | 58.6305 | 52.0750 |
| Full-resolution PTV D95 | 59.72 Gy | 59.76 Gy |
| Full-resolution solve time | 30.2 s | 39.2 s |

GA search: best fitness 77.4600, 725 unique solves,
7.6 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_11_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_11_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_11_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_11_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
