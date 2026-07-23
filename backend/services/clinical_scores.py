"""
Clinical scoring engine for ICU deterioration & adverse-event risk.

Each function implements a published, validated bedside score faithfully to its
source definition and returns a structured result (value, risk band, the
contributing components, an interpretation, the clinical target it predicts, and
a literature reference). Every score computes only from the inputs it needs and
reports gracefully when data is missing — so a partial snapshot still yields
whatever can be computed.

IMPORTANT — clinical safety
    This is research / decision-support software, NOT a validated medical device.
    Thresholds follow published guidelines but must be validated against the
    deploying institution's protocols and patient population before any clinical
    use. Scores support, and never replace, clinician judgement.

Inputs use a flat snapshot dict with SI-ish clinical units (documented per field
in api/risk.py). Missing values are None.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# Risk bands, ordered by severity (used to compute an overall level).
BANDS = ["low", "low-medium", "medium", "high", "critical"]
_BAND_RANK = {b: i for i, b in enumerate(BANDS)}


@dataclass
class ScoreResult:
    key: str
    name: str
    target: str  # the clinical event/condition this score helps predict
    score: Optional[float] = None
    max_score: Optional[float] = None
    band: str = "unknown"
    interpretation: str = ""
    components: List[Dict[str, Any]] = field(default_factory=list)
    reference: str = ""
    computable: bool = True
    missing: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _num(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _component(name: str, value: Any, points: Optional[int] = None) -> Dict[str, Any]:
    return {"name": name, "value": value, "points": points}


def _insufficient(key: str, name: str, target: str, reference: str,
                  missing: List[str]) -> ScoreResult:
    return ScoreResult(
        key=key, name=name, target=target, reference=reference,
        band="unknown", computable=False, missing=missing,
        interpretation="Insufficient data to compute this score.",
    )


# ---------------------------------------------------------------------------
# NEWS2 — National Early Warning Score 2 (Royal College of Physicians, 2017)
# Predicts clinical deterioration: cardiac arrest, unplanned ICU admission and
# death within 24 h. This is the score behind "spotting cardiac-arrest signs
# during admission".
# ---------------------------------------------------------------------------
def score_news2(s: Dict[str, Any]) -> ScoreResult:
    key, name = "news2", "NEWS2"
    target = "Clinical deterioration (cardiac arrest / ICU transfer / death within 24h)"
    ref = "Royal College of Physicians, National Early Warning Score (NEWS) 2, 2017"

    rr = _num(s.get("resp_rate"))
    spo2 = _num(s.get("spo2"))
    temp = _num(s.get("temperature"))
    sbp = _num(s.get("sbp"))
    hr = _num(s.get("heart_rate"))
    on_o2 = s.get("on_supplemental_o2")
    # Consciousness: 'A' (alert) scores 0; anything else (Confusion/V/P/U) scores 3.
    acvpu = (s.get("consciousness") or ("A" if not s.get("confusion") else "C"))
    gcs = _num(s.get("gcs"))
    if gcs is not None and gcs < 15:
        acvpu = "C"

    required = {"resp_rate": rr, "spo2": spo2, "temperature": temp,
                "sbp": sbp, "heart_rate": hr}
    missing = [k for k, v in required.items() if v is None]
    if missing:
        return _insufficient(key, name, target, ref, missing)

    comps: List[Dict[str, Any]] = []
    total = 0

    def add(nm, val, pts):
        nonlocal total
        total += pts
        comps.append(_component(nm, val, pts))

    # Respiration rate
    if rr <= 8: p = 3
    elif rr <= 11: p = 1
    elif rr <= 20: p = 0
    elif rr <= 24: p = 2
    else: p = 3
    add("Respiratory rate", rr, p)

    # SpO2 (Scale 1 — the default target range)
    if spo2 <= 91: p = 3
    elif spo2 <= 93: p = 2
    elif spo2 <= 95: p = 1
    else: p = 0
    add("SpO2 (Scale 1)", spo2, p)

    # Air vs supplemental O2
    p = 2 if on_o2 else 0
    add("Supplemental O2", bool(on_o2), p)

    # Temperature
    if temp <= 35.0: p = 3
    elif temp <= 36.0: p = 1
    elif temp <= 38.0: p = 0
    elif temp <= 39.0: p = 1
    else: p = 2
    add("Temperature", temp, p)

    # Systolic BP
    if sbp <= 90: p = 3
    elif sbp <= 100: p = 2
    elif sbp <= 110: p = 1
    elif sbp <= 219: p = 0
    else: p = 3
    add("Systolic BP", sbp, p)

    # Pulse
    if hr <= 40: p = 3
    elif hr <= 50: p = 1
    elif hr <= 90: p = 0
    elif hr <= 110: p = 1
    elif hr <= 130: p = 2
    else: p = 3
    add("Heart rate", hr, p)

    # Consciousness (ACVPU)
    p = 0 if acvpu == "A" else 3
    add("Consciousness (ACVPU)", acvpu, p)

    single_param_3 = any(c["points"] == 3 for c in comps)

    if total >= 7:
        band, interp = "critical", "Emergency response — high risk of deterioration; urgent critical-care review."
    elif total >= 5:
        band, interp = "high", "Urgent response — key threshold for clinical review by a team with critical-care competencies."
    elif single_param_3:
        band, interp = "medium", "Low-medium risk — a single parameter scoring 3 warrants urgent ward-based review."
    elif total >= 1:
        band, interp = "low-medium", "Low risk — routine monitoring, increase observation frequency."
    else:
        band, interp = "low", "Low risk — continue routine monitoring."

    return ScoreResult(key, name, target, score=total, max_score=20, band=band,
                       interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# qSOFA — quick SOFA (Sepsis-3, JAMA 2016)
# Bedside screen for poor outcome in suspected infection.
# ---------------------------------------------------------------------------
def score_qsofa(s: Dict[str, Any]) -> ScoreResult:
    key, name = "qsofa", "qSOFA"
    target = "Sepsis-related organ dysfunction / in-hospital death (suspected infection)"
    ref = "Singer et al., Sepsis-3, JAMA 2016;315(8):801-810"

    rr = _num(s.get("resp_rate"))
    sbp = _num(s.get("sbp"))
    gcs = _num(s.get("gcs"))
    altered = bool(s.get("confusion")) or (gcs is not None and gcs < 15)

    required = {"resp_rate": rr, "sbp": sbp}
    missing = [k for k, v in required.items() if v is None]
    if missing:
        return _insufficient(key, name, target, ref, missing)

    comps, total = [], 0
    p = 1 if rr >= 22 else 0; total += p
    comps.append(_component("Respiratory rate ≥ 22", rr, p))
    p = 1 if sbp <= 100 else 0; total += p
    comps.append(_component("Systolic BP ≤ 100", sbp, p))
    p = 1 if altered else 0; total += p
    comps.append(_component("Altered mentation (GCS<15)", altered, p))

    if total >= 2:
        band = "high"
        interp = "≥2 points: high risk of poor outcome in suspected infection — assess for sepsis, escalate."
    elif total == 1:
        band = "medium"
        interp = "1 point: monitor closely for sepsis in the context of suspected infection."
    else:
        band = "low"
        interp = "0 points: low qSOFA risk (does not rule out sepsis)."

    return ScoreResult(key, name, target, score=total, max_score=3, band=band,
                       interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# SOFA — Sequential Organ Failure Assessment (Vincent et al., 1996)
# Quantifies organ dysfunction across 6 systems; Sepsis-3 organ-failure marker.
# Computes each subscore independently; missing systems are noted.
# ---------------------------------------------------------------------------
def score_sofa(s: Dict[str, Any]) -> ScoreResult:
    key, name = "sofa", "SOFA"
    target = "Multi-organ dysfunction / ICU mortality"
    ref = "Vincent et al., Intensive Care Med 1996;22:707-710 (Sepsis-3 organ dysfunction)"

    comps: List[Dict[str, Any]] = []
    total = 0
    scored_systems = 0
    missing: List[str] = []

    # Respiration: PaO2/FiO2 (mmHg)
    pao2 = _num(s.get("pao2"))
    fio2 = _num(s.get("fio2"))
    vent = bool(s.get("mechanical_ventilation"))
    if pao2 is not None and fio2 and fio2 > 0:
        pf = pao2 / fio2
        if pf >= 400: p = 0
        elif pf >= 300: p = 1
        elif pf >= 200: p = 2
        elif pf >= 100: p = 3 if vent else 2
        else: p = 4 if vent else 2
        total += p; scored_systems += 1
        comps.append(_component("Respiration (PaO2/FiO2)", round(pf, 0), p))
    else:
        missing.append("respiration (PaO2 & FiO2)")

    # Coagulation: platelets (x10^3/µL)
    plt = _num(s.get("platelets"))
    if plt is not None:
        if plt >= 150: p = 0
        elif plt >= 100: p = 1
        elif plt >= 50: p = 2
        elif plt >= 20: p = 3
        else: p = 4
        total += p; scored_systems += 1
        comps.append(_component("Coagulation (platelets)", plt, p))
    else:
        missing.append("coagulation (platelets)")

    # Liver: bilirubin (mg/dL)
    bili = _num(s.get("bilirubin"))
    if bili is not None:
        if bili < 1.2: p = 0
        elif bili < 2.0: p = 1
        elif bili < 6.0: p = 2
        elif bili < 12.0: p = 3
        else: p = 4
        total += p; scored_systems += 1
        comps.append(_component("Liver (bilirubin)", bili, p))
    else:
        missing.append("liver (bilirubin)")

    # Cardiovascular: MAP / vasopressors
    map_val = _num(s.get("map"))
    sbp, dbp = _num(s.get("sbp")), _num(s.get("dbp"))
    if map_val is None and sbp is not None and dbp is not None:
        map_val = round((sbp + 2 * dbp) / 3, 0)
    vaso = bool(s.get("vasopressors"))
    if map_val is not None or vaso:
        if vaso:
            p = 3  # any vasopressor ⇒ at least 3 (norepinephrine dose not captured)
        elif map_val is not None and map_val < 70:
            p = 1
        else:
            p = 0
        total += p; scored_systems += 1
        comps.append(_component("Cardiovascular (MAP/vasopressors)",
                                "vasopressors" if vaso else map_val, p))
    else:
        missing.append("cardiovascular (MAP or vasopressors)")

    # CNS: GCS
    gcs = _num(s.get("gcs"))
    if gcs is not None:
        if gcs >= 15: p = 0
        elif gcs >= 13: p = 1
        elif gcs >= 10: p = 2
        elif gcs >= 6: p = 3
        else: p = 4
        total += p; scored_systems += 1
        comps.append(_component("CNS (GCS)", gcs, p))
    else:
        missing.append("CNS (GCS)")

    # Renal: creatinine (mg/dL)
    cr = _num(s.get("creatinine"))
    if cr is not None:
        if cr < 1.2: p = 0
        elif cr < 2.0: p = 1
        elif cr < 3.5: p = 2
        elif cr < 5.0: p = 3
        else: p = 4
        total += p; scored_systems += 1
        comps.append(_component("Renal (creatinine)", cr, p))
    else:
        missing.append("renal (creatinine)")

    if scored_systems == 0:
        return _insufficient(key, name, target, ref, missing)

    # Banding on the (possibly partial) total. Full SOFA max is 24.
    if total >= 11: band, interp = "critical", "Severe multi-organ dysfunction — mortality rises steeply above ~9-11."
    elif total >= 8: band, interp = "high", "Significant organ dysfunction — high mortality risk."
    elif total >= 5: band, interp = "medium", "Moderate organ dysfunction."
    elif total >= 2: band, interp = "low-medium", "Mild organ dysfunction (≥2 rise = Sepsis-3 organ dysfunction)."
    else: band, interp = "low", "Minimal organ dysfunction."

    if scored_systems < 6:
        interp += f" (Partial: {scored_systems}/6 systems scored.)"

    return ScoreResult(key, name, target, score=total, max_score=24, band=band,
                       interpretation=interp, components=comps, reference=ref,
                       missing=missing)


# ---------------------------------------------------------------------------
# SIRS — Systemic Inflammatory Response Syndrome (ACCP/SCCM 1992)
# ---------------------------------------------------------------------------
def score_sirs(s: Dict[str, Any]) -> ScoreResult:
    key, name = "sirs", "SIRS"
    target = "Systemic inflammation / early sepsis screen"
    ref = "ACCP/SCCM Consensus Conference, Chest 1992;101:1644-1655"

    temp = _num(s.get("temperature"))
    hr = _num(s.get("heart_rate"))
    rr = _num(s.get("resp_rate"))
    paco2 = _num(s.get("paco2"))
    wbc = _num(s.get("wbc"))

    if all(v is None for v in [temp, hr, rr, wbc]):
        return _insufficient(key, name, target, ref, ["temperature/HR/RR/WBC"])

    comps, total = [], 0
    if temp is not None:
        met = temp > 38.0 or temp < 36.0
        total += int(met); comps.append(_component("Temp >38 or <36°C", temp, int(met)))
    if hr is not None:
        met = hr > 90
        total += int(met); comps.append(_component("Heart rate >90", hr, int(met)))
    if rr is not None or paco2 is not None:
        met = (rr is not None and rr > 20) or (paco2 is not None and paco2 < 32)
        total += int(met); comps.append(_component("RR >20 or PaCO2 <32", rr, int(met)))
    if wbc is not None:
        met = wbc > 12 or wbc < 4
        total += int(met); comps.append(_component("WBC >12 or <4 (x10³)", wbc, int(met)))

    if total >= 2:
        band = "medium"
        interp = "≥2 SIRS criteria met — consider infection/sepsis (nonspecific)."
    else:
        band = "low"
        interp = "<2 SIRS criteria."

    return ScoreResult(key, name, target, score=total, max_score=4, band=band,
                       interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# CURB-65 — pneumonia severity / 30-day mortality (Lim et al., Thorax 2003)
# The user's pneumonia example.
# ---------------------------------------------------------------------------
def score_curb65(s: Dict[str, Any]) -> ScoreResult:
    key, name = "curb65", "CURB-65"
    target = "Community-acquired pneumonia severity / 30-day mortality"
    ref = "Lim et al., Thorax 2003;58:377-382"

    gcs = _num(s.get("gcs"))
    confusion = bool(s.get("confusion")) or (gcs is not None and gcs < 15)
    urea = _num(s.get("urea"))              # mmol/L
    bun = _num(s.get("bun"))                # mg/dL (BUN); urea_mmol = bun/2.8
    if urea is None and bun is not None:
        urea = bun / 2.8
    rr = _num(s.get("resp_rate"))
    sbp = _num(s.get("sbp"))
    dbp = _num(s.get("dbp"))
    age = _num(s.get("age"))

    # Needs at least the vitals + age; urea optional (scored 0 if absent, noted).
    required = {"resp_rate": rr, "sbp": sbp, "age": age}
    missing = [k for k, v in required.items() if v is None]
    if missing:
        return _insufficient(key, name, target, ref, missing)

    comps, total = [], 0
    p = int(confusion); total += p; comps.append(_component("Confusion", confusion, p))
    if urea is not None:
        p = int(urea > 7); comps.append(_component("Urea >7 mmol/L", round(urea, 1), p))
    else:
        p = 0; comps.append(_component("Urea >7 mmol/L", "n/a", p))
    total += p
    p = int(rr >= 30); total += p; comps.append(_component("Resp rate ≥30", rr, p))
    low_bp = sbp < 90 or (dbp is not None and dbp <= 60)
    p = int(low_bp); total += p; comps.append(_component("SBP<90 or DBP≤60", (sbp, dbp), p))
    p = int(age >= 65); total += p; comps.append(_component("Age ≥65", age, p))

    mortality = {0: "0.6%", 1: "2.7%", 2: "6.8%", 3: "14.0%", 4: "27.8%", 5: "27.8%"}
    if total >= 3:
        band = "high"
        interp = f"Severe pneumonia (30-day mortality ~{mortality[total]}) — hospitalize; consider ICU for 4-5."
    elif total == 2:
        band = "medium"
        interp = f"Moderate (30-day mortality ~{mortality[total]}) — consider short-stay/supervised treatment."
    else:
        band = "low"
        interp = f"Low severity (30-day mortality ~{mortality[total]}) — outpatient management may be suitable."

    return ScoreResult(key, name, target, score=total, max_score=5, band=band,
                       interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# Shock Index (SI) & Modified Shock Index (MSI)
# ---------------------------------------------------------------------------
def score_shock_index(s: Dict[str, Any]) -> ScoreResult:
    key, name = "shock_index", "Shock Index"
    target = "Occult hypoperfusion / hemodynamic instability"
    ref = "Allgöwer & Burri, 1967; Rady et al., Am J Emerg Med 1994"

    hr = _num(s.get("heart_rate"))
    sbp = _num(s.get("sbp"))
    dbp = _num(s.get("dbp"))
    map_val = _num(s.get("map"))
    if map_val is None and sbp is not None and dbp is not None:
        map_val = (sbp + 2 * dbp) / 3

    if hr is None or sbp is None or sbp == 0:
        return _insufficient(key, name, target, ref, ["heart_rate", "sbp"])

    si = hr / sbp
    comps = [_component("Shock Index (HR/SBP)", round(si, 2), None)]
    if map_val:
        comps.append(_component("Modified SI (HR/MAP)", round(hr / map_val, 2), None))

    if si >= 1.0:
        band = "high"
        interp = "SI ≥1.0 — significant hemodynamic compromise; associated with increased mortality."
    elif si >= 0.9:
        band = "medium"
        interp = "SI ≥0.9 — early hemodynamic instability; reassess perfusion."
    elif si < 0.5:
        band = "low-medium"
        interp = "SI <0.5 — possible bradycardia/hypertension context; interpret clinically."
    else:
        band = "low"
        interp = "SI 0.5-0.9 — normal range."

    return ScoreResult(key, name, target, score=round(si, 2), max_score=None,
                       band=band, interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# ROX index — HFNC failure / intubation risk (Roca et al., AJRCCM 2019)
# ---------------------------------------------------------------------------
def score_rox(s: Dict[str, Any]) -> ScoreResult:
    key, name = "rox", "ROX Index"
    target = "Respiratory failure / high-flow O2 failure & intubation risk"
    ref = "Roca et al., Am J Respir Crit Care Med 2019;199:1368-1376"

    spo2 = _num(s.get("spo2"))
    fio2 = _num(s.get("fio2"))
    rr = _num(s.get("resp_rate"))
    if spo2 is None or not fio2 or fio2 <= 0 or rr is None or rr == 0:
        return _insufficient(key, name, target, ref, ["spo2", "fio2", "resp_rate"])

    # FiO2 as fraction (0.21-1.0); accept percent too.
    f = fio2 / 100.0 if fio2 > 1.0 else fio2
    # ROX = (SpO2[%] / FiO2[fraction]) / RR
    rox = (spo2 / f) / rr
    comps = [
        _component("SpO2/FiO2", round(spo2 / f, 0), None),
        _component("ROX = (SpO2/FiO2)/RR", round(rox, 2), None),
    ]
    if rox >= 4.88:
        band = "low"
        interp = "ROX ≥4.88 — lower risk of high-flow failure/intubation."
    elif rox < 3.85:
        band = "high"
        interp = "ROX <3.85 — high risk of high-flow nasal cannula failure; anticipate intubation."
    else:
        band = "medium"
        interp = "ROX 3.85-4.88 — indeterminate; recheck at 2/6/12 h."

    return ScoreResult(key, name, target, score=round(rox, 2), max_score=None,
                       band=band, interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# PaO2/FiO2 (P/F) ratio — ARDS / oxygenation (Berlin definition, JAMA 2012)
# ---------------------------------------------------------------------------
def score_pf_ratio(s: Dict[str, Any]) -> ScoreResult:
    key, name = "pf_ratio", "PaO2/FiO2 Ratio"
    target = "Acute hypoxemic respiratory failure / ARDS severity"
    ref = "ARDS Definition Task Force (Berlin), JAMA 2012;307:2526-2533"

    pao2 = _num(s.get("pao2"))
    fio2 = _num(s.get("fio2"))
    if pao2 is None or not fio2 or fio2 <= 0:
        return _insufficient(key, name, target, ref, ["pao2", "fio2"])

    f = fio2 / 100.0 if fio2 > 1.0 else fio2
    pf = pao2 / f
    comps = [_component("PaO2/FiO2 (mmHg)", round(pf, 0), None)]
    if pf > 300:
        band, interp = "low", "P/F >300 — no ARDS-range hypoxemia."
    elif pf > 200:
        band, interp = "medium", "P/F 200-300 — mild ARDS range (with PEEP ≥5)."
    elif pf > 100:
        band, interp = "high", "P/F 100-200 — moderate ARDS range."
    else:
        band, interp = "critical", "P/F ≤100 — severe ARDS range; consider lung-protective ventilation / prone."

    return ScoreResult(key, name, target, score=round(pf, 0), max_score=None,
                       band=band, interpretation=interp, components=comps, reference=ref)


# ---------------------------------------------------------------------------
# KDIGO AKI stage — acute kidney injury (KDIGO, Kidney Int Suppl 2012)
# Uses creatinine vs. baseline (and/or absolute creatinine).
# ---------------------------------------------------------------------------
def score_kdigo_aki(s: Dict[str, Any]) -> ScoreResult:
    key, name = "kdigo_aki", "KDIGO AKI Stage"
    target = "Acute kidney injury"
    ref = "KDIGO Clinical Practice Guideline for AKI, Kidney Int Suppl 2012;2:1-138"

    cr = _num(s.get("creatinine"))
    base = _num(s.get("baseline_creatinine"))
    if cr is None:
        return _insufficient(key, name, target, ref, ["creatinine"])

    ratio = (cr / base) if base and base > 0 else None
    stage = 0
    if ratio is not None:
        if ratio >= 3.0 or cr >= 4.0:
            stage = 3
        elif ratio >= 2.0:
            stage = 2
        elif ratio >= 1.5 or (cr - base) >= 0.3:
            stage = 1
    else:
        # Without baseline, use absolute creatinine as a coarse proxy.
        if cr >= 4.0: stage = 3
        elif cr >= 2.0: stage = 1

    comps = [
        _component("Creatinine (mg/dL)", cr, None),
        _component("Baseline creatinine", base if base else "n/a", None),
        _component("Creatinine ratio", round(ratio, 2) if ratio else "n/a", None),
    ]
    band = {0: "low", 1: "medium", 2: "high", 3: "critical"}[stage]
    interp = {
        0: "No AKI by creatinine criteria (urine output not assessed).",
        1: "AKI Stage 1 — 1.5-1.9× baseline or ≥0.3 mg/dL rise.",
        2: "AKI Stage 2 — 2.0-2.9× baseline.",
        3: "AKI Stage 3 — ≥3× baseline or creatinine ≥4.0 mg/dL; consider renal support.",
    }[stage]
    if base is None:
        interp += " (No baseline provided — staged from absolute creatinine only.)"

    return ScoreResult(key, name, target, score=stage, max_score=3, band=band,
                       interpretation=interp, components=comps, reference=ref,
                       missing=[] if base else ["baseline_creatinine (recommended)"])


# The ordered catalog of scoring functions.
_SCORERS = [
    score_news2, score_qsofa, score_sofa, score_sirs, score_curb65,
    score_shock_index, score_rox, score_pf_ratio, score_kdigo_aki,
]


def assess(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Run every score over the snapshot and build a prioritized summary."""
    results = [fn(snapshot) for fn in _SCORERS]
    computed = [r for r in results if r.computable]

    # Overall level = the most severe band among computed scores.
    overall = "low"
    for r in computed:
        if _BAND_RANK.get(r.band, -1) > _BAND_RANK.get(overall, -1):
            overall = r.band

    # Prioritized alerts: medium+ scores, most severe first.
    alerts = sorted(
        [
            {
                "key": r.key,
                "name": r.name,
                "target": r.target,
                "score": r.score,
                "band": r.band,
                "message": r.interpretation,
            }
            for r in computed
            if _BAND_RANK.get(r.band, 0) >= _BAND_RANK["medium"]
        ],
        key=lambda a: _BAND_RANK.get(a["band"], 0),
        reverse=True,
    )

    return {
        "overall_risk": overall,
        "scores": [r.as_dict() for r in results],
        "alerts": alerts,
        "computed_count": len(computed),
        "total_scores": len(results),
        "disclaimer": (
            "Decision-support only. Not a validated medical device. Scores follow "
            "published guidelines but must be validated locally and interpreted by a "
            "qualified clinician; do not use as the sole basis for clinical decisions."
        ),
    }
