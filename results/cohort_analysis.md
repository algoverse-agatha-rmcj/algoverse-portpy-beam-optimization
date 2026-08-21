# Cohort analysis

Generated from the committed full-resolution GA-vs-clinician comparisons. All aggregate values are arithmetic means.

## Headline

- 17 usable lung patients; GA wins 12, loses 5, and ties 0.
- Mean objective improvement: 10.14% (positive favors GA).
- Sensitivity disclosure: the arithmetic mean is 4.88% when the two largest gains are excluded.
- Mean PTV D95: expert 59.48 Gy; GA 59.67 Gy.
- Protocol-limit violations: expert 1; GA 0.

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

## Mean clinical-criteria values

The delta is GA minus expert. Positive means the GA plan delivered a higher dose or volume for that metric; clinical desirability depends on whether the row is a target or an organ at risk.

| Criterion | n | Expert mean | GA mean | Mean delta | Missing |
|---|---:|---:|---:|---:|:---|
| GTV max | 17 | 63.67 Gy | 62.82 Gy | -0.86 Gy | - |
| PTV max | 17 | 65.32 Gy | 64.45 Gy | -0.86 Gy | - |
| ESOPHAGUS max | 17 | 44.86 Gy | 44.21 Gy | -0.65 Gy | - |
| ESOPHAGUS mean | 17 | 8.95 Gy | 8.45 Gy | -0.50 Gy | - |
| ESOPHAGUS V60Gy | 17 | 4.07 % | 3.57 % | -0.50 % | - |
| HEART max | 16 | 32.70 Gy | 31.12 Gy | -1.58 Gy | P8 |
| HEART mean | 16 | 5.18 Gy | 4.64 Gy | -0.54 Gy | P8 |
| HEART V30Gy | 16 | 3.98 % | 3.09 % | -0.89 % | P8 |
| LUNG_L max | 17 | 33.16 Gy | 42.17 Gy | +9.01 Gy | - |
| LUNG_R max | 17 | 58.65 Gy | 59.12 Gy | +0.47 Gy | - |
| CORD max | 17 | 30.43 Gy | 30.37 Gy | -0.06 Gy | - |
| SKIN max | 17 | 48.65 Gy | 47.86 Gy | -0.78 Gy | - |
| LUNGS_NOT_GTV max | 17 | 64.80 Gy | 64.13 Gy | -0.67 Gy | - |
| LUNGS_NOT_GTV mean | 17 | 8.27 Gy | 8.54 Gy | +0.27 Gy | - |
| LUNGS_NOT_GTV V20Gy | 17 | 15.24 % | 15.20 % | -0.03 % | - |

## Compute timing

- Mean full-run GA wall time across 16 patients: 1.42 hours.
- P11 was resumed from a checkpoint; its wall time covers only the resumed process segment and is excluded from the full-run mean.
- Pooled arithmetic mean across 4224 measured solves from 6 patients: 6.120 seconds per solve.
- Tail disclosure: largest reported p95 12.517 seconds; largest observed solve 17.032 seconds.

## Review priorities

- GA losses: P6, P7, P9, P10, P15.
- Largest absolute objective changes: P14 (+65.83%, expert/GA PTV D95 58.48/59.71 Gy), P17 (+33.29%, expert/GA PTV D95 57.90/59.36 Gy), P18 (+11.85%, expert/GA PTV D95 59.72/59.79 Gy).
- GTV target-versus-organ interpretation remains a clinical methodology decision; this report presents its raw mean delta without declaring a winner.

## Focused loss and outlier analysis

The five losses are small and the two largest gains are shown alongside them. Clinical deltas are GA minus expert; units are Gy except V20, which is in percentage points.

| Patient | Reason | Objective | D95 | GTV max | PTV max | Eso mean | Heart mean | Left lung max | Lungs-not-GTV mean | V20 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P6 | GA loss | -0.15% | -0.02 | -0.03 | -0.30 | -1.10 | -0.16 | +14.91 | +0.01 | -0.50 |
| P7 | GA loss | -1.32% | +0.00 | -0.33 | -0.75 | +0.12 | +0.00 | +6.77 | +0.14 | -0.14 |
| P9 | GA loss | -1.37% | -0.02 | -0.04 | +0.02 | +0.02 | -0.01 | +0.61 | +0.08 | +1.19 |
| P10 | GA loss | -1.50% | -0.01 | +0.20 | -0.15 | -0.11 | -0.35 | +24.65 | +0.61 | -0.57 |
| P15 | GA loss | -0.37% | -0.00 | +0.63 | -0.03 | -0.08 | +0.34 | -0.37 | -0.10 | +0.03 |
| P14 | largest GA gain | +65.83% | +1.24 | -4.37 | -2.70 | -3.53 | -5.14 | -1.64 | +0.20 | -0.28 |
| P17 | largest GA gain | +33.29% | +1.46 | -4.21 | -2.95 | +0.24 | +0.00 | +5.82 | +0.83 | +1.22 |

Across the five loss cases, mean objective improvement is -0.94% (that is, a small mean disadvantage). Their PTV D95 changes stay within 0.03 Gy of the expert plans. P14 and P17 instead recover 1.24 Gy and 1.46 Gy of PTV D95, respectively; those coverage changes coincide with the two largest objective gains, but objective-term exports are needed before attributing causality.
