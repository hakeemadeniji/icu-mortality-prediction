"""
End-to-end functional-validation tests on the seeded synthetic cohort.

These both guard against regressions and demonstrate that the scores discriminate
outcomes (AUROC well above chance), with multi-organ severity scores leading — the
clinically expected ordering. Deterministic (fixed seed).
"""

from services import clinical_scores as cs
from services import synthetic_cohort as sc
from services import validation_metrics as vm


def _all_auroc(cohort, outcomes):
    out = {}
    for fn in cs._SCORERS:
        preds, ys, key = [], [], None
        for snap, o in zip(cohort, outcomes):
            r = fn(snap)
            key = r.key
            if r.computable and isinstance(r.score, (int, float)):
                preds.append(cs.RISK_DIRECTION.get(r.key, 1) * float(r.score))
                ys.append(o)
        out[key] = vm.auroc(preds, ys)
    return out


def test_cohort_is_deterministic():
    c1, y1 = sc.generate_cohort(n=400, seed=3)
    c2, y2 = sc.generate_cohort(n=400, seed=3)
    assert c1 == c2 and y1 == y2


def test_event_rate_is_plausible():
    _, y = sc.generate_cohort(n=2500, seed=42)
    rate = sum(y) / len(y)
    assert 0.08 < rate < 0.40, rate


def test_all_scores_discriminate():
    cohort, y = sc.generate_cohort(n=2500, seed=42)
    a = _all_auroc(cohort, y)
    # Every score does better than chance by a clear margin.
    assert all(v is not None and v > 0.58 for v in a.values()), a


def test_multiorgan_scores_lead():
    cohort, y = sc.generate_cohort(n=2500, seed=42)
    a = _all_auroc(cohort, y)
    # Multi-organ severity scores are the strongest discriminators.
    assert a["sofa"] > 0.72
    assert a["apache2"] > 0.70
    assert a["saps2"] > 0.70
    assert a["sofa"] > a["shock_index"]  # multi-organ beats single-axis
