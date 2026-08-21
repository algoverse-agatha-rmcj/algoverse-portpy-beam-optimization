# Paper handoff

The local paper package is ready to move into the shared manuscript. The paper itself is not
stored in this checkout, so this file records the exact inputs and the order in which to use
them.

## Manuscript sections

Copy `docs/results_section_draft.md` into the Results, Discussion, and Limitations sections.
Its values come from the generated 17-patient full-resolution analysis. Keep the comparator
wording as `clinician-selected angles`: both angle sets were re-solved with the same PortPy
fluence optimizer, so `delivered clinical plan` would overstate the comparison.

## Main table

Use `results/paper/cohort_summary_table.tex` in the LaTeX manuscript. It requires the standard
`booktabs` package. For a Google Docs workflow, use `results/paper/cohort_summary_table.csv`.
The table reports arithmetic means and labels every difference as GA minus clinician.

## Main figure

Use `results/paper/objective_improvement.svg`. Suggested caption:

> Full-resolution planning-objective improvement for each patient. Positive values indicate
> a lower objective under the genetic-algorithm beam arrangement. The GA produced a lower
> objective for 12 of 17 patients, with an arithmetic mean improvement of 10.14%. Patients 14
> and 17 are the two largest gains; the arithmetic mean is 4.88% when both are excluded as a
> sensitivity calculation.

## Review before submission

Send `docs/clinical_review_checklist.md` with the draft to Agatha and Ruizhe. Do not strengthen
the claim beyond `comparable to clinician-selected angles` until the target-dose language,
tumor laterality, and left-lung result have been reviewed. The existing cohort does not contain
objective-term exports, repeat seeds, or a global-optimum baseline, and the Limitations section
states each omission directly.
