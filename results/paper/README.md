# Paper assets

Regenerate the cohort table and per-patient objective figure with:

```bash
python3 scripts/generate_paper_assets.py
```

The command reads the authoritative full-resolution comparisons through the cohort analyzer
and writes:

- `cohort_summary_table.tex`, a LaTeX table using `booktabs`;
- `cohort_summary_table.csv`, the same values in a format suitable for Google Docs; and
- `objective_improvement.svg`, a dependency-free vector figure.

Suggested figure caption: **Full-resolution planning-objective improvement for each patient.**
Positive values indicate a lower objective under the genetic-algorithm beam arrangement.
The GA produced a lower objective for 12 of 17 patients, with an arithmetic mean improvement
of 10.14%. Patients 14 and 17 are the two largest gains; the arithmetic mean is 4.88% when
both are excluded as a sensitivity calculation.
