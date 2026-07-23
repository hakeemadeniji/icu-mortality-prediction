"""
MIMIC-IV → cohort adapter.

Turns the flat per-ICU-stay CSV produced by
`scripts/sql/mimic/first_day_cohort.sql` into `(snapshots, outcomes)` matching the
clinical engine's `ClinicalSnapshot` field names — the exact shape the validation
harness (`validate_scores`) consumes. See `docs/MIMIC_VALIDATION.md`.

The CSV column names are the SQL SELECT *aliases* (this module's stable contract).
If your MIMIC derived-schema column names differ, adjust the SQL's source columns —
the output aliases (and therefore this adapter) stay the same.

This module is dependency-light (stdlib `csv`) and unit-tested against a mock CSV,
so it is verified even without MIMIC access.
"""

from __future__ import annotations

import csv
from typing import Any, Dict, List, Optional, Tuple


def _f(row: Dict[str, str], col: str) -> Optional[float]:
    """Parse a numeric cell → float, or None for missing/blank/NA."""
    v = row.get(col)
    if v is None:
        return None
    v = str(v).strip()
    if v == "" or v.upper() in {"NA", "NAN", "NULL", "NONE"}:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _ethnicity_group(raw: Optional[str]) -> str:
    """Normalize MIMIC `race` free-text into a coarse fairness subgroup."""
    if not raw:
        return "Unknown"
    r = str(raw).upper()
    if "WHITE" in r:
        return "White"
    if "BLACK" in r or "AFRICAN" in r:
        return "Black"
    if "HISPANIC" in r or "LATINO" in r:
        return "Hispanic"
    if "ASIAN" in r:
        return "Asian"
    if any(t in r for t in ("UNKNOWN", "UNABLE", "DECLINED", "NOT SPECIFIED", "PATIENT DECLINED")):
        return "Unknown"
    return "Other"


def _worst_deviation(a: Optional[float], b: Optional[float], center: float) -> Optional[float]:
    """Of two candidate values, return the one furthest from a physiologic center
    (used for parameters that are abnormal in both directions: temp, Na, K)."""
    vals = [x for x in (a, b) if x is not None]
    if not vals:
        return None
    return max(vals, key=lambda x: abs(x - center))


def snapshot_from_row(row: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Map one CSV row → (ClinicalSnapshot dict, outcome 0/1).

    First-24h values are already reduced to the risk-relevant extreme in SQL
    (e.g. sbp_min, heart_rate_max). Bidirectional parameters (temperature, sodium,
    potassium) carry min+max and the worse deviation is chosen here.
    """
    temp = _worst_deviation(_f(row, "temperature_min"), _f(row, "temperature_max"), 37.0)
    sodium = _worst_deviation(_f(row, "sodium_min"), _f(row, "sodium_max"), 140.0)
    potassium = _worst_deviation(_f(row, "potassium_min"), _f(row, "potassium_max"), 4.5)
    gcs = _f(row, "gcs_min")

    fio2 = _f(row, "fio2_max")
    if fio2 is not None and fio2 > 1.0:   # MIMIC stores FiO2 as a percent
        fio2 = fio2 / 100.0
    on_o2 = fio2 is not None and fio2 > 0.24

    vent = (_f(row, "vent_flag") or 0) >= 1
    gender = (str(row.get("gender") or "").strip().upper()[:1]) or None

    snap: Dict[str, Any] = {
        "age": _f(row, "age"),
        "sex": gender,
        "ethnicity": _ethnicity_group(row.get("race")),
        "heart_rate": _f(row, "heart_rate_max"),
        "resp_rate": _f(row, "resp_rate_max"),
        "sbp": _f(row, "sbp_min"),
        "dbp": _f(row, "dbp_min"),
        "map": _f(row, "mbp_min"),
        "temperature": temp,
        "spo2": _f(row, "spo2_min"),
        "fio2": fio2,
        "on_supplemental_o2": on_o2,
        "gcs": gcs,
        "confusion": gcs is not None and gcs < 14,
        "mechanical_ventilation": vent,
        "wbc": _f(row, "wbc_max"),
        "platelets": _f(row, "platelets_min"),
        "bilirubin": _f(row, "bilirubin_max"),
        "creatinine": _f(row, "creatinine_max"),
        "bun": _f(row, "bun_max"),
        "sodium": sodium,
        "potassium": potassium,
        "bicarbonate": _f(row, "bicarbonate_min"),
        "hematocrit": _f(row, "hematocrit_min"),
        "pao2": _f(row, "po2_min"),
        "paco2": _f(row, "pco2_max"),
        "arterial_ph": _f(row, "ph_min"),
        "lactate": _f(row, "lactate_max"),
        "urine_output_ml": _f(row, "urineoutput"),
        # SAPS II admission type is not mapped from MIMIC by default (nuanced);
        # defaults to 'medical'. Refine in SQL if you have surgical-service info.
        "admission_type": "medical",
    }

    mortality = _f(row, "mortality")
    outcome = int(mortality) if mortality is not None else 0
    return snap, outcome


def load_cohort_from_csv(path: str) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Load the MIMIC extract CSV → (snapshots, outcomes)."""
    snapshots: List[Dict[str, Any]] = []
    outcomes: List[int] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            snap, outcome = snapshot_from_row(row)
            snapshots.append(snap)
            outcomes.append(outcome)
    if not snapshots:
        raise ValueError(f"No rows loaded from {path}")
    return snapshots, outcomes
