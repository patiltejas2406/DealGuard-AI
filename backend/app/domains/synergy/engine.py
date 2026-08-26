"""Pure-Python Deterministic Synergy Realization & Value Creation Calculation Engine."""

from typing import Any, Dict, List, Optional
from app.domains.decision.engine import calculate_composite_decision_score
from app.domains.simulation.whatif import (
    ScenarioDealAdapter,
    ScenarioMetricAdapter,
    ScenarioStatementAdapter,
    ScenarioValuationOutputAdapter,
)
from app.domains.synergy.config import (
    DEFAULT_REALIZATION_CURVES,
    SynergyType,
    calculate_expected_value,
    calculate_value_capture_rate,
)
from app.domains.valuation.engine.dcf import DCFEngine


def compute_synergy_5yr_schedule(
    synergies: List[Any],
    base_revenue: float = 50000000.0,
    base_ebitda: float = 15000000.0,
    gross_margin_pct: float = 70.0,
) -> Dict[str, Any]:
    """Calculate 5-year phased trajectory of potential, expected, and realized synergies."""
    schedule: List[Dict[str, Any]] = []
    gm_ratio = gross_margin_pct / 100.0

    for yr in range(1, 6):
        yr_key = f"year_{yr}"
        potential_rev = 0.0
        expected_rev = 0.0
        realized_rev = 0.0

        potential_cost = 0.0
        expected_cost = 0.0
        realized_cost = 0.0

        integration_cost_yr = 0.0

        for syn in synergies:
            curve = getattr(syn, "realization_curve", {}) or DEFAULT_REALIZATION_CURVES["STANDARD"]
            ramp_pct = float(curve.get(yr_key, 100.0)) / 100.0
            prob_ratio = float(getattr(syn, "probability_pct", 80.0)) / 100.0
            real_rate = float(getattr(syn, "realization_rate_pct", 100.0)) / 100.0
            pot_val = float(getattr(syn, "potential_annual_value", 0.0))
            realized_val = float(getattr(syn, "realized_annual_value", 0.0))
            syn_type = getattr(syn, "synergy_type", "COST")

            # Allocate one-time integration cost predominantly to Year 1 (70%) and Year 2 (30%)
            int_cost = float(getattr(syn, "one_time_integration_cost", 0.0))
            if yr == 1:
                integration_cost_yr += int_cost * 0.70
            elif yr == 2:
                integration_cost_yr += int_cost * 0.30

            if syn_type == SynergyType.REVENUE.value:
                potential_rev += pot_val * ramp_pct
                expected_rev += pot_val * ramp_pct * real_rate * prob_ratio
                realized_rev += realized_val * ramp_pct
            else:
                potential_cost += pot_val * ramp_pct
                expected_cost += pot_val * ramp_pct * real_rate * prob_ratio
                realized_cost += realized_val * ramp_pct

        # Combined Impacts
        total_potential = potential_rev + potential_cost
        total_expected = expected_rev + expected_cost
        total_realized = realized_rev + realized_cost

        # Incremental EBITDA = (Rev * GM) + Cost Savings
        ebitda_impact = (expected_rev * gm_ratio) + expected_cost
        net_fcf_impact = (ebitda_impact * 0.75) - integration_cost_yr

        schedule.append({
            "year": yr,
            "period": f"Year {yr}",
            "potential_revenue_synergy": round(potential_rev, 2),
            "expected_revenue_synergy": round(expected_rev, 2),
            "realized_revenue_synergy": round(realized_rev, 2),
            "potential_cost_synergy": round(potential_cost, 2),
            "expected_cost_synergy": round(expected_cost, 2),
            "realized_cost_synergy": round(realized_cost, 2),
            "total_potential": round(total_potential, 2),
            "total_expected": round(total_expected, 2),
            "total_realized": round(total_realized, 2),
            "integration_cost": round(integration_cost_yr, 2),
            "ebitda_impact": round(ebitda_impact, 2),
            "net_cash_flow_impact": round(net_fcf_impact, 2),
        })

    return {
        "schedule": schedule,
        "total_5yr_expected_ebitda_impact": round(sum(s["ebitda_impact"] for s in schedule), 2),
        "total_5yr_net_cash_flow_impact": round(sum(s["net_cash_flow_impact"] for s in schedule), 2),
    }


def compute_synergy_value_bridge(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    synergies: List[Any],
    wacc_pct: float = 10.0,
) -> Dict[str, Any]:
    """Construct mathematical Value Creation Waterfall Bridge and Synergy-Adjusted Decision Score."""
    # 1. Base Financials & Standalone Valuation
    base_target_ev = float(getattr(deal, "target_ev", 0.0) or 0.0)
    base_rev = 50000000.0
    base_ebitda = 15000000.0
    base_gp = 35000000.0

    for stmt in statements:
        if getattr(stmt, "statement_type", "") == "INCOME_STATEMENT":
            items = getattr(stmt, "line_items", {}) or {}
            base_rev = float(items.get("revenue") or items.get("total_revenue") or base_rev)
            base_ebitda = float(items.get("ebitda") or items.get("operating_income") or base_ebitda)
            base_gp = float(items.get("gross_profit") or (base_rev * 0.70))
            break

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
    base_score = base_score_data["overall_score"]
    base_band = base_score_data["decision_band"]

    # 2. Synergy Phasing & NPV Calculations
    gm_pct = (base_gp / base_rev * 100.0) if base_rev > 0 else 70.0
    phasing = compute_synergy_5yr_schedule(synergies, base_rev, base_ebitda, gm_pct)
    schedule = phasing["schedule"]

    wacc_ratio = wacc_pct / 100.0
    pv_revenue_synergies = 0.0
    pv_cost_synergies = 0.0
    total_integration_costs = 0.0
    total_potential_annual = 0.0
    total_expected_annual = 0.0

    for syn in synergies:
        total_potential_annual += float(getattr(syn, "potential_annual_value", 0.0))
        total_expected_annual += float(getattr(syn, "expected_annual_value", 0.0))
        total_integration_costs += float(getattr(syn, "one_time_integration_cost", 0.0))

    for item in schedule:
        yr = item["year"]
        df = 1.0 / ((1.0 + wacc_ratio) ** yr)
        # Gross profit contribution from rev synergies
        rev_fcf = item["expected_revenue_synergy"] * (gm_pct / 100.0) * 0.75
        cost_fcf = item["expected_cost_synergy"] * 0.75

        pv_revenue_synergies += rev_fcf * df
        pv_cost_synergies += cost_fcf * df

    # Risk Adjustment (Uncaptured uncertainty discount)
    realization_risk_discount = max(0.0, (total_potential_annual - total_expected_annual) * 2.5)

    # Waterfall Bridge Steps
    synergy_adjusted_ev = max(
        0.0,
        base_implied_ev + pv_revenue_synergies + pv_cost_synergies - total_integration_costs - realization_risk_discount,
    )
    net_value_creation = synergy_adjusted_ev - base_implied_ev

    # 3. Synergy-Adjusted Projections for Decision Score
    adj_rev = base_rev + (schedule[-1]["expected_revenue_synergy"] if schedule else 0.0)
    adj_ebitda = base_ebitda + (schedule[-1]["ebitda_impact"] if schedule else 0.0)
    adj_margin_pct = (adj_ebitda / adj_rev * 100.0) if adj_rev > 0 else 25.0

    sim_deal = ScenarioDealAdapter(target_ev=base_target_ev, currency=getattr(deal, "currency", "USD"))
    sim_stmts = [
        ScenarioStatementAdapter(
            statement_type="INCOME_STATEMENT",
            line_items={
                "revenue": adj_rev,
                "ebitda": adj_ebitda,
                "gross_profit": adj_rev * (gm_pct / 100.0),
            },
            is_audited=True,
        )
    ]
    sim_metrics = [
        ScenarioMetricAdapter("EBITDA_MARGIN", adj_margin_pct),
        ScenarioMetricAdapter("REVENUE_GROWTH", 10.0),
    ]
    sim_val_outputs = [
        ScenarioValuationOutputAdapter(
            methodology="DCF_PERPETUITY",
            implied_ev=synergy_adjusted_ev,
            base_ev=synergy_adjusted_ev,
        )
    ]

    adj_score_data = calculate_composite_decision_score(
        deal=sim_deal,
        statements=sim_stmts,
        metrics=sim_metrics,
        qoe_adjustments=qoe_adjustments,
        valuation=valuation,
        valuation_outputs=sim_val_outputs,
        risks=risks,
        documents=documents,
        citations=citations,
    )

    return {
        "standalone_ev": round(base_implied_ev, 2),
        "pv_revenue_synergies": round(pv_revenue_synergies, 2),
        "pv_cost_synergies": round(pv_cost_synergies, 2),
        "total_integration_costs": round(total_integration_costs, 2),
        "realization_risk_discount": round(realization_risk_discount, 2),
        "synergy_adjusted_ev": round(synergy_adjusted_ev, 2),
        "net_value_created": round(net_value_creation, 2),
        "value_creation_pct": round((net_value_creation / base_implied_ev * 100.0), 2) if base_implied_ev > 0 else 0.0,
        "base_decision_score": base_score,
        "base_decision_band": base_band,
        "synergy_adjusted_decision_score": adj_score_data["overall_score"],
        "synergy_adjusted_decision_band": adj_score_data["decision_band"],
        "score_delta": round(adj_score_data["overall_score"] - base_score, 1),
        "waterfall_steps": [
            {"label": "Standalone Enterprise Value", "amount": round(base_implied_ev, 2), "type": "BASE"},
            {"label": "+ PV of Revenue Synergies", "amount": round(pv_revenue_synergies, 2), "type": "ADDITION"},
            {"label": "+ PV of Cost Synergies", "amount": round(pv_cost_synergies, 2), "type": "ADDITION"},
            {"label": "- One-Time Integration Costs", "amount": round(-total_integration_costs, 2), "type": "SUBTRACTION"},
            {"label": "- Realization Risk Adjustment", "amount": round(-realization_risk_discount, 2), "type": "SUBTRACTION"},
            {"label": "Synergy-Adjusted Enterprise Value", "amount": round(synergy_adjusted_ev, 2), "type": "TOTAL"},
        ],
    }


def aggregate_synergy_portfolio(synergies: List[Any]) -> Dict[str, Any]:
    """Compute aggregate portfolio KPIs across all registered synergy opportunities."""
    total_potential = 0.0
    total_expected = 0.0
    total_realized = 0.0
    total_integration_cost = 0.0

    by_type: Dict[str, Dict[str, float]] = {
        SynergyType.REVENUE.value: {"potential": 0.0, "expected": 0.0, "realized": 0.0, "count": 0},
        SynergyType.COST.value: {"potential": 0.0, "expected": 0.0, "realized": 0.0, "count": 0},
        SynergyType.OPERATIONAL.value: {"potential": 0.0, "expected": 0.0, "realized": 0.0, "count": 0},
    }

    by_status: Dict[str, int] = {}
    by_confidence: Dict[str, int] = {}

    for syn in synergies:
        pot = float(getattr(syn, "potential_annual_value", 0.0))
        exp = float(getattr(syn, "expected_annual_value", 0.0))
        real = float(getattr(syn, "realized_annual_value", 0.0))
        int_c = float(getattr(syn, "one_time_integration_cost", 0.0))
        stype = getattr(syn, "synergy_type", "COST")
        status = getattr(syn, "status", "IDENTIFIED")
        conf = getattr(syn, "confidence", "MEDIUM")

        total_potential += pot
        total_expected += exp
        total_realized += real
        total_integration_cost += int_c

        if stype in by_type:
            by_type[stype]["potential"] += pot
            by_type[stype]["expected"] += exp
            by_type[stype]["realized"] += real
            by_type[stype]["count"] += 1

        by_status[status] = by_status.get(status, 0) + 1
        by_confidence[conf] = by_confidence.get(conf, 0) + 1

    capture_rate = calculate_value_capture_rate(total_realized, total_potential)

    return {
        "total_opportunities_count": len(synergies),
        "total_potential_annual_value": round(total_potential, 2),
        "total_expected_annual_value": round(total_expected, 2),
        "total_realized_annual_value": round(total_realized, 2),
        "total_one_time_integration_cost": round(total_integration_cost, 2),
        "net_annual_expected_value": round(total_expected - (total_integration_cost / 5.0), 2),
        "overall_value_capture_rate_pct": capture_rate,
        "by_type": by_type,
        "by_status": by_status,
        "by_confidence": by_confidence,
    }
