"""Agent Persistence Repository — Executions & Specialist Assessments."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.agents.contract import BaseAgentAssessment, DecisionAssessment
from app.domains.agents.models import AgentAssessmentRecord, AgentExecution


class AgentRepository:
    """Repository managing agent execution records and persisted assessments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_execution_record(
        self,
        execution_id: uuid.UUID,
        deal_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        orchestration_mode: str,
        query: Optional[str],
        selected_agents: List[str],
        decision: DecisionAssessment,
        duration_ms: float,
    ) -> AgentExecution:
        """Create and persist an AgentExecution record."""
        rec = AgentExecution(
            id=execution_id,
            deal_id=deal_id,
            organization_id=organization_id,
            user_id=user_id,
            orchestration_mode=orchestration_mode,
            query=query,
            status="COMPLETED",
            recommendation=decision.recommendation.value,
            decision_score=decision.deterministic_decision_score,
            confidence=decision.confidence.value,
            confidence_score=decision.confidence_score,
            human_review_required=decision.human_review_required,
            duration_ms=duration_ms,
            selected_agents=selected_agents,
            synthesis_payload=decision.model_dump(mode="json"),
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def create_assessment_record(
        self,
        execution_id: uuid.UUID,
        deal_id: uuid.UUID,
        organization_id: uuid.UUID,
        assessment: BaseAgentAssessment,
    ) -> AgentAssessmentRecord:
        """Create and persist a specialist AgentAssessmentRecord."""
        rec = AgentAssessmentRecord(
            execution_id=execution_id,
            deal_id=deal_id,
            organization_id=organization_id,
            agent_id=assessment.agent_id.value,
            domain=assessment.domain,
            status=assessment.status.value,
            confidence=assessment.confidence.value,
            confidence_score=assessment.confidence_score,
            summary=assessment.summary,
            findings_count=len(assessment.key_findings),
            citations_count=len(assessment.citations),
            tools_invoked=assessment.tools_invoked,
            assessment_payload=assessment.model_dump(mode="json"),
            execution_time_ms=assessment.execution_time_ms,
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def list_executions(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, limit: int = 20
    ) -> List[AgentExecution]:
        """List execution records for a specific deal."""
        q = (
            select(AgentExecution)
            .where(
                AgentExecution.organization_id == organization_id,
                AgentExecution.deal_id == deal_id,
            )
            .order_by(desc(AgentExecution.created_at))
            .limit(limit)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def get_execution_with_assessments(
        self, organization_id: uuid.UUID, execution_id: uuid.UUID
    ) -> Optional[AgentExecution]:
        """Retrieve full execution record including all child assessments."""
        q = (
            select(AgentExecution)
            .options(selectinload(AgentExecution.assessments))
            .where(
                AgentExecution.organization_id == organization_id,
                AgentExecution.id == execution_id,
            )
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()
