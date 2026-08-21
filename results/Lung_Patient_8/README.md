# Lung_Patient_8 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+11.01% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 37, 42, 48, 54, 60, 66 | 0°, 185°, 210°, 240°, 270°, 300°, 330° |
| GA | 3, 18, 33, 45, 48, 57, 63 | 15°, 90°, 165°, 225°, 240°, 285°, 315° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 157.5143 | 140.1784 |
| Full-resolution objective | 120.1214 | 107.6260 |
| Full-resolution PTV D95 | 59.48 Gy | 59.57 Gy |
| Full-resolution solve time | 66.2 s | 65.0 s |

GA search: best fitness 132.5281, 714 unique solves,
129.4 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_8_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_8_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_8_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_8_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
