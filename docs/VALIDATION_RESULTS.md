# Validation Results — functional benchmark (synthetic cohort)

> **Synthetic cohort — methodology / functional validation, NOT clinical evidence.** These numbers show the scores discriminate outcomes on a reproducible synthetic cohort whose mortality is driven by multi-organ organ-failure burden (independent of any score's output). Genuine clinical validation requires a real labeled ICU cohort; the same runner (`backend/validate_scores.py`) accepts one via `MIMIC_COHORT_CSV` — see `docs/MIMIC_VALIDATION.md`.

- Cohort: synthetic (services/synthetic_cohort.py) · n = 3000 · seed = 42
- Outcome: in-hospital mortality · events = 614 (20.5 %)
- Engine version: 1.0.0 · generated 2026-07-23T12:12:08.726357+00:00


## Discrimination (AUROC, risk-oriented)

| Score | n | AUROC |
|---|---:|---:|
| SOFA | 3000 | 0.813 |
| APACHE II | 3000 | 0.784 |
| SAPS II | 3000 | 0.776 |
| NEWS2 | 3000 | 0.765 |
| ROX Index | 3000 | 0.743 |
| PaO2/FiO2 Ratio | 3000 | 0.722 |
| qSOFA | 3000 | 0.715 |
| CURB-65 | 3000 | 0.712 |
| SIRS | 3000 | 0.700 |
| Shock Index | 3000 | 0.674 |
| KDIGO AKI Stage | 3000 | 0.666 |

## SAPS II calibration (predicted mortality probability)

- AUROC 0.776 · Brier 0.1386 · n 3000 · events 614

| Predicted bin | n | mean predicted | observed rate |
|---|---:|---:|---:|
| 0.0-0.1 | 1964 | 0.045 | 0.102 |
| 0.1-0.2 | 556 | 0.146 | 0.282 |
| 0.2-0.3 | 164 | 0.242 | 0.366 |
| 0.3-0.4 | 123 | 0.344 | 0.496 |
| 0.4-0.5 | 64 | 0.450 | 0.562 |
| 0.5-0.6 | 58 | 0.544 | 0.621 |
| 0.6-0.7 | 21 | 0.653 | 0.762 |
| 0.7-0.8 | 30 | 0.751 | 0.900 |
| 0.8-0.9 | 10 | 0.846 | 1.000 |
| 0.9-1.0 | 10 | 0.947 | 1.000 |

## Fairness / subgroup analysis

AUROC (and event rate) for the headline mortality scores by subgroup. Differential discrimination — an AUROC spread of more than ~0.05 across subgroups — can indicate inequitable performance and warrants investigation before deployment.


### By sex

| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |
|---|---:|---:|---:|---:|---:|---:|
| F | 1389 | 19.9% | 0.819 | 0.790 | 0.786 | 0.778 |
| M | 1611 | 21.0% | 0.807 | 0.779 | 0.766 | 0.753 |

### By age group

| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |
|---|---:|---:|---:|---:|---:|---:|
| 50-64 | 1014 | 17.9% | 0.826 | 0.793 | 0.802 | 0.755 |
| 65-79 | 920 | 22.7% | 0.824 | 0.764 | 0.761 | 0.771 |
| 80+ | 414 | 28.0% | 0.777 | 0.757 | 0.712 | 0.751 |
| <50 | 652 | 16.4% | 0.819 | 0.809 | 0.776 | 0.796 |

## Interpretation

Multi-organ severity scores (SOFA, APACHE II, SAPS II) and the NEWS2 early-warning score discriminate best; single-axis scores (Shock Index, KDIGO) discriminate least — the clinically expected ordering, since this cohort's mortality is driven by multi-organ burden. This confirms the engine computes and orders risk correctly end-to-end.

Note the SAPS II calibration table: it discriminates well but **under-predicts** observed mortality on this cohort — exactly the kind of finding real validation surfaces, and why published coefficients generally need **local recalibration**. Absolute values are properties of the synthetic DGP, not any real population; re-run on real ICU data (`MIMIC_COHORT_CSV`) for clinical evidence.

