# Lung_Patient_5 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+13.21% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 6, 12, 18, 24, 30, 35 | 0°, 30°, 60°, 90°, 120°, 150°, 175° |
| GA | 3, 12, 18, 24, 35, 42, 69 | 15°, 60°, 90°, 120°, 175°, 210°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 129.9780 | 112.8143 |
| Full-resolution objective | 79.9823 | 74.7751 |
| Full-resolution PTV D95 | 59.52 Gy | 59.59 Gy |
| Full-resolution pipeline time (setup + solve) | 48.5 s | 47.9 s |

GA search: best fitness 101.5011, 714 unique solves,
86.1 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_5_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_5_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_5_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_5_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
