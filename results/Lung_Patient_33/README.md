# Lung_Patient_33 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+34.52% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 30°, 0°, 330°, 300°, 225°, 205°, 185° |
| GA | 3, 10, 22, 40, 55, 61, 76 | 300°, 15°, 75°, 165°, 240°, 270°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 138.8721 | 90.9316 |
| Full-resolution objective | 51.0883 | 43.0422 |
| Full-resolution PTV D95 | 59.60 Gy | 59.67 Gy |
| Full-resolution MOSEK solve time | 10.2 s | 10.1 s |

GA search: best fitness 79.2122, 715 unique solves,
30.7 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_33_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_33_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_33_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_33_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_33_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
