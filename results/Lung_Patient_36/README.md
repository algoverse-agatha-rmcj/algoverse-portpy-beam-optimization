# Lung_Patient_36 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+29.99% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 175°, 120°, 60°, 30°, 0°, 330° |
| GA | 1, 5, 9, 15, 21, 24, 45 | 120°, 330°, 15°, 45°, 75°, 90°, 195° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 106.3616 | 74.4685 |
| Full-resolution objective | 38.9814 | 35.4897 |
| Full-resolution PTV D95 | 59.72 Gy | 59.77 Gy |
| Full-resolution MOSEK solve time | 7.4 s | 9.3 s |

GA search: best fitness 63.7709, 710 unique solves,
24.4 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_36_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_36_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_36_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_36_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_36_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
