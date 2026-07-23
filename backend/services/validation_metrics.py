"""
Clinical-validation metrics — discrimination & calibration of a score/probability
against observed binary outcomes (e.g. in-hospital mortality).

This is the tooling to *validate* a score on a labeled cohort: point it at
(predictions, outcomes) and it reports AUROC (discrimination), the Brier score and
a calibration table (reliability). Dependency-light (pure Python) and fully
deterministic so it is itself unit-tested.

Establishing that a score discriminates and is well-calibrated *on the target
population* is the core of clinical validation; run this against real ICU outcome
data to produce that evidence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


def _clean(preds: Sequence[float], outcomes: Sequence[int]):
    if len(preds) != len(outcomes):
        raise ValueError("preds and outcomes must be the same length")
    xs, ys = [], []
    for p, o in zip(preds, outcomes):
        if p is None or o is None:
            continue
        xs.append(float(p))
        ys.append(int(o))
    return xs, ys


def auroc(preds: Sequence[float], outcomes: Sequence[int]) -> Optional[float]:
    """Area under the ROC curve via the Mann–Whitney U statistic (tie-corrected).

    Interpretable for any monotonic score (need not be a probability). Returns
    None if there are not both positive and negative outcomes.
    """
    xs, ys = _clean(preds, outcomes)
    n_pos = sum(ys)
    n_neg = len(ys) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None

    # Average ranks (1-based), ties share the mean rank.
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0  # mean of 1-based ranks in the tie block
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1

    sum_ranks_pos = sum(ranks[i] for i in range(len(xs)) if ys[i] == 1)
    u = sum_ranks_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def brier_score(probs: Sequence[float], outcomes: Sequence[int]) -> Optional[float]:
    """Mean squared error between predicted probabilities and outcomes (0=best)."""
    xs, ys = _clean(probs, outcomes)
    if not xs:
        return None
    return sum((p - y) ** 2 for p, y in zip(xs, ys)) / len(xs)


def calibration_table(probs: Sequence[float], outcomes: Sequence[int],
                      bins: int = 10) -> List[Dict[str, Any]]:
    """Reliability table: predicted vs. observed event rate per probability bin."""
    xs, ys = _clean(probs, outcomes)
    table = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(xs) if (p >= lo and (p < hi or (b == bins - 1 and p <= hi)))]
        if not idx:
            continue
        n = len(idx)
        mean_pred = sum(xs[i] for i in idx) / n
        obs_rate = sum(ys[i] for i in idx) / n
        table.append({
            "bin": f"{lo:.1f}-{hi:.1f}",
            "n": n,
            "mean_predicted": round(mean_pred, 4),
            "observed_rate": round(obs_rate, 4),
        })
    return table


def validate(preds: Sequence[float], outcomes: Sequence[int],
             is_probability: bool = False, bins: int = 10) -> Dict[str, Any]:
    """Summary validation report for a score/probability against outcomes."""
    xs, ys = _clean(preds, outcomes)
    n = len(xs)
    events = sum(ys)
    report: Dict[str, Any] = {
        "n": n,
        "events": events,
        "event_rate": round(events / n, 4) if n else None,
        "auroc": auroc(xs, ys),
    }
    if is_probability:
        report["brier_score"] = brier_score(xs, ys)
        report["calibration"] = calibration_table(xs, ys, bins=bins)
    return report
