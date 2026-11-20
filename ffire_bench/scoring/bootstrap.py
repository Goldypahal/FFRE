"""
Statistical uncertainty estimation and hypothesis testing for FFIRE-Bench.
Implements cluster-aware bootstrap confidence intervals and paired significance testing.
"""

import math
import random
from typing import List, Dict, Any, Tuple, Callable


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate the Wilson score confidence interval for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.95996 if abs(confidence - 0.95) < 1e-3 else 2.57583
    p = successes / total
    denominator = 1.0 + (z ** 2) / total
    centre = (p + (z ** 2) / (2.0 * total)) / denominator
    spread = (z * math.sqrt((p * (1.0 - p) + (z ** 2) / (4.0 * total)) / total)) / denominator
    lower = max(0.0, centre - spread)
    upper = min(1.0, centre + spread)
    return (round(lower * 100.0, 2), round(upper * 100.0, 2))


def cluster_bootstrap_ci(
    cases: List[Dict[str, Any]],
    metric_fn: Callable[[List[Dict[str, Any]]], float],
    cluster_key: str = "cluster_id",
    num_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Compute cluster-aware bootstrap confidence interval.
    Resamples clusters with replacement to preserve intra-cluster correlation.
    
    Returns:
        (point_estimate, lower_bound, upper_bound)
    """
    if not cases:
        return (0.0, 0.0, 0.0)

    # Group cases by cluster_id
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for case in cases:
        cid = case.get(cluster_key, "default_cluster")
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(case)

    cluster_ids = list(clusters.keys())
    point_est = metric_fn(cases)

    if len(cluster_ids) <= 1:
        # Fall back to single point estimate if clustering is unavailable
        return (round(point_est, 4), round(point_est, 4), round(point_est, 4))

    rng = random.Random(seed)
    boot_estimates: List[float] = []

    for _ in range(num_resamples):
        sampled_cids = [rng.choice(cluster_ids) for _ in range(len(cluster_ids))]
        resampled_cases = []
        for cid in sampled_cids:
            resampled_cases.extend(clusters[cid])
        score = metric_fn(resampled_cases)
        boot_estimates.append(score)

    boot_estimates.sort()
    alpha = (1.0 - confidence_level) / 2.0
    low_idx = max(0, int(math.floor(alpha * num_resamples)))
    high_idx = min(num_resamples - 1, int(math.ceil((1.0 - alpha) * num_resamples)))

    lower = boot_estimates[low_idx]
    upper = boot_estimates[high_idx]

    return (round(point_est, 4), round(lower, 4), round(upper, 4))


def paired_bootstrap_test(
    cases: List[Dict[str, Any]],
    metric_fn_a: Callable[[List[Dict[str, Any]]], float],
    metric_fn_b: Callable[[List[Dict[str, Any]]], float],
    cluster_key: str = "cluster_id",
    num_resamples: int = 1000,
    seed: int = 42
) -> Tuple[float, bool]:
    """
    Two-sided paired cluster bootstrap test between model A and model B.
    Returns: (p_value, is_significant_at_05)
    """
    diff_observed = metric_fn_a(cases) - metric_fn_b(cases)
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for case in cases:
        cid = case.get(cluster_key, "default_cluster")
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(case)

    cluster_ids = list(clusters.keys())
    rng = random.Random(seed)
    count_extreme = 0

    for _ in range(num_resamples):
        sampled_cids = [rng.choice(cluster_ids) for _ in range(len(cluster_ids))]
        resampled_cases = []
        for cid in sampled_cids:
            resampled_cases.extend(clusters[cid])
        diff_boot = metric_fn_a(resampled_cases) - metric_fn_b(resampled_cases)
        if abs(diff_boot - diff_observed) >= abs(diff_observed):
            count_extreme += 1

    p_val = round(count_extreme / num_resamples, 4)
    return (p_val, p_val < 0.05)
