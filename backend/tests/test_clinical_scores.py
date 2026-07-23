"""
Known-answer tests for the clinical scoring engine.

Each case is worked by hand from the published score definition, so these guard
against regressions in the thresholds/points tables (they already caught a units
bug in the ROX index).
"""

import math

from services import clinical_scores as cs


# --- NEWS2 ------------------------------------------------------------------
def test_news2_deteriorating_patient():
    # RR22(+2) SpO2 93 Scale1(+2) O2(+2) Temp38.5(+1) SBP95(+2) HR115(+2) Alert(0)=11
    r = cs.score_news2({
        "resp_rate": 22, "spo2": 93, "on_supplemental_o2": True,
        "temperature": 38.5, "sbp": 95, "heart_rate": 115, "consciousness": "A",
    })
    assert r.computable and r.score == 11 and r.band == "critical"


def test_news2_normal_patient():
    r = cs.score_news2({
        "resp_rate": 16, "spo2": 98, "on_supplemental_o2": False,
        "temperature": 36.8, "sbp": 120, "heart_rate": 70, "consciousness": "A",
    })
    assert r.score == 0 and r.band == "low"


def test_news2_single_param_3_is_medium():
    # All normal except SpO2 90 (+3) -> aggregate 3 but a single-parameter 3
    r = cs.score_news2({
        "resp_rate": 16, "spo2": 90, "on_supplemental_o2": False,
        "temperature": 36.8, "sbp": 120, "heart_rate": 70, "consciousness": "A",
    })
    assert r.score == 3 and r.band == "medium"


def test_news2_missing_data():
    r = cs.score_news2({"resp_rate": 16})
    assert not r.computable and "spo2" in r.missing


# --- qSOFA ------------------------------------------------------------------
def test_qsofa_high():
    r = cs.score_qsofa({"resp_rate": 24, "sbp": 96, "confusion": True})
    assert r.score == 3 and r.band == "high"


def test_qsofa_low():
    r = cs.score_qsofa({"resp_rate": 16, "sbp": 120, "confusion": False})
    assert r.score == 0 and r.band == "low"


# --- SOFA -------------------------------------------------------------------
def test_sofa_full_six_systems():
    # plt80(+2) bili3.0(+2) cr2.5(+2) gcs13(+1) map65(+1) pf180 not-vent(+2) = 10
    r = cs.score_sofa({
        "platelets": 80, "bilirubin": 3.0, "creatinine": 2.5, "gcs": 13,
        "map": 65, "pao2": 90, "fio2": 0.5,
    })
    assert r.score == 10 and r.band == "high"
    assert not r.missing  # all six systems scored


def test_sofa_partial():
    r = cs.score_sofa({"platelets": 40})  # only coagulation
    assert r.computable and r.score == 3 and len(r.missing) == 5


# --- SIRS -------------------------------------------------------------------
def test_sirs_all_four():
    r = cs.score_sirs({"temperature": 38.5, "heart_rate": 95, "resp_rate": 22, "wbc": 14})
    assert r.score == 4 and r.band == "medium"


# --- CURB-65 ----------------------------------------------------------------
def test_curb65_severe():
    r = cs.score_curb65({
        "confusion": True, "urea": 8, "resp_rate": 32, "sbp": 85, "dbp": 55, "age": 70,
    })
    assert r.score == 5 and r.band == "high"


def test_curb65_low():
    r = cs.score_curb65({
        "confusion": False, "urea": 5, "resp_rate": 18, "sbp": 130, "dbp": 80, "age": 50,
    })
    assert r.score == 0 and r.band == "low"


def test_curb65_bun_converts_to_urea():
    # BUN 28 mg/dL -> urea 10 mmol/L (>7) -> +1
    r = cs.score_curb65({"resp_rate": 18, "sbp": 120, "age": 40, "bun": 28})
    urea_comp = next(c for c in r.components if "Urea" in c["name"])
    assert urea_comp["points"] == 1


# --- Shock Index ------------------------------------------------------------
def test_shock_index_high():
    r = cs.score_shock_index({"heart_rate": 120, "sbp": 80})
    assert math.isclose(r.score, 1.5, abs_tol=0.01) and r.band == "high"


def test_shock_index_normal():
    r = cs.score_shock_index({"heart_rate": 70, "sbp": 120})
    assert r.band == "low"


# --- ROX index (regression guard for the units bug) -------------------------
def test_rox_value_and_band():
    # (92 / 0.5) / 28 = 6.57 -> low risk (>=4.88)
    r = cs.score_rox({"spo2": 92, "fio2": 0.5, "resp_rate": 28})
    assert math.isclose(r.score, 6.57, abs_tol=0.05) and r.band == "low"


def test_rox_high_risk():
    # (90 / 0.8) / 34 = 3.31 -> high risk (<3.85)
    r = cs.score_rox({"spo2": 90, "fio2": 0.8, "resp_rate": 34})
    assert r.score < 3.85 and r.band == "high"


def test_rox_accepts_percent_fio2():
    # FiO2 given as 50 (%) should behave like 0.5
    r = cs.score_rox({"spo2": 92, "fio2": 50, "resp_rate": 28})
    assert math.isclose(r.score, 6.57, abs_tol=0.05)


# --- PaO2/FiO2 --------------------------------------------------------------
def test_pf_ratio_moderate_ards():
    r = cs.score_pf_ratio({"pao2": 90, "fio2": 0.5})  # 180 -> moderate
    assert r.score == 180 and r.band == "high"


# --- KDIGO AKI --------------------------------------------------------------
def test_kdigo_stage3_by_ratio():
    r = cs.score_kdigo_aki({"creatinine": 3.0, "baseline_creatinine": 1.0})
    assert r.score == 3 and r.band == "critical"


def test_kdigo_stage1_by_small_rise():
    r = cs.score_kdigo_aki({"creatinine": 1.4, "baseline_creatinine": 1.05})  # +0.35
    assert r.score == 1


# --- Aggregate --------------------------------------------------------------
def test_assess_overall_and_alerts():
    out = cs.assess({
        "resp_rate": 24, "spo2": 90, "on_supplemental_o2": True, "temperature": 39.2,
        "sbp": 85, "dbp": 50, "heart_rate": 125, "confusion": True, "age": 72,
        "creatinine": 3.2, "baseline_creatinine": 1.0, "platelets": 60,
    })
    assert out["overall_risk"] in ("high", "critical")
    assert out["computed_count"] >= 5
    assert len(out["alerts"]) >= 1
    # alerts sorted most-severe first
    assert out["alerts"][0]["band"] in ("high", "critical")
