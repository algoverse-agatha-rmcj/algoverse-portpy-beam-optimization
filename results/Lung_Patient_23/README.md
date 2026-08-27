# Lung_Patient_23 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+37.14% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 145°, 120°, 55°, 25°, 0°, 340° |
| GA | 5, 16, 22, 25, 28, 46, 73 | 0°, 45°, 75°, 90°, 105°, 195°, 330° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 165.7861 | 104.2122 |
| Full-resolution objective | 52.7870 | 44.3036 |
| Full-resolution PTV D95 | 59.63 Gy | 59.71 Gy |
| Full-resolution MOSEK solve time | 10.5 s | 11.0 s |

GA search: best fitness 86.7626, 696 unique solves,
34.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_23_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_23_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_23_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_23_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_23_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
