# Lung_Patient_19 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+14.76% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 0°, 335°, 305°, 238°, 212°, 185° |
| GA | 4, 5, 9, 27, 57, 69, 75 | 212°, 185°, 15°, 105°, 255°, 315°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 167.7842 | 143.0237 |
| Full-resolution objective | 107.4744 | 95.3860 |
| Full-resolution PTV D95 | 59.55 Gy | 59.66 Gy |
| Full-resolution pipeline time (setup + solve) | 42.4 s | 44.6 s |

GA search: best fitness 134.0750, 712 unique solves,
106.4 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_19_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_19_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_19_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_19_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
