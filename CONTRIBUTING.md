# Contributing

Keep `main` reviewable and the experiment artifacts reproducible.

1. Start from current `main` and create a short-lived branch.
2. Keep raw PortPy patient data and resumable caches out of Git.
3. Do not change `scripts/experiment_protocol.py` during a primary cohort batch. Use a
   new batch ID and report a separate experiment for any different seed or search budget.
4. Run the lightweight repository checks before committing:

   ```bash
   python3 -m compileall -q .
   python3 -m unittest discover -s tests -v
   ```

5. Open a pull request and have another team member review it before merging.
6. Delete merged branches only after confirming their commits are reachable from `main`.

Full PortPy/MOSEK runs require the Python 3.11 research environment and patient data; the
lightweight checks deliberately do not download data or run clinical optimization.
