# ga_bao.py — Setup & How to Run

Two parts: **Part 1** is the one-time setup (do it once per machine); **Part 2** is how to
run the genetic-algorithm experiment afterward. Companion to `ga_bao_walkthrough.md`.

---

# Part 1 — One-time setup (per machine)

## 1. Install the prerequisites
- **Git** — https://git-scm.com/downloads
- **VS Code** — https://code.visualstudio.com/ , plus its **Python** and **Jupyter** extensions.
- **Conda** — Miniforge (lightweight, recommended: https://github.com/conda-forge/miniforge) or Anaconda.

> ⚠️ **Do NOT use the system Python** (especially 3.13/3.14) — the scientific libraries often
> won't build on it. We pin Python 3.11 in a conda environment to avoid that.

## 2. Create the conda environment (Python 3.11)
```bash
conda create -n portpy python=3.11 -y
conda activate portpy
```
Your prompt should now start with `(portpy)`. Everything below runs inside this env.

## 3. Install PortPy + solver + data + down-sampling tools
```bash
pip install "portpy[mosek,data]" jupyter ipykernel patchify
pip install "numpy==2.4.6"
```
- `portpy[mosek,data]` = PortPy core + MOSEK + the HuggingFace downloader + pydicom. (We avoid `portpy[all]`, which pulls a ~2 GB PyTorch stack we don't need.)
- `patchify` is required for voxel down-sampling. Installing it downgrades numpy, which breaks cvxpy — so we immediately re-pin `numpy==2.4.6`. A pip dependency-conflict warning here is harmless.

## 4. MOSEK license (free for academics)
1. Request a free academic license with your `.edu` email: https://www.mosek.com/products/academic-licenses/
2. You'll receive a file named `mosek.lic`.
3. Put it at `C:\Users\<you>\mosek\mosek.lic` (Windows) or `~/mosek/mosek.lic` (Mac/Linux). Create the `mosek` folder if needed.
4. Verify:
   ```bash
   python -c "import cvxpy as cp; x=cp.Variable(2,nonneg=True); p=cp.Problem(cp.Minimize(cp.sum_squares(x-1)),[cp.sum(x)<=1]); p.solve(solver=cp.MOSEK); print('MOSEK OK', p.status)"
   ```
   Should print `MOSEK OK optimal`.

## 5. Get the code (two repos, side by side)
Put both repos in the SAME parent folder (example uses Downloads):
```bash
cd C:\Users\jpwun\Downloads
git clone https://github.com/algoverse-agatha-rmcj/algoverse-portpy-beam-optimization.git
git clone https://github.com/PortPy-Project/PortPy.git
cd PortPy
git checkout -b research-v1.1.4 v1.1.4
```
PortPy is pinned to tag **v1.1.4** because its `master` branch has Python-3.12-only syntax that crashes on 3.11.

## 6. Apply the PortPy down-sampler patch (required)
PortPy v1.1.4's down-sampler crashes on the current data format. Apply the one-line patch (idempotent, makes a backup):
```bash
cd C:\Users\jpwun\Downloads\algoverse-portpy-beam-optimization
python scripts/patch_portpy_downsampler.py
```
Re-run this after any `pip install`/reinstall of PortPy.

## 7. Download the patient data (GA candidate pool)
Download with `--beam-mode ga`. This fetches the no-180 candidate grid plus any
off-grid clinician beams and keeps the large data outside the repo:
```bash
python scripts/download_patient_data.py Lung_Patient_3 --beam-mode ga
```
Data lands in `C:\Users\jpwun\Downloads\data\Lung_Patient_3` — a sibling of the repo, which is where the code expects it.

---

# Part 2 — Running the experiment

## Step 1 — open a terminal
Easiest is inside VS Code: **Terminal → New Terminal**. Any PowerShell / Anaconda Prompt window also works.

## Step 2 — move into the repo folder
The script and its default data path only work if you run from the repo folder:
```powershell
cd "C:\Users\jpwun\Downloads\algoverse-portpy-beam-optimization"
```
Confirm with `dir ga_bao.py` — it should list the file, and the prompt should end with `...\algoverse-portpy-beam-optimization>`.

> **Common error:** `can't open file 'C:\Users\jpwun\ga_bao.py': No such file or directory`
> means the terminal was still in your home folder. Run the `cd` line above and try again.

## Step 3 — run the genetic algorithm
Full real run (population 20, 40 generations, 24-angle pool, pick 7 beams):
```powershell
C:\Users\jpwun\anaconda3\envs\portpy\python.exe ga_bao.py --patient Lung_Patient_3 --k 7 --pop 20 --gens 40
```
Using the full path to `python.exe` guarantees the correct environment, so you don't need `conda activate` first.

Quick 2-minute sanity check (smaller config) before the long run:
```powershell
C:\Users\jpwun\anaconda3\envs\portpy\python.exe ga_bao.py --patient Lung_Patient_3 --k 5 --pop 6 --gens 3
```

## What you will see
- First ~2 minutes: `[setup] down-sampling 24-beam pool...` — the one-time down-sample; no per-generation output yet.
- Then one line per generation, live: `gen 0 | gen-best 94.30 | overall-best 94.30 | angles [...] | solves 20`
- The fitness (lower = better) should trend downward across generations.
- When finished: a `=== RESULT ===` summary, and results saved under
  `results/<patient>/ga_runs/` (for example,
  `results/Lung_Patient_3/ga_runs/Lung_Patient_3_ga_downsampled_seed_0.json`).

## Stopping, resuming, sleeping
- Press **Ctrl+C** to stop anytime.
- Re-running the same command **resumes**: it reloads a protocol-fingerprinted
  `.cache.json` from the patient's `cache/` folder and continues, wasting no compute.
  A cache from another patient, configuration, dataset revision, or code version is
  rejected rather than silently reused. Legacy caches without an identity are not reused.
- If the laptop sleeps mid-run, it picks back up on wake.

## The knobs you change in the command
- `--pop` and `--gens` — how hard it searches (and how long it runs). The primary cohort
  is frozen at 20 × 40. A 6 × 3 run is only a software sanity check; 30 × 60 belongs in a
  separately reported experiment and must not be pooled with the primary cohort.
- `--pool` — the candidate beam IDs. By default, the code reads each patient's real
  gantry-angle metadata, selects the 15-degree grid, excludes every beam at 180 degrees,
  and adds missing non-180 clinician beams. Beam IDs do not encode angles.
- `--k` — how many beams to select (7 matches the PortPy benchmark).
- `--seed` — random seed. Seed 0 is the primary cohort. Additional seeds form a separate
  robustness study; summarize all predeclared seeds rather than selecting their best result.
- `--no-downsample` — use full-resolution matrices (slower per solve; for comparing against the expert plan, not the MILP).
- `--out` — optional results filename; by default it is organized under
  `results/<patient>/ga_runs/` and includes the resolution and seed.
