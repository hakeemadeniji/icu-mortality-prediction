"""
Trend-based clinical scoring — deterioration / treatment response over time.

Single-snapshot scores miss trajectory. These operate on a short time series of
snapshots and surface two high-value trends:

  - **NEWS2 trend** — a *rising* aggregate early-warning score is central to the
    RCP NEWS2 "track-and-trigger" philosophy; the change matters as much as the
    absolute value.
  - **Lactate clearance** — failure to clear lactate during resuscitation is
    strongly associated with mortality in sepsis/septic shock.

Same safety posture as the snapshot engine: decision-support only, NOT a validated
medical device.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services import clinical_scores as cs

ENGINE_VERSION = cs.ENGINE_VERSION


def _num(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _sorted(timepoints: List[Dict]) -> List[Dict]:
    return sorted(timepoints, key=lambda t: _num(t.get("hours")) or 0.0)


def _insufficient(key, name, target, ref, msg) -> Dict[str, Any]:
    return {
        "key": key, "name": name, "target": target, "value": None, "band": "unknown",
        "interpretation": msg, "components": [], "reference": ref,
        "computable": False, "series": [],
    }


# ---------------------------------------------------------------------------
# NEWS2 trend — track-and-trigger deterioration
# ---------------------------------------------------------------------------
def news2_trend(timepoints: List[Dict]) -> Dict[str, Any]:
    key, name = "news2_trend", "NEWS2 Trend"
    target = "Clinical deterioration trajectory (track-and-trigger)"
    ref = "Royal College of Physicians, NEWS2, 2017 (trend monitoring)"

    series = []
    for tp in _sorted(timepoints):
        r = cs.score_news2(tp.get("snapshot") or {})
        if r.computable:
            series.append({"hours": _num(tp.get("hours")) or 0.0, "news2": r.score})
    if len(series) < 2:
        return _insufficient(key, name, target, ref,
                             "Need ≥2 timepoints with a computable NEWS2.")

    first, last = series[0]["news2"], series[-1]["news2"]
    delta = last - first
    span = series[-1]["hours"] - series[0]["hours"]

    if delta >= 2:
        band = "high"
    elif delta == 1:
        band = "medium"
    elif delta <= -2:
        band = "low"
    else:
        band = "low-medium"

    traj = "rising" if delta > 0 else ("falling" if delta < 0 else "unchanged")
    tail = ("Rising score — deterioration; escalate and reassess." if delta >= 2
            else "Improving." if delta <= -2 else "Broadly stable; continue monitoring.")
    interp = f"NEWS2 {first}→{last} over {span:g} h (Δ{delta:+d}, {traj}). {tail}"

    comps = [{"name": f"NEWS2 @ {p['hours']:g}h", "value": p["news2"], "points": None}
             for p in series]
    return {
        "key": key, "name": name, "target": target, "value": delta, "band": band,
        "interpretation": interp, "components": comps, "reference": ref,
        "computable": True, "series": series,
    }


# ---------------------------------------------------------------------------
# Lactate clearance — resuscitation response
# ---------------------------------------------------------------------------
def lactate_clearance(timepoints: List[Dict]) -> Dict[str, Any]:
    key, name = "lactate_clearance", "Lactate Clearance"
    target = "Resuscitation response / sepsis mortality"
    ref = "Nguyen et al., Crit Care Med 2004;32:1637-1642; Surviving Sepsis Campaign"

    lacs = []
    for tp in _sorted(timepoints):
        val = _num((tp.get("snapshot") or {}).get("lactate"))
        if val is not None:
            lacs.append({"hours": _num(tp.get("hours")) or 0.0, "lactate": val})
    if len(lacs) < 2:
        return _insufficient(key, name, target, ref,
                             "Need ≥2 timepoints with a lactate measurement.")

    l0, lt = lacs[0]["lactate"], lacs[-1]["lactate"]
    if l0 <= 0:
        return _insufficient(key, name, target, ref, "Initial lactate must be > 0.")
    span = lacs[-1]["hours"] - lacs[0]["hours"]
    clearance = (l0 - lt) / l0 * 100.0

    if clearance >= 10:
        band, note = "low", "Adequate clearance (≥10%) — favorable."
    elif clearance >= 0:
        band, note = "medium", ("Inadequate clearance (<10%) — associated with higher "
                                "mortality; reassess resuscitation.")
    elif lt >= 4:
        band, note = "critical", "Rising lactate with hyperlactatemia — worsening perfusion; urgent review."
    else:
        band, note = "high", "Rising lactate — worsening perfusion; reassess."

    interp = (f"Lactate {l0:g}→{lt:g} mmol/L over {span:g} h = {clearance:.0f}% "
              f"clearance. {note}")
    comps = [{"name": f"Lactate @ {p['hours']:g}h", "value": p["lactate"], "points": None}
             for p in lacs]
    return {
        "key": key, "name": name, "target": target, "value": round(clearance, 1),
        "band": band, "interpretation": interp, "components": comps, "reference": ref,
        "computable": True, "series": lacs,
    }


_TRENDS = [news2_trend, lactate_clearance]


def assess_trends(timepoints: List[Dict]) -> Dict[str, Any]:
    """Run all trend analyses over a series of timepoints ({hours, snapshot})."""
    results = [fn(timepoints) for fn in _TRENDS]
    computed = [r for r in results if r["computable"]]

    overall = "low"
    for r in computed:
        if cs._BAND_RANK.get(r["band"], -1) > cs._BAND_RANK.get(overall, -1):
            overall = r["band"]

    hours = [h for h in (_num(t.get("hours")) for t in timepoints) if h is not None]
    span = (max(hours) - min(hours)) if len(hours) >= 2 else 0.0

    return {
        "engine_version": ENGINE_VERSION,
        "n_timepoints": len(timepoints),
        "hours_span": span,
        "overall_trend_risk": overall,
        "computed_count": len(computed),
        "total_trends": len(results),
        "trends": results,
        "disclaimer": cs.INTENDED_USE["not_for"],
    }
