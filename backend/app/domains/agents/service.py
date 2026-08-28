"""Agent Orchestration Domain Service — Execution, Persistence & Lifecycle API."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.contract import (
    AgentExecutionRequest,
    AgentId,
    AgentMetadata,
    BaseAgentAssessment,
)
from app.domains.agents.orchestrator import AgentOrchestrator, AgentOrchestrationResult
from app.domains.agents.post_deal.extensibility import (
    CorporateStrategyAgent,
    CostOptimizationAgent,
    CustomerRetentionAgent,
    FPandAAgent,
    GrowthIntelligenceAgent,
    MarketingIntelligenceAgent,
    OperationsIntelligenceAgent,
    PerformanceMonitoringAgent,
    RevenueOptimizationAgent,
)
from app.domains.agents.repository import AgentRepository
from app.domains.agents.specialists.finance import FinanceIntelligenceAgent
from app.domains.agents.specialists.integration import IntegrationIntelligenceAgent
from app.domains.agents.specialists.legal import LegalIntelligenceAgent
from app.domains.agents.specialists.risk import RiskIntelligenceAgent
from app.domains.agents.specialists.scenario import ScenarioSimulationAgent
from app.domains.agents.specialists.synergy import SynergyValueCreationAgent
from app.domains.agents.specialists.technology import TechnologyOperationsAgent
from app.domains.agents.specialists.valuation import ValuationAgent
from app.domains.common.context import TenantContext


class AgentOrchestrationService:
    """Service governing agent lifecycle execution, persistence, and querying."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AgentRepository(session)
        self.orchestrator = AgentOrchestrator(session)

    def list_available_agents(self) -> List[AgentMetadata]:
        """List metadata for all 18 registered institutional agents."""
        agents_to_query = [
            FinanceIntelligenceAgent(self.session),
            ValuationAgent(self.session),
            RiskIntelligenceAgent(self.session),
            LegalIntelligenceAgent(self.session),
            TechnologyOperationsAgent(self.session),
            ScenarioSimulationAgent(self.session),
            IntegrationIntelligenceAgent(self.session),
            SynergyValueCreationAgent(self.session),
            # Post-Deal Extensions
            GrowthIntelligenceAgent(self.session),
            RevenueOptimizationAgent(self.session),
            CustomerRetentionAgent(self.session),
            CostOptimizationAgent(self.session),
            OperationsIntelligenceAgent(self.session),
            FPandAAgent(self.session),
            CorporateStrategyAgent(self.session),
            PerformanceMonitoringAgent(self.session),
        ]
        meta_list = [a.metadata for a in agents_to_query]
        meta_list.insert(0, self.orchestrator.decision_agent.metadata)
        return meta_list

    def get_agent_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Retrieve metadata for a specific agent by ID."""
        for meta in self.list_available_agents():
            if meta.agent_id.value == agent_id:
                return meta
        return None

    async def run_orchestrated_diligence(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        orchestration_mode: str = "FULL_DEAL_DECISION",
        query: Optional[str] = None,
        target_agent_ids: Optional[List[str]] = None,
    ) -> AgentOrchestrationResult:
        """
        Execute an orchestrated multi-agent diligence pipeline, persist results, and commit.
        """
        target_enums = None
        if target_agent_ids:
            target_enums = [AgentId(a) for a in target_agent_ids if a in [e.value for e in AgentId]]

        request = AgentExecutionRequest(
            deal_id=deal_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
            query=query,
            required_evidence=True,
        )

        result = await self.orchestrator.orchestrate(
            request=request,
            orchestration_mode=orchestration_mode,
            target_agent_ids=target_enums,
        )

        # Persist Execution Record
        await self.repo.create_execution_record(
            execution_id=result.execution_id,
            deal_id=deal_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
            orchestration_mode=orchestration_mode,
            query=query,
            selected_agents=[a.value for a in result.selected_agents],
            decision=result.decision_assessment,
            duration_ms=result.total_duration_ms,
        )

        # Persist Specialist Assessment Records
        for a_id, assessment in result.specialist_assessments.items():
            await self.repo.create_assessment_record(
                execution_id=result.execution_id,
                deal_id=deal_id,
                organization_id=context.organization_id,
                assessment=assessment,
            )

        await self.session.commit()
        return result

    async def run_standalone_specialist(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        agent_id: str,
        query: Optional[str] = None,
    ) -> BaseAgentAssessment:
        """Execute a single specialist agent standalone."""
        enum_id = AgentId(agent_id)
        agent_inst = self.orchestrator._instantiate_specialist(enum_id)

        request = AgentExecutionRequest(
            deal_id=deal_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
            query=query,
            required_evidence=True,
        )

        assessment = await agent_inst.execute(request)
        return assessment

    async def list_deal_executions(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[Any]:
        """List past orchestration runs for a deal."""
        executions = await self.repo.list_executions(context.organization_id, deal_id)
        return executions

    async def get_execution_details(
        self, context: TenantContext, execution_id: uuid.UUID
    ) -> Optional[Any]:
        """Retrieve full details of an orchestration execution."""
        return await self.repo.get_execution_with_assessments(context.organization_id, execution_id)
