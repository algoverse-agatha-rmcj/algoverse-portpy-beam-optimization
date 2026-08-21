# Algoverse: Beam-Angle Optimization on PortPy

Algoverse AI Research Fellowship project. We're extending prior linear-programming-based
radiotherapy beam-angle optimization by testing a genetic algorithm on open-source
[PortPy](https://github.com/PortPy-Project/PortPy) lung-cancer benchmark cases.

## Results

Experiment outputs are organized by patient under [`results/`](results/). Each completed
patient bundle keeps the GA result JSON, clinician comparison metrics, and its
dose-volume histogram (DVH) together. Complete seed-0 bundles are committed for
[`Lung_Patient_2` through `Lung_Patient_6`](results/).

## Project status

The current implementation and research backlog are tracked in
[`docs/project_status.md`](docs/project_status.md). Simulated annealing and other heuristic
extensions are deferred until the GA implementation, repeat-seed study, and compute
comparison are complete.

## Contributing

Use a branch and pull request for every change; do not commit raw PortPy patient data or
derived caches. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the lightweight checks.
