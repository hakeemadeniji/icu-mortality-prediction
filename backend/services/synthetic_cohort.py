"""
Seeded synthetic ICU cohort with a transparent data-generating process (DGP).

Used to *functionally* validate the clinical scoring engine end-to-end: it is
fully reproducible (no external data — runs anywhere, including CI) and lets us
measure each score's discrimination (AUROC) and calibration.

Design (important for a fair, clinically-grounded test):
  - Real ICU mortality is driven by MULTI-ORGAN dysfunction, which is exactly why
    SOFA/APACHE/SAPS exist. So each patient has semi-independent organ-failure axes
    (cardiovascular, respiratory, renal, hepatic, coagulation, neuro, metabolic,
    infection), sharing a mild frailty term.
  - Each organ's physiology (vitals/labs) is generated from its axis with noise.
  - The mortality outcome depends on the total organ-failure BURDEN + age with
    independent noise — NOT on any score's output. So multi-organ scores that
    aggregate several axes should discriminate better than single-axis scores, as
    they do clinically; there is no circularity and no tuning to a target ranking.

This is a METHODOLOGY / functional benchmark, NOT clinical-validation evidence.
Real evidence requires a labeled real-world ICU cohort; the same runner accepts one.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def generate_cohort(n: int = 3000, seed: int = 42) -> Tuple[List[Dict], List[int]]:
    """Return (snapshots, outcomes). Snapshots use ClinicalSnapshot field names."""
    rng = np.random.default_rng(seed)

    def relu(x):
        return np.maximum(x, 0.0)

    age = np.clip(rng.normal(63, 16, n), 18, 95)

    # Semi-independent organ-failure axes (shared frailty + independent component).
    frailty = rng.normal(0, 0.7, n)

    def axis():
        return frailty + rng.normal(0, 0.9, n)

    cardio, resp, renal, hepatic = axis(), axis(), axis(), axis()
    coag, neuro, metab, infection = axis(), axis(), axis(), axis()

    # Cardiovascular
    hr = np.clip(82 + 12 * relu(cardio) + rng.normal(0, 8, n), 45, 185)
    sbp = np.clip(122 - 16 * relu(cardio) + rng.normal(0, 12, n), 60, 210)
    dbp = np.clip(sbp * 0.6 + rng.normal(0, 6, n), 30, 120)
    lactate = np.clip(1.1 + 1.4 * relu(cardio) + rng.normal(0, 0.5, n), 0.3, 15)
    vaso = (relu(cardio) + rng.normal(0, 0.5, n)) > 1.4

    # Respiratory
    spo2 = np.clip(98 - 5 * relu(resp) + rng.normal(0, 1.5, n), 70, 100)
    fio2 = np.clip(0.21 + 0.22 * relu(resp) + rng.normal(0, 0.03, n), 0.21, 1.0)
    pao2 = np.clip(96 - 15 * relu(resp) + rng.normal(0, 10, n), 40, 130)
    rr = np.clip(16 + 5 * relu(resp) + 2 * relu(cardio) + rng.normal(0, 2.5, n), 8, 45)
    paco2 = np.clip(40 - 3 * relu(resp) + rng.normal(0, 6, n), 20, 80)
    vent = (relu(resp) + rng.normal(0, 0.5, n)) > 1.3

    # Renal
    creatinine = np.clip(0.9 + 0.8 * relu(renal) + rng.normal(0, 0.3, n), 0.3, 12)
    baseline_cr = np.clip(0.9 + rng.normal(0, 0.15, n), 0.4, 2.0)
    bun = np.clip(creatinine * 18 + 10 * relu(renal) + rng.normal(0, 6, n), 4, 200)
    urine = np.clip(1600 - 500 * relu(renal) + rng.normal(0, 300, n), 40, 3000)
    potassium = np.clip(4.1 + 0.4 * relu(renal) + rng.normal(0, 0.4, n), 2.5, 7)

    # Hepatic / coagulation
    bilirubin = np.clip(0.6 + 0.9 * relu(hepatic) + rng.normal(0, 0.3, n), 0.1, 30)
    platelets = np.clip(255 - 50 * relu(coag) + rng.normal(0, 45, n), 5, 500)
    hct = np.clip(38 - 2 * relu(coag) + rng.normal(0, 4, n), 18, 55)

    # Neuro / metabolic / infection
    gcs = np.clip(np.round(15 - 3.5 * relu(neuro) + rng.normal(0, 1, n)), 3, 15)
    ph = np.clip(7.40 - 0.06 * relu(metab) + rng.normal(0, 0.03, n), 6.9, 7.6)
    bicarb = np.clip(24 - 3 * relu(metab) + rng.normal(0, 2.5, n), 8, 38)
    temp = np.clip(37.0 + 0.7 * relu(infection) + rng.normal(0, 0.5, n), 34, 41.5)
    wbc = np.clip(9 + 5 * relu(infection) + rng.normal(0, 3, n), 0.5, 45)
    sodium = np.clip(139 + 3 * metab + rng.normal(0, 3, n), 120, 160)

    metastatic = rng.random(n) < 0.05
    heme = rng.random(n) < 0.03
    aids = rng.random(n) < 0.01

    # TRUE outcome model: total organ-failure burden (SOFA-like) + age + noise.
    burden = (relu(cardio) + relu(resp) + relu(renal) + relu(hepatic)
              + relu(coag) + relu(neuro) + relu(metab))
    logit = -3.8 + 0.55 * burden + 0.03 * (age - 60) + rng.normal(0, 0.4, n)
    p = 1.0 / (1.0 + np.exp(-logit))
    y = (rng.random(n) < p).astype(int)

    cohort: List[Dict] = []
    for i in range(n):
        cohort.append({
            "age": float(age[i]),
            "sex": "M" if rng_bit(age[i]) else "F",
            "heart_rate": float(hr[i]),
            "resp_rate": float(rr[i]),
            "sbp": float(sbp[i]),
            "dbp": float(dbp[i]),
            "temperature": float(temp[i]),
            "spo2": float(spo2[i]),
            "fio2": float(fio2[i]),
            "on_supplemental_o2": bool(fio2[i] > 0.24),
            "gcs": int(gcs[i]),
            "confusion": bool(gcs[i] < 14),
            "mechanical_ventilation": bool(vent[i]),
            "vasopressors": bool(vaso[i]),
            "wbc": float(wbc[i]),
            "platelets": float(platelets[i]),
            "bilirubin": float(bilirubin[i]),
            "creatinine": float(creatinine[i]),
            "baseline_creatinine": float(baseline_cr[i]),
            "bun": float(bun[i]),
            "lactate": float(lactate[i]),
            "pao2": float(pao2[i]),
            "paco2": float(paco2[i]),
            "arterial_ph": float(ph[i]),
            "sodium": float(sodium[i]),
            "potassium": float(potassium[i]),
            "bicarbonate": float(bicarb[i]),
            "hematocrit": float(hct[i]),
            "urine_output_ml": float(urine[i]),
            "admission_type": "medical",
            "metastatic_cancer": bool(metastatic[i]),
            "hematologic_malignancy": bool(heme[i]),
            "aids": bool(aids[i]),
        })
    return cohort, [int(v) for v in y]


def rng_bit(x: float) -> bool:
    """Deterministic pseudo-bit from a float (sex assignment only)."""
    return int(x * 100) % 2 == 0
