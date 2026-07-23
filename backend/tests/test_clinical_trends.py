"""Known-answer tests for the trend-based scoring engine."""

from services import clinical_trends as ct

# NEWS2 = 0
MILD = {"resp_rate": 16, "spo2": 98, "on_supplemental_o2": False,
        "temperature": 36.8, "sbp": 120, "heart_rate": 70, "consciousness": "A"}
# NEWS2 = 11 (RR24+2, SpO2 92+2, O2+2, temp38.5+1, SBP95+2, HR115+2)
SEVERE = {"resp_rate": 24, "spo2": 92, "on_supplemental_o2": True,
          "temperature": 38.5, "sbp": 95, "heart_rate": 115, "consciousness": "A"}


# --- NEWS2 trend ------------------------------------------------------------
def test_news2_trend_rising():
    r = ct.news2_trend([{"hours": 0, "snapshot": MILD}, {"hours": 4, "snapshot": SEVERE}])
    assert r["computable"] and r["value"] == 11 and r["band"] == "high"


def test_news2_trend_improving():
    r = ct.news2_trend([{"hours": 0, "snapshot": SEVERE}, {"hours": 6, "snapshot": MILD}])
    assert r["value"] == -11 and r["band"] == "low"


def test_news2_trend_sorts_by_hours():
    # Out of order input; must sort so SEVERE (later) is last → Δ = +11
    r = ct.news2_trend([{"hours": 6, "snapshot": SEVERE}, {"hours": 0, "snapshot": MILD}])
    assert r["value"] == 11


def test_news2_trend_insufficient():
    assert not ct.news2_trend([{"hours": 0, "snapshot": MILD}])["computable"]


# --- Lactate clearance ------------------------------------------------------
def test_lactate_clearance_adequate():
    r = ct.lactate_clearance([{"hours": 0, "snapshot": {"lactate": 4.0}},
                              {"hours": 6, "snapshot": {"lactate": 2.0}}])
    assert r["computable"] and r["value"] == 50.0 and r["band"] == "low"


def test_lactate_clearance_inadequate():
    r = ct.lactate_clearance([{"hours": 0, "snapshot": {"lactate": 4.0}},
                              {"hours": 6, "snapshot": {"lactate": 3.8}}])
    assert r["band"] == "medium"  # ~5% clearance


def test_lactate_rising_is_critical():
    r = ct.lactate_clearance([{"hours": 0, "snapshot": {"lactate": 4.0}},
                              {"hours": 4, "snapshot": {"lactate": 5.0}}])
    assert r["value"] < 0 and r["band"] == "critical"


def test_lactate_insufficient():
    assert not ct.lactate_clearance([{"hours": 0, "snapshot": {"lactate": 4.0}}])["computable"]


# --- Aggregate --------------------------------------------------------------
def test_assess_trends_aggregate():
    tps = [
        {"hours": 0, "snapshot": {**MILD, "lactate": 4.0}},
        {"hours": 6, "snapshot": {**SEVERE, "lactate": 5.0}},
    ]
    out = ct.assess_trends(tps)
    assert out["overall_trend_risk"] in ("high", "critical")
    assert out["computed_count"] == 2 and out["total_trends"] == 2
    assert out["engine_version"] == ct.ENGINE_VERSION
    assert out["hours_span"] == 6.0
