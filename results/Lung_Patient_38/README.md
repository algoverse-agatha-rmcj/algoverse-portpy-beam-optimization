# Lung_Patient_38 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+59.15% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 160°, 140°, 55°, 30°, 0°, 330° |
| GA | 1, 2, 25, 46, 52, 61, 76 | 160°, 140°, 90°, 195°, 225°, 270°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 523.6070 | 213.8805 |
| Full-resolution objective | 250.8083 | 119.6294 |
| Full-resolution PTV D95 | 59.07 Gy | 59.56 Gy |
| Full-resolution MOSEK solve time | 34.3 s | 37.1 s |

GA search: best fitness 204.5958, 704 unique solves,
89.5 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_38_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_38_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_38_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_38_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_38_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
