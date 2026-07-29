# Lung_Patient_2 — GA vs. clinician, first end-to-end comparison

Milen, 2026-07-29. Branch `milen/patient2-expert-pool`. All runs on a Mac Studio (M4 Max, 36 GB).

## Headline

On Lung_Patient_2 the GA finds beam angles that **reduce heart V30Gy by 32% and lung
V20Gy by 6%** relative to the clinical plan, with **identical target coverage**
(PTV D95 59.5 Gy) and **every protocol criterion met** — at the cost of a higher spinal
cord max dose (28.4 → 42.3 Gy, still inside the 48 Gy goal and 50 Gy limit).

That trade is real and a planner would weigh it. It is a stronger and more defensible
claim than "the GA beat the expert objective by 3.8%".

## A bug that invalidated the comparison (fixed)

`ga_bao.py` searched a pool of `range(0,72,3)` — every 15°. Beams are 5° apart
(`beam_id * 5 = gantry angle`), and **the expert's beams are not all on that grid**:

| patient | expert beams | gantry | off-grid |
|---|---|---|---|
| Lung_Patient_2 | 0, 37, 42, 48, 54, 60, 66 | 0, **185**, 210, 240, 270, 300, 330 | 37 (185°) |
| Lung_Patient_3 | 0, 6, 12, 18, 24, 30, 35 | 0, 30, 60, 90, 120, 150, **175** | 35 (175°) |

The GA could not select the clinician's plan on either patient — so any GA-vs-expert
comparison run before this was rigged. Both patients place one beam a single 5° step off
180°, which is the standard practice of avoiding a beam straight through the treatment
couch and its support rails.

**Fix:** `main()` now reads `PlannerBeams.json` and folds any missing planner beams into
the pool automatically. Generalises to any patient; no hardcoded angles.

## Objective results (down-sampled search)

Expert baseline scored with the identical fitness function: **106.6195**.

| run | pool | best | vs expert | angles (gantry) | solves | wall | converged |
|---|---|---|---|---|---|---|---|
| A | 25 beams (180° allowed) | 102.6027 | **+3.77%** | 30, 165, **180**, 195, 255, 285, 330 | 720 | 82 min | gen 24/40 |
| B | 24 beams (180° removed) | 103.8477 | **+2.60%** | 45, 165, 195, 255, 285, 300, 330 | 721 | 80 min | gen 33/40 |
| — | best of 20 random (gen 0 of A) | 112.21 | −5.24% | — | 20 | — | — |

Run B is the defensible number: PortPy does **not** model the treatment couch, so a beam
at exactly 180° is free in simulation but attenuated in reality. B removes that exploit
and still beats the clinician. B had not converged at generation 40, so 103.85 is likely
not its ceiling.

**Compute argument:** C(25,7) = 480,700 candidate sets. At 6.8 s/solve exhaustive search
is ~38 days; the GA reached its answer in 452 solves (~51 min), 0.09% of the space.

## Down-sampling fidelity (Agatha's question)

The margin is stable across three different discretizations:

| treatment | expert | GA A | margin |
|---|---|---|---|
| 25-beam pool, down-sampled | 106.62 | 102.60 | 3.77% |
| 7-beam pool, down-sampled | 111.75 | 107.72 | 3.60% |
| 7-beam pool, **full resolution** | 87.55 | 84.29 | 3.72% |

**Down-sampling distorts the absolute scale by ~28% but preserves the ranking.** It is a
valid search surrogate.

**But it does NOT preserve per-organ clinical metrics** — esophagus max and heart V30
both flipped direction between the down-sampled and full-resolution tables. Search
down-sampled; **evaluate at full resolution, always.**

Full resolution is also much cheaper than assumed: **42 s/solve**, matrix 386,585 × 6,004,
comfortable in 36 GB. A complete 720-solve GA at native resolution is ~8 h — an overnight
job. The team may not need down-sampling at all for single-patient work.

## Clinical criteria — full resolution (the numbers that matter)

All three plans meet every limit and goal (sole exception: expert PTV max 66.11 vs a
66 Gy goal). Bold = best.

| criterion | limit / goal | expert | GA A | GA B |
|---|---|---|---|---|
| HEART V30Gy (%) | 50 / 48 | 10.50 | 8.04 | **7.10** |
| LUNGS_NOT_GTV V20Gy (%) | 37 | 17.95 | 18.04 | **16.93** |
| ESOPHAGUS max (Gy) | 66 | 33.53 | **28.07** | 31.57 |
| LUNGS_NOT_GTV mean (Gy) | 21 / 20 | 9.74 | **9.69** | **9.69** |
| PTV max (Gy) | 69 / 66 | 66.11 | **66.00** | **66.00** |
| HEART mean (Gy) | 27 / 20 | **10.92** | 11.59 | 11.78 |
| CORD max (Gy) | 50 / 48 | **28.42** | 41.75 | 42.25 |
| LUNG_L max (Gy) | 66 | **14.87** | 33.18 | 32.13 |
| SKIN max (Gy) | 60 | **52.35** | 57.35 | 54.00 |
| PTV D95 (Gy) | — | 59.48 | 59.49 | 59.46 |

`HEART max`, `LUNG_R max`, `LUNGS_NOT_GTV max` are 66.00 for all three plans — those
structures abut the target, so the value is target dose leaking in. Uninformative rows.

### Why the GA behaves this way

The objective weights PTV underdose at 100,000 and PTV overdose at 10,000, against 3–20
for every organ at risk, plus a non-clinical `smoothness-quadratic` term at 100. The
optimizer faithfully buys target homogeneity and pays with organ dose. **The objective
value is a search signal, not a measure of plan quality** — a percentage on that scale
has no clinical meaning, and it is quadratic, so a 3.8% objective change is roughly a
1.9% change in dose error.

## Corrections to team assumptions

1. **CompressRTP (NeurIPS 2024) is not a beam-angle paper.** Its examples are
   `fluence_wavelets`, `matrix_sparse_only`, `matrix_sparse_plus_low_rank`; its DVH curves
   compare approximated vs actual dose under sparsification, on a fixed plan. There is no
   beam-angle result to compare against. Slack action item 1 assumes otherwise.
2. **PortPy 1.1.4 ships no MILP beam-angle optimizer.** Grep for `beam_angle|bao|milp|
   mixed-integer` returns nothing. The "within X% of optimal" claim has no source yet.
3. **Patient data is ~33 GB each** at `--beam-mode all`, not "multi-GB". Downloading many
   patients is a storage decision. The dataset has 331 patients (201 lung, 129 prostate).

## Reproduce

```bash
# env (no conda needed; Homebrew python3.11 + venv)
python3.11 -m venv ../portpy-venv
../portpy-venv/bin/pip install "portpy[mosek,data]" patchify && ../portpy-venv/bin/pip install numpy==2.4.6
../portpy-venv/bin/python scripts/patch_portpy_downsampler.py   # required, PortPy crashes without it
# MOSEK academic licence -> ~/mosek/mosek.lic

../portpy-venv/bin/python scripts/download_patient_data.py Lung_Patient_2 --beam-mode all

../portpy-venv/bin/python ga_bao.py --patient Lung_Patient_2 --k 7 --pop 20 --gens 40 \
    --out ga_results_lung2.json
../portpy-venv/bin/python scripts/score_beam_set.py --patient Lung_Patient_2   # expert baseline
../portpy-venv/bin/python scripts/clinical_compare.py --out clinical_compare_full.json
```

## Open

- One patient, one seed, no error bars. Needs repeat seeds before any claim is firm.
- Run B had not converged at 40 generations.
- DVH plot (GA curve vs expert curve) not yet built — the remaining Slack action item.
- Lung_Patient_3 has no expert baseline; nobody has scored `[0, 6, 12, 18, 24, 30, 35]`,
  so Jordan's 82.817 has nothing to measure against. Needs the Patient 3 download.
- Run A converged at gen 24 and burned 268 solves (~30 min) for nothing. Early stopping
  would roughly halve runtime.
