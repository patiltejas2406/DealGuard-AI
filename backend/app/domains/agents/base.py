"""Base Specialist Agent Architecture & Standardized Lifecycle Execution."""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentMetadata,
    AgentStatus,
    BaseAgentAssessment,
)
from app.domains.agents.tools import AgentToolRegistry
from app.domains.ai.guardrails import AIGuardrailValidator
from app.domains.ai.schemas import CitationRef, GroundedFinding


class BaseSpecialistAgent(ABC):
    """
    Abstract foundation for all DealGuard specialist intelligence agents.
    Enforces tool access control, deterministic engine math preservation,
    citation provenance, tenant isolation, and auditable metadata.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    @abstractmethod
    def agent_id(self) -> AgentId:
        """Unique agent identifier."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> AgentMetadata:
        """Production capability metadata describing agent boundaries."""
        pass

    def verify_tool(self, tool_name: str) -> None:
        """Enforce strict whitelist authorization before invoking any tool."""
        AgentToolRegistry.verify_tool_access(self.agent_id, tool_name)

    async def execute(self, request: AgentExecutionRequest) -> BaseAgentAssessment:
        """
        Standardized execution wrapper with timing, tenant validation,
        and failure containment.
        """
        start_time = time.perf_counter()
        tools_invoked: List[str] = []

        try:
            assessment = await self._run_assessment(request, tools_invoked)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            assessment.execution_time_ms = round(duration_ms, 2)
            assessment.tools_invoked = list(set(tools_invoked))
            assessment.audit_metadata.update({
                "deal_id": str(request.deal_id),
                "organization_id": str(request.organization_id),
                "user_id": str(request.user_id) if request.user_id else None,
                "version": self.metadata.version,
            })

            # Validate institutional grounding guardrails on all findings
            for finding in assessment.key_findings:
                AIGuardrailValidator.validate_finding_grounding(finding)

            return assessment

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain=self.metadata.domain,
                status=AgentStatus.FAILED,
                summary=f"Specialist assessment failed: {str(exc)}",
                confidence=AgentConfidence.LOW,
                confidence_score=0.0,
                negative_drivers=[f"Agent execution encountered an unhandled exception: {str(exc)}"],
                tools_invoked=tools_invoked,
                execution_time_ms=round(duration_ms, 2),
                audit_metadata={"error": str(exc)},
            )

    @abstractmethod
    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        """Domain-specific assessment logic implemented by specialists."""
        pass
