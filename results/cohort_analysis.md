# Cohort analysis

Generated from the committed full-resolution GA-vs-clinician comparisons. All aggregate values are arithmetic means.

## Headline

- 18 usable lung patients; GA wins 12, loses 6, and ties 0.
- Mean objective improvement: 9.34% (positive favors GA).
- Sensitivity disclosure: the arithmetic mean is 4.31% when the two largest gains are excluded.
- Mean PTV D95: expert 59.48 Gy; GA 59.65 Gy.
- Protocol-limit violations: expert 2; GA 1.

## Per-patient objective and target coverage

| Patient | Expert objective | GA objective | Improvement | Outcome | Expert PTV D95 | GA PTV D95 | D95 delta |
|---|---:|---:|---:|:---:|---:|---:|---:|
| P2 | 87.552 | 85.190 | +2.70% | win | 59.48 Gy | 59.46 Gy | -0.02 Gy |
| P3 | 53.224 | 52.503 | +1.35% | win | 59.74 Gy | 59.75 Gy | +0.01 Gy |
| P4 | 89.899 | 87.654 | +2.50% | win | 59.65 Gy | 59.67 Gy | +0.02 Gy |
| P5 | 79.982 | 74.775 | +6.51% | win | 59.52 Gy | 59.59 Gy | +0.07 Gy |
| P6 | 44.283 | 44.349 | -0.15% | loss | 59.76 Gy | 59.74 Gy | -0.02 Gy |
| P7 | 66.923 | 67.809 | -1.32% | loss | 59.74 Gy | 59.74 Gy | +0.00 Gy |
| P8 | 120.121 | 107.626 | +10.40% | win | 59.48 Gy | 59.57 Gy | +0.10 Gy |
| P9 | 84.768 | 85.930 | -1.37% | loss | 59.73 Gy | 59.70 Gy | -0.02 Gy |
| P10 | 68.811 | 69.845 | -1.50% | loss | 59.69 Gy | 59.68 Gy | -0.01 Gy |
| P11 | 58.631 | 52.075 | +11.18% | win | 59.72 Gy | 59.76 Gy | +0.04 Gy |
| P14 | 188.465 | 64.407 | +65.83% | win | 58.48 Gy | 59.71 Gy | +1.24 Gy |
| P15 | 64.355 | 64.594 | -0.37% | loss | 59.74 Gy | 59.74 Gy | -0.00 Gy |
| P16 | 59.578 | 53.126 | +10.83% | win | 59.70 Gy | 59.73 Gy | +0.03 Gy |
| P17 | 413.092 | 275.572 | +33.29% | win | 57.90 Gy | 59.36 Gy | +1.46 Gy |
| P18 | 47.895 | 42.221 | +11.85% | win | 59.72 Gy | 59.79 Gy | +0.06 Gy |
| P19 | 107.474 | 95.386 | +11.25% | win | 59.55 Gy | 59.66 Gy | +0.10 Gy |
| P20 | 93.356 | 84.601 | +9.38% | win | 59.63 Gy | 59.69 Gy | +0.06 Gy |
| P21 | 172.434 | 179.835 | -4.29% | loss | 59.50 Gy | 59.43 Gy | -0.08 Gy |

## Mean clinical-criteria values

The delta is GA minus expert. Positive means the GA plan delivered a higher dose or volume for that metric; clinical desirability depends on whether the row is a target or an organ at risk.

| Criterion | n | Expert mean | GA mean | Mean delta | Missing |
|---|---:|---:|---:|---:|:---|
| GTV max | 18 | 63.72 Gy | 62.94 Gy | -0.77 Gy | - |
| PTV max | 18 | 65.33 Gy | 64.51 Gy | -0.82 Gy | - |
| ESOPHAGUS max | 18 | 45.84 Gy | 45.27 Gy | -0.58 Gy | - |
| ESOPHAGUS mean | 18 | 9.82 Gy | 9.37 Gy | -0.46 Gy | - |
| ESOPHAGUS V60Gy | 18 | 4.98 % | 4.62 % | -0.36 % | - |
| HEART max | 17 | 34.50 Gy | 32.95 Gy | -1.55 Gy | P8 |
| HEART mean | 17 | 5.14 Gy | 4.60 Gy | -0.54 Gy | P8 |
| HEART V30Gy | 17 | 3.94 % | 3.12 % | -0.83 % | P8 |
| LUNG_L max | 18 | 34.82 Gy | 43.31 Gy | +8.49 Gy | - |
| LUNG_R max | 18 | 59.01 Gy | 59.47 Gy | +0.46 Gy | - |
| CORD max | 18 | 31.51 Gy | 31.46 Gy | -0.05 Gy | - |
| SKIN max | 18 | 48.72 Gy | 47.81 Gy | -0.91 Gy | - |
| LUNGS_NOT_GTV max | 18 | 64.82 Gy | 64.21 Gy | -0.61 Gy | - |
| LUNGS_NOT_GTV mean | 18 | 8.49 Gy | 8.75 Gy | +0.26 Gy | - |
| LUNGS_NOT_GTV V20Gy | 18 | 15.72 % | 15.94 % | +0.22 % | - |

## Compute timing

- Mean full-run GA wall time across 17 patients: 1.50 hours.
- P11 was resumed from a checkpoint; its wall time covers only the resumed process segment and is excluded from the full-run mean.
- Pooled arithmetic mean across 4937 measured solves from 7 patients: 7.085 seconds per solve.
- Tail disclosure: largest reported p95 14.437 seconds; largest observed solve 18.439 seconds.

## Review priorities

- GA losses: P6, P7, P9, P10, P15, P21.
- Largest absolute objective changes: P14 (+65.83%, expert/GA PTV D95 58.48/59.71 Gy), P17 (+33.29%, expert/GA PTV D95 57.90/59.36 Gy), P18 (+11.85%, expert/GA PTV D95 59.72/59.79 Gy).
- GTV target-versus-organ interpretation remains a clinical methodology decision; this report presents its raw mean delta without declaring a winner.

## Focused loss and outlier analysis

The 6 losses and the two largest gains are shown together. Clinical deltas are GA minus expert; units are Gy except V20, which is in percentage points.

| Patient | Reason | Objective | D95 | GTV max | PTV max | Eso mean | Heart mean | Left lung max | Lungs-not-GTV mean | V20 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P6 | GA loss | -0.15% | -0.02 | -0.03 | -0.30 | -1.10 | -0.16 | +14.91 | +0.01 | -0.50 |
| P7 | GA loss | -1.32% | +0.00 | -0.33 | -0.75 | +0.12 | +0.00 | +6.77 | +0.14 | -0.14 |
| P9 | GA loss | -1.37% | -0.02 | -0.04 | +0.02 | +0.02 | -0.01 | +0.61 | +0.08 | +1.19 |
| P10 | GA loss | -1.50% | -0.01 | +0.20 | -0.15 | -0.11 | -0.35 | +24.65 | +0.61 | -0.57 |
| P15 | GA loss | -0.37% | -0.00 | +0.63 | -0.03 | -0.08 | +0.34 | -0.37 | -0.10 | +0.03 |
| P21 | GA loss | -4.29% | -0.08 | +0.64 | -0.08 | +0.30 | -0.58 | -0.36 | +0.16 | +4.50 |
| P14 | largest GA gain | +65.83% | +1.24 | -4.37 | -2.70 | -3.53 | -5.14 | -1.64 | +0.20 | -0.28 |
| P17 | largest GA gain | +33.29% | +1.46 | -4.21 | -2.95 | +0.24 | +0.00 | +5.82 | +0.83 | +1.22 |

Across the 6 loss cases, mean objective improvement is -1.50%. Their largest absolute PTV D95 change is 0.08 Gy. P14 and P17 instead recover 1.24 Gy and 1.46 Gy of PTV D95, respectively; those coverage changes coincide with the two largest objective gains, but objective-term exports are needed before attributing causality.
