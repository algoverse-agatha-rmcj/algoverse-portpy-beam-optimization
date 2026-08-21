# Clinical review checklist

This checklist isolates the claims that need a radiation-oncology or medical-physics read
before the paper is finalized. The reviewer should use the full-resolution cohort table and
the focused P6, P7, P9, P10, P14, P15, and P17 rows in `results/cohort_analysis.md`.

- Confirm that `clinician-selected angles` is the correct comparator language. Both angle sets
  were re-optimized with the same PortPy fluence objective; the study does not use the original
  delivered clinical fluence.
- Confirm how GTV maximum and PTV maximum should be interpreted once D95 is near prescription.
  A lower target maximum is not automatically better, and the draft currently avoids making
  that claim.
- Assess whether the PTV D95 increases of 1.24 Gy for Patient 14 and 1.46 Gy for Patient 17 are
  clinically meaningful and whether their clinician-angle baselines indicate undercoverage or
  a possible solve-quality issue.
- Determine the tumor laterality for each patient before interpreting `LUNG_L max`. The current
  files identify left and right lungs but do not say whether the left lung is ipsilateral or
  contralateral to the tumor.
- Assess the clinical importance of the mean changes: heart -0.54 Gy, esophagus -0.50 Gy,
  lungs excluding GTV +0.27 Gy, and lungs-excluding-GTV V20 -0.03 percentage points.
- Review the +9.01 Gy mean left-lung maximum difference, including Patients 6 (+14.91 Gy) and
  10 (+24.65 Gy), and decide whether maximum dose is the appropriate lung endpoint to report.
- Verify the Patient 8 clinician-angle esophagus V60 result of 20.05% against the 17% protocol
  limit and confirm that describing it as one protocol-limit violation is appropriate.
- Confirm that missing Patient 8 heart rows should be reported as unavailable rather than zero
  or excluded without explanation.
- Approve the restrained conclusion: the GA generally matches the objective quality of
  clinician-selected angles in this sample, but organ-level tradeoffs prevent a uniform claim
  of clinical improvement.
