# Lung_Patient_6 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+10.35% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 37, 42, 48, 54, 60, 66 | 0°, 185°, 210°, 240°, 270°, 300°, 330° |
| GA | 3, 6, 18, 37, 48, 57, 69 | 15°, 30°, 90°, 185°, 240°, 285°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 95.8997 | 85.9729 |
| Full-resolution objective | 44.2826 | 44.3495 |
| Full-resolution PTV D95 | 59.76 Gy | 59.74 Gy |
| Full-resolution pipeline time (setup + solve) | 21.1 s | 20.1 s |

GA search: best fitness 76.2525, 704 unique solves,
33.7 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_6_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_6_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_6_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_6_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
