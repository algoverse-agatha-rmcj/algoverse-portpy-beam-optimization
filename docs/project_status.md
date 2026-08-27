# Project status and unfinished work

Updated 2026-08-26. This is the repository backlog; meeting transcripts and Slack determine
individual ownership.

## Completed

- The ASCI abstract registration was submitted; the full paper is now the deadline-driving
  deliverable.
- The no-180 genetic algorithm runs end to end and checkpoints after every generation.
- Patients 2–6 have committed seed-0 GA results, full-resolution clinician comparisons,
  and three-page DVH reports.
- GA winners and clinician angles are re-solved at the same resolution before comparison.
- Patient data can be downloaded one selected beam set at a time and removed after bundle
  validation.
- Beam selection, the 180-degree exclusion, and every reported angle are resolved from each
  beam's real `gantry_angle` rather than from `beam_id * 5`. That arithmetic is only valid
  for Patients 2-10 and silently produced a wrong pool, a wrong exclusion, and wrong reported
  angles from Patient 11 onward. See the README section "Beam IDs do not encode gantry
  angles"; guarded by `tests/test_beam_angles.py`.
- The pipeline accepts any patient in the catalogue, not only Patients 3-6.
- The matched seed-0 cohort now contains 18 usable patients (Patients 2-11 and 14-21),
  with Patients 12 and 13 excluded for documented upstream data defects.
- The Algoverse Patient 21 protocol-lock pilot, batch ID
  `lung-seed0-pilot-20260826-v2`, completed the 40-generation GA, both clinical
  comparisons, DVH generation, bundle validation, and raw-data cleanup. Its reduced
  resolution result was 1.18 percent better than the clinician, while its full-resolution
  objective was 4.29 percent worse. Full-resolution results remain the clinical source of
  truth. See `docs/large_batch_handoff.md` for the exact handoff.
- Future cohort extensions use a frozen primary protocol, a predeclared patient-list
  manifest, exact candidate-pool validation, run/data/code provenance, and
  protocol-fingerprinted caches. These safeguards only record or reject state; they do not
  give new patients more optimizer data, attempts, or compute. Corrected timing and
  objective-term exports remain new-only analysis fields unless old cases are re-solved.
- `scripts/analyze_cohort.py` regenerates the cohort evidence from the authoritative
  full-resolution comparisons using arithmetic means and explicit outlier disclosure.
- `scripts/generate_paper_assets.py` regenerates the manuscript cohort table and vector
  per-patient objective figure from the same summary.
- Patient 11's timing discrepancy is resolved: it resumed with 653 cached solves, so its
  456-second wall time is a process segment and is excluded from the 16-patient full-run mean.

## Active priorities

1. Copy the drafted Results, Discussion, Limitations, cohort table, and objective figure into
   the shared paper, then send that draft to Ruizhe for the review promised on the PI call.
2. Get clinical review of the target-dose language, left-lung maximum, Patient 8 violation,
   and Patients 14/17 using `docs/clinical_review_checklist.md`.
3. Export objective terms on future full-resolution comparisons so the team can distinguish
   target-coverage gains from organ-at-risk penalties instead of inferring from total score.
4. Have a second team member review the GA, clinical-comparison, aggregation, and reporting
   logic in depth.
5. Repeat the GA across several seeds and report variability; one seed is not evidence of
   convergence or robustness.
6. Define a fair compute benchmark before claiming speedup. A same-budget random search is
   immediately feasible; PortPy 1.1.4 does not ship the assumed exact MILP beam-angle
   optimizer, and the PI call placed MILP after the core paper work if time remains.
7. Regenerate the Patients 2–6 PDFs from their cached curves so the committed figures use
   the corrected target-versus-organ emphasis rule. No clinical solve needs to be repeated.
8. Obtain approved compute before scaling much beyond the committed patients. The cohort
   size is now confirmed rather than assumed: PortPy publishes **201 lung patients**
   (`Lung_Patient_2` through `Lung_Patient_202`, contiguous) and 129 prostate patients, so
   the meeting estimates of "20 or 50" were both wrong. At roughly one hour of GA wall time
   per patient per seed, the full lung cohort is ~200 hours for a single seed; any paper
   claim should describe a **sampled** subset with the sampling rule stated, not "the PortPy
   cohort".

## Repository administration

- Enable `main` branch protection in GitHub so changes require a reviewed pull request.
- Remove merged/stale remote branches only after confirming they are reachable from `main`.
- Update the GitHub repository description, which still says "prostate-cancer" although the
  committed experiments use lung cases.

## Useful improvements after the core study

- Add an evidence-based early-stopping rule; Patient 2's earlier run converged well before
  generation 40, while the current run had not converged at generation 40.
- Investigate whether fitness weights should penalize recurring organ-at-risk tradeoffs.
- Evaluate the threshold-sparsification idea from CompressRTP as a separate experiment;
  CompressRTP itself is not a beam-angle optimizer.
- Add a simple random-search baseline using the same solve budget.

## Deferred

- Simulated annealing, memetic algorithms, and explainability extensions.
- Clinical-expert outreach and paper promotion until the implementation and results are
  validated.
- MILP development until the core Results section, review, and objective-term analysis are
  complete.
