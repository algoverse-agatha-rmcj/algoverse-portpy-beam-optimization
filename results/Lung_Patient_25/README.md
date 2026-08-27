# Lung_Patient_25 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+31.73% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 150°, 0°, 340°, 320°, 240°, 210°, 185° |
| GA | 3, 4, 6, 13, 40, 61, 67 | 320°, 240°, 185°, 30°, 165°, 270°, 300° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 210.6869 | 143.8351 |
| Full-resolution objective | 127.3320 | 105.0425 |
| Full-resolution PTV D95 | 59.49 Gy | 59.64 Gy |
| Full-resolution MOSEK solve time | 38.2 s | 40.4 s |

GA search: best fitness 135.0769, 708 unique solves,
95.2 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_25_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_25_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_25_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_25_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_25_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
