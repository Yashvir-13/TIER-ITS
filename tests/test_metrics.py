import pytest
from evaluation.metrics import (
    compute_classification_metrics,
    compute_evidence_metrics,
    compute_correction_metrics,
    paired_bootstrap_ci
)

def test_classification_metrics_perfect():
    y_true = [True, True, False, False]
    y_pred = [True, True, False, False]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics.accuracy == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.specificity == 1.0
    assert metrics.f1 == 1.0

def test_classification_metrics_with_errors():
    y_true = [True, True, False, False]
    y_pred = [True, False, True, False]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics.tp == 1
    assert metrics.fn == 1
    assert metrics.fp == 1
    assert metrics.tn == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5

def test_evidence_metrics():
    retrieved = [[5, 6], [10], []]
    gt = [[5], [10, 11], []]
    metrics = compute_evidence_metrics(retrieved, gt)
    assert metrics.precision > 0.0
    assert metrics.recall > 0.0
    assert metrics.exact_match > 0.0

def test_correction_metrics():
    # 2 resolution cases (False in is_non_corr), 2 non-correction controls (True in is_non_corr)
    is_non_corr = [False, False, True, True]
    ledger_invalidated = [True, True, False, False]  # Perfect invalidation
    active_risk_reported = [False, False, True, True]
    
    metrics = compute_correction_metrics(is_non_corr, ledger_invalidated, active_risk_reported)
    assert metrics.total_correction_cases == 2
    assert metrics.resolution_fidelity == 1.0
    assert metrics.total_control_cases == 2
    assert metrics.false_resolution_rate == 0.0
    assert metrics.active_risk_f1 == 1.0

def test_paired_bootstrap_ci():
    scores_a = [1.0, 1.0, 1.0, 0.9, 1.0]
    scores_b = [0.5, 0.6, 0.4, 0.5, 0.5]
    res = paired_bootstrap_ci(scores_a, scores_b, n_resamples=500, seed=42)
    assert res.mean_diff > 0.4
    assert res.ci_lower > 0.3
    assert res.ci_upper > res.ci_lower
