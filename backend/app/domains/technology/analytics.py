"""Deterministic Technology Risk, Cloud Cost & Operational Analytics Engine."""

from typing import Any, Dict, List, Optional
from app.domains.technology.models import (
    OperationalMetric,
    TechnologyDependency,
    TechnologyFinding,
)

SEVERITY_WEIGHTS = {"CRITICAL": 25.0, "HIGH": 12.0, "MEDIUM": 5.0, "LOW": 2.0}
LIKELIHOOD_MULTIPLIERS = {"HIGH": 1.0, "MEDIUM": 0.75, "LOW": 0.5}


def calculate_technology_risk_score(
    findings: List[TechnologyFinding],
    metrics: List[OperationalMetric],
    dependencies: List[TechnologyDependency],
) -> Dict[str, Any]:
    """Calculate deterministic Technology Risk Score (0-100) and Technology Health Score (100 - Risk Score)."""
    raw_risk = 0.0

    # 1. Findings risk contribution
    for f in findings:
        if f.status not in ["MITIGATED", "ACCEPTED"]:
            s_wt = SEVERITY_WEIGHTS.get(f.severity.upper(), 5.0)
            l_mult = LIKELIHOOD_MULTIPLIERS.get(f.likelihood.upper(), 0.75)
            raw_risk += s_wt * l_mult

    # 2. SLA Deviations / Operational Breaches
    for m in metrics:
        if m.status == "CRITICAL_BREACH":
            raw_risk += 15.0
        elif m.status == "DEVIATION":
            raw_risk += 8.0

    # 3. Single Points of Failure (SPOF)
    spof_count = sum(1 for d in dependencies if d.is_single_point_of_failure)
    raw_risk += spof_count * 10.0

    risk_score = round(min(100.0, max(0.0, raw_risk)), 1)
    health_score = round(max(0.0, 100.0 - risk_score), 1)

    if risk_score >= 60.0:
        risk_band = "CRITICAL"
    elif risk_score >= 35.0:
        risk_band = "HIGH"
    elif risk_score >= 15.0:
        risk_band = "MODERATE"
    else:
        risk_band = "LOW"

    return {
        "technology_risk_score": risk_score,
        "technology_health_score": health_score,
        "risk_band": risk_band,
        "spof_count": spof_count,
    }


def calculate_cloud_cost_summary(
    metrics: List[OperationalMetric],
    dependencies: List[TechnologyDependency],
) -> Dict[str, Any]:
    """Aggregate cloud infrastructure spend and major cost drivers."""
    cloud_metrics = [m for m in metrics if m.metric_category == "CLOUD_SPEND"]
    annual_spend = 0.0

    if cloud_metrics:
        # If monthly spend metric present
        monthly_m = next((m for m in cloud_metrics if "monthly" in m.metric_name.lower()), None)
        if monthly_m:
            annual_spend = monthly_m.observed_value * 12.0
        else:
            annual_spend = sum(m.observed_value for m in cloud_metrics)
    else:
        # Fallback to summing cloud provider dependency costs
        cloud_deps = [d for d in dependencies if d.dependency_type in ["CLOUD_PROVIDER", "DATABASE"]]
        annual_spend = sum(float(d.annual_cost or 0.0) for d in cloud_deps)

    return {
        "annual_cloud_spend": round(annual_spend, 2),
        "monthly_run_rate": round(annual_spend / 12.0, 2) if annual_spend > 0 else 0.0,
    }


def compute_technology_summary_metrics(
    findings: List[TechnologyFinding],
    metrics: List[OperationalMetric],
    dependencies: List[TechnologyDependency],
) -> Dict[str, Any]:
    """Aggregate complete executive technology diligence summary."""
    risk_info = calculate_technology_risk_score(findings, metrics, dependencies)
    cloud_info = calculate_cloud_cost_summary(metrics, dependencies)

    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f.severity.upper() if f.severity else "MEDIUM"
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    sla_metrics = [m for m in metrics if m.metric_category == "UPTIME_SLA"]
    avg_uptime = (
        round(sum(m.observed_value for m in sla_metrics) / len(sla_metrics), 2)
        if sla_metrics
        else 99.9
    )
    sla_breaches = sum(1 for m in sla_metrics if m.status in ["DEVIATION", "CRITICAL_BREACH"])

    critical_deps_count = sum(1 for d in dependencies if d.criticality in ["CRITICAL", "HIGH"])

    total_exposure = sum(float(f.monetary_exposure or 0.0) for f in findings)

    return {
        **risk_info,
        **cloud_info,
        "total_findings_count": len(findings),
        "critical_findings_count": sev_counts["CRITICAL"],
        "high_findings_count": sev_counts["HIGH"],
        "medium_findings_count": sev_counts["MEDIUM"],
        "low_findings_count": sev_counts["LOW"],
        "total_dependencies_count": len(dependencies),
        "critical_dependencies_count": critical_deps_count,
        "average_uptime_pct": avg_uptime,
        "sla_breaches_count": sla_breaches,
        "total_monetary_exposure": round(total_exposure, 2),
    }
