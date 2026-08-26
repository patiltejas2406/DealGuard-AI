"""Pure-Python / NumPy Deterministic Monte Carlo Simulation Engine with Statistical Lineage."""

from typing import Any, Dict, List, Optional
import numpy as np
from app.domains.simulation.config import (
    DEFAULT_MONTE_CARLO_ITERATIONS,
    MAX_MONTE_CARLO_ITERATIONS,
    MIN_MONTE_CARLO_ITERATIONS,
    MONTE_CARLO_ENGINE_VERSION,
    DistributionType,
    validate_variable_value,
)
from app.domains.simulation.whatif import evaluate_whatif_scenario


def sample_distribution(
    dist_config: Dict[str, Any],
    iterations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate deterministic random samples based on specified probability distribution."""
    dist_type = dist_config.get("distribution_type", DistributionType.TRIANGULAR.value)

    if dist_type == DistributionType.TRIANGULAR.value:
        left = float(dist_config.get("min_val", 0.0))
        mode = float(dist_config.get("mode_val", (left + float(dist_config.get("max_val", 10.0))) / 2.0))
        right = float(dist_config.get("max_val", 10.0))
        if left >= right:
            raise ValueError(f"Triangular min_val ({left}) must be strictly less than max_val ({right}).")
        if not (left <= mode <= right):
            mode = (left + right) / 2.0
        return rng.triangular(left=left, mode=mode, right=right, size=iterations)

    elif dist_type == DistributionType.NORMAL.value:
        mean = float(dist_config.get("mean", 0.0))
        std_dev = float(dist_config.get("std_dev", 1.0))
        if std_dev <= 0:
            raise ValueError("Normal distribution std_dev must be strictly positive.")
        return rng.normal(loc=mean, scale=std_dev, size=iterations)

    elif dist_type == DistributionType.UNIFORM.value:
        low = float(dist_config.get("min_val", 0.0))
        high = float(dist_config.get("max_val", 1.0))
        if low >= high:
            raise ValueError(f"Uniform min_val ({low}) must be strictly less than max_val ({high}).")
        return rng.uniform(low=low, high=high, size=iterations)

    elif dist_type == DistributionType.LOGNORMAL.value:
        mean = float(dist_config.get("mean", 0.0))
        sigma = float(dist_config.get("sigma", 0.5))
        return rng.lognormal(mean=mean, sigma=sigma, size=iterations)

    else:
        raise ValueError(f"Unsupported distribution type '{dist_type}'.")


def run_monte_carlo_simulation(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    variable_distributions: Dict[str, Dict[str, Any]],
    iterations: int = DEFAULT_MONTE_CARLO_ITERATIONS,
    random_seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Execute complete deterministic Monte Carlo simulation and compute statistical distributions."""
    clamped_iterations = max(MIN_MONTE_CARLO_ITERATIONS, min(MAX_MONTE_CARLO_ITERATIONS, int(iterations)))
    rng = np.random.default_rng(random_seed)

    # 1. Sample inputs across all uncertain variables
    sampled_arrays: Dict[str, np.ndarray] = {}
    for var_name, dist_cfg in variable_distributions.items():
        validate_variable_value(var_name, float(dist_cfg.get("mode_val", dist_cfg.get("mean", dist_cfg.get("min_val", 0.0)))))
        sampled_arrays[var_name] = sample_distribution(dist_cfg, clamped_iterations, rng)

    # 2. Iterate through Monte Carlo draws
    simulated_valuations: List[float] = []
    simulated_scores: List[float] = []
    band_counts: Dict[str, int] = {
        "STRONG": 0,
        "FAVORABLE": 0,
        "CAUTION": 0,
        "HIGH_RISK": 0,
        "AVOID": 0,
    }

    # Evaluate across iterations
    for i in range(clamped_iterations):
        draw_overlay: Dict[str, Any] = {}
        for var_name, arr in sampled_arrays.items():
            draw_overlay[var_name] = float(arr[i])

        try:
            res = evaluate_whatif_scenario(
                deal=deal,
                statements=statements,
                metrics=metrics,
                qoe_adjustments=qoe_adjustments,
                valuation=valuation,
                valuation_outputs=valuation_outputs,
                risks=risks,
                documents=documents,
                citations=citations,
                assumptions_overlay=draw_overlay,
            )
            ev = res["scenario_case"]["implied_ev"]
            score = res["scenario_case"]["decision_score"]
            band = res["scenario_case"]["decision_band"]

            simulated_valuations.append(ev)
            simulated_scores.append(score)
            if band in band_counts:
                band_counts[band] += 1
        except Exception:
            continue

    val_np = np.array(simulated_valuations)
    score_np = np.array(simulated_scores)
    actual_runs = len(simulated_valuations)

    if actual_runs == 0:
        raise ValueError("Monte Carlo simulation produced 0 valid iterations.")

    # 3. Statistical Percentiles & Metrics
    val_percentiles = {
        "p5": round(float(np.percentile(val_np, 5)), 2),
        "p10": round(float(np.percentile(val_np, 10)), 2),
        "p25": round(float(np.percentile(val_np, 25)), 2),
        "p50": round(float(np.percentile(val_np, 50)), 2),
        "p75": round(float(np.percentile(val_np, 75)), 2),
        "p90": round(float(np.percentile(val_np, 90)), 2),
        "p95": round(float(np.percentile(val_np, 95)), 2),
    }

    score_percentiles = {
        "p5": round(float(np.percentile(score_np, 5)), 1),
        "p10": round(float(np.percentile(score_np, 10)), 1),
        "p25": round(float(np.percentile(score_np, 25)), 1),
        "p50": round(float(np.percentile(score_np, 50)), 1),
        "p75": round(float(np.percentile(score_np, 75)), 1),
        "p90": round(float(np.percentile(score_np, 90)), 1),
        "p95": round(float(np.percentile(score_np, 95)), 1),
    }

    # Decision Band Probabilities
    band_probabilities = {
        k: round(v / actual_runs * 100.0, 1) for k, v in band_counts.items()
    }

    # Downside Metrics
    target_ev = float(getattr(deal, "target_ev", 0.0) or 0.0)
    prob_below_purchase_price = round(float(np.mean(val_np < target_ev)) * 100.0, 1) if target_ev > 0 else 0.0
    prob_high_risk = round(float(np.mean(score_np < 50.0)) * 100.0, 1)
    var_95 = round(max(0.0, target_ev - val_percentiles["p5"]), 2) if target_ev > 0 else 0.0

    # 4. Histogram Generation (10 bins for visualization)
    val_hist, val_bin_edges = np.histogram(val_np, bins=10)
    score_hist, score_bin_edges = np.histogram(score_np, bins=10)

    val_bins = [
        {"bin_start": round(float(val_bin_edges[b]), 2), "bin_end": round(float(val_bin_edges[b+1]), 2), "count": int(val_hist[b])}
        for b in range(len(val_hist))
    ]
    score_bins = [
        {"bin_start": round(float(score_bin_edges[b]), 1), "bin_end": round(float(score_bin_edges[b+1]), 1), "count": int(score_hist[b])}
        for b in range(len(score_hist))
    ]

    return {
        "engine_version": MONTE_CARLO_ENGINE_VERSION,
        "iterations_requested": clamped_iterations,
        "iterations_completed": actual_runs,
        "random_seed": random_seed,
        "variable_distributions": variable_distributions,
        "valuation_statistics": {
            "mean": round(float(np.mean(val_np)), 2),
            "median": round(float(np.median(val_np)), 2),
            "std_dev": round(float(np.std(val_np)), 2),
            "min": round(float(np.min(val_np)), 2),
            "max": round(float(np.max(val_np)), 2),
            "percentiles": val_percentiles,
            "histogram": val_bins,
        },
        "decision_score_statistics": {
            "mean": round(float(np.mean(score_np)), 1),
            "median": round(float(np.median(score_np)), 1),
            "std_dev": round(float(np.std(score_np)), 1),
            "min": round(float(np.min(score_np)), 1),
            "max": round(float(np.max(score_np)), 1),
            "percentiles": score_percentiles,
            "histogram": score_bins,
        },
        "band_probabilities": band_probabilities,
        "downside_metrics": {
            "prob_below_target_ev_pct": prob_below_purchase_price,
            "prob_high_risk_pct": prob_high_risk,
            "value_at_risk_95": var_95,
        },
    }
