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

## Cohort aggregate figures (2026-09-09, built outside this repo)

Meeting 10 asked for an aggregate that summarizes all 37 patients alongside the
single-patient DVH. An averaged DVH was considered and rejected: between-patient anatomy
variance dwarfs the GA-versus-clinician difference, so the mean curves overlap and show
nothing. The aggregate is instead a per-term decomposition of the objective gap.

Those figures are PDFs in OneDrive under
`Summer 26/Algoverse/Research Group/Results/`, with `make_figures.py` beside them:

- `Fig_objective_term_drivers.pdf` — per-term decomposition, two panels (objective points
  recovered, and percent improvement per term). PTV underdose and overdose account for
  83% of the mean 17.22-point gap. **Now n=37**, the full cohort, after the objective-term
  backfill was verified and adopted on 2026-09-10.
- `Fig_cohort_clinical_metrics.pdf` — the same comparison in Gy across all 37 patients,
  with a per-patient count column. The mean and the count disagree on spinal cord and left
  lung; both are shown.
- `Fig_per_patient_improvement.pdf` — PDF form of `objective_improvement.svg`, with the
  arithmetic mean marked.
- `Fig_example_DVH_P18_nearest_mean.pdf` — the single-patient DVH. Patient 18 (+11.85%) is
  the closest of the 37 to the cohort mean of 12.14%; P19 is the alternate. Meeting 10
  requires the patient ID be stated in the caption.
- `equation.tex` — the bilevel objective, verified against
  `portpy/photon/optimization.py` and consistent with `docs/fitness_function.pdf`.

Percentages in these figures are ratios of cohort means, never means of per-patient ratios:
small denominators (left lung, RIND_4) make per-patient ratios swing past -1000%.
