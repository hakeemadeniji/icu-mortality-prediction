"""Tests for the clinical-validation metrics harness (AUROC / Brier / calibration)."""

import math

from services import validation_metrics as vm


def test_auroc_perfect_separation():
    assert vm.auroc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0


def test_auroc_reversed():
    assert vm.auroc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) == 0.0


def test_auroc_known_example():
    # Classic worked example -> AUROC 0.75
    assert math.isclose(vm.auroc([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1]), 0.75, abs_tol=1e-9)


def test_auroc_all_tied_is_half():
    assert vm.auroc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5


def test_auroc_none_when_single_class():
    assert vm.auroc([0.2, 0.4, 0.6], [1, 1, 1]) is None


def test_brier_perfect_and_worst():
    assert vm.brier_score([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1]) == 0.0
    assert vm.brier_score([0.5, 0.5], [0, 1]) == 0.25


def test_calibration_table_bins():
    probs = [0.05, 0.15, 0.85, 0.95]
    outcomes = [0, 0, 1, 1]
    table = vm.calibration_table(probs, outcomes, bins=10)
    # Two populated bins (low and high); observed rates 0 and 1
    assert {row["observed_rate"] for row in table} == {0.0, 1.0}


def test_validate_report_shape():
    rep = vm.validate([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1], is_probability=True)
    assert rep["n"] == 4 and rep["events"] == 2
    assert math.isclose(rep["auroc"], 0.75, abs_tol=1e-9)
    assert "brier_score" in rep and "calibration" in rep


def test_length_mismatch_raises():
    try:
        vm.auroc([0.1, 0.2], [1])
        assert False, "expected ValueError"
    except ValueError:
        pass
