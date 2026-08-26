"""Pure-Python Deterministic What-If Scenario Evaluator.

Recalculates 3-statement trajectories, DCF valuation, risk exposure adjustments,
and Phase 8 Composite Decision Score for user-defined assumption overlays.
"""

from typing import Any, Dict, List, Optional
from app.domains.decision.engine import calculate_composite_decision_score
from app.domains.simulation.config import SCENARIO_ENGINE_VERSION, validate_variable_value
from app.domains.valuation.engine.dcf import DCFEngine


class WhatIfCalculationError(ValueError):
    """Raised when What-If scenario evaluation fails mathematical constraints."""
    pass


class ScenarioStatementAdapter:
    """Mock-safe immutable statement adapter representing modified scenario financials."""
    def __init__(self, statement_type: str, line_items: Dict[str, Any], is_audited: bool = True):
        self.statement_type = statement_type
        self.line_items = line_items
        self.is_audited = is_audited


class ScenarioMetricAdapter:
    """Mock-safe immutable metric adapter."""
    def __init__(self, metric_name: str, value: float):
        self.metric_name = metric_name
        self.value = value


class ScenarioValuationOutputAdapter:
    """Mock-safe immutable valuation output adapter."""
    def __init__(self, methodology: str, implied_ev: float, base_ev: float):
        self.methodology = methodology
        self.implied_ev = implied_ev
        self.enterprise_value_base = base_ev


class ScenarioDealAdapter:
    """Mock-safe immutable deal adapter."""
    def __init__(self, target_ev: float, currency: str = "USD"):
        self.target_ev = target_ev
        self.currency = currency


class ScenarioRiskAdapter:
    """Mock-safe immutable risk adapter."""
    def __init__(self, category: str, risk_level: str, status: str = "IDENTIFIED", title: str = "Scenario Risk"):
        self.category = category
        self.risk_level = risk_level
        self.status = status
        self.title = title


def evaluate_whatif_scenario(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    assumptions_overlay: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute complete deterministic What-If scenario calculation against base case context."""
    # 1. Validate all requested overlay variables
    validated_assumptions: Dict[str, float] = {}
    for k, v in assumptions_overlay.items():
        if v is not None:
            validated_assumptions[k] = validate_variable_value(k, float(v))

    # 2. Extract Base Case Values
    base_target_ev = float(getattr(deal, "target_ev", 0.0) or 0.0)
    base_currency = getattr(deal, "currency", "USD")

    base_rev = 0.0
    base_ebitda = 0.0
    base_gp = 0.0
    for stmt in statements:
        if getattr(stmt, "statement_type", "") == "INCOME_STATEMENT":
            items = getattr(stmt, "line_items", {}) or {}
            base_rev = float(items.get("revenue") or items.get("total_revenue") or 0.0)
            base_ebitda = float(items.get("ebitda") or items.get("operating_income") or 0.0)
            base_gp = float(items.get("gross_profit") or (base_rev * 0.70))
            break

    # If no statements, fallback to default base
    if base_rev <= 0:
        base_rev = 50000000.0
        base_ebitda = 15000000.0
        base_gp = 35000000.0

    base_ebitda_margin_pct = (base_ebitda / base_rev * 100.0) if base_rev > 0 else 25.0

    # Base Valuation Implied EV
    base_implied_ev = 0.0
    for out in valuation_outputs:
        val_ev = getattr(out, "implied_ev", None) or getattr(out, "enterprise_value_base", None)
        if val_ev and float(val_ev) > 0:
            base_implied_ev = float(val_ev)
            break
    if base_implied_ev <= 0:
        base_implied_ev = base_target_ev if base_target_ev > 0 else (base_ebitda * 8.0)

    # Base Decision Score
    base_score_data = calculate_composite_decision_score(
        deal=deal,
        statements=statements,
        metrics=metrics,
        qoe_adjustments=qoe_adjustments,
        valuation=valuation,
        valuation_outputs=valuation_outputs,
        risks=risks,
        documents=documents,
        citations=citations,
    )
    base_decision_score = base_score_data["overall_score"]
    base_decision_band = base_score_data["decision_band"]

    # 3. Apply Scenario Overlays
    # Target EV / Purchase Price
    scenario_target_ev = validated_assumptions.get("purchase_price", base_target_ev)

    # Revenue
    rev_growth_overlay = validated_assumptions.get("revenue_growth_pct")
    rev_mult_overlay = validated_assumptions.get("revenue_multiplier")

    if rev_mult_overlay is not None:
        scenario_rev = base_rev * rev_mult_overlay
    elif rev_growth_overlay is not None:
        scenario_rev = base_rev * (1.0 + (rev_growth_overlay / 100.0))
    else:
        scenario_rev = base_rev

    # EBITDA Margin & Synergies
    margin_overlay = validated_assumptions.get("ebitda_margin_pct")
    scenario_ebitda_margin_pct = margin_overlay if margin_overlay is not None else base_ebitda_margin_pct

    synergy_val = validated_assumptions.get("synergy_value", 0.0)
    synergy_rate = validated_assumptions.get("synergy_realization_rate_pct", 100.0) / 100.0
    effective_synergies = synergy_val * synergy_rate

    integration_cost = validated_assumptions.get("integration_cost", 0.0)

    scenario_ebitda = (scenario_rev * (scenario_ebitda_margin_pct / 100.0)) + effective_synergies
    scenario_gp = scenario_rev * (base_gp / base_rev)

    # 4. Calculate Scenario DCF & Implied Valuation
    scenario_wacc_pct = validated_assumptions.get("wacc_pct", 10.0)
    scenario_t_growth_pct = validated_assumptions.get("terminal_growth_rate_pct", 2.5)

    if scenario_t_growth_pct >= scenario_wacc_pct:
        raise WhatIfCalculationError(
            f"Terminal growth rate ({scenario_t_growth_pct}%) cannot be equal to or greater than WACC ({scenario_wacc_pct}%)."
        )

    # Project 5-year FCF trajectory from scenario EBITDA
    projections: List[Dict[str, Any]] = []
    curr_ebitda = scenario_ebitda
    curr_rev = scenario_rev
    growth_rate = (rev_growth_overlay / 100.0) if rev_growth_overlay is not None else 0.08

    for yr in range(1, 6):
        curr_rev = curr_rev * (1.0 + growth_rate)
        curr_ebitda = curr_ebitda * (1.0 + growth_rate)
        projections.append({
            "period": f"Year {yr}",
            "revenue": curr_rev,
            "ebitda": curr_ebitda,
            "ebit": curr_ebitda * 0.85,
            "tax_rate": 25.0,
            "depreciation_amortization": curr_ebitda * 0.15,
            "capex": curr_ebitda * 0.12,
            "working_capital_change": curr_ebitda * 0.03,
        })

    try:
        dcf_res = DCFEngine.calculate_dcf(
            projections=projections,
            wacc=scenario_wacc_pct,
            terminal_growth_rate=scenario_t_growth_pct,
            terminal_method="PERPETUITY_GROWTH",
        )
        scenario_implied_ev = max(0.0, float(dcf_res["implied_enterprise_value"]) - integration_cost)
    except Exception:
        # Fallback multiple-based valuation
        exit_mult = validated_assumptions.get("exit_multiple", 8.0)
        scenario_implied_ev = max(0.0, (scenario_ebitda * exit_mult) - integration_cost)

    # 5. Calculate Scenario Risk Adjustments
    scenario_risks = list(risks)
    churn_overlay = validated_assumptions.get("churn_rate_pct")
    if churn_overlay is not None and churn_overlay > 15.0:
        scenario_risks.append(
            ScenarioRiskAdapter(
                category="REVENUE_QUALITY",
                risk_level="CRITICAL" if churn_overlay > 25.0 else "HIGH",
                title=f"Simulated Customer Churn Spike ({churn_overlay:.1f}%)",
            )
        )

    cust_conc_overlay = validated_assumptions.get("customer_concentration_pct")
    if cust_conc_overlay is not None and cust_conc_overlay > 30.0:
        scenario_risks.append(
            ScenarioRiskAdapter(
                category="CUSTOMER_CONCENTRATION",
                risk_level="CRITICAL" if cust_conc_overlay > 45.0 else "HIGH",
                title=f"Simulated Single-Customer Revenue Concentration ({cust_conc_overlay:.1f}%)",
            )
        )

    # 6. Recalculate Scenario Composite Decision Score
    sim_deal = ScenarioDealAdapter(target_ev=scenario_target_ev, currency=base_currency)
    sim_stmts = [
        ScenarioStatementAdapter(
            statement_type="INCOME_STATEMENT",
            line_items={
                "revenue": scenario_rev,
                "ebitda": scenario_ebitda,
                "gross_profit": scenario_gp,
            },
            is_audited=True,
        )
    ]
    sim_metrics = [
        ScenarioMetricAdapter("EBITDA_MARGIN", scenario_ebitda_margin_pct),
        ScenarioMetricAdapter("REVENUE_GROWTH", rev_growth_overlay if rev_growth_overlay is not None else 8.0),
    ]
    sim_val_outputs = [
        ScenarioValuationOutputAdapter(
            methodology="DCF_PERPETUITY",
            implied_ev=scenario_implied_ev,
            base_ev=scenario_implied_ev,
        )
    ]

    scenario_score_data = calculate_composite_decision_score(
        deal=sim_deal,
        statements=sim_stmts,
        metrics=sim_metrics,
        qoe_adjustments=qoe_adjustments,
        valuation=valuation,
        valuation_outputs=sim_val_outputs,
        risks=scenario_risks,
        documents=documents,
        citations=citations,
    )

    scenario_decision_score = scenario_score_data["overall_score"]
    scenario_decision_band = scenario_score_data["decision_band"]

    # 7. Formulate Deltas & Explainability Lineage
    val_delta_abs = scenario_implied_ev - base_implied_ev
    val_delta_pct = (val_delta_abs / base_implied_ev * 100.0) if base_implied_ev > 0 else 0.0
    score_delta = round(scenario_decision_score - base_decision_score, 1)

    return {
        "engine_version": SCENARIO_ENGINE_VERSION,
        "assumptions_applied": validated_assumptions,
        "base_case": {
            "target_ev": base_target_ev,
            "revenue": round(base_rev, 2),
            "ebitda": round(base_ebitda, 2),
            "ebitda_margin_pct": round(base_ebitda_margin_pct, 2),
            "implied_ev": round(base_implied_ev, 2),
            "decision_score": base_decision_score,
            "decision_band": base_decision_band,
        },
        "scenario_case": {
            "target_ev": scenario_target_ev,
            "revenue": round(scenario_rev, 2),
            "ebitda": round(scenario_ebitda, 2),
            "ebitda_margin_pct": round(scenario_ebitda_margin_pct, 2),
            "implied_ev": round(scenario_implied_ev, 2),
            "decision_score": scenario_decision_score,
            "decision_band": scenario_decision_band,
            "components": scenario_score_data["components"],
        },
        "deltas": {
            "revenue_delta_abs": round(scenario_rev - base_rev, 2),
            "revenue_delta_pct": round(((scenario_rev - base_rev) / base_rev * 100.0), 2) if base_rev > 0 else 0.0,
            "ebitda_delta_abs": round(scenario_ebitda - base_ebitda, 2),
            "ebitda_delta_pct": round(((scenario_ebitda - base_ebitda) / base_ebitda * 100.0), 2) if base_ebitda > 0 else 0.0,
            "valuation_delta_abs": round(val_delta_abs, 2),
            "valuation_delta_pct": round(val_delta_pct, 2),
            "decision_score_delta": score_delta,
            "band_changed": base_decision_band != scenario_decision_band,
            "band_transition": f"{base_decision_band} -> {scenario_decision_band}",
        },
        "positive_drivers": scenario_score_data["positive_drivers"],
        "negative_drivers": scenario_score_data["negative_drivers"],
        "recommendations": scenario_score_data["recommendations"],
    }
