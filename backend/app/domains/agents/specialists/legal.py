"""Legal Intelligence Agent."""

import uuid
from typing import List
from sqlalchemy import select

from app.domains.agents.base import BaseSpecialistAgent
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentMetadata,
    AgentStatus,
    LegalAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.documents.models import Citation, Document
from app.domains.legal.models import (
    ComplianceRequirement,
    ContractClause,
    ContractRecord,
    LegalFinding,
)


class LegalIntelligenceAgent(BaseSpecialistAgent):
    """
    Specialist agent for evaluating contract clauses, change of control consent,
    non-compete liabilities, and regulatory compliance posture.
    """

    @property
    def agent_id(self) -> AgentId:
        return AgentId.LEGAL

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Legal Intelligence Specialist",
            version="1.0.0",
            purpose="Analyze contracts for change of control triggers, customer consent requirements, legal value-at-risk, and regulatory compliance.",
            domain="LEGAL_CONTRACTS",
            allowed_tools=[
                "contract_clause_tool",
                "legal_value_at_risk_tool",
                "compliance_matrix_tool",
            ],
            evidence_requirements=["Material Contracts", "Customer MSAs", "Compliance Registers"],
            confidence_policy="Requires verified clause extractions with page and quote citations.",
            limitations=["Does not replace formal outside legal counsel closing opinions."],
            handoff_targets=["deal_decision_agent", "integration_intelligence_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> LegalAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        # Tool 1: Contract Clauses
        self.verify_tool("contract_clause_tool")
        tools_invoked.append("contract_clause_tool")

        clause_q = select(ContractClause).where(
            ContractClause.deal_id == deal_id,
            ContractClause.organization_id == org_id,
        )
        clause_res = await self.session.execute(clause_q)
        clauses = list(clause_res.scalars().all())

        # Tool 2: Legal Findings
        self.verify_tool("legal_value_at_risk_tool")
        tools_invoked.append("legal_value_at_risk_tool")

        findings_q = select(LegalFinding).where(
            LegalFinding.deal_id == deal_id,
            LegalFinding.organization_id == org_id,
        )
        findings_res = await self.session.execute(findings_q)
        legal_findings = list(findings_res.scalars().all())

        # Tool 3: Compliance Requirements
        self.verify_tool("compliance_matrix_tool")
        tools_invoked.append("compliance_matrix_tool")

        comp_q = select(ComplianceRequirement).where(
            ComplianceRequirement.deal_id == deal_id,
            ComplianceRequirement.organization_id == org_id,
        )
        comp_res = await self.session.execute(comp_q)
        compliance_items = list(comp_res.scalars().all())

        if not clauses and not legal_findings and not compliance_items:
            return LegalAssessment(
                agent_id=self.agent_id,
                domain="LEGAL_CONTRACTS",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient contract repository records or legal diligence disclosures in the Data Room.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No material contracts, MSAs, or change-of-control schedules ingested."],
                data_gaps=[
                    "Top 10 customer Master Services Agreements (MSAs) and change-of-control clauses",
                    "Key vendor and cloud infrastructure licensing agreements",
                    "Regulatory compliance audit reports and litigation history",
                ],
                required_diligence=["Upload executed customer agreements and commercial contracts to the Data Room."],
                deterministic_references={
                    "contracts_analyzed": 0,
                    "change_of_control_triggers": 0,
                    "value_at_risk_usd": 0.0,
                    "compliance_requirements_count": 0,
                },
                contracts_analyzed_count=0,
                change_of_control_clauses_count=0,
                value_at_risk_usd=0.0,
                regulatory_compliance_status="DATA_ROOM_PENDING",
            )

        coc_clauses = [c for c in clauses if c.category == "CHANGE_OF_CONTROL" or c.requires_consent]
        total_var = sum(f.monetary_exposure for f in legal_findings) if legal_findings else 0.0

        positive_drivers = []
        negative_drivers = []
        unresolved = []

        if not coc_clauses:
            positive_drivers.append("No restrictive Change of Control consent barriers identified in material customer agreements.")
        else:
            negative_drivers.append(f"Identified {len(coc_clauses)} material contracts with Change of Control consent triggers.")
            unresolved.append(f"Obtain written counterparty consents for {len(coc_clauses)} material agreements prior to close.")

        if total_var > 0:
            negative_drivers.append(f"Estimated legal monetary exposure / Value-at-Risk of ${total_var:,.0f}.")
        else:
            positive_drivers.append("Zero pending material litigation or quantified legal Value-at-Risk exposure.")

        grounded_findings: List[GroundedFinding] = []
        for cl in clauses[:3]:
            grounded_findings.append(
                GroundedFinding(
                    domain_pillar="LEGAL",
                    category=cl.category,
                    headline=cl.clause_title,
                    detailed_reasoning=f'Clause text: "{cl.clause_text}". Requires Consent: {cl.requires_consent}.',
                    finding_type="FACT",
                    severity_level="HIGH" if cl.requires_consent else "LOW",
                    confidence_score=0.94,
                    is_deterministic_calculation=False,
                    citations=[],
                )
            )

        summary = (
            f"Legal diligence complete: Analyzed {len(clauses)} clauses and {len(legal_findings)} findings. Change of control triggers: {len(coc_clauses)}. Legal Exposure: ${total_var:,.0f}."
        )

        data_gaps = []
        if len(clauses) < 5:
            data_gaps.append("Comprehensive vendor and employee IP assignment contract review.")

        return LegalAssessment(
            agent_id=self.agent_id,
            domain="LEGAL_CONTRACTS",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH if clauses else AgentConfidence.MEDIUM,
            confidence_score=0.90 if clauses else 0.70,
            key_findings=grounded_findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unresolved_issues=unresolved,
            data_gaps=data_gaps,
            metrics={
                "contracts_analyzed": len(clauses),
                "change_of_control_triggers": len(coc_clauses),
                "value_at_risk_usd": total_var,
                "compliance_items": len(compliance_items),
            },
            required_diligence=["Execute counterparty consent solicitation schedule 30 days prior to targeted closing date."],
            deterministic_references={
                "contracts_analyzed": len(clauses),
                "change_of_control_triggers": len(coc_clauses),
                "value_at_risk_usd": total_var,
                "compliance_requirements_count": len(compliance_items),
            },
            contracts_analyzed_count=len(clauses),
            change_of_control_clauses_count=len(coc_clauses),
            value_at_risk_usd=total_var,
            regulatory_compliance_status="COMPLIANT" if not any(c.status == "NON_COMPLIANT" for c in compliance_items) else "REQUIRES_REMEDIATION",
        )
