# Lung_Patient_21 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its
objective was **+1.18% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5, 6, 7 | 175°, 143°, 110°, 45°, 0°, 315°, 248°, 210° |
| GA | 7, 23, 35, 41, 47, 65, 77 | 210°, 75°, 135°, 165°, 195°, 285°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 341.3699 | 337.3321 |
| Full-resolution objective | 172.4336 | 179.8351 |
| Full-resolution PTV D95 | 59.50 Gy | 59.43 Gy |
| Full-resolution MOSEK solve time | 75.4 s | 60.9 s |

GA search: best fitness 328.3742, 713 unique solves,
161.2 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_21_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `ga_runs/Lung_Patient_21_ga_downsampled_seed_0.manifest.json` - protocol, input, environment, and code provenance.
- `clinical_comparison/Lung_Patient_21_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_21_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_21_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
