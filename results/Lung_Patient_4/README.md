# Lung_Patient_4 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+8.09% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 37, 42, 48, 54, 60, 66 | 0°, 185°, 210°, 240°, 270°, 300°, 330° |
| GA | 6, 12, 30, 37, 51, 60, 69 | 30°, 60°, 150°, 185°, 255°, 300°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 177.5672 | 163.2103 |
| Full-resolution objective | 89.8995 | 87.6541 |
| Full-resolution PTV D95 | 59.65 Gy | 59.67 Gy |
| Full-resolution pipeline time (setup + solve) | 42.1 s | 38.6 s |

GA search: best fitness 153.3489, 674 unique solves,
70.7 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_4_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_4_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_4_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_4_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
