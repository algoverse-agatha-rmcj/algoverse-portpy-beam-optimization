# Lung_Patient_28 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+27.77% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 160°, 0°, 330°, 305°, 245°, 215°, 185° |
| GA | 3, 4, 6, 55, 82, 103, 106 | 305°, 245°, 185°, 30°, 165°, 270°, 285° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 138.0349 | 99.6957 |
| Full-resolution objective | 72.3338 | 58.3224 |
| Full-resolution PTV D95 | 59.50 Gy | 59.66 Gy |
| Full-resolution MOSEK solve time | 19.4 s | 23.7 s |

GA search: best fitness 91.1229, 701 unique solves,
65.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_28_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_28_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_28_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_28_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_28_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
