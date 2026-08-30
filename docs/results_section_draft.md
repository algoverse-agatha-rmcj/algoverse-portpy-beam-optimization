# Results

## Cohort and primary planning objective

We evaluated the sequentially numbered PortPy lung cases from Patient 2 through Patient 41.
Thirty-seven of the 40 cases produced matched full-resolution comparisons. Patient 12 was
excluded because dose-influence matrices were unavailable for part of its published beam
catalogue. Patients 13 and 35 were excluded because their structure indices exceeded the
corresponding influence-matrix dimensions, which prevented even the clinician-selected beam
sets from being re-solved.

The genetic algorithm produced a lower full-resolution planning objective than the
clinician-selected angle arrangement for 30 of 37 patients (Figure 1). The arithmetic mean
objective improvement was 12.14%, where positive values indicate a lower objective under the
GA angles. Patients 14 and 38 had the two largest improvements, 65.83% and 52.30%,
respectively. Excluding these two cases as a sensitivity calculation reduced the arithmetic
mean improvement to 9.46%. The GA produced a higher objective in seven patients. Six of these
losses were 1.51% or smaller, while Patient 21 had the largest loss at 4.29%. The mean loss
across the seven cases was 1.49%.

## Effect of full-resolution re-evaluation

At the reduced resolution used during the search, the GA plan had a lower objective in 35 of
37 patients. Full-resolution re-evaluation changed the outcome for five patients: Patients 6,
7, 10, 21, and 32 changed from a reduced-resolution GA win to a full-resolution loss. No case
changed from a reduced-resolution loss to a full-resolution win. Patient 32 showed the largest
change, from a 25.14% improvement at reduced resolution to a 1.40% loss at full resolution.
These reversals support using the matched full-resolution re-solves, rather than the search
fitness, for the primary comparison.

Objective-term exports were available for the 20 newer cases, Patients 21 through 41 except
Patient 35. Within this subset, the combined PTV penalty was lower under the GA angles in 19
of 20 patients, and the combined organ-at-risk penalty was lower in 16 of 20. Averaged across
the subset, the clinician-minus-GA objective differences were 12.55 objective units for PTV
terms, 2.03 for organ-at-risk terms, 0.24 for ring terms, and 0.99 for fluence smoothness.
Thus, the target terms accounted for most of the mean objective reduction in the cases where
term-level analysis was available.

The decomposition also separated two different patient-level outcomes. For Patient 38,
129.42 of the 131.18 objective-unit difference came from lower PTV penalties, and PTV D95
increased by 0.48 Gy. For Patient 32, the PTV terms improved by 1.25 objective units, but the
organ-at-risk and smoothness terms worsened by 1.32 and 0.53 units, respectively, producing a
0.64-unit full-resolution loss overall. These cases show that the total objective can improve
through different combinations of target coverage, organ dose, and fluence regularity.

## Target coverage and clinical dose criteria

Mean PTV D95 was 59.68 Gy under the GA angles and 59.54 Gy under the clinician-selected
angles, against a 60 Gy prescription. Across the seven objective-loss cases, the largest
absolute change in PTV D95 was 0.08 Gy. The three largest objective gains coincided with
increased target coverage: PTV D95 increased by 1.24 Gy for Patient 14, 0.48 Gy for Patient
38, and 1.46 Gy for Patient 17. Because objective-term exports were unavailable for Patients
14 and 17, those two associations are descriptive rather than a decomposition of the cause.

Organ-at-risk metrics moved in both directions (Table 1). Mean esophagus dose decreased by
0.49 Gy, and mean heart dose decreased by 0.62 Gy across the 36 patients with heart
measurements. Mean dose to the lungs excluding the GTV increased by 0.32 Gy, while V20 for
the same structure increased by 0.14 percentage points. Maximum left-lung and right-lung dose
increased by 6.35 Gy and 2.08 Gy on average, respectively. These side-specific lung maxima
are reported without assigning clinical benefit because the current data do not identify tumor
laterality.

The clinician-angle re-solves had three protocol-limit violations and the GA re-solves had
one. All four were esophagus V60 violations. The clinician-angle violations occurred in
Patients 8, 21, and 38; the GA violation occurred in Patient 21. Heart measurements were
unavailable for Patient 8 and were excluded only from the heart-specific cohort means.

## Computation

To avoid mixing sequential and parallel execution conditions, the runtime summary uses only
the original 18-patient sequential cohort. Patient 11 was resumed from a checkpoint, so its
wall time covered only the final process segment and was excluded from the full-run mean. The
mean GA wall time was 1.50 hours across the remaining 17 complete sequential runs. Seven of
the sequential cases recorded per-solve timing, covering 4,937 solves with a pooled arithmetic
mean of 7.085 seconds. The largest patient-level p95 was 14.437 seconds, and the largest
observed solve was 18.439 seconds. Timing from the 19 extension patients is not pooled with
these values because those patients ran in three concurrent lanes.

# Discussion

The GA found a lower full-resolution PortPy objective for 30 of 37 patients, and the
sensitivity mean remained positive after removing the two largest gains. The seven losses
were generally small and did not produce a large change in PTV D95. In the 20 patients with
term-level exports, PTV penalties were lower in 19 cases and accounted for most of the mean
objective reduction. The gains for Patients 14, 17, and 38 also coincided with recovery of
target coverage relative to the clinician-angle re-solves.

The clinical metrics do not support describing every lower objective as a uniformly better
plan. Heart and esophagus means were lower under the GA angles on average, but mean dose and
V20 for lungs excluding the GTV increased slightly, and the side-specific lung maximum doses
increased more substantially. Patient 32 provides a direct example: its target penalty
improved, but organ-at-risk and smoothness penalties outweighed that gain at full resolution.
The five resolution reversals also show that a beam arrangement selected on the reduced
problem can change rank when evaluated on the full influence matrix.

The strongest supported conclusion is that GA-selected angles often improve the PortPy
objective relative to clinician-selected angles under a shared fluence-optimization pipeline,
while maintaining similar target coverage across this 37-patient sample. This is a comparison
of beam geometries after both angle sets are re-optimized in PortPy. It is not a comparison
against the original delivered clinical fluence, and it does not establish clinical
superiority or a global optimum.

# Limitations

Each patient has one seed-0 GA run, so the study does not measure variability across random
initializations or demonstrate convergence. The 37 cases are a sequential subset of the 201
released PortPy lung patients rather than a random sample of the full catalogue. Three cases
were excluded for documented upstream data defects that prevented a matched comparison.

Objective-term exports are available for only the 20 newer cases. The full-cohort clinical
criteria remain comparable, but term-level claims must retain the 20-patient denominator.
Tumor laterality is also unavailable in the current analysis, which limits interpretation of
the left-lung and right-lung maximum-dose results. Clinical review is still required for the
target-dose language, side-specific lung findings, and protocol-limit violations.

The timing data describe workload under the sequential runs but do not support a speedup
claim. Hardware and execution conditions were not recorded uniformly, two runs were resumed,
and the extension cohort ran concurrently. The study also lacks an exact MILP or other
global-optimum baseline, so it cannot report an optimality gap.
