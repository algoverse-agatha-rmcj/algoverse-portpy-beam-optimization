# Lung_Patient_37 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+14.41% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 150°, 125°, 58°, 30°, 0°, 200° |
| GA | 5, 19, 25, 34, 40, 46, 52 | 0°, 60°, 90°, 135°, 165°, 195°, 225° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 80.2056 | 68.6500 |
| Full-resolution objective | 45.5902 | 44.9618 |
| Full-resolution PTV D95 | 59.69 Gy | 59.73 Gy |
| Full-resolution MOSEK solve time | 13.1 s | 13.4 s |

GA search: best fitness 60.2271, 698 unique solves,
41.8 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_37_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_37_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_37_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_37_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_37_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
