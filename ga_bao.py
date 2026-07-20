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
- Patient data downloaded with `--beam-mode all` so a real candidate pool exists
  (planner-only data has just ~7 beams).
- The PortPy down-sampler patch applied (scripts/patch_portpy_downsampler.py),
  otherwise create_down_sample crashes on the current data format.

USAGE
-----
    python ga_bao.py --patient Lung_Patient_3 --pool 0 3 6 9 ... --k 7
    python ga_bao.py --patient Lung_Patient_3 --pop 20 --gens 40 --out ga_results.json

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
import random
import time
from pathlib import Path

import numpy as np
import portpy.photon as pp


# ===========================================================================
# 1. THE PROBLEM: one-time PortPy setup + the evaluate(beam_ids) fitness seam
# ===========================================================================
class BAOProblem:
    """Loads a patient once, down-samples once, and scores beam sets on demand."""

    def __init__(self, data_dir, patient_id, candidate_pool,
                 protocol_name="Lung_2Gy_30Fx",
                 voxel_factors=(6, 6, 1), beamlet_factor=4):
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

        # --- build the FULL candidate-pool influence matrix, down-sample ONCE ---
        beams = pp.Beams(data, beam_ids=self.candidate_pool)
        inf = pp.InfluenceMatrix(ct=self.ct, structs=self.structs, beams=beams)
        opt_vox = [r * f for r, f in zip(self.ct.get_ct_res_xyz_mm(), voxel_factors)]
        bw = beams.get_finest_beamlet_width() * beamlet_factor
        bh = beams.get_finest_beamlet_height() * beamlet_factor

        print(f"[setup] down-sampling {len(self.candidate_pool)}-beam pool (one-time)...")
        t = time.time()
        self.inf_dbv = inf.create_down_sample(beamlet_width_mm=bw,
                                              beamlet_height_mm=bh,
                                              opt_vox_xyz_res_mm=opt_vox)
        print(f"[setup] done in {time.time() - t:.0f}s  (influence matrix A: {self.inf_dbv.A.shape})")

        self.plan = pp.Plan(ct=self.ct, structs=self.structs, beams=beams,
                            inf_matrix=self.inf_dbv, clinical_criteria=self.cc)

        # --- map each beam_id -> its slice of the beamlet-intensity vector x ---
        self._beam_slices = {}
        for i in range(len(self.inf_dbv.beamlets_dict)):
            bd = self.inf_dbv.beamlets_dict[i]
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

        _, prob = opt.solve(solver="MOSEK", verbose=False, return_cvxpy_prob=True)
        score = float(prob.value)
        self._cache[key] = score
        return score

    @property
    def num_solves(self):
        return len(self._cache)


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
def run_ga(problem, k, pop_size, generations, mutation_rate, seed=0):
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
    ap.add_argument("--pool", type=int, nargs="+", default=list(range(0, 72, 3)),
                    help="Candidate beam_ids to search over (needs --beam-mode all data).")
    ap.add_argument("--k", type=int, default=7, help="Number of beams to select.")
    ap.add_argument("--pop", type=int, default=20, help="Population size.")
    ap.add_argument("--gens", type=int, default=40, help="Number of generations.")
    ap.add_argument("--mutation-rate", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="ga_results.json")
    args = ap.parse_args()

    problem = BAOProblem(args.data_dir, args.patient, args.pool)

    t = time.time()
    best, best_fit, history = run_ga(problem, args.k, args.pop, args.gens,
                                     args.mutation_rate, args.seed)
    elapsed = time.time() - t

    print(f"\n=== RESULT ===")
    print(f"best angles (beam_ids): {list(best)}")
    print(f"best fitness         : {best_fit:.4f}")
    print(f"unique MOSEK solves  : {problem.num_solves}  (of {args.pop * args.gens} evaluations)")
    print(f"wall time            : {elapsed:.0f}s")

    Path(args.out).write_text(json.dumps({
        "patient": args.patient, "pool": args.pool, "k": args.k,
        "pop": args.pop, "gens": args.gens, "mutation_rate": args.mutation_rate,
        "seed": args.seed,
        "best_angles": list(best), "best_fitness": best_fit,
        "unique_solves": problem.num_solves, "wall_time_s": elapsed,
        "history": history,
    }, indent=2))
    print(f"saved -> {args.out}")


if __name__ == "__main__":
    main()
