import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from pydantic import BaseModel, Field

class ClassificationMetrics(BaseModel):
    tp: int
    fp: int
    tn: int
    fn: int
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1: float

class EvidenceMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    exact_match: float

class CorrectionMetrics(BaseModel):
    total_correction_cases: int
    resolution_fidelity: float  # Correctly invalidated / total correction cases
    total_control_cases: int
    false_resolution_rate: float  # Mistakenly invalidated / total control cases
    active_risk_f1: float

class BootstrapResult(BaseModel):
    mean_diff: float
    ci_lower: float
    ci_upper: float
    p_value: float

def compute_classification_metrics(y_true: List[bool], y_pred: List[bool]) -> ClassificationMetrics:
    """
    Computes confusion matrix and metrics: Precision, Recall, Specificity, F1, Accuracy.
    """
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
    
    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return ClassificationMetrics(
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        accuracy=round(accuracy, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        specificity=round(specificity, 4),
        f1=round(f1, 4)
    )

def compute_evidence_metrics(
    retrieved_turns_list: List[List[int]], 
    ground_truth_turns_list: List[List[int]]
) -> EvidenceMetrics:
    """
    Computes turn-level evidence precision, recall, and exact match across cases.
    """
    precisions = []
    recalls = []
    exact_matches = []
    
    for retrieved, gt in zip(retrieved_turns_list, ground_truth_turns_list):
        ret_set = set(retrieved)
        gt_set = set(gt)
        
        if not gt_set:
            # Negative case (no ground truth evidence)
            if not ret_set:
                precisions.append(1.0)
                recalls.append(1.0)
                exact_matches.append(1.0)
            else:
                precisions.append(0.0)
                recalls.append(1.0)
                exact_matches.append(0.0)
            continue
            
        if not ret_set:
            precisions.append(0.0)
            recalls.append(0.0)
            exact_matches.append(0.0)
            continue
            
        intersection = ret_set.intersection(gt_set)
        p = len(intersection) / len(ret_set)
        r = len(intersection) / len(gt_set)
        em = 1.0 if ret_set == gt_set else 0.0
        
        precisions.append(p)
        recalls.append(r)
        exact_matches.append(em)
        
    mean_p = float(np.mean(precisions)) if precisions else 0.0
    mean_r = float(np.mean(recalls)) if recalls else 0.0
    mean_em = float(np.mean(exact_matches)) if exact_matches else 0.0
    f1 = (2 * mean_p * mean_r) / (mean_p + mean_r) if (mean_p + mean_r) > 0 else 0.0
    
    return EvidenceMetrics(
        precision=round(mean_p, 4),
        recall=round(mean_r, 4),
        f1=round(f1, 4),
        exact_match=round(mean_em, 4)
    )

def compute_correction_metrics(
    is_non_correction: List[bool],
    ledger_invalidated: List[bool],
    active_risk_reported: List[bool]
) -> CorrectionMetrics:
    """
    Computes correction fidelity and false resolution rate:
    - Resolution Fidelity: proportion of resolution cases correctly marked invalidated.
    - False Resolution Rate: proportion of non-correction controls mistakenly marked invalidated.
    """
    # Resolution cases
    corr_indices = [i for i, is_ctrl in enumerate(is_non_correction) if not is_ctrl]
    corr_invalidated = sum(1 for i in corr_indices if ledger_invalidated[i])
    res_fidelity = corr_invalidated / len(corr_indices) if corr_indices else 0.0
    
    # Non-correction control cases
    ctrl_indices = [i for i, is_ctrl in enumerate(is_non_correction) if is_ctrl]
    ctrl_invalidated = sum(1 for i in ctrl_indices if ledger_invalidated[i])
    false_res_rate = ctrl_invalidated / len(ctrl_indices) if ctrl_indices else 0.0
    
    # Active risk F1 (ground truth: True for controls, False for resolutions)
    y_true_active = [is_ctrl for is_ctrl in is_non_correction]
    cls_metrics = compute_classification_metrics(y_true_active, active_risk_reported)
    
    return CorrectionMetrics(
        total_correction_cases=len(corr_indices),
        resolution_fidelity=round(res_fidelity, 4),
        total_control_cases=len(ctrl_indices),
        false_resolution_rate=round(false_res_rate, 4),
        active_risk_f1=cls_metrics.f1
    )

def paired_bootstrap_ci(
    scores_a: List[float], 
    scores_b: List[float], 
    n_resamples: int = 1000, 
    alpha: float = 0.05,
    seed: int = 42
) -> BootstrapResult:
    """
    Computes paired difference (A - B) and 95% bootstrap confidence interval (Efron & Tibshirani 1993).
    """
    np.random.seed(seed)
    a = np.array(scores_a, dtype=float)
    b = np.array(scores_b, dtype=float)
    diff = a - b
    mean_diff = float(np.mean(diff))
    
    n = len(diff)
    if n == 0:
        return BootstrapResult(mean_diff=0.0, ci_lower=0.0, ci_upper=0.0, p_value=1.0)
        
    boot_means = np.empty(n_resamples)
    for i in range(n_resamples):
        indices = np.random.randint(0, n, size=n)
        boot_means[i] = np.mean(diff[indices])
        
    ci_lower = float(np.percentile(boot_means, (alpha / 2.0) * 100))
    ci_upper = float(np.percentile(boot_means, (1.0 - alpha / 2.0) * 100))
    
    # Two-sided empirical p-value for null hypothesis H0: diff == 0
    p_val = float(2.0 * min(np.mean(boot_means <= 0), np.mean(boot_means >= 0)))
    p_val = min(1.0, max(0.0, p_val))
    
    return BootstrapResult(
        mean_diff=round(mean_diff, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        p_value=round(p_val, 4)
    )

def cluster_bootstrap_ci(
    df: "pd.DataFrame",
    cluster_col: str,
    col_a: str,
    col_b: str,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> BootstrapResult:
    """
    Cluster/block bootstrap by base scenario (cluster_col), preserving within-scenario correlations.
    Resamples whole scenarios with replacement (Efron & Tibshirani 1993, Cameron & Miller 2015).
    """
    import pandas as pd
    np.random.seed(seed)
    
    clusters = df[cluster_col].unique()
    n_clusters = len(clusters)
    if n_clusters == 0:
        return BootstrapResult(mean_diff=0.0, ci_lower=0.0, ci_upper=0.0, p_value=1.0)
        
    cluster_groups = {c: df[df[cluster_col] == c] for c in clusters}
    orig_diff = df[col_a].mean() - df[col_b].mean()
    
    boot_diffs = np.empty(n_resamples)
    for i in range(n_resamples):
        sampled_clusters = np.random.choice(clusters, size=n_clusters, replace=True)
        sample_dfs = [cluster_groups[c] for c in sampled_clusters]
        boot_df = pd.concat(sample_dfs, ignore_index=True)
        boot_diffs[i] = boot_df[col_a].mean() - boot_df[col_b].mean()
        
    ci_lower = float(np.percentile(boot_diffs, (alpha / 2.0) * 100))
    ci_upper = float(np.percentile(boot_diffs, (1.0 - alpha / 2.0) * 100))
    
    # Valid cluster-level hypothesis test: Paired test across scenario cluster means (Cameron & Miller 2015)
    cluster_means_a = np.array([cluster_groups[c][col_a].mean() for c in clusters])
    cluster_means_b = np.array([cluster_groups[c][col_b].mean() for c in clusters])
    cluster_diffs = cluster_means_a - cluster_means_b
    
    if np.all(cluster_diffs == 0):
        p_val = 1.0
    else:
        from scipy import stats
        _, p_val = stats.ttest_rel(cluster_means_a, cluster_means_b)
        p_val = float(p_val)
    
    return BootstrapResult(
        mean_diff=round(float(orig_diff), 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        p_value=round(p_val, 4)
    )
