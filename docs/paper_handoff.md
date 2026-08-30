# Paper handoff

The local paper package is ready to move into the shared manuscript. The paper itself is not
stored in this checkout, so this file records the exact inputs and the order in which to use
them.

## Manuscript sections

Copy `docs/results_section_draft.md` into the Results, Discussion, and Limitations sections.
Its values come from the generated 37-patient full-resolution analysis. Keep the comparator
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
> objective for 30 of 37 patients, with an arithmetic mean improvement of 12.14%. Patients 14
> and 38 are the two largest gains; the arithmetic mean is 9.46% when both are excluded as a
> sensitivity calculation.

## Review before submission

Send `docs/clinical_review_checklist.md` with the draft to Agatha and Ruizhe. Do not strengthen
the claim beyond `comparable to clinician-selected angles` until the target-dose language,
tumor laterality, lung maximum-dose results, and protocol-limit violations have been reviewed.
Objective-term exports cover only the 20 newer cases, and the study still lacks repeat seeds and
a global-optimum baseline. The Limitations section states each omission directly.
