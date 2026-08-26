"""Deterministic Contract Value at Risk and Exposure Analytics Engine."""

from typing import Any, Dict, List, Optional
from app.domains.legal.models import (
    ComplianceRequirement,
    ContractClause,
    ContractRecord,
    LegalFinding,
)


def calculate_contract_value_at_risk(
    contracts: List[ContractRecord],
    clauses: List[ContractClause],
    findings: List[LegalFinding],
) -> Dict[str, Any]:
    """Calculate deterministic revenue at risk and change-of-control contract metrics.
    
    A contract's annual value is considered AT RISK if it possesses:
    1. A CHANGE_OF_CONTROL or ASSIGNMENT_RESTRICTION clause requiring counterparty consent.
    2. A TERMINATION_RIGHT clause triggered upon merger or acquisition.
    3. An unmitigated CRITICAL or HIGH legal finding.
    """
    contracts_by_id = {c.id: c for c in contracts}
    
    coc_contract_ids = set()
    consent_contract_ids = set()
    at_risk_contract_ids = set()

    for cl in clauses:
        if cl.category in ["CHANGE_OF_CONTROL", "ASSIGNMENT_RESTRICTION"]:
            if cl.contract_id:
                coc_contract_ids.add(cl.contract_id)
            if cl.requires_consent and cl.contract_id:
                consent_contract_ids.add(cl.contract_id)
                at_risk_contract_ids.add(cl.contract_id)
        elif cl.category == "TERMINATION_RIGHT" and cl.severity in ["CRITICAL", "HIGH"]:
            if cl.contract_id:
                at_risk_contract_ids.add(cl.contract_id)

    for f in findings:
        if f.status not in ["MITIGATED", "CONSENT_OBTAINED", "ACCEPTED"] and f.severity in ["CRITICAL", "HIGH"]:
            if f.contract_id:
                at_risk_contract_ids.add(f.contract_id)

    total_annual_value = sum(float(c.annual_value or 0.0) for c in contracts)
    revenue_at_risk = sum(
        float(contracts_by_id[cid].annual_value or 0.0)
        for cid in at_risk_contract_ids
        if cid in contracts_by_id
    )

    revenue_at_risk_pct = (
        round((revenue_at_risk / total_annual_value) * 100.0, 2)
        if total_annual_value > 0
        else 0.0
    )

    return {
        "total_annual_contract_value": round(total_annual_value, 2),
        "revenue_at_risk": round(revenue_at_risk, 2),
        "revenue_at_risk_pct": revenue_at_risk_pct,
        "total_contracts_reviewed": len(contracts),
        "contracts_at_risk_count": len(at_risk_contract_ids),
        "change_of_control_contracts_count": len(coc_contract_ids),
        "consents_required_count": len(consent_contract_ids),
    }


def compute_legal_summary_metrics(
    contracts: List[ContractRecord],
    clauses: List[ContractClause],
    findings: List[LegalFinding],
    compliance_reqs: List[ComplianceRequirement],
) -> Dict[str, Any]:
    """Compute aggregated executive legal diligence KPIs."""
    exposure = calculate_contract_value_at_risk(contracts, clauses, findings)

    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f.severity.upper() if f.severity else "MEDIUM"
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    comp_status_counts = {
        "EVIDENCE_PRESENT": 0,
        "EVIDENCE_MISSING": 0,
        "POTENTIAL_GAP": 0,
        "REQUIRES_REVIEW": 0,
        "COMPLIANT": 0,
    }
    for req in compliance_reqs:
        st = req.status.upper() if req.status else "REQUIRES_REVIEW"
        comp_status_counts[st] = comp_status_counts.get(st, 0) + 1

    conf_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for cl in clauses:
        conf = cl.confidence.upper() if cl.confidence else "HIGH"
        conf_counts[conf] = conf_counts.get(conf, 0) + 1

    return {
        **exposure,
        "total_clauses_extracted": len(clauses),
        "total_findings_count": len(findings),
        "critical_findings_count": sev_counts.get("CRITICAL", 0),
        "high_findings_count": sev_counts.get("HIGH", 0),
        "medium_findings_count": sev_counts.get("MEDIUM", 0),
        "low_findings_count": sev_counts.get("LOW", 0),
        "compliance_total_requirements": len(compliance_reqs),
        "compliance_evidence_present": comp_status_counts.get("EVIDENCE_PRESENT", 0),
        "compliance_evidence_missing": comp_status_counts.get("EVIDENCE_MISSING", 0),
        "compliance_potential_gaps": comp_status_counts.get("POTENTIAL_GAP", 0),
        "confidence_distribution": conf_counts,
    }
