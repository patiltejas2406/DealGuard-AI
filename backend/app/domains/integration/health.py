"""Deterministic Integration Health Score Engine and Execution Metrics."""

from typing import Any, Dict, List
from app.domains.integration.config import IntegrationHealthBand


def calculate_integration_health_score(
    workstreams: List[Any],
    milestones: List[Any],
    blockers: List[Any],
    current_day_offset: int = 1,
) -> Dict[str, Any]:
    """Calculate deterministic Integration Health Score (0-100) and identify execution risk drivers."""
    if not milestones and not workstreams:
        return {
            "health_score": 100.0,
            "health_band": IntegrationHealthBand.HEALTHY.value,
            "penalties": {},
            "metrics": {
                "total_workstreams": 0,
                "total_milestones": 0,
                "completed_milestones": 0,
                "overdue_milestones": 0,
                "open_blockers": 0,
                "critical_blockers": 0,
                "overall_progress_pct": 0.0,
            },
        }

    total_milestones = len(milestones)
    completed_milestones = 0
    overdue_milestones = 0
    at_risk_milestones = 0
    blocked_milestones = 0
    synergy_delayed_milestones = 0

    total_completion_sum = 0.0

    for m in milestones:
        t_day = getattr(m, "target_day", 100)
        status = getattr(m, "status", "NOT_STARTED")
        c_pct = float(getattr(m, "completion_pct", 0.0) or 0.0)
        total_completion_sum += c_pct

        if status == "COMPLETED" or c_pct >= 100.0:
            completed_milestones += 1
        elif (t_day < current_day_offset and c_pct < 100.0) or status == "OVERDUE":
            overdue_milestones += 1
        elif status == "BLOCKED":
            blocked_milestones += 1
        elif status == "AT_RISK":
            at_risk_milestones += 1

        if getattr(m, "linked_synergy_id", None) and status in ["OVERDUE", "BLOCKED", "AT_RISK"]:
            synergy_delayed_milestones += 1

    overall_progress = round(total_completion_sum / max(1, total_milestones), 1)

    # Blockers count
    open_blockers = [b for b in blockers if getattr(b, "status", "OPEN") == "OPEN"]
    critical_blockers = [b for b in open_blockers if getattr(b, "severity", "MEDIUM") == "CRITICAL"]
    high_blockers = [b for b in open_blockers if getattr(b, "severity", "MEDIUM") == "HIGH"]

    # Blocked/At-Risk Workstreams
    blocked_workstreams = [w for w in workstreams if getattr(w, "status", "NOT_STARTED") == "BLOCKED"]
    at_risk_workstreams = [w for w in workstreams if getattr(w, "status", "NOT_STARTED") == "AT_RISK"]

    # Calculate Deductions
    penalty_overdue = min(30.0, overdue_milestones * 6.0)
    penalty_critical_blockers = min(30.0, len(critical_blockers) * 15.0)
    penalty_high_blockers = min(20.0, len(high_blockers) * 7.5)
    penalty_blocked_milestones = min(20.0, blocked_milestones * 5.0)
    penalty_at_risk_ws = min(15.0, (len(blocked_workstreams) * 8.0) + (len(at_risk_workstreams) * 4.0))
    penalty_synergy_delay = min(15.0, synergy_delayed_milestones * 5.0)

    total_deductions = (
        penalty_overdue
        + penalty_critical_blockers
        + penalty_high_blockers
        + penalty_blocked_milestones
        + penalty_at_risk_ws
        + penalty_synergy_delay
    )

    final_score = round(max(0.0, min(100.0, 100.0 - total_deductions)), 1)

    # Determine Health Band
    if final_score >= 80.0:
        band = IntegrationHealthBand.HEALTHY.value
    elif final_score >= 65.0:
        band = IntegrationHealthBand.WATCH.value
    elif final_score >= 50.0:
        band = IntegrationHealthBand.AT_RISK.value
    else:
        band = IntegrationHealthBand.CRITICAL.value

    return {
        "health_score": final_score,
        "health_band": band,
        "penalties": {
            "overdue_milestones_penalty": penalty_overdue,
            "critical_blockers_penalty": penalty_critical_blockers,
            "high_blockers_penalty": penalty_high_blockers,
            "blocked_milestones_penalty": penalty_blocked_milestones,
            "workstream_risk_penalty": penalty_at_risk_ws,
            "synergy_milestone_delay_penalty": penalty_synergy_delay,
            "total_deductions": round(total_deductions, 1),
        },
        "metrics": {
            "total_workstreams": len(workstreams),
            "blocked_workstreams": len(blocked_workstreams),
            "at_risk_workstreams": len(at_risk_workstreams),
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "overdue_milestones": overdue_milestones,
            "blocked_milestones": blocked_milestones,
            "at_risk_milestones": at_risk_milestones,
            "open_blockers": len(open_blockers),
            "critical_blockers": len(critical_blockers),
            "high_blockers": len(high_blockers),
            "overall_progress_pct": overall_progress,
        },
    }
