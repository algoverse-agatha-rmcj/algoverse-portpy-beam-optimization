# Lung_Patient_24 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+42.38% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6 | 0°, 340°, 315°, 295°, 235°, 210°, 185° |
| GA | 4, 6, 13, 22, 25, 67, 76 | 235°, 185°, 30°, 75°, 90°, 300°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 260.9941 | 150.3752 |
| Full-resolution objective | 167.7628 | 119.6230 |
| Full-resolution PTV D95 | 59.08 Gy | 59.57 Gy |
| Full-resolution MOSEK solve time | 60.0 s | 52.9 s |

GA search: best fitness 142.6046, 715 unique solves,
143.2 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_24_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_24_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_24_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_24_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_24_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
