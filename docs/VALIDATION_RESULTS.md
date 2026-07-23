# Validation Results — functional benchmark (synthetic cohort)

> **Synthetic cohort — methodology / functional validation, NOT clinical evidence.** These numbers show the scores discriminate outcomes on a reproducible synthetic cohort whose mortality is driven by multi-organ organ-failure burden (independent of any score's output). Genuine clinical validation requires a real labeled ICU cohort; the same runner (`backend/validate_scores.py`) accepts one via `MIMIC_COHORT_CSV` — see `docs/MIMIC_VALIDATION.md`.

- Cohort: synthetic (services/synthetic_cohort.py) · n = 3000 · seed = 42
- Outcome: in-hospital mortality · events = 631 (21.0 %)
- Engine version: 1.0.0 · generated 2026-07-23T12:24:44.136374+00:00


## Discrimination (AUROC, risk-oriented)

| Score | n | AUROC |
|---|---:|---:|
| SOFA | 3000 | 0.810 |
| APACHE II | 3000 | 0.797 |
| SAPS II | 3000 | 0.783 |
| NEWS2 | 3000 | 0.749 |
| CURB-65 | 3000 | 0.716 |
| ROX Index | 3000 | 0.716 |
| qSOFA | 3000 | 0.708 |
| PaO2/FiO2 Ratio | 3000 | 0.700 |
| SIRS | 3000 | 0.696 |
| Shock Index | 3000 | 0.683 |
| KDIGO AKI Stage | 3000 | 0.664 |

## SAPS II calibration (predicted mortality probability)

- AUROC 0.783 · Brier 0.1408 · n 3000 · events 631

| Predicted bin | n | mean predicted | observed rate |
|---|---:|---:|---:|
| 0.0-0.1 | 1964 | 0.045 | 0.096 |
| 0.1-0.2 | 556 | 0.146 | 0.308 |
| 0.2-0.3 | 164 | 0.242 | 0.408 |
| 0.3-0.4 | 123 | 0.344 | 0.496 |
| 0.4-0.5 | 64 | 0.450 | 0.578 |
| 0.5-0.6 | 58 | 0.544 | 0.810 |
| 0.6-0.7 | 21 | 0.653 | 0.952 |
| 0.7-0.8 | 30 | 0.751 | 0.733 |
| 0.8-0.9 | 10 | 0.846 | 0.800 |
| 0.9-1.0 | 10 | 0.947 | 1.000 |

## Fairness / subgroup analysis

AUROC (and event rate) for the headline mortality scores by subgroup. Differential discrimination — an AUROC spread of more than ~0.05 across subgroups — can indicate inequitable performance and warrants investigation before deployment.


### By sex

| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |
|---|---:|---:|---:|---:|---:|---:|
| F | 1389 | 20.3% | 0.789 | 0.777 | 0.769 | 0.729 |
| M | 1611 | 21.7% | 0.828 | 0.812 | 0.795 | 0.766 |

### By age group

| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |
|---|---:|---:|---:|---:|---:|---:|
| 50-64 | 1014 | 20.3% | 0.803 | 0.782 | 0.771 | 0.736 |
| 65-79 | 920 | 24.3% | 0.815 | 0.792 | 0.787 | 0.755 |
| 80+ | 414 | 27.5% | 0.821 | 0.772 | 0.778 | 0.768 |
| <50 | 652 | 13.3% | 0.821 | 0.806 | 0.751 | 0.759 |

### By ethnicity

| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |
|---|---:|---:|---:|---:|---:|---:|
| Asian | 130 | 19.2% | 0.867 | 0.789 | 0.853 | 0.820 |
| Black | 432 | 23.2% | 0.799 | 0.766 | 0.770 | 0.728 |
| Hispanic | 310 | 16.8% | 0.750 | 0.773 | 0.764 | 0.687 |
| Other | 310 | 20.6% | 0.798 | 0.780 | 0.783 | 0.742 |
| White | 1818 | 21.4% | 0.819 | 0.811 | 0.784 | 0.760 |

## Interpretation

Multi-organ severity scores (SOFA, APACHE II, SAPS II) and the NEWS2 early-warning score discriminate best; single-axis scores (Shock Index, KDIGO) discriminate least — the clinically expected ordering, since this cohort's mortality is driven by multi-organ burden. This confirms the engine computes and orders risk correctly end-to-end.

Note the SAPS II calibration table: it discriminates well but **under-predicts** observed mortality on this cohort — exactly the kind of finding real validation surfaces, and why published coefficients generally need **local recalibration**. Absolute values are properties of the synthetic DGP, not any real population; re-run on real ICU data (`MIMIC_COHORT_CSV`) for clinical evidence.

