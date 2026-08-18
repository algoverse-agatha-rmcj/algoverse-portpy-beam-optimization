# Lung_Patient_16 - GA vs. clinician

## Headline

The no-180 genetic algorithm searched on reduced-resolution PortPy data using population
20, 40 generations, and seed 0. Its objective was **+27.66% better**
than the clinician beam set at the same reduced resolution (positive means lower/better).
The winning and clinician angles were then re-solved at full resolution for the clinical
metrics and DVH.

| plan | beam IDs | gantry angles |
|---|---|---|
| Clinician | 0, 1, 2, 3, 4, 5 | 0°, 334°, 310°, 245°, 212°, 185° |
| GA | 5, 48, 87, 93, 96, 102, 111 | 185°, 30°, 225°, 255°, 270°, 300°, 345° |

| measurement | clinician | GA |
|---|---:|---:|
| Down-sampled objective | 135.7929 | 98.2262 |
| Full-resolution objective | 59.5779 | 53.1260 |
| Full-resolution PTV D95 | 59.70 Gy | 59.73 Gy |
| Full-resolution solve time | 17.4 s | 17.6 s |

GA search: best fitness 84.5441, 705 unique solves,
55.5 minutes wall time. Organ-specific conclusions must use the
full-resolution JSON and matching PDF, not the reduced-resolution comparison.

## Files

- `ga_runs/Lung_Patient_16_ga_downsampled_seed_0.json` - raw reduced-resolution GA history and winner.
- `clinical_comparison/Lung_Patient_16_clinical_metrics_downsampled.json` - clinician vs. GA at search resolution.
- `clinical_comparison/Lung_Patient_16_clinical_metrics_full_resolution.json` - clinical source of truth at full resolution.
- `figures/Lung_Patient_16_DVH_clinical_metrics.pdf` - three-page DVH with per-organ metrics and criteria table.
- `cache/` - ignored derived files used to resume/replot without repeating computation.
