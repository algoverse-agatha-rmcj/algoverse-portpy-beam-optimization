# Lung_Patient_26 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+26.35% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 175°, 150°, 120°, 45°, 20°, 0°, 210° |
| GA | 0, 19, 25, 34, 46, 52, 58 | 175°, 60°, 90°, 135°, 195°, 225°, 255° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 124.0622 | 91.3749 |
| Full-resolution objective | 67.1846 | 57.3864 |
| Full-resolution PTV D95 | 59.73 Gy | 59.77 Gy |
| Full-resolution MOSEK solve time | 52.6 s | 50.3 s |

GA search: best fitness 83.9211, 702 unique solves,
133.4 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_26_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_26_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_26_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_26_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_26_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
