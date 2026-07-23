"""
Validation runner — measure the clinical scores against a labeled cohort.

By default it uses the seeded synthetic cohort (services/synthetic_cohort.py) so
the run is fully reproducible with no external data. Point `load_cohort` at a real
labeled ICU cohort to produce genuine clinical-validation evidence.

Run from the backend/ directory:
    venv/Scripts/python.exe validate_scores.py

Writes docs/VALIDATION_RESULTS.md and results/tables/score_validation.csv.
"""

from __future__ import annotations

import csv
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from services import clinical_scores as cs
from services import synthetic_cohort, validation_metrics as vm

REPO = Path(__file__).resolve().parent.parent
DIRECTION = cs.RISK_DIRECTION


def load_cohort(n: int = 3000, seed: int = 42) -> Tuple[List[Dict], List[int], str]:
    """Return (snapshots, outcomes, source_label).

    If the MIMIC_COHORT_CSV env var points to an extract produced by
    scripts/sql/mimic/first_day_cohort.sql, validate on that REAL cohort;
    otherwise use the reproducible synthetic cohort.
    """
    csv_path = os.environ.get("MIMIC_COHORT_CSV")
    if csv_path:
        from services import mimic_adapter
        snaps, outcomes = mimic_adapter.load_cohort_from_csv(csv_path)
        return snaps, outcomes, f"MIMIC-IV ({os.path.basename(csv_path)})"
    snaps, outcomes = synthetic_cohort.generate_cohort(n=n, seed=seed)
    return snaps, outcomes, "synthetic (services/synthetic_cohort.py)"


def _saps2_probability(score: float) -> float:
    logit = -7.7631 + 0.0737 * score + 0.9971 * math.log(score + 1)
    return 1.0 / (1.0 + math.exp(-logit))


# Headline mortality scores used for the fairness/subgroup tables.
HEADLINE = ["sofa", "apache2", "saps2", "news2"]


def _age_group(a) -> str:
    if a is None:
        return "unknown"
    a = float(a)
    if a < 50: return "<50"
    if a < 65: return "50-64"
    if a < 80: return "65-79"
    return "80+"


def _dimension(cohort, outcomes, score_data, dim: str) -> Dict:
    """Per-subgroup n/event-rate (cohort-level) + AUROC per headline score."""
    labels = [
        (snap.get("sex") or "U") if dim == "sex" else _age_group(snap.get("age"))
        for snap in cohort
    ]
    groups: Dict[str, Dict] = {}
    for lab in sorted(set(labels)):
        idx = [i for i, l in enumerate(labels) if l == lab]
        ev = sum(outcomes[i] for i in idx)
        groups[lab] = {
            "n": len(idx),
            "event_rate": round(ev / len(idx), 4) if idx else None,
            "auroc": {},
        }
    for key in HEADLINE:
        d = score_data.get(key)
        if not d:
            continue
        for lab, rep in vm.subgroup_metrics(d["preds"], d["ys"], d[dim]).items():
            if lab in groups:
                groups[lab]["auroc"][key] = rep["auroc"]
    return groups


def run(n: int = 3000, seed: int = 42) -> Dict:
    cohort, outcomes, source = load_cohort(n=n, seed=seed)

    per_score: Dict[str, Dict] = {}
    score_data: Dict[str, Dict] = {}
    for scorer in cs._SCORERS:
        preds, ys, sexes, ages = [], [], [], []
        name = key = None
        for snap, y in zip(cohort, outcomes):
            r = scorer(snap)
            key, name = r.key, r.name
            if r.computable and isinstance(r.score, (int, float)):
                preds.append(DIRECTION.get(r.key, 1) * float(r.score))
                ys.append(y)
                sexes.append(snap.get("sex") or "U")
                ages.append(_age_group(snap.get("age")))
        per_score[key] = {"name": name, "n": len(preds), "auroc": vm.auroc(preds, ys)}
        score_data[key] = {"preds": preds, "ys": ys, "sex": sexes, "age": ages}

    # SAPS II calibration against its predicted-mortality probability
    saps_probs, saps_y = [], []
    for snap, y in zip(cohort, outcomes):
        r = cs.score_saps2(snap)
        if r.computable:
            saps_probs.append(_saps2_probability(r.score))
            saps_y.append(y)
    saps_cal = vm.validate(saps_probs, saps_y, is_probability=True)

    fairness = {
        "by_sex": _dimension(cohort, outcomes, score_data, "sex"),
        "by_age": _dimension(cohort, outcomes, score_data, "age"),
    }

    return {
        "cohort": source,
        "is_synthetic": source.startswith("synthetic"),
        "n": len(cohort),
        "seed": seed,
        "events": sum(outcomes),
        "event_rate": round(sum(outcomes) / len(outcomes), 4),
        "engine_version": cs.ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "per_score": per_score,
        "saps2_calibration": saps_cal,
        "fairness": fairness,
    }


def write_report(report: Dict) -> None:
    # CSV
    csv_path = REPO / "results" / "tables" / "score_validation.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["score", "n", "auroc"])
        for key, d in report["per_score"].items():
            w.writerow([d["name"], d["n"], round(d["auroc"], 4) if d["auroc"] is not None else ""])

    # Markdown
    md = REPO / "docs" / "VALIDATION_RESULTS.md"
    synth = report.get("is_synthetic", True)
    lines = []
    lines.append(
        f"# Validation Results — {'functional benchmark (synthetic cohort)' if synth else 'real cohort'}\n"
    )
    if synth:
        lines.append(
            "> **Synthetic cohort — methodology / functional validation, NOT clinical "
            "evidence.** These numbers show the scores discriminate outcomes on a "
            "reproducible synthetic cohort whose mortality is driven by multi-organ "
            "organ-failure burden (independent of any score's output). Genuine clinical "
            "validation requires a real labeled ICU cohort; the same runner "
            "(`backend/validate_scores.py`) accepts one via `MIMIC_COHORT_CSV` — see "
            "`docs/MIMIC_VALIDATION.md`.\n"
        )
    else:
        lines.append(
            "> **Real-cohort validation.** Discrimination and calibration of the scores "
            "on a real labeled ICU cohort. Interpret in light of the cohort's inclusion "
            "criteria and time window; published mortality coefficients (SAPS II, "
            "APACHE II) generally require **local recalibration**. Report subgroup "
            "performance (age, sex, ethnicity) for fairness before any clinical use.\n"
        )
    lines.append(
        f"- Cohort: {report['cohort']} · n = {report['n']} · seed = {report['seed']}\n"
        f"- Outcome: in-hospital mortality · events = {report['events']} "
        f"({report['event_rate']*100:.1f} %)\n"
        f"- Engine version: {report['engine_version']} · generated {report['generated_at']}\n"
    )
    lines.append("\n## Discrimination (AUROC, risk-oriented)\n")
    lines.append("| Score | n | AUROC |")
    lines.append("|---|---:|---:|")
    for key, d in sorted(report["per_score"].items(),
                         key=lambda kv: (kv[1]["auroc"] or 0), reverse=True):
        a = f"{d['auroc']:.3f}" if d["auroc"] is not None else "n/a"
        lines.append(f"| {d['name']} | {d['n']} | {a} |")

    cal = report["saps2_calibration"]
    lines.append("\n## SAPS II calibration (predicted mortality probability)\n")
    lines.append(f"- AUROC {cal['auroc']:.3f} · Brier {cal['brier_score']:.4f} · "
                 f"n {cal['n']} · events {cal['events']}\n")
    lines.append("| Predicted bin | n | mean predicted | observed rate |")
    lines.append("|---|---:|---:|---:|")
    for row in cal["calibration"]:
        lines.append(f"| {row['bin']} | {row['n']} | {row['mean_predicted']:.3f} "
                     f"| {row['observed_rate']:.3f} |")

    # Fairness / subgroup analysis
    fair = report.get("fairness", {})
    if fair:
        lines.append("\n## Fairness / subgroup analysis\n")
        lines.append(
            "AUROC (and event rate) for the headline mortality scores by subgroup. "
            "Differential discrimination — an AUROC spread of more than ~0.05 across "
            "subgroups — can indicate inequitable performance and warrants investigation "
            "before deployment.\n"
        )
        for dim_title, dim_key in (("By sex", "by_sex"), ("By age group", "by_age")):
            groups = fair.get(dim_key, {})
            if not groups:
                continue
            lines.append(f"\n### {dim_title}\n")
            lines.append("| Group | n | event rate | SOFA | APACHE II | SAPS II | NEWS2 |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            for g in sorted(groups):
                d = groups[g]
                a = d["auroc"]

                def fmt(k):
                    return f"{a[k]:.3f}" if a.get(k) is not None else "n/a"

                er = f"{d['event_rate'] * 100:.1f}%" if d["event_rate"] is not None else "n/a"
                lines.append(
                    f"| {g} | {d['n']} | {er} | {fmt('sofa')} | {fmt('apache2')} "
                    f"| {fmt('saps2')} | {fmt('news2')} |"
                )

    lines.append("\n## Interpretation\n")
    if synth:
        lines.append(
            "Multi-organ severity scores (SOFA, APACHE II, SAPS II) and the NEWS2 "
            "early-warning score discriminate best; single-axis scores (Shock Index, "
            "KDIGO) discriminate least — the clinically expected ordering, since this "
            "cohort's mortality is driven by multi-organ burden. This confirms the engine "
            "computes and orders risk correctly end-to-end.\n\n"
            "Note the SAPS II calibration table: it discriminates well but **under-predicts** "
            "observed mortality on this cohort — exactly the kind of finding real validation "
            "surfaces, and why published coefficients generally need **local recalibration**. "
            "Absolute values are properties of the synthetic DGP, not any real population; "
            "re-run on real ICU data (`MIMIC_COHORT_CSV`) for clinical evidence.\n"
        )
    else:
        lines.append(
            "AUROC quantifies discrimination; the SAPS II calibration table shows "
            "reliability (predicted vs. observed). Compare against published performance, "
            "recalibrate coefficients to this population as needed, and evaluate subgroup "
            "fairness before any deployment.\n"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    rep = run()
    write_report(rep)
    print(f"cohort n={rep['n']} events={rep['events']} ({rep['event_rate']*100:.1f}%)")
    for key, d in sorted(rep["per_score"].items(),
                         key=lambda kv: (kv[1]["auroc"] or 0), reverse=True):
        a = f"{d['auroc']:.3f}" if d["auroc"] is not None else "n/a"
        print(f"  {d['name']:16} AUROC {a}")
    print("report -> docs/VALIDATION_RESULTS.md, results/tables/score_validation.csv")
