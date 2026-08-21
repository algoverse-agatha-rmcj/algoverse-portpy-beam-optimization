# Project status and unfinished work

Updated 2026-08-12. This is the repository backlog; meeting transcripts and Slack determine
individual ownership.

## Completed

- The no-180 genetic algorithm runs end to end and checkpoints after every generation.
- Patients 2–6 have committed seed-0 GA results, full-resolution clinician comparisons,
  and three-page DVH reports.
- GA winners and clinician angles are re-solved at the same resolution before comparison.
- Patient data can be downloaded one selected beam set at a time and removed after bundle
  validation.

## Active priorities

1. Have a second team member review the GA, clinical-comparison, and reporting logic in depth.
2. Regenerate the Patients 2–6 PDFs from their cached curves so the committed figures use
   the corrected target-versus-organ emphasis rule. No clinical solve needs to be repeated.
3. Repeat the GA across several seeds and report variability; one seed is not evidence of
   convergence or robustness.
4. Define a fair compute benchmark. PortPy 1.1.4 does not ship the assumed exact MILP
   beam-angle optimizer, so document a reproducible baseline before claiming speedup.
5. Add end-to-end compute measurements beyond per-solve time, including total wall time and
   the hardware/environment used.
6. Aggregate the patient results: win/loss rate versus clinician angles, target coverage,
   organ-at-risk tradeoffs, and patient-to-patient consistency.
7. Confirm the intended cohort size and obtain approved compute before scaling beyond the
   five committed patients.

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
- Paper drafting beyond methods scaffolding until the compute comparison and repeat-seed
  results are available.
