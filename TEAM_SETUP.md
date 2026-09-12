# PortPy setup guide

This walks you from a **fresh machine** to a **working PortPy environment** where you can
run the example notebooks (starting with `examples/1_basic_tutorial.ipynb`) in VS Code,
with the MOSEK solver and a downloaded patient dataset.

It bakes in the **traps we already hit and solved**, so you don't lose a day to them:
- Modern Python (3.13/3.14) **breaks** the scientific stack → we pin **Python 3.11** in a conda env.
- PortPy's `master` branch **crashes on Python 3.11** → we pin the PortPy clone to tag **`v1.1.4`**.
- The HuggingFace data CDN **resets connections under load** on many networks → we download with a **single-connection retry** helper.
- The dataset is **multiple GB** → we keep it **outside the git repos** so nobody commits it.

> Times are approximate. Budget ~30–45 min, most of it downloads.

---

## 0. How the pieces fit together (read this first)

There are **two separate git repos**, kept side-by-side in one parent folder:

```
<some-folder>/                              <- e.g. C:\Users\<you>\Downloads
├── algoverse-portpy-beam-optimization/     <- this repo (this guide + the BAO code)
│   ├── scripts/
│   │   ├── download_patient_data.py
│   │   └── patch_portpy_downsampler.py
│   ├── ga_bao.py                            <- the genetic-algorithm BAO experiment
│   └── TEAM_SETUP.md                        <- this file
├── PortPy/                                  <- upstream PortPy, cloned SEPARATELY (branch: research-v1.1.4)
│   └── examples/                            <- the notebooks you run
└── data/                                    <- patient data, shared, sits NEXT TO both repos
    └── Lung_Patient_3/
```

- **This repo** (`algoverse-portpy-beam-optimization`) holds the algorithm code and docs.
- **PortPy** is the upstream library + example notebooks; we don't fork it, we just clone it.
- **`data/`** is a sibling of both, so both the notebooks (`../../data`) and the download
  script resolve to the same place — and neither repo tracks the gigabytes.

> 🔑 **Keep both repos in the SAME parent folder** (the `<some-folder>` above). The data
> paths depend on it.

A conda env named **`portpy`** (Python 3.11) ties it together, with a MOSEK license at
`~/mosek/mosek.lic`.

---

## 1. Prerequisites (install these first)

| Tool | Notes |
|---|---|
| **Git** | https://git-scm.com/downloads |
| **VS Code** | https://code.visualstudio.com/ — plus the **Python** and **Jupyter** extensions (see step 4) |
| **Conda** | **Miniforge** (recommended, lightweight): https://github.com/conda-forge/miniforge — or Anaconda if you already have it |

> ⚠️ **Do NOT use your system Python** (especially 3.13/3.14). NumPy/SciPy/CVXPy/MOSEK
> often have no prebuilt wheels for the newest Python and will fail to build on Windows.
> We use a conda env pinned to 3.11 to avoid this entirely.

---

## 2. Create the conda environment (Python 3.11)

Open a terminal that has conda (on Windows: **"Miniforge Prompt"** or **"Anaconda Prompt"**).

```bash
conda create -n portpy python=3.11 -y
conda activate portpy
```

Your prompt should now start with `(portpy)`. Everything below runs **inside this env**.

---

## 3. Install PortPy + solver + data tools

```bash
pip install "portpy[mosek,data]" jupyter ipykernel
pip install patchify            # needed for voxel down-sampling (the BAO benchmark)
pip install "numpy==2.4.6"      # re-pin: patchify tries to downgrade numpy, which breaks cvxpy
```

- `portpy[mosek,data]` = PortPy core (NumPy/SciPy/CVXPy/Matplotlib/pandas/h5py) **+ MOSEK + the HuggingFace downloader (`huggingface_hub`) + pydicom**.
- We deliberately **avoid `portpy[all]`** — it pulls the full PyTorch/deep-learning stack (~2+ GB) that the BAO work doesn't need. (Only add it if you plan to run the AI dose-prediction notebooks.)
- **`patchify`** is required to down-sample the influence matrix used by the GA; it isn't in `[mosek,data]`. ⚠️ Installing it downgrades numpy to <2, which breaks cvxpy — so we immediately re-pin `numpy==2.4.6` (patchify still works fine with numpy 2). pip may print a harmless dependency-conflict warning; ignore it.
- `jupyter ipykernel` = needed to run notebooks and register the kernel (step 4).

Sanity check:
```bash
python -c "import portpy.photon as pp; print('portpy', __import__('importlib.metadata',fromlist=['version']).version('portpy'))"
```
Should print `portpy 1.1.4`.

---

## 4. VS Code extensions + Jupyter kernel

**Extensions** (once): in VS Code, install **Python** (`ms-python.python`) and **Jupyter** (`ms-toolsai.jupyter`). Or from a terminal:
```bash
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
```

**Register the env as a named kernel** so it's easy to pick in VS Code:
```bash
python -m ipykernel install --user --name portpy --display-name "Python 3.11 (portpy)"
```

---

## 5. Get the code (two repos, side by side)

Pick a parent folder (this guide uses `Downloads`) and put **both** repos in it.

**a) This repo** — you've probably already cloned it (you're reading this from it).
If not:
```bash
cd ~/Downloads
git clone https://github.com/algoverse-agatha-rmcj/algoverse-portpy-beam-optimization.git
```

**b) PortPy (the library) — clone upstream as a sibling, and pin it to `v1.1.4`:**
```bash
cd ~/Downloads          # same parent folder as this repo
git clone https://github.com/PortPy-Project/PortPy.git
cd PortPy
git checkout -b research-v1.1.4 v1.1.4
```

> **Why pin PortPy to `v1.1.4` and not `master`?**
> The `master` branch contains Python-3.12-only syntax (nested-quote f-strings in
> `portpy/photon/vmat_scp/vmat_scp_optimization.py`) that raises a `SyntaxError` on
> Python 3.11 — the notebooks won't even import. The `v1.1.4` **tag** is clean on 3.11
> and matches the pip package, giving us a stable, reproducible base.

---

## 5b. Apply the PortPy down-sampler patch (required for BAO)

PortPy v1.1.4's down-sampler crashes on the current dataset format
(`TypeError: only 0-dimensional arrays can be converted to Python scalars`).
Down-sampling is required for the current genetic-algorithm search, so apply our
one-line patch to the installed package. It's
idempotent and makes a `.orig_backup`:

```bash
python scripts/patch_portpy_downsampler.py
```

Expect `patched successfully` (or `Already patched`). **Re-run it after any
`pip install`/reinstall of PortPy**, since that restores the unpatched file.

---

## 6. MOSEK license (free for academics)

1. Request a **free academic license** with your **.edu email**:
   https://www.mosek.com/products/academic-licenses/
2. You'll get a file named **`mosek.lic`** by email.
3. Put it where MOSEK looks by default:
   - **Windows:** `C:\Users\<you>\mosek\mosek.lic`
   - **macOS/Linux:** `~/mosek/mosek.lic`
   (Create the `mosek` folder if it doesn't exist. No environment variables needed.)
4. **Verify** it activates:
   ```bash
   python -c "import cvxpy as cp; x=cp.Variable(2,nonneg=True); p=cp.Problem(cp.Minimize(cp.sum_squares(x-1)),[cp.sum(x)<=1]); p.solve(solver=cp.MOSEK); print('MOSEK OK, status:', p.status)"
   ```
   Should print `MOSEK OK, status: optimal`.

---

## 7. Download patient data from HuggingFace

Use the helper script in **this repo**. Run it from the project repo's root, with the
`portpy` env active:

```bash
cd ~/Downloads/algoverse-portpy-beam-optimization
python scripts/download_patient_data.py Lung_Patient_3
```

This downloads into **`<parent>/data/Lung_Patient_3`** — the shared `data/` folder next to
both repos, which is exactly where the notebooks look (`data_dir='../../data'`), and which
keeps the multi-GB data **out of git**.

- Multiple patients: `python scripts/download_patient_data.py Lung_Patient_3 Lung_Patient_4`
- **For beam-angle search**, add `--beam-mode ga`. This downloads the no-180 candidate
  grid plus any off-grid clinician beams, without storing unused beam angles.

> **Why not just call `pp.download_portpy_data(...)` directly?**
> The data is served from the `xethub.hf.co` CDN, which on many campus/AV networks resets
> connections under the default 8 parallel workers (`WinError 10054` /
> `RemoteProtocolError`) and then hangs forever. The script forces a **single connection
> + resume-on-failure retry**, which gets through. If you still see resets, see
> Troubleshooting.

---

## 8. Verify: run the basic tutorial in VS Code

1. Open the **PortPy** repo: `cd ~/Downloads/PortPy && code .`, then open
   `examples/1_basic_tutorial.ipynb`.
2. Top-right **Select Kernel → Jupyter Kernel → "Python 3.11 (portpy)"**.
3. **Run All** (or Shift+Enter top-to-bottom).
   - **Cell 9 takes ~30–40 s** — that's MOSEK solving. Normal.
   - Expected result around cell 9: `Optimal value: ~53.2`.
4. **Two cells are expected to misbehave — this is normal:**
   - **Cell 15 (3D Slicer)** fails unless you've installed 3D Slicer separately. It's optional visualization; skip it.
   - **Cell 14** writes ~2 GB pickle files to `C:\temp\<patient>`. Skip it unless you need them, and clean up periodically.

If cells 3–13 run and you get a DVH plot and a clinical-criteria table, **you're done — your setup can run the full PortPy IMRT pipeline.**

---

## 9. Running the beam-angle-optimization GA

`ga_bao.py` runs the genetic algorithm. Download its no-180 candidate beam pool first:

```bash
# from the project repo root, portpy env active, AFTER steps 3 (patchify) + 5b (patch)
python scripts/download_patient_data.py Lung_Patient_3 --beam-mode ga
python ga_bao.py --patient Lung_Patient_3 --k 7 --pop 20 --gens 40
```

Results (best angles, per-generation history, timing) are written under the patient's
folder in `results/`, for example
`results/Lung_Patient_3/ga_runs/Lung_Patient_3_ga_downsampled_seed_0.json`.
Useful flags: `--pool` (candidate angles), `--k` (beam budget),
`--pop` / `--gens` (search size = compute budget), `--mutation-rate`, `--seed`.

**Where to modify the code** (`ga_bao.py`):
- **the fitness** → `BAOProblem.evaluate()` (e.g. swap `prob.value` for a clinical score)
- **the GA operators** → Section 2 (`tournament`, `crossover`, `mutate`)
- **the loop / elitism / termination** → `run_ga()` in Section 3

> First run is slow: the one-time down-sample (~minutes) happens before the GA
> starts. Each fitness evaluation after that is a ~10 s MOSEK solve.

---

## Troubleshooting

**`SyntaxError: f-string: unmatched '['` on import** → Your PortPy clone is on `master` with
Python 3.11. Check out the pinned tag: `git checkout -b research-v1.1.4 v1.1.4`.

**`AttributeError: 'DataExplorer' object has no attribute 'patient_id'`** → You ran a cell
out of order. `data.patient_id = '...'` (an earlier cell) must run before `pp.CT(data)`.
Use **Run All** or "Run All Above". (Jupyter keeps kernel state; order matters.)

**Download stalls / `WinError 10054` / `RemoteProtocolError`** → Network is resetting the
HuggingFace CDN. Options, in order:
1. Make sure you're using `scripts/download_patient_data.py` (single-connection retry).
2. **Temporarily pause antivirus HTTPS/web scanning** during the download.
3. Try a **different network** (e.g. phone hotspot) — campus/VPN networks are common culprits.
4. Re-run the script; it **resumes** from what already downloaded.

**`FileNotFoundError: ...\<patient>\StructureSet_MetaData.json`** → Data isn't where the
notebooks expect. Confirm the patient folder is at `<parent>/data/<patient>` — a sibling of
**both** repos. If you downloaded manually, note that `download_portpy_data(out=X)` creates
`X/data/<patient>`, so pass `out=<parent>`.

**MOSEK errors** → Confirm `mosek.lic` is at `~/mosek/mosek.lic` and not expired. Re-run
the verify command in step 6. Free academic licenses are time-limited; renew when needed.

**`TypeError: only 0-dimensional arrays can be converted to Python scalars`** (during
down-sampling) → PortPy's down-sampler bug on the current data format. Apply the patch:
`python scripts/patch_portpy_downsampler.py` (step 5b).

**`ModuleNotFoundError: No module named 'patchify'`** → `pip install patchify`, then
re-pin `pip install "numpy==2.4.6"`.

**`No module named 'numpy.lib.array_utils'` / cvxpy fails to import** → numpy got
downgraded to <2 (usually by installing patchify). Fix: `pip install "numpy==2.4.6"`.

**`conda` not found** → Open the "Miniforge Prompt"/"Anaconda Prompt", or add conda to PATH.

---

## Quick reference (the whole thing, condensed)

```bash
# 1. env
conda create -n portpy python=3.11 -y
conda activate portpy

# 2. install
pip install "portpy[mosek,data]" jupyter ipykernel patchify
pip install "numpy==2.4.6"      # undo patchify's numpy downgrade
python -m ipykernel install --user --name portpy --display-name "Python 3.11 (portpy)"

# 3. code: both repos in the same parent folder
cd ~/Downloads
git clone https://github.com/algoverse-agatha-rmcj/algoverse-portpy-beam-optimization.git   # this repo
git clone https://github.com/PortPy-Project/PortPy.git                        # the library
cd PortPy && git checkout -b research-v1.1.4 v1.1.4 && cd ..

# 4. patch PortPy's down-sampler + MOSEK license
cd algoverse-portpy-beam-optimization
python scripts/patch_portpy_downsampler.py
# MOSEK license -> ~/mosek/mosek.lic  (request at mosek.com, .edu email)

# 5. data (single-connection, resumable). Downloads only the no-180 GA pool.
python scripts/download_patient_data.py Lung_Patient_3 --beam-mode ga

# 6. run the GA
python ga_bao.py --patient Lung_Patient_3 --k 7 --pop 20 --gens 40

# (to learn PortPy first: open PortPy in VS Code, pick the "Python 3.11 (portpy)" kernel,
#  Run All on examples/1_basic_tutorial.ipynb  -> cell 9 ~= Optimal value 53.2)
```
