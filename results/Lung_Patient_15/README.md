# Lung_Patient_15 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **-0.02% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 0°, 330°, 300°, 270°, 240°, 210°, 185° |
| GA | 0, 1, 2, 3, 4, 5, 10 | 0°, 330°, 300°, 270°, 240°, 210°, 15° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 91.8674 | 91.8850 |
| Full-resolution objective | 64.3553 | 64.5936 |
| Full-resolution PTV D95 | 59.74 Gy | 59.74 Gy |
| Full-resolution pipeline time (setup + solve) | 143.6 s | 143.6 s |

GA search: best fitness 85.9924, 727 unique solves,
325.6 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_15_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_15_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_15_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_15_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
