# Clinical Scoring Engine — ICU Deterioration & Adverse-Event Risk

This system augments the single mortality-risk model with a panel of **validated,
guideline-based bedside scores**, each targeting a specific ICU deterioration
syndrome with *measurable* predictors. Instead of one opaque percentage, a
clinician sees an interpretable, per-syndrome risk profile with the contributing
variables and the recommended response.

- **Engine:** [`backend/services/clinical_scores.py`](../backend/services/clinical_scores.py)
- **API:** `POST /api/v1/risk/assess`, `GET /api/v1/risk/catalog`
- **Tests:** [`backend/tests/test_clinical_scores.py`](../backend/tests/test_clinical_scores.py) (known-answer cases)

> ⚠️ **Clinical safety.** This is **research / decision-support** software, *not a
> validated medical device*. Thresholds follow published guidelines but must be
> validated against the deploying institution's protocols and population before any
> clinical use. Scores **support**, and never replace, clinician judgement, and must
> not be the sole basis for a clinical decision.

Each score computes only from the inputs it needs; a partial snapshot still returns
whatever can be computed, and reports what was missing. Risk bands are normalized to
`low → low-medium → medium → high → critical`, and the overall risk is the most
severe band across all computed scores.

---

## Scores implemented (Phase 1)

| Score | Clinical target | Key inputs |
|---|---|---|
| **NEWS2** | Clinical deterioration — cardiac arrest / ICU transfer / death ≤24h | RR, SpO₂, O₂, temp, SBP, HR, consciousness |
| **qSOFA** | Sepsis-related organ dysfunction (suspected infection) | RR, SBP, mentation |
| **SOFA** | Multi-organ dysfunction / ICU mortality | PaO₂/FiO₂, platelets, bilirubin, MAP/pressors, GCS, creatinine |
| **SIRS** | Systemic inflammation / early sepsis screen | temp, HR, RR/PaCO₂, WBC |
| **CURB-65** | Community-acquired pneumonia severity / 30-day mortality | confusion, urea, RR, BP, age |
| **Shock Index** | Occult hypoperfusion / hemodynamic instability | HR, SBP (MAP) |
| **ROX Index** | Respiratory failure — high-flow O₂ failure & intubation risk | SpO₂, FiO₂, RR |
| **PaO₂/FiO₂** | Acute hypoxemic respiratory failure / ARDS severity | PaO₂, FiO₂ |
| **KDIGO AKI** | Acute kidney injury stage | creatinine, baseline creatinine |

---

### NEWS2 — National Early Warning Score 2
Aggregate of 7 physiological parameters (0–3 points each). This is the score behind
"spotting cardiac-arrest signs during admission": it predicts the composite of
cardiac arrest, unplanned ICU admission, and death within 24 hours.

- **Points table** (per RCP 2017): RR ≤8 / ≥25 → 3; SpO₂ ≤91 → 3; any supplemental
  O₂ → 2; temp ≤35 → 3; SBP ≤90 or ≥220 → 3; HR ≤40 / ≥131 → 3; not "Alert" (ACVPU)
  → 3. (Full bands in code.)
- **Response bands:** 0–4 low; a single parameter = 3 → urgent ward review; 5–6
  medium (urgent); ≥7 high (emergency, critical-care).
- **Ref:** Royal College of Physicians, *National Early Warning Score (NEWS) 2*, 2017.

### qSOFA — quick SOFA
Bedside screen (0–3): RR ≥22, SBP ≤100, altered mentation (GCS<15). **≥2 → high risk**
of poor outcome in suspected infection.
- **Ref:** Singer et al., *Sepsis-3*, JAMA 2016;315(8):801–810.

### SOFA — Sequential Organ Failure Assessment
Six organ systems, 0–4 each (max 24): respiration (PaO₂/FiO₂), coagulation
(platelets), liver (bilirubin), cardiovascular (MAP / vasopressors), CNS (GCS),
renal (creatinine). A rise of **≥2** defines Sepsis-3 organ dysfunction. Subscores
compute independently; partial totals are labelled with the number of systems scored.
- **Ref:** Vincent et al., *Intensive Care Med* 1996;22:707–710.

### SIRS — Systemic Inflammatory Response Syndrome
≥2 of: temp >38 or <36 °C; HR >90; RR >20 (or PaCO₂ <32); WBC >12 or <4 ×10³/µL.
Sensitive but nonspecific.
- **Ref:** ACCP/SCCM Consensus, *Chest* 1992;101:1644–1655.

### CURB-65 — pneumonia severity
1 point each: **C**onfusion, **U**rea >7 mmol/L, **R**R ≥30, low **B**P (SBP<90 or
DBP≤60), age ≥**65**. Maps to 30-day mortality (0→0.6%, 1→2.7%, 2→6.8%, 3→14%,
4–5→27.8%) and disposition (0–1 outpatient, 2 observe, 3–5 admit / consider ICU).
BUN (mg/dL) is auto-converted to urea (mmol/L) when only BUN is provided.
- **Ref:** Lim et al., *Thorax* 2003;58:377–382.

### Shock Index (SI) & Modified SI
SI = HR / SBP (normal 0.5–0.9). **≥0.9** early instability, **≥1.0** significant
compromise / increased mortality. MSI = HR / MAP reported when MAP is available.
- **Ref:** Allgöwer & Burri 1967; Rady et al., *Am J Emerg Med* 1994.

### ROX Index
(SpO₂/FiO₂) / RR, for patients on oxygen. **≥4.88** lower risk of high-flow failure;
**<3.85** high risk → anticipate intubation; 3.85–4.88 indeterminate (recheck at
2/6/12 h). FiO₂ accepted as fraction (0.5) or percent (50).
- **Ref:** Roca et al., *Am J Respir Crit Care Med* 2019;199:1368–1376.

### PaO₂/FiO₂ (P/F) ratio
Oxygenation / ARDS severity (Berlin): >300 none; 200–300 mild; 100–200 moderate;
≤100 severe (assumes PEEP ≥5 for ARDS classification).
- **Ref:** ARDS Definition Task Force, *JAMA* 2012;307:2526–2533.

### KDIGO AKI stage
Staged by creatinine vs. baseline: Stage 1 = 1.5–1.9× or ≥0.3 mg/dL rise; Stage 2 =
2.0–2.9×; Stage 3 = ≥3× or creatinine ≥4.0 mg/dL. Urine-output criteria are not yet
captured. Without a baseline, staged coarsely from absolute creatinine.
- **Ref:** KDIGO AKI Guideline, *Kidney Int Suppl* 2012;2:1–138.

---

## API

`POST /api/v1/risk/assess` with any subset of the fields in
[`ClinicalSnapshot`](../backend/api/risk.py) returns:

```jsonc
{
  "overall_risk": "critical",
  "scores": [ { "key": "news2", "name": "NEWS2", "score": 18, "band": "critical",
                "components": [...], "interpretation": "...", "reference": "...",
                "computable": true, "missing": [] }, ... ],
  "alerts": [ { "name": "NEWS2", "band": "critical", "score": 18, "message": "..." }, ... ],
  "computed_count": 9, "total_scores": 9,
  "disclaimer": "Decision-support only. Not a validated medical device. ..."
}
```

`GET /api/v1/risk/catalog` lists the scores and the clinical targets they predict.

---

## Roadmap (candidate additions)

Higher-effort or more data-hungry scores to add next, grouped by syndrome:

- **ICU mortality:** APACHE II, SAPS II (need ABG, electrolytes, chronic-health items).
- **Sepsis/shock:** lactate clearance trend, MAP-targeted resuscitation flags.
- **Cardiac:** in-hospital cardiac-arrest risk (eCART), arrhythmia burden.
- **Respiratory:** SpO₂/FiO₂ (non-invasive P/F surrogate), HACOR for NIV failure.
- **Neuro:** CAM-ICU (delirium), RASS sedation.
- **Coagulation/liver/GI:** ISTH DIC score, MELD, Glasgow-Blatchford (GI bleed).
- **Prophylaxis/safety:** Padua/Caprini (VTE), Braden (pressure injury), NUTRIC.

Each new score is a single pure function returning a `ScoreResult`, registered in
`_SCORERS`, plus known-answer tests — so the panel extends without touching the API
or frontend.
