# Results

The genetic algorithm produced a lower full-resolution planning objective than the
clinician-selected beam arrangement for 12 of the 17 usable lung patients. The arithmetic
mean improvement was 10.14%, where a positive value indicates a lower objective under the
GA plan. This mean is influenced by Patients 14 and 17, which improved by 65.83% and 33.29%,
respectively; after excluding those two cases as a sensitivity calculation, the arithmetic
mean improvement was 4.88%. The five losses were small, ranging from 0.15% to 1.50%, with a
mean disadvantage of 0.94% across those cases.

Target coverage was similar at the cohort level. Mean PTV D95 was 59.67 Gy under the GA
angles and 59.48 Gy under the clinician angles against a 60 Gy prescription. In each of the
five loss cases, the PTV D95 difference was no larger than 0.03 Gy. The two largest objective
gains occurred in cases with lower clinician-plan coverage: PTV D95 increased from 58.48 Gy
to 59.71 Gy for Patient 14 and from 57.90 Gy to 59.36 Gy for Patient 17. These coverage
changes coincide with the large objective reductions, but the saved results contain only
the total objective, so an objective-term decomposition is needed before assigning the
improvements to a specific penalty.

The organ-at-risk results were mixed. Mean heart dose decreased from 5.18 Gy to 4.64 Gy
across the 16 patients with an available heart measurement, and mean esophagus dose
decreased from 8.95 Gy to 8.45 Gy across all 17 patients. Mean dose to lungs excluding the
GTV increased from 8.27 Gy to 8.54 Gy, while V20 for the same structure changed from 15.24%
to 15.20%. The largest cohort-level difference was maximum left-lung dose, which increased
from 33.16 Gy to 42.17 Gy and was higher under the GA angles in 13 of 17 patients. The GA
plans met every reported protocol limit; the clinician plans had one esophagus V60 limit
violation in Patient 8.

The per-patient analysis did not identify one clinical metric that explained every loss.
Patients 6 and 10 had left-lung maximum-dose increases of 14.91 Gy and 24.65 Gy, while their
objective disadvantages were only 0.15% and 1.50%. Patient 9 instead had a 1.19 percentage
point increase in lungs-excluding-GTV V20, and Patient 15 showed only small changes across
the reported criteria. Patient 14 combined improved target coverage with lower heart and
esophagus mean doses, whereas Patient 17 recovered target coverage while increasing mean
lungs-excluding-GTV dose by 0.83 Gy and V20 by 1.22 percentage points. The total objective
therefore describes one weighting of these tradeoffs, not a uniform clinical improvement.

Mean full-run GA wall time was 1.42 hours across the 16 runs completed in one process.
Patient 11 was resumed from a checkpoint containing 653 solves, so its 456-second wall time
covers only the final process segment and is excluded from that mean. Per-solve timing was
available for six patients, covering 4,224 measured solves with a pooled arithmetic mean of
6.120 seconds. The largest reported patient-level p95 was 12.517 seconds and the largest
observed solve was 17.032 seconds.

# Discussion

The genetic algorithm usually found a beam arrangement with a lower planning objective than
the clinician-selected angles, but the comparison does not support a claim that every GA plan
was clinically better. The five objective losses were all below 1.51%, and their target
coverage stayed within 0.03 Gy of the corresponding clinician-angle plans. The positive mean
was driven partly by Patients 14 and 17, where the clinician-angle re-solves had lower PTV D95
and the GA plans recovered 1.24 Gy and 1.46 Gy. Reporting the 10.14% cohort mean together with
the 4.88% sensitivity mean and every patient-level value makes that dependence explicit.

The physical dose metrics also move in different directions. Heart and esophagus mean doses
were lower under the GA angles on average, but the mean dose to lungs excluding the GTV rose
by 0.27 Gy and the maximum left-lung dose rose by 9.01 Gy. These changes show why the weighted
objective and the protocol metrics need to be reported together: a lower total objective is
one mathematical balance among target and organ penalties, not evidence that each structure
improved. The left-lung result also needs review against tumor laterality because the released
labels alone do not establish whether the left lung is ipsilateral or contralateral for each
patient.

The strongest current conclusion is therefore that GA-selected angles can reproduce or modestly
improve the PortPy objective obtained from clinician-selected angles across this 17-patient
sample, while preserving target coverage and protocol compliance. This is a comparison of beam
geometries under a shared fluence-optimization pipeline. It is not a comparison against the
original delivered clinical fluence, and it does not establish clinical superiority or a
global optimum.

# Limitations

Each patient has one seed-0 GA run, so the study does not yet measure variability across random
initializations or demonstrate convergence. The 17 patients are a usable subset of the released
PortPy lung data rather than a random sample of the full catalogue: Patients 12 and 13 were
excluded because their published dose and structure data cannot produce a matched comparison.
Heart metrics are also unavailable for Patient 8, leaving 16 patients in those rows.

The saved full-resolution comparisons contain the total objective but not its individual target,
organ-at-risk, and smoothness terms. The association between recovered PTV D95 and the large
gains for Patients 14 and 17 is therefore descriptive rather than causal. Future comparison
runs now export the individual objective terms, but backfilling the present cohort requires
re-solving both angle sets for each patient.

The timing data are sufficient for workload description but not for a speedup claim. Hardware
and execution conditions were not recorded uniformly, per-solve timing is available for only
six patients, and Patient 11 was completed across checkpointed processes. The study also lacks
an exact MILP or other global-optimum baseline, so it cannot report an optimality gap. These
experiments remain useful follow-up work, but they are separate from the current GA-versus-
clinician-angle result.
