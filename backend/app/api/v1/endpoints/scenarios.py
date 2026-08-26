"""REST API Endpoints for What-If Deal Simulation, Sensitivity Surfaces, and Monte Carlo Analysis."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.simulation.schemas import (
    MonteCarloRequest,
    MonteCarloResponse,
    ScenarioCreateRequest,
    ScenarioResponse,
    SensitivityRequest,
    SensitivityResponse,
)
from app.domains.simulation.service import SimulationService

router = APIRouter(prefix="/deals/{deal_id}/scenarios", tags=["scenarios"])


@router.get(
    "",
    summary="List Saved Scenarios for Deal Workspace",
    status_code=status.HTTP_200_OK,
    response_model=List[ScenarioResponse],
)
async def list_scenarios(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ScenarioResponse]:
    """Retrieve all saved What-If and stress test scenarios for a deal workspace."""
    context.require_permission(PERM_DEALS_READ)
    service = SimulationService(db)
    return await service.list_scenarios(context, deal_id)


@router.post(
    "",
    summary="Create & Evaluate New What-If Deal Scenario",
    status_code=status.HTTP_201_CREATED,
    response_model=ScenarioResponse,
)
async def create_scenario(
    deal_id: uuid.UUID,
    payload: ScenarioCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ScenarioResponse:
    """Create and compute a persistent What-If scenario with valuation and decision score deltas."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SimulationService(db)
    return await service.create_scenario(context, deal_id, payload)


@router.get(
    "/{scenario_id}",
    summary="Get Specific Scenario Details & Outputs",
    status_code=status.HTTP_200_OK,
    response_model=ScenarioResponse,
)
async def get_scenario(
    deal_id: uuid.UUID,
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ScenarioResponse:
    """Retrieve details, assumptions, and evaluated outputs for a specific scenario."""
    context.require_permission(PERM_DEALS_READ)
    service = SimulationService(db)
    return await service.get_scenario(context, deal_id, scenario_id)


@router.post(
    "/{scenario_id}/run",
    summary="Re-evaluate Saved Scenario",
    status_code=status.HTTP_200_OK,
    response_model=ScenarioResponse,
)
async def run_scenario(
    deal_id: uuid.UUID,
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ScenarioResponse:
    """Re-run a saved scenario against updated base case financial statements and risk items."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SimulationService(db)
    return await service.run_scenario(context, deal_id, scenario_id)


@router.delete(
    "/{scenario_id}",
    summary="Delete Saved Scenario",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_scenario(
    deal_id: uuid.UUID,
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> None:
    """Delete a saved scenario and any attached simulation run records."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SimulationService(db)
    await service.delete_scenario(context, deal_id, scenario_id)


@router.post(
    "/sensitivity",
    summary="Compute 1D or 2D Sensitivity Matrix & Tipping Points",
    status_code=status.HTTP_200_OK,
    response_model=SensitivityResponse,
)
async def run_sensitivity(
    deal_id: uuid.UUID,
    payload: SensitivityRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SensitivityResponse:
    """Execute on-demand parameter sweeps (1D curve or 2D matrix) and detect break-even inflection points."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SimulationService(db)
    return await service.run_sensitivity(context, deal_id, payload)


@router.post(
    "/monte-carlo",
    summary="Execute Statistical Monte Carlo Deal Simulation",
    status_code=status.HTTP_200_OK,
    response_model=MonteCarloResponse,
)
async def run_monte_carlo(
    deal_id: uuid.UUID,
    payload: MonteCarloRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> MonteCarloResponse:
    """Execute deterministic Monte Carlo simulation and compute percentile distributions and band probabilities."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SimulationService(db)
    return await service.run_monte_carlo(context, deal_id, payload)
