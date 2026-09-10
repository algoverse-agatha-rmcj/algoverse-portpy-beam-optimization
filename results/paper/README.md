# Paper assets

Regenerate the cohort table and per-patient objective figure with:

```bash
../portpy-venv/bin/python scripts/generate_paper_assets.py
```

The command reads the authoritative full-resolution comparisons through the cohort analyzer
and writes:

- `cohort_summary_table.tex`, a LaTeX table using `booktabs`;
- `cohort_summary_table.csv`, the same values in a format suitable for Google Docs; and
- `objective_improvement.svg`, a dependency-free vector figure.

Suggested figure caption: **Full-resolution planning-objective improvement for each patient.**
Positive values indicate a lower objective under the genetic-algorithm beam arrangement.
The GA produced a lower objective for 30 of 37 patients, with an arithmetic mean improvement
of 12.14%. Patients 14 and 38 are the two largest gains; the arithmetic mean is 9.46% when
both are excluded as a sensitivity calculation.

## Cohort aggregate figures

The manuscript's remaining figures are built outside this repository from the same
`*_full_resolution.json` comparisons.

- **No averaged DVH.** Between-patient anatomy varies far more than the GA-versus-clinician
  difference, so mean curves overlap and show nothing. The cohort aggregate is instead a
  per-term decomposition of the objective gap: PTV underdose and overdose penalties supply 83%
  of the mean 17.22-point objective difference across all 37 patients.
- **Clinical metrics in Gy** accompany the decomposition, because objective terms are weighted
  quadratic penalties rather than doses.
- **The single-patient DVH names its patient.** Patient 18 (+11.85%) is shown because it is the
  closest of the 37 to the cohort mean of 12.14%, not because of the size of its gain.

Term percentages are ratios of cohort totals, never means of per-patient ratios: small
denominators (left lung, the outermost ring) make per-patient ratios swing past -1000%.
