# Lung_Patient_27 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+14.32% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 175°, 145°, 115°, 65°, 30°, 0° |
| GA | 0, 1, 4, 18, 24, 45, 75 | 175°, 145°, 30°, 60°, 90°, 195°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 101.0019 | 86.5419 |
| Full-resolution objective | 63.2963 | 60.1266 |
| Full-resolution PTV D95 | 59.76 Gy | 59.80 Gy |
| Full-resolution MOSEK solve time | 22.1 s | 29.3 s |

GA search: best fitness 80.1952, 717 unique solves,
81.0 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_27_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_27_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_27_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_27_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_27_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
