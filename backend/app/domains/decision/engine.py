"""Pure-Python Deterministic Decision Scoring Engine for DealGuard AI.

Calculates the Composite DealGuard Decision Score (0-100), individual component scores,
confidence metrics, and structured explainability drivers without non-deterministic LLM reliance.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.domains.decision.config import (
    CURRENT_SCORING_VERSION,
    DEFAULT_COMPONENT_WEIGHTS,
    DataAvailabilityStatus,
    DecisionBand,
    classify_decision_band,
    get_band_description,
)


class DecisionScoringError(ValueError):
    """Raised when scoring inputs or weight configurations violate mathematical integrity."""
    pass


def validate_weights(weights: Dict[str, float]) -> None:
    """Ensure scoring weights sum exactly to 1.00 within floating point tolerance."""
    total = sum(weights.values())
    if abs(total - 1.00) > 0.001:
        raise DecisionScoringError(
            f"Component weights must sum to 1.00 (100%), got {total:.4f}"
        )
    for k, v in weights.items():
        if v < 0.0:
            raise DecisionScoringError(f"Weight for '{k}' cannot be negative: {v}")


# ==========================================
# 1. Component Normalization Engines
# ==========================================

def normalize_financial_health(
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
) -> Dict[str, Any]:
    """Calculate normalized Financial Health score (0-100) from 3-statement data and metrics."""
    if not statements and not metrics:
        return {
            "name": "FINANCIAL_HEALTH",
            "score": 50.0,
            "status": DataAvailabilityStatus.INSUFFICIENT_DATA.value,
            "confidence": 0.20,
            "raw_inputs": {},
            "explanation": "No financial statements or normalized metrics available for this deal workspace.",
            "drivers": [],
        }

    raw_inputs: Dict[str, Any] = {}
    sub_scores: List[float] = []
    drivers: List[Dict[str, Any]] = []

    # 1. EBITDA Margin Analysis
    ebitda_margin: Optional[float] = None
    for m in metrics:
        if getattr(m, "metric_name", None) in ["EBITDA_MARGIN", "ebitda_margin"]:
            ebitda_margin = float(getattr(m, "value", 0.0))
            break

    # Fallback to computing from statements
    if ebitda_margin is None:
        for stmt in statements:
            if getattr(stmt, "statement_type", "") == "INCOME_STATEMENT":
                items = getattr(stmt, "line_items", {}) or {}
                rev = items.get("revenue") or items.get("total_revenue")
                ebitda = items.get("ebitda") or items.get("operating_income")
                if rev and ebitda and float(rev) > 0:
                    ebitda_margin = (float(ebitda) / float(rev)) * 100.0
                    break

    if ebitda_margin is not None:
        raw_inputs["ebitda_margin_pct"] = round(ebitda_margin, 2)
        if ebitda_margin >= 25.0:
            sub_scores.append(100.0)
            drivers.append({"driver": "Exceptional EBITDA profitability margin (>25%)", "type": "POSITIVE", "impact": "HIGH"})
        elif ebitda_margin >= 15.0:
            sub_scores.append(85.0)
            drivers.append({"driver": "Healthy operational EBITDA margin (15-25%)", "type": "POSITIVE", "impact": "MEDIUM"})
        elif ebitda_margin >= 5.0:
            sub_scores.append(65.0)
            drivers.append({"driver": "Moderate operational EBITDA margin (5-15%)", "type": "NEUTRAL", "impact": "LOW"})
        elif ebitda_margin >= 0.0:
            sub_scores.append(40.0)
            drivers.append({"driver": "Low single-digit EBITDA profitability (<5%)", "type": "NEGATIVE", "impact": "MEDIUM"})
        else:
            sub_scores.append(15.0)
            drivers.append({"driver": "Negative operational EBITDA / operating loss", "type": "NEGATIVE", "impact": "HIGH"})

    # 2. Revenue Trajectory (Growth / Scale)
    rev_growth: Optional[float] = None
    for m in metrics:
        if getattr(m, "metric_name", None) in ["REVENUE_CAGR", "revenue_growth_yoy", "REVENUE_GROWTH"]:
            rev_growth = float(getattr(m, "value", 0.0))
            break

    if rev_growth is not None:
        raw_inputs["revenue_growth_pct"] = round(rev_growth, 2)
        if rev_growth >= 20.0:
            sub_scores.append(95.0)
            drivers.append({"driver": "Rapid revenue growth rate (>20% YoY)", "type": "POSITIVE", "impact": "HIGH"})
        elif rev_growth >= 10.0:
            sub_scores.append(80.0)
            drivers.append({"driver": "Solid double-digit revenue expansion (10-20%)", "type": "POSITIVE", "impact": "MEDIUM"})
        elif rev_growth >= 0.0:
            sub_scores.append(60.0)
        else:
            sub_scores.append(30.0)
            drivers.append({"driver": "Contracting top-line revenue trend", "type": "NEGATIVE", "impact": "HIGH"})

    # 3. Quality of Earnings (QoE) Adjustments Drag
    total_qoe_drag = 0.0
    if qoe_adjustments:
        aggressive_count = sum(1 for q in qoe_adjustments if getattr(q, "category", "") in ["PRO_FORMA", "MANAGEMENT_ADJUSTMENT"])
        raw_inputs["qoe_adjustments_count"] = len(qoe_adjustments)
        raw_inputs["aggressive_qoe_count"] = aggressive_count
        if aggressive_count > 2:
            total_qoe_drag = 15.0
            drivers.append({"driver": "Multiple aggressive pro-forma QoE earnings adjustments", "type": "NEGATIVE", "impact": "MEDIUM"})

    # Aggregate Financial Health
    if sub_scores:
        base_score = sum(sub_scores) / len(sub_scores)
        final_score = max(0.0, min(100.0, base_score - total_qoe_drag))
        status = DataAvailabilityStatus.AVAILABLE.value if len(sub_scores) >= 2 else DataAvailabilityStatus.PARTIAL.value
        confidence = 0.90 if status == DataAvailabilityStatus.AVAILABLE.value else 0.65
        explanation = f"Evaluated from {len(statements)} financial statements and {len(metrics)} operational metrics."
    else:
        final_score = 55.0
        status = DataAvailabilityStatus.PARTIAL.value
        confidence = 0.40
        explanation = "Limited financial line-items available; baseline score assigned."

    return {
        "name": "FINANCIAL_HEALTH",
        "score": round(final_score, 1),
        "status": status,
        "confidence": confidence,
        "raw_inputs": raw_inputs,
        "explanation": explanation,
        "drivers": drivers,
    }


def normalize_valuation_attractiveness(
    target_ev: Optional[float],
    valuation: Optional[Any],
    outputs: List[Any],
) -> Dict[str, Any]:
    """Calculate normalized Valuation Attractiveness score (0-100) vs proposed transaction target EV."""
    if not target_ev or target_ev <= 0 or not outputs:
        return {
            "name": "VALUATION_ATTRACTIVENESS",
            "score": 50.0,
            "status": DataAvailabilityStatus.INSUFFICIENT_DATA.value,
            "confidence": 0.25,
            "raw_inputs": {"target_ev": target_ev},
            "explanation": "No comprehensive DCF/Comps valuation outputs available against Target EV.",
            "drivers": [],
        }

    raw_inputs: Dict[str, Any] = {"target_ev": target_ev}
    drivers: List[Dict[str, Any]] = []

    # Find primary implied DCF or Summary EV
    implied_ev: Optional[float] = None
    for out in outputs:
        if getattr(out, "methodology", "") in ["SUMMARY", "DCF_PERPETUITY", "DCF_EXIT_MULTIPLE"]:
            implied_ev = getattr(out, "implied_ev", None) or getattr(out, "enterprise_value_base", None)
            if implied_ev and implied_ev > 0:
                raw_inputs["primary_valuation_method"] = getattr(out, "methodology", "")
                break

    if implied_ev is None and outputs:
        implied_ev = getattr(outputs[0], "implied_ev", None) or getattr(outputs[0], "enterprise_value_base", None)

    if implied_ev and implied_ev > 0:
        raw_inputs["implied_ev"] = implied_ev
        # Spread = (Implied EV - Target EV) / Target EV
        spread_pct = ((implied_ev - target_ev) / target_ev) * 100.0
        raw_inputs["valuation_spread_pct"] = round(spread_pct, 2)

        if spread_pct >= 25.0:
            score = 95.0
            drivers.append({"driver": f"Significant intrinsic valuation upside (+{spread_pct:.1f}% DCF spread vs purchase price)", "type": "POSITIVE", "impact": "HIGH"})
        elif spread_pct >= 10.0:
            score = 85.0
            drivers.append({"driver": f"Attractive purchase price with positive valuation cushion (+{spread_pct:.1f}%)", "type": "POSITIVE", "impact": "MEDIUM"})
        elif spread_pct >= -5.0:
            score = 70.0
            drivers.append({"driver": "Fair transaction pricing aligned with peer median / intrinsic DCF", "type": "NEUTRAL", "impact": "LOW"})
        elif spread_pct >= -20.0:
            score = 45.0
            drivers.append({"driver": f"Target EV reflects moderate premium over intrinsic valuation ({spread_pct:.1f}%)", "type": "NEGATIVE", "impact": "MEDIUM"})
        else:
            score = 25.0
            drivers.append({"driver": f"Substantial valuation overpayment premium ({spread_pct:.1f}% vs intrinsic DCF)", "type": "NEGATIVE", "impact": "HIGH"})

        status = DataAvailabilityStatus.AVAILABLE.value
        confidence = 0.85
        explanation = f"Evaluated intrinsic implied EV ({implied_ev:,.0f}) against proposed target EV ({target_ev:,.0f})."
    else:
        score = 50.0
        status = DataAvailabilityStatus.PARTIAL.value
        confidence = 0.40
        explanation = "Valuation project exists but lacks calculable implied EV baseline."

    return {
        "name": "VALUATION_ATTRACTIVENESS",
        "score": round(score, 1),
        "status": status,
        "confidence": confidence,
        "raw_inputs": raw_inputs,
        "explanation": explanation,
        "drivers": drivers,
    }


def normalize_risk_exposure(risks: List[Any]) -> Dict[str, Any]:
    """Calculate normalized Risk Exposure score (0-100) consuming Phase 7 17-pillar intelligence."""
    raw_inputs: Dict[str, Any] = {
        "total_risks_count": len(risks),
        "critical_count": 0,
        "high_count": 0,
        "moderate_count": 0,
        "low_count": 0,
    }
    drivers: List[Dict[str, Any]] = []

    if not risks:
        return {
            "name": "RISK_EXPOSURE",
            "score": 85.0,  # Neutral-positive baseline when no risks found
            "status": DataAvailabilityStatus.PARTIAL.value,
            "confidence": 0.50,
            "raw_inputs": raw_inputs,
            "explanation": "No active risks registered. Run Automated Document Risk Scan for full verification.",
            "drivers": [{"driver": "No active diligence risks flagged", "type": "POSITIVE", "impact": "LOW"}],
        }

    penalty = 0.0
    for r in risks:
        level = getattr(r, "risk_level", "LOW")
        status = getattr(r, "status", "IDENTIFIED")
        is_mitigated = status in ["MITIGATED", "ACCEPTED"]
        mult = 0.50 if is_mitigated else 1.0

        if level == "CRITICAL":
            raw_inputs["critical_count"] += 1
            penalty += 16.0 * mult
            if not is_mitigated:
                drivers.append({"driver": f"Critical unmitigated risk: {getattr(r, 'title', 'Critical Risk')}", "type": "NEGATIVE", "impact": "CRITICAL"})
        elif level == "HIGH":
            raw_inputs["high_count"] += 1
            penalty += 8.0 * mult
            if not is_mitigated and len(drivers) < 4:
                drivers.append({"driver": f"High risk exposure: {getattr(r, 'title', 'High Risk')}", "type": "NEGATIVE", "impact": "HIGH"})
        elif level == "MODERATE":
            raw_inputs["moderate_count"] += 1
            penalty += 3.0 * mult
        else:
            raw_inputs["low_count"] += 1
            penalty += 1.0 * mult

    score = max(0.0, min(100.0, 100.0 - penalty))

    if raw_inputs["critical_count"] == 0 and raw_inputs["high_count"] == 0:
        drivers.append({"driver": "Zero critical or high severity diligence risks detected", "type": "POSITIVE", "impact": "HIGH"})

    return {
        "name": "RISK_EXPOSURE",
        "score": round(score, 1),
        "status": DataAvailabilityStatus.AVAILABLE.value,
        "confidence": 0.92,
        "raw_inputs": raw_inputs,
        "explanation": f"Evaluated {len(risks)} diligence findings ({raw_inputs['critical_count']} Critical, {raw_inputs['high_count']} High).",
        "drivers": drivers,
    }


def normalize_revenue_quality(
    statements: List[Any],
    risks: List[Any],
) -> Dict[str, Any]:
    """Calculate normalized Revenue Quality score (0-100) from margin durability & customer concentration."""
    score = 75.0
    drivers: List[Dict[str, Any]] = []
    raw_inputs: Dict[str, Any] = {}

    # Check for Customer Concentration / Revenue Quality risks
    has_cust_conc = any(
        getattr(r, "category", "") == "CUSTOMER_CONCENTRATION" and getattr(r, "risk_level", "") in ["CRITICAL", "HIGH"]
        for r in risks
    )
    has_rev_quality_risk = any(
        getattr(r, "category", "") == "REVENUE_QUALITY" and getattr(r, "risk_level", "") in ["CRITICAL", "HIGH"]
        for r in risks
    )

    if has_cust_conc:
        score -= 25.0
        raw_inputs["customer_concentration_flag"] = True
        drivers.append({"driver": "High customer concentration exposure dampens revenue durability", "type": "NEGATIVE", "impact": "HIGH"})
    else:
        raw_inputs["customer_concentration_flag"] = False

    if has_rev_quality_risk:
        score -= 20.0
        raw_inputs["revenue_quality_risk_flag"] = True
        drivers.append({"driver": "Identified churn or aggressive revenue recognition concerns", "type": "NEGATIVE", "impact": "HIGH"})

    # Check gross margin from statements
    for stmt in statements:
        if getattr(stmt, "statement_type", "") == "INCOME_STATEMENT":
            items = getattr(stmt, "line_items", {}) or {}
            rev = items.get("revenue") or items.get("total_revenue")
            gp = items.get("gross_profit")
            if rev and gp and float(rev) > 0:
                gm_pct = (float(gp) / float(rev)) * 100.0
                raw_inputs["gross_margin_pct"] = round(gm_pct, 2)
                if gm_pct >= 70.0:
                    score += 15.0
                    drivers.append({"driver": f"High gross margin software/service profile ({gm_pct:.1f}%)", "type": "POSITIVE", "impact": "MEDIUM"})
                elif gm_pct < 35.0:
                    score -= 10.0
                break

    score = max(0.0, min(100.0, score))
    status = DataAvailabilityStatus.AVAILABLE.value if statements else DataAvailabilityStatus.PARTIAL.value
    confidence = 0.85 if status == DataAvailabilityStatus.AVAILABLE.value else 0.50

    return {
        "name": "REVENUE_QUALITY",
        "score": round(score, 1),
        "status": status,
        "confidence": confidence,
        "raw_inputs": raw_inputs,
        "explanation": "Evaluated revenue durability, recurring profile, and customer concentration.",
        "drivers": drivers,
    }


def normalize_evidence_confidence(
    documents: List[Any],
    citations: List[Any],
    statements: List[Any],
) -> Dict[str, Any]:
    """Calculate normalized Evidence Confidence score (0-100) based on audit completeness & citations."""
    doc_count = len(documents)
    cit_count = len(citations)
    is_audited = any(getattr(s, "is_audited", False) for s in statements)

    raw_inputs = {
        "documents_count": doc_count,
        "citations_count": cit_count,
        "is_audited_financials": is_audited,
    }
    drivers: List[Dict[str, Any]] = []

    score = 40.0
    if doc_count >= 3:
        score += 25.0
    elif doc_count >= 1:
        score += 15.0

    if cit_count >= 5:
        score += 25.0
        drivers.append({"driver": f"Extensive grounded evidence ({cit_count} verifiable citations)", "type": "POSITIVE", "impact": "MEDIUM"})
    elif cit_count >= 1:
        score += 15.0

    if is_audited:
        score += 10.0
        drivers.append({"driver": "Audited financial statements provided in data room", "type": "POSITIVE", "impact": "MEDIUM"})
    else:
        drivers.append({"driver": "Unaudited management financial reports; independent audit recommended", "type": "NEGATIVE", "impact": "LOW"})

    score = max(0.0, min(100.0, score))
    status = DataAvailabilityStatus.AVAILABLE.value if (doc_count > 0 and cit_count > 0) else DataAvailabilityStatus.PARTIAL.value
    confidence = min(1.0, score / 100.0)

    return {
        "name": "EVIDENCE_CONFIDENCE",
        "score": round(score, 1),
        "status": status,
        "confidence": round(confidence, 2),
        "raw_inputs": raw_inputs,
        "explanation": f"Grounded in {doc_count} data room documents and {cit_count} verified citations.",
        "drivers": drivers,
    }


def normalize_deal_complexity(risks: List[Any], deal: Optional[Any]) -> Dict[str, Any]:
    """Calculate normalized Deal Complexity score (0-100; Higher = Cleaner / Lower Friction)."""
    score = 85.0
    drivers: List[Dict[str, Any]] = []
    complexity_categories = ["INTEGRATION_COMPLEXITY", "CHANGE_OF_CONTROL", "REGULATORY", "LEGAL_LITIGATION", "LABOR_WORKFORCE"]

    complex_risks = [r for r in risks if getattr(r, "category", "") in complexity_categories]
    raw_inputs = {
        "complex_risks_count": len(complex_risks),
    }

    for r in complex_risks:
        level = getattr(r, "risk_level", "LOW")
        if level == "CRITICAL":
            score -= 18.0
            drivers.append({"driver": f"Critical deal complexity hurdle: {getattr(r, 'title', 'Hurdle')}", "type": "NEGATIVE", "impact": "HIGH"})
        elif level == "HIGH":
            score -= 10.0
            drivers.append({"driver": f"High integration/regulatory complexity: {getattr(r, 'title', 'Complexity')}", "type": "NEGATIVE", "impact": "MEDIUM"})
        elif level == "MODERATE":
            score -= 4.0

    if not complex_risks:
        drivers.append({"driver": "Clean operational structure with minimal integration friction", "type": "POSITIVE", "impact": "MEDIUM"})

    score = max(0.0, min(100.0, score))
    return {
        "name": "DEAL_COMPLEXITY",
        "score": round(score, 1),
        "status": DataAvailabilityStatus.AVAILABLE.value,
        "confidence": 0.88,
        "raw_inputs": raw_inputs,
        "explanation": f"Evaluated {len(complex_risks)} structural/integration complexity factors.",
        "drivers": drivers,
    }


# ==========================================
# 2. Master Composite Scoring Orchestrator
# ==========================================

def calculate_composite_decision_score(
    deal: Any,
    statements: List[Any],
    metrics: List[Any],
    qoe_adjustments: List[Any],
    valuation: Optional[Any],
    valuation_outputs: List[Any],
    risks: List[Any],
    documents: List[Any],
    citations: List[Any],
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate the complete, deterministic Composite DealGuard Decision Score and structured explanation."""
    weights = dict(custom_weights or DEFAULT_COMPONENT_WEIGHTS)
    validate_weights(weights)

    target_ev = getattr(deal, "target_ev", None)

    # 1. Compute Individual Normalized Components
    c_fin = normalize_financial_health(statements, metrics, qoe_adjustments)
    c_val = normalize_valuation_attractiveness(target_ev, valuation, valuation_outputs)
    c_risk = normalize_risk_exposure(risks)
    c_rev = normalize_revenue_quality(statements, risks)
    c_evid = normalize_evidence_confidence(documents, citations, statements)
    c_cmpx = normalize_deal_complexity(risks, deal)

    components = {
        "FINANCIAL_HEALTH": c_fin,
        "VALUATION_ATTRACTIVENESS": c_val,
        "RISK_EXPOSURE": c_risk,
        "REVENUE_QUALITY": c_rev,
        "EVIDENCE_CONFIDENCE": c_evid,
        "DEAL_COMPLEXITY": c_cmpx,
    }

    # 2. Compute Weighted Composite Score
    composite_score = 0.0
    total_confidence = 0.0
    all_positive_drivers: List[Dict[str, Any]] = []
    all_negative_drivers: List[Dict[str, Any]] = []
    missing_info: List[str] = []

    for name, comp in components.items():
        w = weights[name]
        comp["weight"] = round(w, 4)
        comp_score = comp["score"]
        weighted_contrib = comp_score * w
        comp["weighted_contribution"] = round(weighted_contrib, 2)
        composite_score += weighted_contrib
        total_confidence += comp["confidence"] * w

        # Collect drivers
        for d in comp.get("drivers", []):
            if d.get("type") == "POSITIVE":
                all_positive_drivers.append({**d, "component": name})
            elif d.get("type") == "NEGATIVE":
                all_negative_drivers.append({**d, "component": name})

        # Track missing info
        if comp["status"] == DataAvailabilityStatus.INSUFFICIENT_DATA.value:
            missing_info.append(f"Insufficient data for {name.replace('_', ' ').title()}")
        elif comp["status"] == DataAvailabilityStatus.PARTIAL.value:
            missing_info.append(f"Partial data available for {name.replace('_', ' ').title()}")

    final_score = round(max(0.0, min(100.0, composite_score)), 1)
    final_confidence = round(max(0.0, min(1.0, total_confidence)), 2)
    decision_band = classify_decision_band(final_score)
    band_desc = get_band_description(decision_band)

    # 3. Formulate Actionable Structured Recommendations
    recommendations: List[str] = []
    if final_score >= 80.0:
        recommendations.append("Priority acquisition candidate. Proceed to definitive purchase agreement drafting.")
        recommendations.append("Execute confirmatory customer call diligence and lock executive retention contracts.")
    elif final_score >= 65.0:
        recommendations.append("Favorable acquisition opportunity. Recommends standard 12-month general indemnity escrow (10% of EV).")
        recommendations.append("Verify working capital peg and debt-like item definitions before closing.")
    elif final_score >= 50.0:
        recommendations.append("Proceed with caution. Recommend negotiating a 10-15% purchase price reduction or earnout structure.")
        recommendations.append("Require pre-closing remediation for highlighted critical/high diligence findings.")
    else:
        recommendations.append("High downside exposure. Diligence committee recommends against acquisition at current terms.")
        recommendations.append("If pursuing, mandate special indemnity carve-outs and escrow covering all identified risks.")

    return {
        "scoring_version": CURRENT_SCORING_VERSION,
        "overall_score": final_score,
        "decision_band": decision_band.value,
        "decision_band_description": band_desc,
        "confidence_score": final_confidence,
        "weights_used": weights,
        "components": components,
        "positive_drivers": all_positive_drivers,
        "negative_drivers": all_negative_drivers,
        "missing_information": missing_info,
        "recommendations": recommendations,
    }
