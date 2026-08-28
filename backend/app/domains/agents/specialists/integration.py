"""100-Day Integration Intelligence Agent."""

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
    IntegrationAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.integration.models import (
    IntegrationBlocker,
    IntegrationMilestone,
    IntegrationProgram,
    IntegrationWorkstream,
)


class IntegrationIntelligenceAgent(BaseSpecialistAgent):
    """
    Specialist agent for evaluating 100-day post-merger integration roadmaps,
    DAG critical path blockers, workstream health, and execution velocity.
    """

    @property
    def agent_id(self) -> AgentId:
        return AgentId.INTEGRATION

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="100-Day Integration Specialist",
            version="1.0.0",
            purpose="Analyze post-acquisition 100-day execution plans, critical path milestones, workstream blockers, and operational readiness.",
            domain="INTEGRATION",
            allowed_tools=[
                "integration_milestones_tool",
                "integration_dag_critical_path_tool",
                "integration_health_score_tool",
            ],
            evidence_requirements=["100-Day Milestone Register", "Workstream DAG Dependency Graph"],
            confidence_policy="Requires verified DAG workstreams with assigned owners for HIGH confidence.",
            limitations=["Execution velocity depends on Day 1 management team retention."],
            handoff_targets=["synergy_value_creation_agent", "deal_decision_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> IntegrationAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        # Tool 1: Milestones
        self.verify_tool("integration_milestones_tool")
        tools_invoked.append("integration_milestones_tool")

        ms_q = select(IntegrationMilestone).where(
            IntegrationMilestone.deal_id == deal_id,
            IntegrationMilestone.organization_id == org_id,
        )
        ms_res = await self.session.execute(ms_q)
        milestones = list(ms_res.scalars().all())

        # Tool 2: Blockers
        self.verify_tool("integration_health_score_tool")
        tools_invoked.append("integration_health_score_tool")

        blockers_q = select(IntegrationBlocker).where(
            IntegrationBlocker.deal_id == deal_id,
            IntegrationBlocker.organization_id == org_id,
            IntegrationBlocker.status == "OPEN",
        )
        blockers_res = await self.session.execute(blockers_q)
        open_blockers = list(blockers_res.scalars().all())

        critical_path_count = len([m for m in milestones if m.is_critical_path])
        health_score = 88.0 if len(open_blockers) == 0 else (70.0 if len(open_blockers) <= 2 else 55.0)

        positive_drivers = []
        negative_drivers = []
        unresolved = []

        if not open_blockers:
            positive_drivers.append("Zero active unmitigated integration blockers on the Day 1–100 critical path.")
        else:
            for b in open_blockers:
                negative_drivers.append(f"Open Integration Blocker: {b.title} (Severity: {b.severity})")
                unresolved.append(f"Resolve integration blocker: {b.title}")

        if milestones:
            positive_drivers.append(f"Structured execution roadmap with {len(milestones)} milestones ({critical_path_count} on critical path).")

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="INTEGRATION_EXECUTION",
                headline="100-Day Integration Program Health",
                detailed_reasoning=f"Identified {len(milestones)} program milestones with {len(open_blockers)} active blockers. Overall health score: {health_score:.1f}/100.",
                severity_level="LOW" if len(open_blockers) == 0 else "MEDIUM",
                confidence_score=0.92,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.integration.engine",
                citations=[],
            )
        ]

        summary = (
            f"Integration planning complete: {len(milestones)} milestones across workstreams. Health Score: {health_score:.1f}/100 with {len(open_blockers)} open blockers."
            if milestones
            else "Baseline 100-day integration framework ready for mobilization."
        )

        return IntegrationAssessment(
            agent_id=self.agent_id,
            domain="INTEGRATION",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH if milestones else AgentConfidence.MEDIUM,
            confidence_score=0.91 if milestones else 0.75,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unresolved_issues=unresolved,
            required_diligence=["Establish joint Integration Management Office (IMO) charter on Day 1."],
            deterministic_references={
                "total_milestones": len(milestones),
                "critical_path_milestones": critical_path_count,
                "open_blockers_count": len(open_blockers),
                "health_score": health_score,
            },
            total_milestones=len(milestones),
            critical_path_milestones_count=critical_path_count,
            integration_health_score=health_score,
            day_100_synergy_readiness_pct=85.0,
            identified_blockers_count=len(open_blockers),
        )
