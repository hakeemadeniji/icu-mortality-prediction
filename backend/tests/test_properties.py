"""
Property, determinism, safety-layer and contract tests for the engine.

These assert invariants that must hold for *any* input, complementing the
known-answer and boundary tests.
"""

from services import clinical_scores as cs


# --- Determinism / reproducibility ------------------------------------------
def test_assess_is_deterministic():
    snap = {"resp_rate": 24, "spo2": 90, "sbp": 88, "heart_rate": 120,
            "temperature": 39, "gcs": 13, "age": 70}
    a, b = cs.assess(snap), cs.assess(snap)
    assert a == b
    assert a["input_hash"] == b["input_hash"]


def test_input_hash_changes_with_input():
    h1 = cs.assess({"age": 70, "gcs": 15})["input_hash"]
    h2 = cs.assess({"age": 71, "gcs": 15})["input_hash"]
    assert h1 != h2


# --- Response contract ------------------------------------------------------
def test_assess_response_contract():
    out = cs.assess({"age": 60, "gcs": 15, "heart_rate": 80})
    for k in ("engine_version", "input_hash", "input_warnings", "overall_risk",
              "scores", "alerts", "computed_count", "total_scores",
              "intended_use", "disclaimer"):
        assert k in out, f"missing key: {k}"
    assert out["engine_version"] == cs.ENGINE_VERSION
    assert out["total_scores"] == len(cs._SCORERS)
    assert out["intended_use"]["not_for"]  # non-empty safety statement


def test_every_score_result_has_required_fields():
    out = cs.assess({"age": 70, "gcs": 12, "heart_rate": 120, "sbp": 85,
                     "resp_rate": 26, "spo2": 90, "temperature": 39})
    required = {"key", "name", "target", "score", "max_score", "band",
                "interpretation", "components", "reference", "computable", "missing"}
    for s in out["scores"]:
        assert required.issubset(s.keys())
        assert s["band"] in cs.BANDS or s["band"] == "unknown"


# --- Monotonicity (worsening a variable never lowers the score) -------------
def test_news2_monotonic_in_hypoxia():
    base = {"resp_rate": 16, "on_supplemental_o2": False, "temperature": 36.8,
            "sbp": 120, "heart_rate": 70, "consciousness": "A"}
    scores = [cs.score_news2({**base, "spo2": s}).score for s in (98, 96, 95, 94, 93, 92, 91, 88)]
    assert scores == sorted(scores)  # non-decreasing as SpO2 falls


def test_sofa_monotonic_in_creatinine():
    scores = [cs.score_sofa({"creatinine": c}).score for c in (0.5, 1.0, 1.5, 2.5, 4.0, 6.0)]
    assert scores == sorted(scores)


# --- Safety: input validation -----------------------------------------------
def test_validation_flags_out_of_range():
    w = cs.validate_inputs({"spo2": 150, "heart_rate": 80})
    assert any(x["field"] == "spo2" for x in w)


def test_validation_clean_when_normal():
    assert cs.validate_inputs({"spo2": 96, "heart_rate": 80, "sbp": 120, "dbp": 70}) == []


def test_validation_flags_diastolic_over_systolic():
    w = cs.validate_inputs({"sbp": 90, "dbp": 100})
    assert any(x["field"] == "dbp" for x in w)


def test_validation_accepts_fio2_as_percent():
    # FiO2 given as 50 (%) is within range; 150 (%) is not
    assert cs.validate_inputs({"fio2": 50}) == []
    assert any(x["field"] == "fio2" for x in cs.validate_inputs({"fio2": 150}))


def test_assess_surfaces_warnings():
    out = cs.assess({"age": 70, "gcs": 15, "spo2": 250})
    assert any(x["field"] == "spo2" for x in out["input_warnings"])
