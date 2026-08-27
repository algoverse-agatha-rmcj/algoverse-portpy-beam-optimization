# Lung_Patient_41 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+15.47% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 175°, 147°, 115°, 60°, 32°, 5° |
| GA | 5, 15, 27, 33, 45, 57, 75 | 5°, 45°, 105°, 135°, 195°, 255°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 110.7536 | 93.6201 |
| Full-resolution objective | 73.5965 | 68.6349 |
| Full-resolution PTV D95 | 59.69 Gy | 59.75 Gy |
| Full-resolution MOSEK solve time | 53.4 s | 37.0 s |

GA search: best fitness 86.4894, 714 unique solves,
94.7 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_41_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_41_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_41_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_41_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_41_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
