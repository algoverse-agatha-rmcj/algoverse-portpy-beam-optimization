# Algoverse: Beam-Angle Optimization on PortPy

Algoverse AI Research Fellowship project. We're extending prior linear-programming-based
radiotherapy beam-angle optimization by testing alternative optimization techniques
(genetic algorithm, simulated annealing, memetic algorithm) on the open-source
[PortPy](https://github.com/PortPy-Project/PortPy) prostate-cancer benchmark dataset.

## Results

Experiment outputs are organized by patient under [`results/`](results/). Each completed
patient bundle keeps the GA result JSON, clinician comparison metrics, and its
dose-volume histogram (DVH) together. The current complete bundle is
[`Lung_Patient_2`](results/Lung_Patient_2/).

