"""REST API Endpoints for Agentic Intelligence Orchestration."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_context, validate_deal_membership
from app.core.database import get_db
from app.domains.agents.contract import AgentMetadata, BaseAgentAssessment
from app.domains.agents.service import AgentOrchestrationService
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext

router = APIRouter(tags=["agents"])


class OrchestrationRunPayload(BaseModel):
    """Payload for submitting an orchestrated multi-agent diligence request."""
    orchestration_mode: str = Field(
        default="FULL_DEAL_DECISION",
        description="Mode: FULL_DEAL_DECISION, TECH_AND_INTEGRATION_RISK, FINANCIAL_AND_VALUATION, LEGAL_AND_RISK, or CUSTOM",
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional high-level analytical query or hypothesis to guide agent diligence.",
    )
    target_agent_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific specialist agent IDs to invoke.",
    )


class StandaloneAgentRunPayload(BaseModel):
    """Payload for invoking a single specialist agent directly."""
    query: Optional[str] = None


# 1. Global Agent Registry Metadata Endpoints
@router.get(
    "/agents",
    summary="List All Available Agents",
    status_code=status.HTTP_200_OK,
    response_model=List[AgentMetadata],
)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(get_tenant_context),
) -> List[AgentMetadata]:
    """List metadata, domains, purposes, and authorized tool whitelists for all registered agents."""
    service = AgentOrchestrationService(db)
    return service.list_available_agents()


@router.get(
    "/agents/{agent_id}",
    summary="Get Agent Metadata",
    status_code=status.HTTP_200_OK,
    response_model=AgentMetadata,
)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(get_tenant_context),
) -> AgentMetadata:
    """Retrieve capabilities and input/output contracts for a specific agent."""
    service = AgentOrchestrationService(db)
    meta = service.get_agent_metadata(agent_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' is not registered in the agent registry.",
        )
    return meta


# 2. Deal-Scoped Agent Orchestration Endpoints
@router.post(
    "/deals/{deal_id}/agents/orchestrate",
    summary="Run Multi-Agent Diligence Orchestration",
    status_code=status.HTTP_200_OK,
)
async def orchestrate_agents(
    deal_id: uuid.UUID,
    payload: OrchestrationRunPayload,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """
    Execute orchestrated multi-agent diligence pipeline with parallel specialist execution,
    grounded evidence verification, and explainable decision synthesis.
    """
    context.require_permission(PERM_ANALYSIS_RUN)
    service = AgentOrchestrationService(db)
    result = await service.run_orchestrated_diligence(
        context=context,
        deal_id=deal_id,
        orchestration_mode=payload.orchestration_mode,
        query=payload.query,
        target_agent_ids=payload.target_agent_ids,
    )
    return result.to_dict()


@router.post(
    "/deals/{deal_id}/agents/{agent_id}/run",
    summary="Run Standalone Specialist Agent",
    status_code=status.HTTP_200_OK,
)
async def run_standalone_agent(
    deal_id: uuid.UUID,
    agent_id: str,
    payload: StandaloneAgentRunPayload,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Invoke an individual specialist agent standalone."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = AgentOrchestrationService(db)
    try:
        assessment = await service.run_standalone_specialist(
            context=context,
            deal_id=deal_id,
            agent_id=agent_id,
            query=payload.query,
        )
        return assessment.model_dump(mode="json")
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        )


@router.get(
    "/deals/{deal_id}/agents/executions",
    summary="List Deal Agent Executions",
    status_code=status.HTTP_200_OK,
)
async def list_deal_executions(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[Dict[str, Any]]:
    """List historical multi-agent orchestration runs for the deal workspace."""
    context.require_permission(PERM_DEALS_READ)
    service = AgentOrchestrationService(db)
    executions = await service.list_deal_executions(context, deal_id)
    return [
        {
            "id": str(e.id),
            "deal_id": str(e.deal_id),
            "orchestration_mode": e.orchestration_mode,
            "query": e.query,
            "status": e.status,
            "recommendation": e.recommendation,
            "decision_score": e.decision_score,
            "confidence": e.confidence,
            "confidence_score": e.confidence_score,
            "human_review_required": e.human_review_required,
            "duration_ms": e.duration_ms,
            "selected_agents": e.selected_agents,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in executions
    ]


@router.get(
    "/deals/{deal_id}/agents/executions/{execution_id}",
    summary="Get Agent Execution Details",
    status_code=status.HTTP_200_OK,
)
async def get_execution_details(
    deal_id: uuid.UUID,
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Retrieve detailed orchestration execution graph and all specialist assessment outputs."""
    context.require_permission(PERM_DEALS_READ)
    service = AgentOrchestrationService(db)
    execution = await service.get_execution_details(context, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found.",
        )

    return {
        "id": str(execution.id),
        "deal_id": str(execution.deal_id),
        "orchestration_mode": execution.orchestration_mode,
        "query": execution.query,
        "status": execution.status,
        "recommendation": execution.recommendation,
        "decision_score": execution.decision_score,
        "confidence": execution.confidence,
        "confidence_score": execution.confidence_score,
        "human_review_required": execution.human_review_required,
        "duration_ms": execution.duration_ms,
        "selected_agents": execution.selected_agents,
        "synthesis_payload": execution.synthesis_payload,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "assessments": [
            {
                "id": str(a.id),
                "agent_id": a.agent_id,
                "domain": a.domain,
                "status": a.status,
                "confidence": a.confidence,
                "confidence_score": a.confidence_score,
                "summary": a.summary,
                "findings_count": a.findings_count,
                "citations_count": a.citations_count,
                "tools_invoked": a.tools_invoked,
                "execution_time_ms": a.execution_time_ms,
                "assessment_payload": a.assessment_payload,
            }
            for a in execution.assessments
        ],
    }
