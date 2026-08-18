# Lung_Patient_20 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+16.78% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 0°, 335°, 306°, 238°, 212°, 185° |
| GA | 5, 45, 51, 57, 66, 96, 108 | 185°, 15°, 45°, 75°, 120°, 270°, 330° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 144.9055 | 120.5941 |
| Full-resolution objective | 93.3560 | 84.6010 |
| Full-resolution PTV D95 | 59.63 Gy | 59.69 Gy |
| Full-resolution solve time | 28.2 s | 936.6 s |

GA search: best fitness 112.0570, 733 unique solves,
88.3 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_20_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_20_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_20_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_20_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
