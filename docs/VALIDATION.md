# Validation & Device-Readiness Dossier

This document describes the verification, safety, and validation posture of the
ICU clinical scoring engine, and — importantly — states honestly **what has been
done in software** versus **what still remains** for the system to become an
actual regulated medical device.

> **Regulatory status: NOT a medical device.** This is research / clinical
> decision-support software. It has **not** been cleared or approved by the FDA,
> UKCA, or under EU MDR, and must not be used as the sole basis for diagnosis or
> treatment. The work below raises the *software* to validation-grade rigor; it
> does **not** constitute regulatory clearance.

Engine version covered: **1.0.0** (`clinical_scores.ENGINE_VERSION`).

---

## 1. Intended use

| Item | Statement |
|---|---|
| **Intended use** | Decision support for qualified adult-ICU clinicians: compute validated early-warning and severity-of-illness scores from a patient snapshot to aid recognition of deterioration, sepsis, and organ dysfunction. |
| **Intended users** | Qualified clinicians (physicians, nurses, intensivists). Not for patient self-use. |
| **Patient population** | Adult (≥18y) intensive-care / acutely-ill inpatients. |
| **Operating environment** | Hospital / ICU, as an adjunct to — not a replacement for — monitoring and clinical assessment. |
| **Indications** | Situational awareness of deterioration risk; triage/escalation prompts; documentation. |
| **Contraindications / not for** | Pediatric/neonatal or non-ICU populations (not validated); autonomous diagnosis or treatment; sole basis for clinical decisions; use outside the input ranges in §5. |

The same statement is served at runtime: `GET /api/v1/risk/intended-use` and in every
`/assess` response (`intended_use`).

---

## 2. Verification (V&V) — done

The engine is **deterministic** and covered by an automated test suite that runs in
CI on every change (`.github/workflows/ci.yml`), with a **≥90 % line-coverage gate**
on the clinical modules.

| Verification activity | Where | What it proves |
|---|---|---|
| **Known-answer tests** | `tests/test_clinical_scores.py` | Each score reproduces cases worked by hand from the source publication. |
| **Boundary tests** | `tests/test_boundaries.py` | Points are correct *at and around every threshold* (guards off-by-one / wrong-inequality bugs). |
| **Property / invariant tests** | `tests/test_properties.py` | Monotonicity (worsening a variable never lowers the score), determinism, response contract, reproducible input hash. |
| **Safety-layer tests** | `tests/test_properties.py` | Out-of-range and inconsistent inputs are flagged. |
| **Metrics-harness tests** | `tests/test_validation_metrics.py` | AUROC/Brier/calibration functions are numerically correct. |
| **Coverage gate** | CI | ≥90 % of `clinical_scores.py` + `validation_metrics.py` executed by tests. |

A real bug was caught by this process during development (a ×100 units error in the
ROX index), which is exactly what verification is for.

### Traceability matrix (requirement → source → implementation → tests)

| Score | Source | Implementation | Tests |
|---|---|---|---|
| NEWS2 | RCP 2017 | `score_news2` | known-answer + full boundary set |
| qSOFA | Sepsis-3, JAMA 2016 | `score_qsofa` | known-answer |
| SOFA | Vincent 1996 | `score_sofa` | known-answer + per-system boundaries |
| SIRS | ACCP/SCCM 1992 | `score_sirs` | known-answer |
| CURB-65 | Lim 2003 | `score_curb65` | known-answer + BUN→urea conversion |
| Shock Index | Rady 1994 | `score_shock_index` | known-answer |
| ROX | Roca 2019 | `score_rox` | known-answer + units regression |
| PaO₂/FiO₂ | Berlin 2012 | `score_pf_ratio` | known-answer |
| KDIGO AKI | KDIGO 2012 | `score_kdigo_aki` | known-answer |
| APACHE II | Knaus 1985 | `score_apache2` | known-answer + temperature bands |
| SAPS II | Le Gall 1993 | `score_saps2` | known-answer + age/GCS bands + mortality logistic |

See `docs/CLINICAL_SCORES.md` for the full variable/threshold definitions and citations.

---

## 3. Safety / risk management — done (software-level)

An ISO 14971-style hazard analysis of the software behaviour, with the mitigations
implemented in this engine.

| # | Hazard | Cause | Mitigation (implemented) |
|---|---|---|---|
| H1 | Score computed on an impossible value | Data-entry / unit error | Physiologic range validation (`validate_inputs`) flags out-of-range values in every response (`input_warnings`). |
| H2 | Inconsistent inputs trusted | e.g. DBP ≥ SBP | Cross-field consistency checks flagged. |
| H3 | Under-estimation from missing data | Unmeasured variables scored 0 (APACHE/SOFA/SAPS convention) | Data completeness reported (`n/12`, `missing[]`) and stated in the interpretation. |
| H4 | Silent unit mismatch | BUN vs urea, FiO₂ fraction vs % | Explicit units per field; automatic BUN→urea and FiO₂ %→fraction handling. |
| H5 | Over-reliance / automation bias | Clinician defers to the number | Prominent "decision-support, not a device" statement in the API, UI, and docs; interpretations phrase actions as prompts, not directives. |
| H6 | Non-reproducible / untraceable result | Ambiguity about which algorithm produced a number | Versioned engine + deterministic input hash + unique assessment id + timestamp + append-only audit trail. |
| H7 | Wrong-population use | Applied to peds/non-ICU | Intended-use / contraindications stated in API, UI, and this document. |

**Traceability / audit.** Each assessment carries `engine_version`, a deterministic
`input_hash`, a unique `assessment_id`, and `assessed_at`, and is recorded to an
append-only audit log (`logs/risk_audit.jsonl`, input **hash** + result summary — not
raw PHI). A production system would persist full inputs in a secured, access-
controlled, retention-managed store.

---

## 4. Clinical validation — tooling ready, evidence pending

Verification (§2) proves the scores are computed **correctly**. Clinical validation
asks whether they **discriminate and are well-calibrated on the deploying
population** — this requires a labeled outcome cohort and is the key remaining step.

**Provided:**
- A tested validation harness (`services/validation_metrics.py`) that, given
  `(predictions, outcomes)`, reports **AUROC** (discrimination), **Brier score**, and
  a **calibration table** (reliability).
- A reproducible **functional benchmark** on a seeded synthetic multi-organ cohort
  (`services/synthetic_cohort.py`, runner `validate_scores.py`) whose mortality is
  driven by organ-failure burden independent of the scores. Results:
  **[docs/VALIDATION_RESULTS.md](VALIDATION_RESULTS.md)** — every score discriminates
  (AUROC ≈ 0.67–0.81), with multi-organ severity scores (SOFA, APACHE II, SAPS II)
  and NEWS2 leading, as expected. It also demonstrates the harness detecting
  **SAPS II miscalibration** (under-prediction) — i.e. why local recalibration is
  needed. This is a *functional* validation of the engine, **not** clinical evidence.

> The synthetic benchmark proves the engine computes/orders risk correctly and that
> the validation tooling works. It is **not** evidence of performance on real
> patients.

**Real-cohort path (built and ready):** a tested **MIMIC-IV adapter**
(`services/mimic_adapter.py`) + a documented SQL extraction
(`scripts/sql/mimic/first_day_cohort.sql`) turn a credentialed MIMIC-IV build into
the cohort the harness consumes. With `MIMIC_COHORT_CSV` set, `validate_scores.py`
produces a real-cohort report. Full instructions, variable mapping and caveats:
**[docs/MIMIC_VALIDATION.md](MIMIC_VALIDATION.md)**.

**Validation plan (to generate real evidence):**
1. Obtain credentialed MIMIC-IV access, build the derived concepts, run the SQL
   extraction, and run the harness (see MIMIC_VALIDATION.md). The cohort is first
   adult ICU stays with first-24h physiology and in-hospital mortality.
2. Run each score over the cohort; compute AUROC + calibration with the harness,
   overall and across subgroups (age, sex, ethnicity) for fairness.
3. Report discrimination, calibration (and recalibrate/ refit coefficients if
   needed — e.g. SAPS II is known to need local recalibration), and decision-curve
   utility at the intended alert thresholds.
4. Prospective / silent-mode evaluation before any live alerting.

---

## 5. Input ranges (validated bounds)

`validate_inputs` flags values outside these plausible ranges (see
`PARAM_RANGES`): age 0–120 yr, HR 10–300 bpm, RR 2–80 /min, SBP 30–300, DBP 10–200,
MAP 20–250 mmHg, temp 25–45 °C, SpO₂ 30–100 %, FiO₂ 0.21–1.0, GCS 3–15, WBC 0–200,
platelets 0–2000 ×10³, bilirubin 0–80, creatinine 0–25, BUN 0–300 mg/dL, urea
0–100 mmol/L, lactate 0–40, PaO₂ 20–700, PaCO₂ 5–200 mmHg, pH 6.5–8.0, Na 90–200,
K 1–10 mmol/L, HCO₃ 2–60 mEq/L, hematocrit 5–75 %, urine 0–12000 mL/24h.

---

## 6. Known limitations

- Scores use a single time point; trends (e.g. lactate clearance, rising NEWS2) are
  not yet modelled.
- Missing variables are scored 0 (per the original methods) which can under-estimate;
  completeness is surfaced but not enforced.
- SOFA cardiovascular uses a vasopressor flag (not dose-stratified). APACHE II does
  not double creatinine for acute renal failure. NEWS2 uses Scale 1 only.
- Published mortality figures (CURB-65, SAPS II, APACHE II) reflect the original
  derivation cohorts and generally require local recalibration.

---

## 7. Regulatory gap — what remains for actual clearance

To become a cleared/CE-marked device, the following (outside this repository) would
still be required:

- **Clinical evaluation / validation study** on the target population (§4) with
  pre-registered endpoints and, ideally, prospective evaluation.
- **Quality Management System** — ISO 13485.
- **Software lifecycle processes** — IEC 62304 (development, maintenance, SOUP/OSS
  management, configuration management).
- **Risk management file** — ISO 14971 (this document is a starting hazard analysis,
  not the full file).
- **Usability / human-factors engineering** — IEC 62366-1.
- **Clinical safety** (jurisdiction-specific, e.g. UK DCB0129/0160).
- **Cybersecurity & data protection** — threat modelling, access control, audit,
  HIPAA/GDPR data-processing agreements, penetration testing.
- **Regulatory submission** — FDA 510(k)/De Novo (likely Class II SaMD) or EU MDR
  technical documentation + Notified Body review; labelling and IFU.
- **Post-market surveillance** — performance monitoring, drift detection, incident
  reporting.

---

## 8. References
Score citations are listed in `docs/CLINICAL_SCORES.md`. Standards referenced:
ISO 13485, ISO 14971, IEC 62304, IEC 62366-1; FDA Software as a Medical Device
(SaMD) guidance; EU Regulation 2017/745 (MDR).
