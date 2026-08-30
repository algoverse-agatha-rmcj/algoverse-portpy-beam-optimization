# Clinical review checklist

This checklist isolates the claims that need a radiation-oncology or medical-physics read
before the paper is finalized. The reviewer should use the full-resolution cohort table, the
seven loss cases, and the focused Patients 14, 17, 32, and 38 in
`results/cohort_analysis.md` and `docs/results_section_draft.md`.

- Confirm that `clinician-selected angles` is the correct comparator language. Both angle sets
  were re-optimized with the same PortPy fluence objective; the study does not use the original
  delivered clinical fluence.
- Confirm how GTV maximum and PTV maximum should be interpreted once D95 is near prescription.
  A lower target maximum is not automatically better, and the draft currently avoids making
  that claim.
- Assess whether the PTV D95 increases of 1.24 Gy for Patient 14, 1.46 Gy for Patient 17, and
  0.48 Gy for Patient 38 are clinically meaningful and whether their clinician-angle baselines
  indicate undercoverage or a possible solve-quality issue.
- Determine the tumor laterality for each patient before interpreting `LUNG_L max`. The current
  files identify left and right lungs but do not say whether the left lung is ipsilateral or
  contralateral to the tumor.
- Assess the clinical importance of the mean changes: heart -0.62 Gy, esophagus -0.49 Gy,
  lungs excluding GTV +0.32 Gy, and lungs-excluding-GTV V20 +0.14 percentage points.
- Review the +6.35 Gy mean left-lung maximum and +2.08 Gy mean right-lung maximum differences,
  including the large left-lung increases for Patients 6, 10, and 32, and decide whether maximum
  dose is the appropriate lung endpoint to report.
- Review the four esophagus V60 limit violations. The clinician-angle re-solves exceed the 17%
  limit for Patients 8, 21, and 38, and the GA re-solve exceeds it for Patient 21.
- Confirm that missing Patient 8 heart rows should be reported as unavailable rather than zero
  or excluded without explanation.
- Review the full-resolution reversals for Patients 6, 7, 10, 21, and 32, all of which changed
  from reduced-resolution GA wins to full-resolution losses.
- Approve the restrained conclusion: the GA often improves the PortPy objective relative to
  clinician-selected angles in this sample, but organ-level tradeoffs prevent a uniform claim
  of clinical improvement.
