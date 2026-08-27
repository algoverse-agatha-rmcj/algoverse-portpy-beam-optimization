# Lung_Patient_34 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+27.10% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 153°, 130°, 60°, 30°, 0°, 320° |
| GA | 5, 10, 16, 25, 31, 58, 76 | 0°, 15°, 45°, 90°, 120°, 255°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 161.7491 | 117.9156 |
| Full-resolution objective | 51.8512 | 43.8059 |
| Full-resolution PTV D95 | 59.63 Gy | 59.71 Gy |
| Full-resolution MOSEK solve time | 12.7 s | 13.2 s |

GA search: best fitness 101.2094, 723 unique solves,
35.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_34_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_34_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_34_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_34_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_34_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
