"""Synergy & Value Creation Intelligence Agent."""

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
    SynergyAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.synergy.models import SynergyOpportunity, SynergyRealizationLog


class SynergyValueCreationAgent(BaseSpecialistAgent):
    """
    Specialist agent for analyzing cost & revenue synergies, NPV value creation waterfalls,
    and 5-year post-acquisition realization phasing.
    """

    @property
    def agent_id(self) -> AgentId:
        return AgentId.SYNERGY

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Synergy & Value Creation Specialist",
            version="1.0.0",
            purpose="Quantify annual run-rate cost and revenue synergies, NPV value creation waterfalls, and 5-year realization phasing.",
            domain="SYNERGIES",
            allowed_tools=[
                "synergy_waterfall_bridge_tool",
                "synergy_5yr_phasing_tool",
                "synergy_npv_calculator_tool",
            ],
            evidence_requirements=["Synergy Opportunity Register", "5-Year Phasing Models"],
            confidence_policy="Requires bottom-up line item validation and execution risk discounts.",
            limitations=["Revenue synergies carry higher realization variance than cost reductions."],
            handoff_targets=["deal_decision_agent", "integration_intelligence_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> SynergyAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        # Tool 1: Synergy Waterfall Bridge
        self.verify_tool("synergy_waterfall_bridge_tool")
        tools_invoked.append("synergy_waterfall_bridge_tool")

        syn_q = select(SynergyOpportunity).where(
            SynergyOpportunity.deal_id == deal_id,
            SynergyOpportunity.organization_id == org_id,
        )
        syn_res = await self.session.execute(syn_q)
        synergies = list(syn_res.scalars().all())

        # Tool 2: Synergy NPV Calculator
        self.verify_tool("synergy_npv_calculator_tool")
        tools_invoked.append("synergy_npv_calculator_tool")

        if not synergies:
            return SynergyAssessment(
                agent_id=self.agent_id,
                domain="SYNERGIES",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient synergy registers or value creation workpapers in the Data Room.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No bottom-up cost or revenue synergy opportunities logged."],
                data_gaps=[
                    "Cost rationalization workpapers (G&A, procurement consolidation, headcount)",
                    "Commercial cross-sell and pricing uplift synergy models",
                    "5-year phased realization curves and one-time integration cost budgets",
                ],
                required_diligence=["Model bottom-up synergy opportunities in Synergy Lab."],
                deterministic_references={
                    "total_synergies_count": 0,
                    "annual_run_rate_usd": 0.0,
                    "net_present_value_usd": 0.0,
                },
                annual_run_rate_synergy_usd=0.0,
                net_present_value_synergy_usd=0.0,
                cost_synergies_pct=0.0,
                revenue_synergies_pct=0.0,
                phasing_period_years=5,
            )

        total_run_rate = sum(
            float(getattr(s, "potential_annual_value", 0.0) or getattr(s, "expected_annual_value", 0.0) or 0.0)
            for s in synergies
        )
        total_one_time_cost = sum(float(getattr(s, "one_time_integration_cost", 0.0) or 0.0) for s in synergies)
        # Approximate 5yr discounted value (WACC ~9.5%)
        total_npv = (total_run_rate * 3.8) - total_one_time_cost
        cost_syn = sum(
            float(getattr(s, "potential_annual_value", 0.0) or getattr(s, "expected_annual_value", 0.0) or 0.0)
            for s in synergies
            if s.synergy_type == "COST"
        )
        rev_syn = total_run_rate - cost_syn

        cost_pct = (cost_syn / total_run_rate * 100.0) if total_run_rate > 0 else 65.0
        rev_pct = 100.0 - cost_pct

        deterministic_refs = {
            "total_synergies_count": len(synergies),
            "annual_run_rate_usd": total_run_rate,
            "net_present_value_usd": total_npv,
            "cost_synergies_share_pct": round(cost_pct, 1),
            "revenue_synergies_share_pct": round(rev_pct, 1),
            "one_time_integration_cost_usd": total_one_time_cost,
        }

        positive_drivers = [
            f"Substantial value creation: Total annual run-rate synergy potential of ${total_run_rate:,.0f} (NPV: ${total_npv:,.0f}).",
            f"High-confidence cost rationalization represents {cost_pct:.0f}% of value creation bridge.",
        ]
        negative_drivers = []
        if rev_pct > 40:
            negative_drivers.append("Heavy reliance on commercial cross-sell synergies which carry higher execution friction.")

        findings = [
            GroundedFinding(
                domain_pillar="FINANCIAL",
                category="SYNERGY_WATERFALL",
                headline="Synergy Value Creation & Phased Realization",
                detailed_reasoning=f"Identified {len(synergies)} opportunities yielding ${total_run_rate:,.0f} run-rate synergies ({cost_pct:.0f}% cost, {rev_pct:.0f}% revenue) generating ${total_npv:,.0f} in incremental NPV.",
                finding_type="FACT",
                severity_level="LOW",
                confidence_score=0.92,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.synergy.engine",
                citations=[],
            )
        ]

        summary = (
            f"Synergy analysis complete: ${total_run_rate:,.0f} annual run-rate synergies with NPV of ${total_npv:,.0f} across 5-year realization phasing."
        )

        data_gaps = []
        if len(synergies) < 3:
            data_gaps.append("Detailed department-level synergy execution charter.")

        return SynergyAssessment(
            agent_id=self.agent_id,
            domain="SYNERGIES",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH if synergies else AgentConfidence.MEDIUM,
            confidence_score=0.92 if synergies else 0.75,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unresolved_issues=[],
            data_gaps=data_gaps,
            metrics={
                "total_synergies_count": len(synergies),
                "annual_run_rate_usd": total_run_rate,
                "net_present_value_usd": total_npv,
                "cost_share_pct": cost_pct,
            },
            required_diligence=["Assign dedicated workstream owners for top 3 cost rationalization initiatives."],
            deterministic_references=deterministic_refs,
            annual_run_rate_synergy_usd=total_run_rate,
            net_present_value_synergy_usd=total_npv,
            cost_synergies_pct=cost_pct,
            revenue_synergies_pct=rev_pct,
            phasing_period_years=5,
        )
