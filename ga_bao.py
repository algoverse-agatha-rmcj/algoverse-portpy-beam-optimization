"""
ga_bao.py -- Genetic Algorithm for Beam Angle Optimization (BAO) on PortPy.

WHAT THIS IS
------------
A genetic algorithm that searches for a good set of IMRT beam angles. PortPy is
treated as a black-box "fitness function": we hand it a set of beam angles, it
runs the (convex) fluence optimization with MOSEK and returns an objective
value; lower = better. The GA evolves a population of beam-angle sets toward
lower objective values, and we compare the winner against PortPy's MILP global
optimum.

KEY DESIGN: "down-sample once"
------------------------------
Down-sampling the influence matrix is expensive (~minutes) but a per-solve is
cheap (~seconds). So we down-sample the FULL candidate-beam pool a SINGLE time,
then score each candidate beam set by DEACTIVATING the beams it doesn't use
(forcing their beamlet intensities to 0) instead of rebuilding the matrix.

REQUIREMENTS
------------
- PortPy env with MOSEK (see TEAM_SETUP.md).
- Patient data downloaded with `--beam-mode ga` so the no-180 candidate pool exists
  (planner-only data has just ~7 beams).
- The PortPy down-sampler patch applied (scripts/patch_portpy_downsampler.py),
  otherwise create_down_sample crashes on the current data format.

USAGE
-----
    python ga_bao.py --patient Lung_Patient_3 --pool 0 3 6 9 ... --k 7
    python ga_bao.py --patient Lung_Patient_3 --pop 20 --gens 40

Results are written under results/<patient>/ga_runs/ by default. The default candidate
pool excludes 180 degrees because PortPy does not model the treatment couch;
each patient's clinician beams are added automatically if the grid omits them.

WHERE TO MODIFY (for teammates)
-------------------------------
- Change the FITNESS (what "good" means):  BAOProblem.evaluate()  [Section 1]
      e.g. replace `prob.value` with a clinical score built from pp.Evaluation.
- Change the GA OPERATORS:                  Section 2
      tournament() = selection, crossover() = breeding, mutate() = exploration.
- Change the LOOP (elitism, termination):   run_ga()  [Section 3]
- Tune HYPERPARAMETERS without editing code: the CLI flags in main() [Section 4]
      --pop, --gens, --mutation-rate, --k, --pool, --seed.
- Do NOT edit PortPy itself; everything radiotherapy-related is behind evaluate().
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import portpy.photon as pp

FAILED_SOLVE_SCORE = 1e12  # penalty recorded when a solve fails/infeasible (JSON-safe, sorts worst)


# ===========================================================================
# 1. THE PROBLEM: one-time PortPy setup + the evaluate(beam_ids) fitness seam
# ===========================================================================
class BAOProblem:
    """Loads a patient once, down-samples once, and scores beam sets on demand."""

    def __init__(self, data_dir, patient_id, candidate_pool,
                 protocol_name="Lung_2Gy_30Fx",
                 voxel_factors=(6, 6, 1), beamlet_factor=4,
                 downsample=True):
        self.candidate_pool = list(candidate_pool)

        # --- load the patient (cheap handles) ---
        data = pp.DataExplorer(data_dir=data_dir)
        data.patient_id = patient_id
        self.ct = pp.CT(data)
        self.structs = pp.Structures(data)
        self.cc = pp.ClinicalCriteria(data, protocol_name=protocol_name)
        self.opt_params = data.load_config_opt_params(protocol_name=protocol_name)
        self.structs.create_opt_structures(opt_params=self.opt_params,
                                            clinical_criteria=self.cc)

        # --- build the FULL candidate-pool influence matrix (down-sample ONCE, optional) ---
        beams = pp.Beams(data, beam_ids=self.candidate_pool)
        inf = pp.InfluenceMatrix(ct=self.ct, structs=self.structs, beams=beams)

        if downsample:
            opt_vox = [r * f for r, f in zip(self.ct.get_ct_res_xyz_mm(), voxel_factors)]
            bw = beams.get_finest_beamlet_width() * beamlet_factor
            bh = beams.get_finest_beamlet_height() * beamlet_factor
            print(f"[setup] down-sampling {len(self.candidate_pool)}-beam pool (one-time)...")
            t = time.time()
            self.inf = inf.create_down_sample(beamlet_width_mm=bw,
                                              beamlet_height_mm=bh,
                                              opt_vox_xyz_res_mm=opt_vox)
            print(f"[setup] down-sampled in {time.time() - t:.0f}s  (A: {self.inf.A.shape})")
        else:
            self.inf = inf   # FULL resolution -- no down-sampling (slower per solve, more RAM,
                             # but skips the patchify dependency + down-sampler patch)
            print(f"[setup] using FULL-resolution matrix (A: {self.inf.A.shape})")

        self.plan = pp.Plan(ct=self.ct, structs=self.structs, beams=beams,
                            inf_matrix=self.inf, clinical_criteria=self.cc)

        # --- map each beam_id -> its slice of the beamlet-intensity vector x ---
        self._beam_slices = {}
        for i in range(len(self.inf.beamlets_dict)):
            bd = self.inf.beamlets_dict[i]
            self._beam_slices[bd["beam_id"]] = (bd["start_beamlet_idx"],
                                                bd["end_beamlet_idx"])

        self._cache = {}   # frozenset(beam_ids) -> score, so we never re-solve a set

    def evaluate(self, beam_ids):
        """FITNESS SEAM: beam angles in -> optimization objective out (lower=better)."""
        key = frozenset(beam_ids)
        if key in self._cache:                      # memoize: identical set never re-solved
            return self._cache[key]

        opt = pp.Optimization(self.plan, opt_params=self.opt_params,
                              clinical_criteria=self.cc)
        opt.create_cvxpy_problem()
        x = opt.vars["x"]                            # beamlet intensities (decision vars)

        # DEACTIVATE every beam not in this candidate set by pinning its beamlets to 0
        for beam_id, (start, end) in self._beam_slices.items():
            if beam_id not in key:
                opt.constraints += [x[start:end] == 0]

        try:
            _, prob = opt.solve(solver="MOSEK", verbose=False, return_cvxpy_prob=True)
            val = prob.value
            score = float(val) if val is not None and math.isfinite(float(val)) else FAILED_SOLVE_SCORE
        except Exception as exc:  # a single bad beam set must not kill the whole run
            print(f"[warn] solve failed for beams {sorted(key)}: {type(exc).__name__}: {exc}")
            score = FAILED_SOLVE_SCORE
        self._cache[key] = score
        return score

    @property
    def num_solves(self):
        return len(self._cache)

    def save_cache(self, path):
        """Persist the solve cache so a crashed/interrupted run can resume for free."""
        data = [{"beams": sorted(bs), "score": sc} for bs, sc in self._cache.items()]
        Path(path).write_text(json.dumps(data))

    def load_cache(self, path):
        """Reload a previously saved cache (same seed => the GA replays instantly)."""
        p = Path(path)
        if p.exists():
            for item in json.loads(p.read_text()):
                self._cache[frozenset(item["beams"])] = item["score"]
            print(f"[checkpoint] loaded {len(self._cache)} cached solves from {p.name}")


# ===========================================================================
# 2. GENETIC ALGORITHM OPERATORS  (pure integer-set logic, no PortPy here)
# ===========================================================================
def random_individual(pool, k, rng):
    """A chromosome = a sorted tuple of k distinct beam_ids drawn from the pool."""
    return tuple(sorted(rng.sample(pool, k)))


def tournament(pop, fits, rng, t=3):
    """Selection: pick t random individuals, return the fittest (lowest objective)."""
    contenders = rng.sample(range(len(pop)), t)
    return pop[min(contenders, key=lambda i: fits[i])]


def crossover(p1, p2, pool, k, rng):
    """Combine two parents' beams, then draw k -- shared beams tend to survive."""
    genes = list(set(p1) | set(p2))
    while len(genes) < k:                            # top up if parents overlap a lot
        genes.append(rng.choice([b for b in pool if b not in genes]))
    return tuple(sorted(rng.sample(genes, k)))


def mutate(ind, pool, k, rng, rate):
    """Each selected beam has `rate` chance of being swapped for an unused one."""
    genes = set(ind)
    for _ in range(k):
        if rng.random() < rate:
            genes.discard(rng.choice(list(genes)))
            genes.add(rng.choice([b for b in pool if b not in genes]))
    genes = list(genes)
    while len(genes) < k:
        genes.append(rng.choice([b for b in pool if b not in genes]))
    return tuple(sorted(genes[:k]))


# ===========================================================================
# 3. THE GA LOOP
# ===========================================================================
def run_ga(problem, k, pop_size, generations, mutation_rate, seed=0,
           checkpoint_path=None, on_generation=None):
    rng = random.Random(seed)
    pool = problem.candidate_pool
    population = [random_individual(pool, k, rng) for _ in range(pop_size)]

    best, best_fit, history = None, float("inf"), []

    for gen in range(generations):
        fits = [problem.evaluate(ind) for ind in population]   # memoized -> few real solves
        gen_best_i = min(range(pop_size), key=lambda i: fits[i])
        if fits[gen_best_i] < best_fit:
            best, best_fit = population[gen_best_i], fits[gen_best_i]

        history.append({"gen": gen,
                        "gen_best_fitness": fits[gen_best_i],
                        "overall_best_fitness": best_fit,
                        "best_angles": list(best),
                        "unique_solves": problem.num_solves})
        print(f"gen {gen:3d} | gen-best {fits[gen_best_i]:10.2f} | "
              f"overall-best {best_fit:10.2f} | angles {list(best)} | "
              f"solves {problem.num_solves}")

        # crash-safety: persist the cache + results after EVERY generation
        if checkpoint_path:
            problem.save_cache(checkpoint_path)
        if on_generation:
            on_generation(best, best_fit, history)

        # build next generation: elitism (keep best) + offspring
        new_pop = [best]
        while len(new_pop) < pop_size:
            p1 = tournament(population, fits, rng)
            p2 = tournament(population, fits, rng)
            child = mutate(crossover(p1, p2, pool, k, rng), pool, k, rng, mutation_rate)
            new_pop.append(child)
        population = new_pop

    return best, best_fit, history


# ===========================================================================
# 4. COMMAND-LINE ENTRY POINT
# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description="GA for beam-angle optimization on PortPy.")
    ap.add_argument("--data-dir", default=r"../data",
                    help="Path to the PortPy data folder (default: ../data, sibling of the repo).")
    ap.add_argument("--patient", default="Lung_Patient_3")
    ap.add_argument("--pool", type=int, nargs="+",
                    default=[b for b in range(0, 72, 3) if b != 36],
                    help="Candidate beam_ids to search over (default: every 15 degrees, "
                         "excluding 180 degrees; needs --beam-mode ga data).")
    ap.add_argument("--k", type=int, default=7, help="Number of beams to select.")
    ap.add_argument("--pop", type=int, default=20, help="Population size.")
    ap.add_argument("--gens", type=int, default=40, help="Number of generations.")
    ap.add_argument("--mutation-rate", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-downsample", action="store_true",
                    help="Use full-resolution matrices (slower per solve, more RAM; "
                         "skips patchify + the down-sampler patch).")
    ap.add_argument("--out", default=None,
                    help="Results JSON (default: results/<patient>/ga_runs/"
                         "<patient>_ga_<resolution>_seed_<seed>.json).")
    ap.add_argument("--checkpoint", default=None,
                    help="Cache file for crash-safe resume (default: matching file in "
                         "results/<patient>/cache/).")
    args = ap.parse_args()

    resolution = "full_resolution" if args.no_downsample else "downsampled"
    using_default_out = args.out is None
    patient_results = Path("results") / args.patient
    if using_default_out:
        args.out = str(
            patient_results / "ga_runs"
            / f"{args.patient}_ga_{resolution}_seed_{args.seed}.json"
        )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    # The planner (expert) beams must be reachable from the pool, otherwise a
    # GA-vs-expert comparison is rigged: on Lung_Patient_2 the expert uses beam 37
    # (185 deg), which a 15-deg grid like range(0,72,3) cannot represent.
    planner = json.loads(
        (Path(args.data_dir) / args.patient / "PlannerBeams.json").read_text())["IDs"]
    # Keep 180 degrees excluded even if a patient planner happens to use it. The
    # clinician plan is still scored exactly as delivered by PortPy; this guard only
    # prevents the GA from exploiting a couch-free 180-degree beam in simulation.
    missing = sorted((set(planner) - {36}) - set(args.pool))
    if missing:
        args.pool = sorted(set(args.pool) | set(missing))
        print(f"[pool] added expert beams {missing}; pool is now {len(args.pool)} beams")
    if 36 in args.pool:
        raise SystemExit("candidate pool contains beam 36 (180 degrees); remove it for "
                         "the couch-aware comparison protocol")

    if args.checkpoint:
        ckpt = args.checkpoint
    elif using_default_out:
        ckpt = str(patient_results / "cache" / (Path(args.out).name + ".cache.json"))
    else:
        ckpt = args.out + ".cache.json"
    Path(ckpt).parent.mkdir(parents=True, exist_ok=True)

    problem = BAOProblem(args.data_dir, args.patient, args.pool,
                         downsample=not args.no_downsample)
    problem.load_cache(ckpt)   # resume: reuse any solves from a previous/interrupted run

    t0 = time.time()

    def write_results(best, best_fit, history):
        Path(args.out).write_text(json.dumps({
            "patient": args.patient, "pool": args.pool, "k": args.k,
            "pop": args.pop, "gens": args.gens, "mutation_rate": args.mutation_rate,
            "seed": args.seed,
            "best_angles": list(best), "best_fitness": best_fit,
            "unique_solves": problem.num_solves,
            "wall_time_s": round(time.time() - t0, 1),
            "history": history,
        }, indent=2))

    best, best_fit, history = run_ga(problem, args.k, args.pop, args.gens,
                                     args.mutation_rate, args.seed,
                                     checkpoint_path=ckpt, on_generation=write_results)
    write_results(best, best_fit, history)   # final write
    problem.save_cache(ckpt)

    print("\n=== RESULT ===")
    print(f"best angles (beam_ids): {list(best)}")
    print(f"best fitness         : {best_fit:.4f}")
    print(f"unique MOSEK solves  : {problem.num_solves}  (of {args.pop * args.gens} evaluations)")
    print(f"wall time            : {time.time() - t0:.0f}s")
    print(f"saved -> {args.out}  (cache: {ckpt})")


if __name__ == "__main__":
    main()
