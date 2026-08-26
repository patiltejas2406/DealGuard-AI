"""Simulation Business Service orchestrating What-If scenarios, sensitivity analysis, and Monte Carlo runs."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.simulation.monte_carlo import run_monte_carlo_simulation
from app.domains.simulation.repository import SimulationRepository
from app.domains.simulation.schemas import (
    DistributionConfig,
    MonteCarloRequest,
    MonteCarloResponse,
    ScenarioCreateRequest,
    ScenarioResponse,
    ScenarioUpdateRequest,
    SensitivityRequest,
    SensitivityResponse,
)
from app.domains.simulation.sensitivity import compute_1d_sensitivity, compute_2d_sensitivity_matrix
from app.domains.simulation.whatif import evaluate_whatif_scenario


class SimulationService:
    """Business service for What-If Deal Simulation, Sensitivity Surfaces, and Monte Carlo Analysis."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SimulationRepository(session)

    async def list_scenarios(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[ScenarioResponse]:
        """List all scenarios for a deal."""
        context.validate_deal_access(deal_id)
        scenarios = await self.repo.list_scenarios(context.organization_id, deal_id)
        return [ScenarioResponse.model_validate(s) for s in scenarios]

    async def get_scenario(
        self, context: TenantContext, deal_id: uuid.UUID, scenario_id: uuid.UUID
    ) -> ScenarioResponse:
        """Fetch a single scenario by ID."""
        context.validate_deal_access(deal_id)
        scenario = await self.repo.get_scenario(
            context.organization_id, deal_id, scenario_id
        )
        if not scenario:
            raise NotFoundException("Scenario", scenario_id)
        return ScenarioResponse.model_validate(scenario)

    async def create_scenario(
        self, context: TenantContext, deal_id: uuid.UUID, payload: ScenarioCreateRequest
    ) -> ScenarioResponse:
        """Evaluate and persist a new What-If deal scenario."""
        context.validate_deal_access(deal_id)
        data = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data:
            raise NotFoundException("Deal", deal_id)

        # Run deterministic What-If calculation
        results = evaluate_whatif_scenario(
            deal=data["deal"],
            statements=data["statements"],
            metrics=data["metrics"],
            qoe_adjustments=data["qoe_adjustments"],
            valuation=data["valuation"],
            valuation_outputs=data["valuation_outputs"],
            risks=data["risks"],
            documents=data["documents"],
            citations=data["citations"],
            assumptions_overlay=payload.assumptions,
        )

        scenario = await self.repo.create_scenario(
            organization_id=context.organization_id,
            deal_id=deal_id,
            name=payload.name,
            description=payload.description,
            scenario_type=payload.scenario_type,
            assumptions=payload.assumptions,
            results=results,
            user_id=context.user_id,
        )

        # Audit Event
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="SCENARIO_CREATED",
                entity_type="Scenario",
                entity_id=scenario.id,
                details={
                    "name": scenario.name,
                    "scenario_type": scenario.scenario_type,
                    "score_delta": results["deltas"]["decision_score_delta"],
                    "val_delta_pct": results["deltas"]["valuation_delta_pct"],
                },
            )
        )
        await self.session.commit()
        return ScenarioResponse.model_validate(scenario)

    async def run_scenario(
        self, context: TenantContext, deal_id: uuid.UUID, scenario_id: uuid.UUID
    ) -> ScenarioResponse:
        """Re-evaluate an existing scenario against current base case data."""
        context.validate_deal_access(deal_id)
        scenario = await self.repo.get_scenario(context.organization_id, deal_id, scenario_id)
        if not scenario:
            raise NotFoundException("Scenario", scenario_id)

        data = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data:
            raise NotFoundException("Deal", deal_id)

        results = evaluate_whatif_scenario(
            deal=data["deal"],
            statements=data["statements"],
            metrics=data["metrics"],
            qoe_adjustments=data["qoe_adjustments"],
            valuation=data["valuation"],
            valuation_outputs=data["valuation_outputs"],
            risks=data["risks"],
            documents=data["documents"],
            citations=data["citations"],
            assumptions_overlay=scenario.assumptions,
        )

        updated = await self.repo.update_scenario(scenario=scenario, results=results)
        await self.session.commit()
        return ScenarioResponse.model_validate(updated)

    async def delete_scenario(
        self, context: TenantContext, deal_id: uuid.UUID, scenario_id: uuid.UUID
    ) -> None:
        """Delete a saved scenario."""
        context.validate_deal_access(deal_id)
        scenario = await self.repo.get_scenario(context.organization_id, deal_id, scenario_id)
        if not scenario:
            raise NotFoundException("Scenario", scenario_id)

        await self.repo.delete_scenario(scenario)
        await self.session.commit()

    async def run_sensitivity(
        self, context: TenantContext, deal_id: uuid.UUID, payload: SensitivityRequest
    ) -> SensitivityResponse:
        """Compute on-demand 1D or 2D sensitivity matrix with break-even tipping points."""
        context.validate_deal_access(deal_id)
        data = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data:
            raise NotFoundException("Deal", deal_id)

        # 2D Matrix
        if payload.row_variable and payload.col_variable and payload.row_steps and payload.col_steps:
            matrix_res = compute_2d_sensitivity_matrix(
                deal=data["deal"],
                statements=data["statements"],
                metrics=data["metrics"],
                qoe_adjustments=data["qoe_adjustments"],
                valuation=data["valuation"],
                valuation_outputs=data["valuation_outputs"],
                risks=data["risks"],
                documents=data["documents"],
                citations=data["citations"],
                row_variable=payload.row_variable,
                row_steps=payload.row_steps,
                col_variable=payload.col_variable,
                col_steps=payload.col_steps,
            )
            return SensitivityResponse(type="2D_MATRIX", data=matrix_res)

        # 1D Sweep
        elif payload.variable_name and payload.steps:
            sweep_res = compute_1d_sensitivity(
                deal=data["deal"],
                statements=data["statements"],
                metrics=data["metrics"],
                qoe_adjustments=data["qoe_adjustments"],
                valuation=data["valuation"],
                valuation_outputs=data["valuation_outputs"],
                risks=data["risks"],
                documents=data["documents"],
                citations=data["citations"],
                variable_name=payload.variable_name,
                steps=payload.steps,
            )
            return SensitivityResponse(type="1D_SWEEP", data=sweep_res)
        else:
            raise ValueError("Sensitivity request must specify either 1D variable+steps or 2D row+col variables and steps.")

    async def run_monte_carlo(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        payload: MonteCarloRequest,
        scenario_id: Optional[uuid.UUID] = None,
    ) -> MonteCarloResponse:
        """Execute Monte Carlo simulation and persist statistical summary run."""
        context.validate_deal_access(deal_id)
        data = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data:
            raise NotFoundException("Deal", deal_id)

        # Convert dict of Pydantic models to dict of dicts
        raw_distributions: Dict[str, Dict[str, Any]] = {
            k: v.model_dump(exclude_unset=True) for k, v in payload.variable_distributions.items()
        }

        sim_output = run_monte_carlo_simulation(
            deal=data["deal"],
            statements=data["statements"],
            metrics=data["metrics"],
            qoe_adjustments=data["qoe_adjustments"],
            valuation=data["valuation"],
            valuation_outputs=data["valuation_outputs"],
            risks=data["risks"],
            documents=data["documents"],
            citations=data["citations"],
            variable_distributions=raw_distributions,
            iterations=payload.iterations,
            random_seed=payload.random_seed,
        )

        run = await self.repo.save_simulation_run(
            organization_id=context.organization_id,
            deal_id=deal_id,
            scenario_id=scenario_id,
            simulation_type="MONTE_CARLO",
            parameters={
                "distributions": raw_distributions,
                "iterations": payload.iterations,
                "seed": payload.random_seed,
            },
            iterations_count=sim_output["iterations_completed"],
            random_seed=payload.random_seed,
            statistics_output=sim_output,
            user_id=context.user_id,
        )

        # Audit Event
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="MONTE_CARLO_SIMULATED",
                entity_type="SimulationRun",
                entity_id=run.id,
                details={
                    "iterations": sim_output["iterations_completed"],
                    "seed": payload.random_seed,
                    "median_ev": sim_output["valuation_statistics"]["median"],
                    "median_score": sim_output["decision_score_statistics"]["median"],
                },
            )
        )
        await self.session.commit()

        return MonteCarloResponse(
            run_id=run.id,
            deal_id=deal_id,
            engine_version=sim_output["engine_version"],
            iterations_requested=sim_output["iterations_requested"],
            iterations_completed=sim_output["iterations_completed"],
            random_seed=sim_output["random_seed"],
            valuation_statistics=sim_output["valuation_statistics"],
            decision_score_statistics=sim_output["decision_score_statistics"],
            band_probabilities=sim_output["band_probabilities"],
            downside_metrics=sim_output["downside_metrics"],
        )
