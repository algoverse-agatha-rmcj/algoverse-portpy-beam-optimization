# Lung_Patient_30 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+19.04% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 140°, 340°, 300°, 240°, 210°, 180° |
| GA | 0, 6, 21, 27, 45, 51, 75 | 140°, 0°, 75°, 105°, 195°, 225°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 282.4632 | 228.6920 |
| Full-resolution objective | 64.3006 | 61.2724 |
| Full-resolution PTV D95 | 59.72 Gy | 59.74 Gy |
| Full-resolution MOSEK solve time | 14.3 s | 16.6 s |

GA search: best fitness 218.3645, 712 unique solves,
42.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_30_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_30_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_30_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_30_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_30_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
