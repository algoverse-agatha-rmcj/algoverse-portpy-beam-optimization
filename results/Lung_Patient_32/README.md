# Lung_Patient_32 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+25.14% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 140°, 355°, 332°, 295°, 240°, 210°, 180° |
| GA | 49, 64, 67, 70, 79, 88, 100 | 0°, 75°, 90°, 105°, 150°, 195°, 255° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 220.2852 | 164.9039 |
| Full-resolution objective | 45.4871 | 46.1253 |
| Full-resolution PTV D95 | 59.69 Gy | 59.70 Gy |
| Full-resolution MOSEK solve time | 11.9 s | 11.5 s |

GA search: best fitness 150.3078, 695 unique solves,
33.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_32_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_32_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_32_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_32_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_32_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
