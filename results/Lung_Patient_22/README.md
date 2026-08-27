# Lung_Patient_22 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+28.81% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 160°, 140°, 60°, 25°, 0°, 330° |
| GA | 5, 10, 22, 49, 64, 70, 76 | 0°, 15°, 75°, 210°, 285°, 315°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 115.4301 | 82.1735 |
| Full-resolution objective | 52.7587 | 48.1732 |
| Full-resolution PTV D95 | 59.75 Gy | 59.80 Gy |
| Full-resolution MOSEK solve time | 29.1 s | 29.6 s |

GA search: best fitness 74.7697, 711 unique solves,
57.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_22_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_22_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_22_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_22_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_22_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
