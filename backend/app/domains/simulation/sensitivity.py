"""Deterministic 1D and 2D Sensitivity Matrix & Tipping-Point Inflection Analysis."""

from typing import Any, Dict, List, Optional, Tuple
from app.domains.simulation.config import validate_variable_value
from app.domains.simulation.whatif import evaluate_whatif_scenario


def compute_1d_sensitivity(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    variable_name: str,
    steps: List[float],
) -> Dict[str, Any]:
    """Compute 1-variable parameter sweep returning valuation and decision score curves."""
    results: List[Dict[str, Any]] = []

    for step_val in steps:
        validated_val = validate_variable_value(variable_name, float(step_val))
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
            assumptions_overlay={variable_name: validated_val},
        )
        results.append({
            "step_value": validated_val,
            "implied_ev": res["scenario_case"]["implied_ev"],
            "decision_score": res["scenario_case"]["decision_score"],
            "decision_band": res["scenario_case"]["decision_band"],
            "valuation_delta_pct": res["deltas"]["valuation_delta_pct"],
            "score_delta": res["deltas"]["decision_score_delta"],
        })

    return {
        "variable_name": variable_name,
        "steps_count": len(results),
        "curve": results,
    }


def compute_2d_sensitivity_matrix(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    row_variable: str,
    row_steps: List[float],
    col_variable: str,
    col_steps: List[float],
) -> Dict[str, Any]:
    """Compute 2-variable cross matrix returning 2D grid of valuations and decision scores."""
    matrix_grid: List[List[Dict[str, Any]]] = []

    for r_val in row_steps:
        validated_r = validate_variable_value(row_variable, float(r_val))
        row_cells: List[Dict[str, Any]] = []

        for c_val in col_steps:
            validated_c = validate_variable_value(col_variable, float(c_val))
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
                assumptions_overlay={row_variable: validated_r, col_variable: validated_c},
            )
            row_cells.append({
                "row_val": validated_r,
                "col_val": validated_c,
                "implied_ev": res["scenario_case"]["implied_ev"],
                "decision_score": res["scenario_case"]["decision_score"],
                "decision_band": res["scenario_case"]["decision_band"],
            })
        matrix_grid.append(row_cells)

    # Calculate Break-Even Tipping Points
    target_ev = float(getattr(deal, "target_ev", 0.0) or 0.0)
    tipping_points: List[Dict[str, Any]] = []

    if target_ev > 0:
        for r_idx, row in enumerate(matrix_grid):
            for c_idx, cell in enumerate(row):
                if cell["implied_ev"] < target_ev and cell["decision_score"] < 50.0:
                    tipping_points.append({
                        f"{row_variable}": cell["row_val"],
                        f"{col_variable}": cell["col_val"],
                        "implied_ev": cell["implied_ev"],
                        "decision_score": cell["decision_score"],
                        "issue": "Valuation below target EV and score enters High Risk",
                    })

    return {
        "row_variable": row_variable,
        "row_steps": row_steps,
        "col_variable": col_variable,
        "col_steps": col_steps,
        "matrix_grid": matrix_grid,
        "tipping_points_count": len(tipping_points),
        "tipping_points": tipping_points[:5],  # Top 5 critical inflection thresholds
    }
