# Lung_Patient_40 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+19.38% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 175°, 155°, 120°, 55°, 25°, 0° |
| GA | 5, 21, 33, 39, 45, 57, 63 | 0°, 75°, 135°, 165°, 195°, 255°, 285° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 141.8423 | 114.3499 |
| Full-resolution objective | 97.5330 | 89.8476 |
| Full-resolution PTV D95 | 59.67 Gy | 59.73 Gy |
| Full-resolution MOSEK solve time | 28.2 s | 27.1 s |

GA search: best fitness 107.5537, 699 unique solves,
72.8 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_40_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_40_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_40_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_40_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_40_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
