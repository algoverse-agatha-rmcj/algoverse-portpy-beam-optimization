# Lung_Patient_39 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+27.11% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 175°, 150°, 124°, 65°, 32°, 0° |
| GA | 3, 5, 39, 48, 57, 63, 69 | 65°, 0°, 165°, 210°, 255°, 285°, 315° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 144.4511 | 105.2942 |
| Full-resolution objective | 90.0025 | 69.0460 |
| Full-resolution PTV D95 | 59.49 Gy | 59.71 Gy |
| Full-resolution MOSEK solve time | 30.0 s | 26.5 s |

GA search: best fitness 95.8018, 700 unique solves,
63.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_39_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_39_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_39_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_39_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_39_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
