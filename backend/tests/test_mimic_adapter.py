"""
Tests for the MIMIC-IV adapter against a mock extract CSV.

Verifies the column mapping, unit normalization, worst-deviation selection and
outcome parsing without needing real MIMIC access, so the adapter is trustworthy
the moment a real extract is produced.
"""

import csv

from services import clinical_scores as cs
from services import mimic_adapter as ma

COLUMNS = [
    "age", "gender", "mortality", "heart_rate_max", "sbp_min", "dbp_min", "mbp_min",
    "resp_rate_max", "temperature_min", "temperature_max", "spo2_min", "gcs_min",
    "wbc_max", "platelets_min", "bilirubin_max", "creatinine_max", "bun_max",
    "sodium_min", "sodium_max", "potassium_min", "potassium_max", "bicarbonate_min",
    "hematocrit_min", "po2_min", "pco2_max", "ph_min", "lactate_max", "fio2_max",
    "urineoutput", "vent_flag",
]

SICK = {
    "age": 72, "gender": "M", "mortality": 1, "heart_rate_max": 130, "sbp_min": 82,
    "dbp_min": 48, "mbp_min": 60, "resp_rate_max": 30, "temperature_min": 35.2,
    "temperature_max": 39.4, "spo2_min": 88, "gcs_min": 11, "wbc_max": 18,
    "platelets_min": 90, "bilirubin_max": 2.4, "creatinine_max": 3.1, "bun_max": 40,
    "sodium_min": 132, "sodium_max": 149, "potassium_min": 3.2, "potassium_max": 5.6,
    "bicarbonate_min": 16, "hematocrit_min": 28, "po2_min": 68, "pco2_max": 52,
    "ph_min": 7.28, "lactate_max": 4.2, "fio2_max": 60, "urineoutput": 400, "vent_flag": 1,
}
WELL = {
    "age": 55, "gender": "F", "mortality": 0, "heart_rate_max": 88, "sbp_min": 118,
    "dbp_min": 70, "mbp_min": 86, "resp_rate_max": 18, "temperature_min": 36.6,
    "temperature_max": 37.2, "spo2_min": 97, "gcs_min": 15, "wbc_max": 8,
    "platelets_min": 240, "bilirubin_max": 0.6, "creatinine_max": 0.9, "bun_max": 14,
    "sodium_min": 138, "sodium_max": 141, "potassium_min": 4.0, "potassium_max": 4.4,
    "bicarbonate_min": 24, "hematocrit_min": 40, "po2_min": "", "pco2_max": "",
    "ph_min": "", "lactate_max": "", "fio2_max": 21, "urineoutput": 1800, "vent_flag": 0,
}


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_adapter_maps_and_normalizes(tmp_path):
    p = tmp_path / "cohort.csv"
    _write_csv(p, [SICK, WELL])
    snaps, outcomes = ma.load_cohort_from_csv(str(p))

    assert outcomes == [1, 0]
    s0, s1 = snaps

    # Direct column mapping (risk-relevant extreme already chosen in SQL)
    assert s0["heart_rate"] == 130 and s0["sbp"] == 82 and s0["map"] == 60
    assert s0["spo2"] == 88 and s0["gcs"] == 11 and s0["creatinine"] == 3.1
    assert s0["pao2"] == 68 and s0["arterial_ph"] == 7.28 and s0["lactate"] == 4.2
    assert s0["sex"] == "M"

    # Worst-deviation selection for bidirectional parameters
    assert s0["temperature"] == 39.4     # |39.4-37| > |35.2-37|
    assert s0["sodium"] == 149           # |149-140| > |132-140|
    assert s0["potassium"] == 3.2        # |3.2-4.5| > |5.6-4.5|

    # FiO2 percent -> fraction, and derived flags
    assert abs(s0["fio2"] - 0.60) < 1e-9
    assert s0["on_supplemental_o2"] is True
    assert s0["confusion"] is True       # GCS 11 < 14
    assert s0["mechanical_ventilation"] is True

    # Well patient: room air, no vent/confusion, missing labs -> None
    assert abs(s1["fio2"] - 0.21) < 1e-9
    assert s1["on_supplemental_o2"] is False
    assert s1["confusion"] is False and s1["mechanical_ventilation"] is False
    assert s1["pao2"] is None and s1["lactate"] is None


def test_adapter_output_feeds_the_engine(tmp_path):
    p = tmp_path / "cohort.csv"
    _write_csv(p, [SICK])
    snaps, _ = ma.load_cohort_from_csv(str(p))
    result = cs.assess(snaps[0])
    # A rich snapshot should compute the full panel including the mortality scores.
    keys = {s["key"] for s in result["scores"] if s["computable"]}
    assert {"news2", "sofa", "apache2", "saps2"}.issubset(keys)


def test_empty_csv_raises(tmp_path):
    p = tmp_path / "empty.csv"
    _write_csv(p, [])
    try:
        ma.load_cohort_from_csv(str(p))
        assert False, "expected ValueError"
    except ValueError:
        pass
