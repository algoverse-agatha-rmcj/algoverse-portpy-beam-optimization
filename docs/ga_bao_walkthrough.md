# ga_bao.py — Line-by-Line Code Walkthrough

Genetic Algorithm for Beam Angle Optimization (BAO) on PortPy. Lives at `ga_bao.py` in the
repo root. Lines 1–43 are the module docstring (what the file is, the "down-sample once"
design, requirements, usage, and a "where to modify" guide). Everything from line 44 on is code.

The design principle: **all the radiotherapy is sealed inside `evaluate()`; the GA itself is
pure integer math** (shuffling beam-ID numbers).

## Imports & module constant
- **44** `from __future__ import annotations` — makes type hints lazy (strings); modern syntax, no runtime cost.
- **46** `import argparse` — parse command-line flags.
- **47** `import json` — read/write JSON (results + cache file).
- **48** `import math` — used for `math.isfinite` in the solve error-check.
- **49** `import random` — the random-number generator the GA uses.
- **50** `import time` — wall-clock timing.
- **51** `from pathlib import Path` — clean file-path handling.
- **53** `import numpy as np` — imported but NOT currently used (harmless leftover; could be deleted).
- **54** `import portpy.photon as pp` — the PortPy radiotherapy engine.
- **56** `FAILED_SOLVE_SCORE = 1e12` — a big finite penalty for failed solves, so the GA treats that beam set as worst-possible without crashing.

## Section 1 — class BAOProblem (the PortPy wrapper)
- **62** `class BAOProblem:` — the class that wraps PortPy.

### `__init__` (one-time setup)
- **65–68** — the constructor signature; required params first (data path, patient, candidate beams), then optional ones with defaults (protocol, down-sample factors, `downsample=True`).
- **69** `self.candidate_pool = list(candidate_pool)` — store a fresh list copy of the beam pool.
- **72** `data = pp.DataExplorer(data_dir=data_dir)` — create the data "librarian".
- **73** `data.patient_id = patient_id` — which patient to load.
- **74** `self.ct = pp.CT(data)` — load the CT scan.
- **75** `self.structs = pp.Structures(data)` — load the organ/tumor structures.
- **76** `self.cc = pp.ClinicalCriteria(...)` — load the prescription + dose limits.
- **77** `self.opt_params = data.load_config_opt_params(...)` — load the objective weights (fitness config).
- **78–79** `self.structs.create_opt_structures(...)` — build the computed structures (the rinds).
- **82** `beams = pp.Beams(data, beam_ids=self.candidate_pool)` — load ALL candidate beams.
- **83** `inf = pp.InfluenceMatrix(...)` — assemble their full influence matrix A.
- **85** `if downsample:` — branch: down-sample or not.
- **86** `opt_vox = [r*f for r,f in zip(self.ct.get_ct_res_xyz_mm(), voxel_factors)]` — coarser voxel resolution.
- **87–88** `bw = ... * beamlet_factor`, `bh = ...` — coarser beamlet width/height.
- **90–93** `self.inf = inf.create_down_sample(...)` — the one-time down-sample; store the small matrix.
- **95–98** `else: self.inf = inf` — keep the full-resolution matrix (the `--no-downsample` path).
- **100–101** `self.plan = pp.Plan(..., inf_matrix=self.inf, ...)` — bundle everything into one reusable Plan.
- **104–108** — build `self._beam_slices` = `{beam_id: (start, end)}`, mapping each beam to its block of `x`.
- **110** `self._cache = {}` — the memoization cache (beam set → score).

### `evaluate` (the fitness seam)
- **112** `def evaluate(self, beam_ids):` — the fitness function.
- **114** `key = frozenset(beam_ids)` — order-independent, hashable key.
- **115–116** `if key in self._cache: return self._cache[key]` — cache hit → return instantly, no solve.
- **118–120** `opt = pp.Optimization(...)`, `opt.create_cvxpy_problem()` — build the problem on the shared plan.
- **121** `x = opt.vars["x"]` — the beamlet-intensity decision variable.
- **124–126** — for every beam NOT in this set, `opt.constraints += [x[start:end] == 0]` (turn it off).
- **128–131** — solve with MOSEK inside a `try`; `score` = `prob.value` if finite, else `FAILED_SOLVE_SCORE`.
- **132–134** `except Exception:` — on error, warn and record `FAILED_SOLVE_SCORE` instead of crashing.
- **135–136** `self._cache[key] = score; return score` — cache and return.

### helper methods
- **138–140** `num_solves` (property) — count of unique beam sets actually solved.
- **142–145** `save_cache(path)` — write the cache to disk as a list of `{beams, score}`.
- **147–153** `load_cache(path)` — reload a saved cache on startup (enables free resume).

## Section 2 — GA operators (pure integer logic, no PortPy)
A chromosome = a sorted tuple of K beam IDs, e.g. `(0, 9, 18, 30, 42, 51, 63)`.
- **159–161** `random_individual(pool, k, rng)` — pick k distinct beams at random → sorted tuple.
- **164–167** `tournament(pop, fits, rng, t=3)` — selection: pick 3 at random, return the fittest (lowest).
- **170–175** `crossover(p1, p2, pool, k, rng)` — union both parents' beams, draw k (shared beams tend to survive).
- **178–188** `mutate(ind, pool, k, rng, rate)` — each beam has `rate` chance to swap for an unused one; keep exactly k.

## Section 3 — run_ga (the evolution loop)
- **194–195** — signature, incl. `checkpoint_path` and `on_generation` callback.
- **196** `rng = random.Random(seed)` — seeded RNG (reproducible).
- **198** `population = [random_individual(...) for _ in range(pop_size)]` — generation 0.
- **200** `best, best_fit, history = None, float("inf"), []` — track the all-time best + a log.
- **202** `for gen in range(generations):` — the generation loop.
- **203** `fits = [problem.evaluate(ind) for ind in population]` — score everyone (memoized).
- **204–206** — find this generation's best; update the champion if it improved.
- **208–215** — record to `history` and print the generation summary line.
- **218–219** `if checkpoint_path: problem.save_cache(...)` — save the cache after every generation.
- **220–221** `if on_generation: on_generation(...)` — call the results-writer callback.
- **224** `new_pop = [best]` — elitism: the champion survives untouched.
- **225–229** — fill the rest via tournament → crossover → mutate.
- **230** `population = new_pop` — replace the population.
- **232** `return best, best_fit, history` — hand back the winner + log.

## Section 4 — main (the CLI)
- **238–239** — define `main()` and the argument parser.
- **240–255** — every flag: `--data-dir`, `--patient`, `--pool`, `--k`, `--pop`, `--gens`, `--mutation-rate`, `--seed`, `--no-downsample`, `--out`, `--checkpoint`.
- **256** `args = ap.parse_args()` — read the command-line values.
- **258** `ckpt = args.checkpoint or (args.out + ".cache.json")` — the checkpoint path.
- **260–262** — build `BAOProblem` (down-sample unless `--no-downsample`), then `load_cache(ckpt)` to resume.
- **264** `t0 = time.time()` — start the run timer.
- **266–275** `write_results(...)` — nested helper that dumps config + best + history to the results JSON.
- **277–279** `run_ga(..., checkpoint_path=ckpt, on_generation=write_results)` — run the GA with checkpointing.
- **280–281** — final results write + cache save.
- **283–288** — print the final summary.
- **291–292** `if __name__ == "__main__": main()` — run `main()` only when executed directly.

## One-sentence summary
`BAOProblem` down-samples PortPy once and turns "beam angles → fitness number" (by toggling
beams and solving, with error-handling); `run_ga` evolves a population toward the lowest
fitness with tournament/crossover/mutation/elitism, checkpointing every generation; `main`
wires up the CLI, resumes from cache, and saves results continuously.
