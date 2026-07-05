"""Statistical utility functions using numpy and scipy."""

import numpy as np
from scipy import stats as scipy_stats
from typing import Optional


def compute_z_scores(values: list[float]) -> list[float]:
    """Compute Z-scores for a list of values."""
    arr = np.array(values)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1) if len(arr) > 1 else 1.0
    if std == 0:
        return [0.0] * len(values)
    return [round(float((v - mean) / std), 4) for v in values]


def compute_percentile_rank(values: list[float], target: float) -> float:
    """Compute percentile rank of a target value within a distribution."""
    return round(float(scipy_stats.percentileofscore(values, target)), 1)


def compute_cohens_d(group_a: list[float], group_b: list[float]) -> float:
    """Compute Cohen's d effect size between two groups."""
    a = np.array(group_a)
    b = np.array(group_b)
    if len(a) < 2 or len(b) < 2:
        return 0.0

    mean_a, mean_b = np.mean(a), np.mean(b)
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)
    na, nb = len(a), len(b)
    pooled_std = np.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))

    if pooled_std == 0:
        return 0.0
    return round(float((mean_a - mean_b) / pooled_std), 3)


def compute_trend_slope(x: list[float], y: list[float]) -> dict:
    """Compute linear regression trend."""
    if len(x) < 2 or len(y) < 2:
        return {"slope": 0.0, "intercept": 0.0, "r_value": 0.0, "p_value": 1.0}

    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
    return {
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "r_value": round(float(r_value), 4),
        "p_value": round(float(p_value), 4),
    }


def compute_summary_stats(values: list[float]) -> dict:
    """Compute descriptive statistics for a set of values."""
    arr = np.array(values)
    return {
        "count": len(arr),
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0,
        "min": round(float(np.min(arr)), 2),
        "q25": round(float(np.percentile(arr, 25)), 2),
        "median": round(float(np.median(arr)), 2),
        "q75": round(float(np.percentile(arr, 75)), 2),
        "max": round(float(np.max(arr)), 2),
    }
