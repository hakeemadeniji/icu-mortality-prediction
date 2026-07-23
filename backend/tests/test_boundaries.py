"""
Boundary (threshold-transition) verification for the scoring engine.

For each scored parameter we assert the points at and around every published
cutoff — the class of off-by-one/wrong-inequality bugs that matter most in a
points-table score. Built by holding all other inputs at their zero-point value
and varying one parameter, so the total equals that parameter's points.
"""

import pytest

from services import clinical_scores as cs

# NEWS2 baseline where every parameter scores 0.
NEWS2_NORMAL = {
    "resp_rate": 16, "spo2": 98, "on_supplemental_o2": False,
    "temperature": 36.8, "sbp": 120, "heart_rate": 70, "consciousness": "A",
}


@pytest.mark.parametrize("field,value,pts", [
    # Respiratory rate
    ("resp_rate", 8, 3), ("resp_rate", 9, 1), ("resp_rate", 11, 1), ("resp_rate", 12, 0),
    ("resp_rate", 20, 0), ("resp_rate", 21, 2), ("resp_rate", 24, 2), ("resp_rate", 25, 3),
    # SpO2 (scale 1)
    ("spo2", 91, 3), ("spo2", 92, 2), ("spo2", 93, 2), ("spo2", 94, 1), ("spo2", 95, 1), ("spo2", 96, 0),
    # Temperature
    ("temperature", 35.0, 3), ("temperature", 35.1, 1), ("temperature", 36.0, 1),
    ("temperature", 36.1, 0), ("temperature", 38.0, 0), ("temperature", 38.1, 1),
    ("temperature", 39.0, 1), ("temperature", 39.1, 2),
    # Systolic BP
    ("sbp", 90, 3), ("sbp", 91, 2), ("sbp", 100, 2), ("sbp", 101, 1),
    ("sbp", 110, 1), ("sbp", 111, 0), ("sbp", 219, 0), ("sbp", 220, 3),
    # Heart rate
    ("heart_rate", 40, 3), ("heart_rate", 41, 1), ("heart_rate", 50, 1), ("heart_rate", 51, 0),
    ("heart_rate", 90, 0), ("heart_rate", 91, 1), ("heart_rate", 110, 1),
    ("heart_rate", 111, 2), ("heart_rate", 130, 2), ("heart_rate", 131, 3),
])
def test_news2_parameter_boundaries(field, value, pts):
    r = cs.score_news2({**NEWS2_NORMAL, field: value})
    assert r.score == pts, f"{field}={value}: expected {pts}, got {r.score}"


def test_news2_supplemental_o2_and_consciousness():
    assert cs.score_news2({**NEWS2_NORMAL, "on_supplemental_o2": True}).score == 2
    # Explicit ACVPU takes precedence, so test 'confusion' without it set.
    base = {k: v for k, v in NEWS2_NORMAL.items() if k != "consciousness"}
    assert cs.score_news2({**base, "confusion": True}).score == 3


# --- SOFA per-system boundaries (each system in isolation) ------------------
@pytest.mark.parametrize("field,value,pts", [
    ("platelets", 149, 1), ("platelets", 150, 0), ("platelets", 99, 2),
    ("platelets", 49, 3), ("platelets", 19, 4),
    ("bilirubin", 1.2, 1), ("bilirubin", 1.19, 0), ("bilirubin", 2.0, 2),
    ("bilirubin", 6.0, 3), ("bilirubin", 12.0, 4),
    ("creatinine", 1.2, 1), ("creatinine", 1.19, 0), ("creatinine", 2.0, 2),
    ("creatinine", 3.5, 3), ("creatinine", 5.0, 4),
])
def test_sofa_single_system_boundaries(field, value, pts):
    r = cs.score_sofa({field: value})
    assert r.score == pts, f"{field}={value}: expected {pts}, got {r.score}"


def test_sofa_gcs_boundaries():
    assert cs.score_sofa({"gcs": 15}).score == 0
    assert cs.score_sofa({"gcs": 14}).score == 1
    assert cs.score_sofa({"gcs": 12}).score == 2
    assert cs.score_sofa({"gcs": 9}).score == 3
    assert cs.score_sofa({"gcs": 5}).score == 4


# --- SAPS II age & GCS bands ------------------------------------------------
@pytest.mark.parametrize("age,pts", [
    (39, 0), (40, 7), (59, 7), (60, 12), (69, 12), (70, 15), (74, 15),
    (75, 16), (79, 16), (80, 18),
])
def test_saps2_age_bands(age, pts):
    r = cs.score_saps2({"age": age, "gcs": 15, "mechanical_ventilation": False,
                        "admission_type": "scheduled_surgical"})
    age_comp = next(c for c in r.components if c["name"] == "Age")
    assert age_comp["points"] == pts


# --- APACHE II temperature & HR bands ---------------------------------------
@pytest.mark.parametrize("temp,pts", [
    (41, 4), (40, 3), (39, 3), (38.5, 1), (38.4, 0), (36, 0),
    (35.9, 1), (33.9, 2), (31.9, 3), (29.9, 4),
])
def test_apache2_temperature_bands(temp, pts):
    r = cs.score_apache2({"age": 30, "gcs": 15, "temperature": temp})
    tcomp = next(c for c in r.components if c["name"] == "Temperature")
    assert tcomp["points"] == pts
