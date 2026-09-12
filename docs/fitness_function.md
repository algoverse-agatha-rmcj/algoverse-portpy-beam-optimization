# The fitness function

Every candidate beam set is scored by the objective value of the fluence-map optimization
PortPy solves for it, so lower is better. This page describes that objective as PortPy 1.1.4
implements it in `Optimization.create_cvxpy_problem()`
(`portpy/photon/optimization.py`), with the weights from the lung protocol used throughout
this study, `Lung_2Gy_30Fx`.

## The two levels

The study is a bilevel search. The genetic algorithm chooses a set $B$ of 7 beams from a
patient-specific candidate pool $\mathcal{P}$ of 24–30 beams:

$$\min_{B \subset \mathcal{P},\ |B| = 7} F(B)$$

The GA is a heuristic, so it does not establish that its best $B$ is the global minimum. The
clinician-selected sets it is compared against contain 6, 7 or 8 beams.

Each $B$ is scored by a convex quadratic program over the beamlet intensities $x$:

$$
F(B) = \min_{x \in \mathcal{X}(B)}\;
\frac{w_u}{|V_{\text{PTV}}|}\left\lVert \left(d_p - A_{B,\text{PTV}}\,x\right)_+ \right\rVert_2^2
+ \frac{w_o}{|V_{\text{PTV}}|}\left\lVert \left(A_{B,\text{PTV}}\,x - d_p\right)_+ \right\rVert_2^2
+ \sum_{s \in \mathcal{S}} \frac{w_s}{|V_s|}\left\lVert A_{B,s}\,x \right\rVert_2^2
+ w_{sm}\left(\frac{0.6}{n_c}\lVert Q_x x\rVert_2^2 + \frac{0.4}{n_r}\lVert Q_y x\rVert_2^2\right)
$$

MOSEK solves it, and the minimum value is the fitness.

## Symbols

| Symbol | Meaning |
|---|---|
| $x$ | Intensity of every beamlet in the plan; $x \ge 0$ |
| $A$ | Influence matrix: $A_{ij}$ is the dose to optimization voxel $i$ from unit intensity in beamlet $j$ |
| $A_{B,s}\,x$ | Dose to each optimization voxel of structure $s$ under beam set $B$ |
| $V_s$ | The structure's optimization voxels, so $\lvert V_s \rvert$ is their count |
| $d_p$ | Prescription dose **per fraction**: 60 Gy over 30 fractions gives 2 Gy |
| $(\cdot)_+$ | Elementwise $\max(0, \cdot)$ |
| $Q_x,\ Q_y$ | Difference operators between neighbouring beamlets along and across the MLC direction |
| $n_c,\ n_r$ | Total beamlet-map columns and rows summed over the beams in the plan |

PortPy writes the two PTV terms with slack variables rather than $\max$: it minimizes
$\lVert d_U \rVert^2$ subject to $A_{\text{PTV}}\,x \ge d_p - d_U$ with $d_U \ge 0$, and the
same for overdose with $d_O$. At the optimum these equal the expressions above.

## The terms and their weights

| Term | Structure | PortPy type | Weight |
|---|---|---|---:|
| Target underdose | PTV | `quadratic-underdose` | 100,000 |
| Target overdose | PTV | `quadratic-overdose` | 10,000 |
| Organ sparing | ESOPHAGUS, HEART | `quadratic` | 20 |
| Organ sparing | CORD, LUNG_L, LUNG_R, LUNGS_NOT_GTV | `quadratic` | 10 |
| Dose fall-off | RIND_0, RIND_1 | `quadratic` | 5 |
| Dose fall-off | RIND_2, RIND_3, RIND_4 | `quadratic` | 3 |
| Fluence smoothness | all beams | `smoothness-quadratic` | 100 |

- **The weights explain the results.** Target terms outweigh every organ term by a factor of
  500 or more, so the optimizer buys target dose accuracy first. That is why most of the
  GA's advantage over the clinician-selected angles comes from the two PTV terms.
- **Organ and ring terms penalize any dose**, because their target dose is zero. The rings are
  shells around the PTV (`RIND_0` is PTV+5 mm minus PTV, out to `RIND_4` beyond PTV+50 mm) and
  push dose to fall off with distance from the target.
- **A term is skipped when its structure is missing or has no optimization voxels.** Eight
  of the 37 patients (3, 7, 8, 17, 18, 33, 37 and 38) have no heart term for this reason.
- **The protocol file also lists a `linear-overdose` term on CORD (weight 100).** PortPy 1.1.4
  does not implement that type and silently skips it.
- **Objective values are weighted penalty points, not doses.** A percentage change in the
  objective has no direct clinical meaning; the clinical comparison is reported separately in Gy.

## Constraints

$\mathcal{X}(B)$ is not just $x \ge 0$. PortPy also adds hard constraints from the clinical
criteria and the optimization parameters:

- **Maximum dose**, per voxel, for PTV (69 Gy), ESOPHAGUS, HEART, LUNG_L, LUNG_R and
  LUNGS_NOT_GTV (66 Gy), SKIN (60 Gy) and CORD (50 Gy). GTV and CTV limits are not enforced.
  A voxel in several structures gets the tightest limit.
- **Ring maximum doses** as fractions of the prescription: RIND_0 1.10, RIND_1 1.05,
  RIND_2 0.90, RIND_3 0.85, RIND_4 0.75.
- **Mean dose** for ESOPHAGUS (34 Gy), HEART (27 Gy) and LUNGS_NOT_GTV (21 Gy). The limit is
  scaled by the fraction of the structure's volume that lies inside the dose-calculation box.

All limits are divided by the number of fractions. The dose-volume criteria in the protocol,
such as esophagus V60 at most 17%, are **not** optimization constraints. They are only
evaluated afterwards, which is how a re-solved plan can violate one.

## How the pipeline uses it

- **During the GA search** (`BAOProblem.evaluate()` in `ga_bao.py`), the influence matrix for
  the whole candidate pool is built and down-sampled once. A beam set is scored by pinning the
  beamlets of every beam outside the set to zero. $\lvert V_s \rvert$ therefore counts
  down-sampled voxels, and $n_c$ and $n_r$ are summed over the whole pool rather than over the
  7 selected beams. Search fitness values are consequently on a different scale from
  full-resolution objectives and are used only to rank beam sets.
- **For the reported comparison** (`scripts/clinical_compare.py`), the GA's winning beams and
  the clinician's beams are each rebuilt as a plan containing only those beams and re-solved at
  full resolution. Each term's solved value is recorded under `objective_terms`, and the script
  refuses to write a result unless the terms sum to the total objective.

For five patients the GA won at search resolution but lost at full resolution, which is why
only the full-resolution comparison is reported.
