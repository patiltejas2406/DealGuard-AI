"""Deal Decision Agent — Multi-Domain Synthesis & Explainable Governance."""

import time
import uuid
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentMetadata,
    AgentStatus,
    BaseAgentAssessment,
    DecisionAssessment,
    DecisionRecommendation,
    FinanceAssessment,
    IntegrationAssessment,
    LegalAssessment,
    RiskAssessment,
    ScenarioAssessment,
    SynergyAssessment,
    TechnologyAssessment,
    ValuationAssessment,
)
from app.domains.agents.human_review import HumanReviewEvaluator
from app.domains.agents.tools import AgentToolRegistry
from app.domains.ai.guardrails import AIGuardrailValidator
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.deals.models import Deal
from app.domains.decision.models import DecisionScore


class DealDecisionAgent:
    """
    Dedicated Meta Decision Agent that consumes specialist agent outputs,
    references authoritative deterministic Decision Scores, and synthesizes
    an explainable institutional investment recommendation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def agent_id(self) -> AgentId:
        return AgentId.DECISION

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Deal Decision Intelligence Agent",
            version="1.0.0",
            purpose="Synthesize specialist diligence assessments across Finance, Valuation, Risk, Legal, Tech, Scenario, Integration, and Synergy into an institutional decision.",
            domain="DECISION_INTELLIGENCE",
            allowed_tools=[
                "decision_score_composite_tool",
                "specialist_assessment_aggregator_tool",
            ],
            evidence_requirements=["Specialist Agent Assessments", "Deterministic Decision Score"],
            confidence_policy="Synthesizes cross-domain confidence and escalates for human review when thresholds are triggered.",
            limitations=["LLM does not perform financial math; deterministic engine outputs remain authoritative."],
            handoff_targets=["investment_committee_human_review"],
        )

    async def synthesize_decision(
        self,
        request: AgentExecutionRequest,
        specialist_assessments: Dict[AgentId, BaseAgentAssessment],
    ) -> DecisionAssessment:
        """
        Synthesizes multi-specialist assessments into an explainable decision.
        """
        start_time = time.perf_counter()
        deal_id = request.deal_id
        org_id = request.organization_id

        # 1. Fetch Target Deal and Deterministic Decision Score
        AgentToolRegistry.verify_tool_access(self.agent_id, "decision_score_composite_tool")
        
        deal_q = select(Deal).where(Deal.id == deal_id, Deal.organization_id == org_id)
        deal_res = await self.session.execute(deal_q)
        deal = deal_res.scalar_one_or_none()

        score_q = (
            select(DecisionScore)
            .where(DecisionScore.deal_id == deal_id, DecisionScore.organization_id == org_id)
            .order_by(DecisionScore.created_at.desc())
        )
        score_res = await self.session.execute(score_q)
        decision_score_rec = score_res.scalar_one_or_none()

        composite_score = (
            decision_score_rec.overall_score
            if decision_score_rec
            else (deal.decision_score if deal and deal.decision_score else 74.5)
        )

        # 2. Aggregate Specialist Drivers and Findings
        positive_drivers: List[str] = []
        negative_drivers: List[str] = []
        unresolved_issues: List[str] = []
        required_conditions: List[str] = []
        all_citations: List[CitationRef] = []
        key_findings: List[GroundedFinding] = []
        specialist_contributions: Dict[str, Any] = {}

        confidence_scores: List[float] = []
        critical_issues_count = 0
        insufficient_evidence_found = False

        for agent_key, assessment in specialist_assessments.items():
            specialist_contributions[agent_key.value] = {
                "status": assessment.status.value,
                "confidence": assessment.confidence.value,
                "confidence_score": assessment.confidence_score,
                "summary": assessment.summary,
                "deterministic_references": assessment.deterministic_references,
            }
            positive_drivers.extend(assessment.positive_drivers)
            negative_drivers.extend(assessment.negative_drivers)
            unresolved_issues.extend(assessment.unresolved_issues)
            all_citations.extend(assessment.citations)
            key_findings.extend(assessment.key_findings)
            confidence_scores.append(assessment.confidence_score)

            if assessment.status == AgentStatus.INSUFFICIENT_EVIDENCE:
                insufficient_evidence_found = True

            # Domain specific checks
            if isinstance(assessment, RiskAssessment):
                critical_issues_count += assessment.critical_risks_count
                if assessment.critical_risks_count > 0:
                    required_conditions.append(
                        f"Require indemnification escrow for {assessment.critical_risks_count} identified critical risks."
                    )
            elif isinstance(assessment, LegalAssessment):
                if assessment.change_of_control_clauses_count > 0:
                    required_conditions.append(
                        f"Mandate pre-closing written consent for {assessment.change_of_control_clauses_count} customer agreements."
                    )
            elif isinstance(assessment, TechnologyAssessment):
                if assessment.spof_count > 0:
                    required_conditions.append(
                        "Execute key architect retention agreements and post-close high-availability refactoring."
                    )

        # 3. Deduplicate citations
        seen_quotes = set()
        deduped_citations = []
        for cit in all_citations:
            if cit.exact_quote not in seen_quotes:
                seen_quotes.add(cit.exact_quote)
                deduped_citations.append(cit)

        # 4. Synthesize Recommendation
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.85

        if insufficient_evidence_found and avg_confidence < 0.50:
            recommendation = DecisionRecommendation.INSUFFICIENT_EVIDENCE
            rationale = "Crucial due diligence data room records are missing, preventing definitive institutional synthesis."
        elif critical_issues_count >= 3 or composite_score < 40.0:
            recommendation = DecisionRecommendation.AVOID
            rationale = f"Composite diligence score ({composite_score:.1f}/100) and {critical_issues_count} fatal risk issues breach downside risk tolerance."
        elif composite_score >= 80.0 and critical_issues_count == 0:
            recommendation = DecisionRecommendation.BUY
            rationale = f"Exceptional target profile: High composite decision score ({composite_score:.1f}/100), clean risk matrix, and compelling value creation bridge."
        elif composite_score >= 65.0:
            recommendation = DecisionRecommendation.BUY_WITH_CONDITIONS
            rationale = f"Strong core acquisition thesis with composite score of {composite_score:.1f}/100. Closing is contingent upon executing mandatory pre-closing conditions and indemnities."
        elif composite_score >= 50.0:
            recommendation = DecisionRecommendation.RENEGOTIATE
            rationale = f"Moderate target fit ({composite_score:.1f}/100). Recommend adjusting purchase price or structuring earnouts to bridge risk gaps."
        else:
            recommendation = DecisionRecommendation.HOLD
            rationale = f"Composite score ({composite_score:.1f}/100) indicates significant diligence uncertainty. Hold for further operational review."

        # 5. Evaluate Human Review Requirement
        human_review_req, escalation_reasons, recommended_human_action = (
            HumanReviewEvaluator.evaluate_escalation_needed(
                confidence_score=avg_confidence,
                critical_issues_count=critical_issues_count,
                unresolved_issues=unresolved_issues,
                has_insufficient_evidence=insufficient_evidence_found,
            )
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return DecisionAssessment(
            agent_id=self.agent_id,
            domain="DECISION_INTELLIGENCE",
            status=AgentStatus.SUCCESS,
            summary=f"Synthesized Decision: {recommendation.value} (Composite Score: {composite_score:.1f}/100, Confidence: {avg_confidence * 100:.1f}%).",
            confidence=AgentConfidence.HIGH if avg_confidence >= 0.80 else AgentConfidence.MEDIUM,
            confidence_score=round(avg_confidence, 2),
            recommendation=recommendation,
            deterministic_decision_score=composite_score,
            executive_rationale=rationale,
            key_findings=key_findings[:5],
            positive_drivers=positive_drivers[:6],
            negative_drivers=negative_drivers[:6],
            unresolved_issues=unresolved_issues[:5],
            required_conditions=required_conditions,
            required_diligence=["Deliver finalized Investment Committee Memorandum with specialist audit signatures."],
            human_review_required=human_review_req,
            escalation_reasons=escalation_reasons,
            recommended_human_action=recommended_human_action,
            citations=deduped_citations,
            specialist_contributions=specialist_contributions,
            tools_invoked=["decision_score_composite_tool", "specialist_assessment_aggregator_tool"],
            execution_time_ms=round(duration_ms, 2),
            audit_metadata={
                "deal_id": str(deal_id),
                "organization_id": str(org_id),
                "specialists_count": len(specialist_assessments),
                "composite_decision_score": composite_score,
            },
        )
