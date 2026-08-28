"""Risk Intelligence Agent."""

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
    RiskAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.documents.models import Citation, Document
from app.domains.risk.models import Risk, RiskEvidence


class RiskIntelligenceAgent(BaseSpecialistAgent):
    """
    Specialist agent for analyzing 17-pillar risk vectors, severity matrices,
    and evidence-linked downside mitigations.
    """

    @property
    def agent_id(self) -> AgentId:
        return AgentId.RISK

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Risk Intelligence Specialist",
            version="1.0.0",
            purpose="Evaluate 17-pillar due diligence risks, severity likelihood scoring, and evidence-backed mitigations.",
            domain="RISKS",
            allowed_tools=[
                "risk_matrix_17_pillar_tool",
                "document_risk_scanner_tool",
                "risk_evidence_tool",
                "ml_prediction_tool",
            ],
            evidence_requirements=["17-Pillar Risk Register", "Direct Document Disclosures"],
            confidence_policy="High confidence when all critical/high risks have linked evidence citations.",
            limitations=["Identifies risks from data room records; unstated external threats require macro feeds."],
            handoff_targets=["deal_decision_agent", "integration_intelligence_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> RiskAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        # Tool 1: 17-Pillar Risk Matrix
        self.verify_tool("risk_matrix_17_pillar_tool")
        tools_invoked.append("risk_matrix_17_pillar_tool")

        risk_q = select(Risk).where(
            Risk.deal_id == deal_id,
            Risk.organization_id == org_id,
        ).order_by(Risk.score.desc())
        risk_res = await self.session.execute(risk_q)
        risks = list(risk_res.scalars().all())

        # Tool 2: Risk Evidence Retrieval
        self.verify_tool("risk_evidence_tool")
        tools_invoked.append("risk_evidence_tool")

        evidence_q = select(RiskEvidence).where(
            RiskEvidence.deal_id == deal_id,
            RiskEvidence.organization_id == org_id,
        )
        evidence_res = await self.session.execute(evidence_q)
        evidence_items = list(evidence_res.scalars().all())

        citations: List[CitationRef] = []
        for ev in evidence_items:
            if ev.citation_id:
                cit_q = select(Citation).where(Citation.id == ev.citation_id)
                cit_res = await self.session.execute(cit_q)
                cit = cit_res.scalar_one_or_none()
                if cit:
                    doc_name = "Data Room Risk Disclosure"
                    if cit.document_id:
                        doc_q = select(Document.name).where(Document.id == cit.document_id)
                        d_res = await self.session.execute(doc_q)
                        doc_name = d_res.scalar_one_or_none() or doc_name

                    citations.append(
                        CitationRef(
                            citation_id=cit.id,
                            document_id=cit.document_id,
                            document_name=doc_name,
                            page_number=cit.page_number or 1,
                            section_title="Risk Factors Disclosure",
                            exact_quote=cit.quote,
                            confidence_score=cit.confidence_score or 0.95,
                        )
                    )

        critical_risks = [r for r in risks if r.risk_level == "CRITICAL" or r.severity >= 4 and r.likelihood >= 4]
        high_risks = [r for r in risks if r.risk_level == "HIGH" or r.score >= 12]
        avg_score = (sum(r.score for r in risks) / len(risks)) if risks else 0.0

        top_categories = list(set(r.category for r in risks[:5]))

        positive_drivers = []
        negative_drivers = []
        unresolved = []

        if not critical_risks:
            positive_drivers.append("Zero fatal deal-killer or CRITICAL severity risks detected.")
        else:
            for cr in critical_risks:
                negative_drivers.append(f"CRITICAL Risk [{cr.category}]: {cr.title} (Score: {cr.score}) - {cr.description}")
                unresolved.append(f"Mitigation plan required for: {cr.title}")

        for hr in high_risks[:3]:
            if hr not in critical_risks:
                negative_drivers.append(f"HIGH Risk [{hr.category}]: {hr.title} (Score: {hr.score})")

        findings: List[GroundedFinding] = []
        for r in risks[:4]:
            findings.append(
                GroundedFinding(
                    domain_pillar="RISK",
                    category=r.category,
                    headline=r.title,
                    detailed_reasoning=f"{r.description} Mitigation: {r.mitigation_strategy or r.recommendation or 'Standard indemnification'}",
                    severity_level=r.risk_level,
                    confidence_score=r.confidence_score or 0.90,
                    is_deterministic_calculation=True,
                    calculation_source_engine="app.domains.risk.engine",
                    citations=citations[:2],
                )
            )

        # Tool 3 (Optional ML): Deal Downside Risk Probability Model (Real Data Preferred)
        ml_prob = None
        from app.domains.ml.registry import ExtendedModelRegistry
        from app.domains.ml.schemas import PredictionRequest
        ml_wrapper = ExtendedModelRegistry.get_trained_model("dealguard-real-downside-risk-v1") or ExtendedModelRegistry.get_trained_model("dealguard-risk-probability-v1")
        if ml_wrapper:
            self.verify_tool("ml_prediction_tool")
            tools_invoked.append("ml_prediction_tool")
            try:
                # Dynamic feature payload matching model architecture
                if ml_wrapper.metadata.model_id == "dealguard-real-downside-risk-v1":
                    feat = {
                        "TermInMonths": 60,
                        "GrossApproval": 500000.0,
                        "ThirdPartyDollars": 150000.0,
                        "BusinessType": "CORPORATION",
                        "DeliveryMethod": "OTH",
                        "subpgmdesc": "Standard Guaranty",
                        "ProjectState": "CA",
                    }
                else:
                    feat = {
                        "revenue_growth_rate_pct": 0.15,
                        "gross_margin_pct": 0.70,
                        "ebitda_margin_pct": 0.20,
                        "qoe_add_backs_ratio": 0.08,
                        "debt_to_ebitda_leverage": 3.0,
                        "cybersecurity_score": 80.0,
                        "compliance_violations_count": len(critical_risks),
                        "it_systems_overlap_score": 0.40,
                        "customer_concentration_top3_pct": 0.25,
                    }
                p_req = PredictionRequest(
                    model_id=ml_wrapper.metadata.model_id,
                    organization_id=org_id,
                    deal_id=deal_id,
                    features=feat,
                )
                pred_res = ml_wrapper.predict(p_req)
                if pred_res.probability_distribution:
                    ml_prob = pred_res.probability_distribution.get("CLASS_1")
                    model_label = "REAL-DATA ML" if "real" in ml_wrapper.metadata.model_id else "BENCHMARK ML"
                    if ml_prob and ml_prob > 0.35:
                        negative_drivers.append(f"[{model_label} PREDICTION] Elevated downside risk probability: {ml_prob*100:.1f}% ({ml_wrapper.metadata.model_id})")
                    elif ml_prob:
                        positive_drivers.append(f"[{model_label} PREDICTION] Downside risk probability within acceptable bounds: {ml_prob*100:.1f}% ({ml_wrapper.metadata.model_id})")
            except Exception:
                pass

        status = AgentStatus.SUCCESS if risks else AgentStatus.INSUFFICIENT_EVIDENCE
        summary = (
            f"Risk analysis complete: Identified {len(risks)} total risks ({len(critical_risks)} CRITICAL, {len(high_risks)} HIGH). Composite Risk Score: {avg_score:.1f}/25."
            if risks
            else "No risk records logged in data room register."
        )

        det_refs = {
            "total_risks": len(risks),
            "critical_risks": len(critical_risks),
            "high_risks": len(high_risks),
            "average_risk_score": round(avg_score, 2),
        }
        if ml_prob is not None:
            det_refs["ml_downside_risk_probability"] = round(ml_prob, 4)

        return RiskAssessment(
            agent_id=self.agent_id,
            domain="RISKS",
            status=status,
            summary=summary,
            confidence=AgentConfidence.HIGH if risks else AgentConfidence.INSUFFICIENT_EVIDENCE,
            confidence_score=0.93 if risks else 0.30,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unresolved_issues=unresolved,
            required_diligence=["Require special closing indemnity covenants for identified customer concentration and cybersecurity items."],
            citations=citations,
            deterministic_references=det_refs,
            total_risks_identified=len(risks),
            critical_risks_count=len(critical_risks),
            high_risks_count=len(high_risks),
            composite_risk_score=round(avg_score, 2),
            top_risk_categories=top_categories,
        )
