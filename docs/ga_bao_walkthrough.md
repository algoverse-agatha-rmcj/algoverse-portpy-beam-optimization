# ga_bao.py walkthrough

A guided tour of `ga_bao.py`, the genetic algorithm for beam-angle optimization, organized by
the file's four numbered sections. It names functions rather than line numbers so it stays
accurate as the file changes.

The design principle: **all of the radiotherapy is sealed inside `BAOProblem.evaluate()`; the
GA itself only shuffles sets of beam-ID integers.** For what `evaluate()` actually minimizes,
see [`fitness_function.md`](fitness_function.md).

## Imports and constants

- `portpy.photon as pp` is the radiotherapy engine: patient loading, influence matrices, and the
  CVXPY optimization.
- From `scripts/beam_angles.py`: `fetch_angle_map()`, `grid_pool()`, `excluded_ids()` and
  `format_angles()`. These read each beam's real gantry angle from metadata, because beam IDs
  do not encode angles (see the README).
- From `scripts/experiment_protocol.py`: the frozen primary protocol (`PRIMARY_K`,
  `PRIMARY_POPULATION`, `PRIMARY_GENERATIONS`, `PRIMARY_MUTATION_RATE`, `PRIMARY_SEED`, the
  down-sampling factors) and the provenance helpers `build_run_manifest()`, `cache_payload()`,
  `validated_cache_entries()` and `fingerprint()`.
- From `scripts/json_io.py`: `atomic_write_json()` and `read_json()`. Results and caches are
  written atomically so a crash can never leave a half-written file.
- `FAILED_SOLVE_SCORE = 1e12` is the score recorded when a solve fails or returns no finite
  value. It is finite so it stays JSON-safe, and large enough to rank as the worst possible set.

## Section 1: `BAOProblem`

One object per patient. It does the expensive setup once, then scores beam sets on demand.

### `__init__`

1. **Load the patient.** `pp.DataExplorer` points at the data folder; `pp.CT`, `pp.Structures`
   and `pp.ClinicalCriteria` load the scan, contours and the `Lung_2Gy_30Fx` protocol.
   `load_config_opt_params()` loads the objective weights, and `create_opt_structures()` builds
   the derived structures, including the `RIND_*` rings.
2. **Build the influence matrix for the whole candidate pool.** `pp.Beams` and
   `pp.InfluenceMatrix` are created for every beam in the pool, not for one candidate set.
3. **Down-sample it once** (unless `downsample=False`). The CT voxel size is multiplied by the
   voxel factors and the finest beamlet size by the beamlet factor, then
   `create_down_sample()` produces the smaller matrix. This takes minutes, which is why it
   happens only here.
4. **Create one reusable `pp.Plan`** on that matrix.
5. **Map each beam to its slice of `x`.** `_beam_slices[beam_id] = (start, end)` records which
   entries of the beamlet-intensity vector belong to which beam.
6. **Start empty caches.** `_cache` maps a `frozenset` of beam IDs to its score, and
   `_solve_seconds` maps it to the time that solve took.

### `evaluate(beam_ids)`: the fitness seam

1. If this set of beams was scored before, return the cached score without solving.
2. Build a fresh `pp.Optimization` on the shared plan and call `create_cvxpy_problem()`.
3. For every beam in the pool that is **not** in the candidate set, add the constraint
   `x[start:end] == 0`. That turns those beams off without rebuilding the matrix.
4. Solve with MOSEK. The score is the problem's objective value, or `FAILED_SOLVE_SCORE` if the
   solve raises or returns a non-finite value. A single bad beam set cannot stop the run.
5. Record the elapsed time and the score, then return the score.

To change what "good" means, this is the only method to edit.

### Supporting members

- `solve_time_stats` summarizes the recorded solve times: count, arithmetic mean, p95, min, max
  and total. The mean is the study's canonical statistic; p95 and max keep slow outliers visible.
- `num_solves` is the number of unique beam sets solved.
- `save_cache(path)` writes every scored set, with its time, tagged with the run's cache
  identity.
- `load_cache(path)` reloads a previous cache, but only through `validated_cache_entries()`,
  which rejects a cache from a different patient, configuration, dataset or code version.

## Section 2: GA operators

Pure integer-set logic with no PortPy calls. A chromosome is a sorted tuple of `k` distinct
beam IDs.

- `random_individual(pool, k, rng)` draws `k` beams from the pool.
- `tournament(pop, fits, rng, t=3)` picks three individuals at random and returns the one with
  the lowest objective.
- `crossover(p1, p2, pool, k, rng)` pools both parents' beams, tops the pool up from unused beams
  if the parents overlap heavily, and draws `k` of them. Every beam in that combined set is
  equally likely to be kept, whether one parent had it or both did.
- `mutate(ind, pool, k, rng, rate)` gives each of the `k` positions a `rate` chance of swapping
  one of the individual's beams for a beam it does not have, then pads back to `k` if needed.

## Section 3: `run_ga()`

1. Seed a `random.Random(seed)` and create `pop_size` random individuals. Everything downstream
   uses this one generator, so the same seed and cache replay the same run.
2. For each generation:
   - Score every individual with `problem.evaluate()`. The memoization means most repeat
     individuals cost nothing.
   - Update the best set seen so far and append a history row: generation, generation best,
     overall best, best beams and unique solves.
   - Save the cache and call `on_generation`, which rewrites the results file. A run killed at
     any point loses at most one generation.
   - Build the next generation with **elitism**: the overall best is carried over unchanged, and
     the rest are children made by tournament selection, crossover and mutation.
3. Return the best set, its fitness and the history.

The loop always runs the full number of generations; there is no early stopping.

## Section 4: `main()`

1. **Parse the flags.** `--patient`, `--pool`, `--k`, `--pop`, `--gens`, `--mutation-rate` and
   `--seed` default to the frozen primary protocol. `--no-downsample` searches at full
   resolution, and `--out` and `--checkpoint` override the default paths.
2. **Resolve the candidate pool from real angles.** `fetch_angle_map()` reads the beam
   metadata, `excluded_ids()` finds the 180-degree beam, and `grid_pool()` selects the 15-degree
   grid unless `--pool` was given.
3. **Make the clinician's beams reachable.** Any beam in `PlannerBeams.json` that is missing
   from the pool is added, except a 180-degree beam, so every clinician beam is available to the
   GA. The clinician's set can still differ in size from `k`: 11 patients use 6 beams and 2 use 8.
4. **Validate the inputs.** The run stops if the pool contains a 180-degree beam, unknown or
   duplicate IDs, or if `k`, the population, the generation count or the mutation rate is out
   of range.
5. **Freeze provenance before optimizing.** `scientific_config()` and `build_run_manifest()`
   record the patient, pool, angles, clinician beams, configuration, data and code hashes. An
   existing result or manifest with different provenance is refused rather than overwritten.
   The manifest is written next to the result.
6. **Pick the cache path.** By default it lives in `results/<patient>/cache/` and its name
   includes a short hash of the cache identity.
7. **Run.** Build `BAOProblem`, load any valid cache, run `run_ga()` with a callback that
   rewrites the results JSON every generation, then write the final results and cache.

The results JSON holds the configuration, the protocol manifest, the best beam IDs and their
gantry angles, the best fitness, unique solves, wall time, solve-time statistics and the
per-generation history. `wall_time_s` covers only what this process ran, so it is not
comparable across resumed runs; `solve_time_s` travels with the cache and is.
