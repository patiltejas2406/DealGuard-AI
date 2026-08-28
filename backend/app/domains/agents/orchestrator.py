"""Agent Orchestration Engine — Dynamic Execution Graph & Parallel Synthesis."""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.base import BaseSpecialistAgent
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentStatus,
    BaseAgentAssessment,
    DecisionAssessment,
)
from app.domains.agents.decision_agent import DealDecisionAgent
from app.domains.agents.specialists.finance import FinanceIntelligenceAgent
from app.domains.agents.specialists.integration import IntegrationIntelligenceAgent
from app.domains.agents.specialists.legal import LegalIntelligenceAgent
from app.domains.agents.specialists.risk import RiskIntelligenceAgent
from app.domains.agents.specialists.scenario import ScenarioSimulationAgent
from app.domains.agents.specialists.synergy import SynergyValueCreationAgent
from app.domains.agents.specialists.technology import TechnologyOperationsAgent
from app.domains.agents.specialists.valuation import ValuationAgent
from app.domains.audit.service import AuditService


class AgentOrchestrationResult:
    """Consolidated payload returned by the multi-agent orchestrator."""

    def __init__(
        self,
        execution_id: uuid.UUID,
        deal_id: uuid.UUID,
        orchestration_mode: str,
        query: Optional[str],
        selected_agents: List[AgentId],
        specialist_assessments: Dict[AgentId, BaseAgentAssessment],
        decision_assessment: DecisionAssessment,
        total_duration_ms: float,
    ) -> None:
        self.execution_id = execution_id
        self.deal_id = deal_id
        self.orchestration_mode = orchestration_mode
        self.query = query
        self.selected_agents = selected_agents
        self.specialist_assessments = specialist_assessments
        self.decision_assessment = decision_assessment
        self.total_duration_ms = total_duration_ms

    def to_dict(self) -> Dict[str, any]:
        return {
            "execution_id": str(self.execution_id),
            "deal_id": str(self.deal_id),
            "orchestration_mode": self.orchestration_mode,
            "query": self.query,
            "selected_agents": [a.value for a in self.selected_agents],
            "specialist_assessments": {
                k.value: v.model_dump(mode="json")
                for k, v in self.specialist_assessments.items()
            },
            "decision_assessment": self.decision_assessment.model_dump(mode="json"),
            "total_duration_ms": self.total_duration_ms,
        }


class AgentOrchestrator:
    """
    Central Supervisor / Orchestrator governing agent selection, bounded execution graphs,
    parallel specialist runs, result aggregation, and audit lineage.
    """

    AGENT_TIMEOUT_SECONDS = 15.0

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = AuditService(session)
        self.decision_agent = DealDecisionAgent(session)

    def _instantiate_specialist(self, agent_id: AgentId) -> BaseSpecialistAgent:
        """Instantiate a specialist agent with the active database session."""
        factories = {
            AgentId.FINANCE: FinanceIntelligenceAgent,
            AgentId.VALUATION: ValuationAgent,
            AgentId.RISK: RiskIntelligenceAgent,
            AgentId.LEGAL: LegalIntelligenceAgent,
            AgentId.TECHNOLOGY: TechnologyOperationsAgent,
            AgentId.SCENARIO: ScenarioSimulationAgent,
            AgentId.INTEGRATION: IntegrationIntelligenceAgent,
            AgentId.SYNERGY: SynergyValueCreationAgent,
        }
        factory = factories.get(agent_id)
        if not factory:
            raise ValueError(f"Unknown or non-instantiable specialist agent: {agent_id}")
        return factory(self.session)

    def select_agents_for_request(
        self, orchestration_mode: Optional[str], query: Optional[str]
    ) -> List[AgentId]:
        """
        Determine which specialist agents are required based on mode or query taxonomy.
        """
        mode = (orchestration_mode or "").upper()
        if mode in ["FULL", "FULL_DEAL_DECISION", "COMPREHENSIVE"] or not mode:
            return [
                AgentId.FINANCE,
                AgentId.VALUATION,
                AgentId.RISK,
                AgentId.LEGAL,
                AgentId.TECHNOLOGY,
                AgentId.SCENARIO,
                AgentId.INTEGRATION,
                AgentId.SYNERGY,
            ]

        if mode == "TECH_AND_INTEGRATION_RISK":
            return [AgentId.TECHNOLOGY, AgentId.INTEGRATION, AgentId.RISK]

        if mode == "FINANCIAL_AND_VALUATION":
            return [AgentId.FINANCE, AgentId.VALUATION, AgentId.SCENARIO]

        if mode == "LEGAL_AND_RISK":
            return [AgentId.LEGAL, AgentId.RISK]

        # Dynamic Query Intent Taxonomy Routing
        q_lower = (query or "").lower()
        selected: Set[AgentId] = set()

        if any(w in q_lower for w in ["finance", "revenue", "ebitda", "qoe", "margin"]):
            selected.add(AgentId.FINANCE)
        if any(w in q_lower for w in ["valuation", "dcf", "multiple", "comps", "precedent"]):
            selected.add(AgentId.VALUATION)
        if any(w in q_lower for w in ["risk", "threat", "concern", "cybersecurity"]):
            selected.add(AgentId.RISK)
        if any(w in q_lower for w in ["legal", "contract", "change of control", "compliance"]):
            selected.add(AgentId.LEGAL)
        if any(w in q_lower for w in ["tech", "cloud", "spof", "architecture", "sla"]):
            selected.add(AgentId.TECHNOLOGY)
        if any(w in q_lower for w in ["scenario", "what-if", "recession", "monte carlo"]):
            selected.add(AgentId.SCENARIO)
        if any(w in q_lower for w in ["integration", "100-day", "milestone", "workstream"]):
            selected.add(AgentId.INTEGRATION)
        if any(w in q_lower for w in ["synergy", "cost savings", "upsell", "waterfall"]):
            selected.add(AgentId.SYNERGY)

        if not selected:
            # Default to complete diligence if intent is broad (e.g. "Should we acquire?")
            return [
                AgentId.FINANCE,
                AgentId.VALUATION,
                AgentId.RISK,
                AgentId.LEGAL,
                AgentId.TECHNOLOGY,
                AgentId.SCENARIO,
                AgentId.INTEGRATION,
                AgentId.SYNERGY,
            ]

        return list(selected)

    async def orchestrate(
        self,
        request: AgentExecutionRequest,
        orchestration_mode: str = "FULL_DEAL_DECISION",
        target_agent_ids: Optional[List[AgentId]] = None,
    ) -> AgentOrchestrationResult:
        """
        Execute orchestrated multi-agent diligence pipeline with bounded steps,
        parallel specialist execution, failure containment, and decision synthesis.
        """
        start_time = time.perf_counter()
        execution_id = uuid.uuid4()

        # 1. Select Agents
        selected_agents = target_agent_ids or self.select_agents_for_request(
            orchestration_mode, request.query
        )

        # 2. Parallel Specialist Agent Execution with Timeouts
        async def run_single_specialist(a_id: AgentId) -> tuple[AgentId, BaseAgentAssessment]:
            agent_inst = self._instantiate_specialist(a_id)
            try:
                assessment = await asyncio.wait_for(
                    agent_inst.execute(request), timeout=self.AGENT_TIMEOUT_SECONDS
                )
                return a_id, assessment
            except asyncio.TimeoutError:
                return a_id, BaseAgentAssessment(
                    agent_id=a_id,
                    domain=agent_inst.metadata.domain,
                    status=AgentStatus.FAILED,
                    summary=f"Agent timed out after {self.AGENT_TIMEOUT_SECONDS}s limit.",
                    confidence=AgentConfidence.LOW,
                    confidence_score=0.0,
                    negative_drivers=[f"Agent execution exceeded timeout limit ({self.AGENT_TIMEOUT_SECONDS}s)."],
                )
            except Exception as exc:
                return a_id, BaseAgentAssessment(
                    agent_id=a_id,
                    domain=agent_inst.metadata.domain,
                    status=AgentStatus.FAILED,
                    summary=f"Agent encountered error: {str(exc)}",
                    confidence=AgentConfidence.LOW,
                    confidence_score=0.0,
                    negative_drivers=[f"Specialist agent error: {str(exc)}"],
                )

        specialist_tasks = [run_single_specialist(a_id) for a_id in selected_agents]
        specialist_results = await asyncio.gather(*specialist_tasks)
        specialist_assessments: Dict[AgentId, BaseAgentAssessment] = {
            a_id: assess for a_id, assess in specialist_results
        }

        # 3. Decision Agent Synthesis
        decision_assessment = await self.decision_agent.synthesize_decision(
            request, specialist_assessments
        )

        total_duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # 4. Audit Event Lineage
        await self.audit_service.log_event(
            deal_id=request.deal_id,
            actor_user_id=request.user_id,
            action="AGENT_ORCHESTRATION_EXECUTED",
            entity_type="AgentExecution",
            entity_id=execution_id,
            details={
                "orchestration_mode": orchestration_mode,
                "selected_agents": [a.value for a in selected_agents],
                "recommendation": decision_assessment.recommendation.value,
                "confidence": decision_assessment.confidence.value,
                "human_review_required": decision_assessment.human_review_required,
                "duration_ms": total_duration_ms,
            },
            organization_id=request.organization_id,
        )

        return AgentOrchestrationResult(
            execution_id=execution_id,
            deal_id=request.deal_id,
            orchestration_mode=orchestration_mode,
            query=request.query,
            selected_agents=selected_agents,
            specialist_assessments=specialist_assessments,
            decision_assessment=decision_assessment,
            total_duration_ms=total_duration_ms,
        )
