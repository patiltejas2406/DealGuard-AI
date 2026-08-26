"""Simulation Database Repository for scenario persistence, parameter runs, and cross-domain data fetching."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.decision.repository import DecisionRepository
from app.domains.simulation.models import Scenario, SimulationRun


class SimulationRepository:
    """Async database repository for Scenario and SimulationRun persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.decision_repo = DecisionRepository(session)

    async def get_deal_diligence_context(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Fetch all cross-domain diligence data for the deal."""
        return await self.decision_repo.get_complete_deal_diligence_context(
            organization_id, deal_id
        )

    async def list_scenarios(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[Scenario]:
        """List all saved scenarios for a deal workspace."""
        query = (
            select(Scenario)
            .where(
                Scenario.organization_id == organization_id,
                Scenario.deal_id == deal_id,
            )
            .order_by(Scenario.created_at.desc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_scenario(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, scenario_id: uuid.UUID
    ) -> Optional[Scenario]:
        """Fetch a specific scenario by ID."""
        query = select(Scenario).where(
            Scenario.organization_id == organization_id,
            Scenario.deal_id == deal_id,
            Scenario.id == scenario_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_scenario(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        name: str,
        description: Optional[str],
        scenario_type: str,
        assumptions: Dict[str, Any],
        results: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> Scenario:
        """Create and persist a new Scenario with its initial calculated results."""
        scenario = Scenario(
            organization_id=organization_id,
            deal_id=deal_id,
            name=name,
            description=description,
            scenario_type=scenario_type,
            status="ACTIVE",
            assumptions=assumptions,
            results=results,
            created_by_id=user_id,
        )
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def update_scenario(
        self,
        scenario: Scenario,
        name: Optional[str] = None,
        description: Optional[str] = None,
        assumptions: Optional[Dict[str, Any]] = None,
        results: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Scenario:
        """Update scenario details and results."""
        if name is not None:
            scenario.name = name
        if description is not None:
            scenario.description = description
        if assumptions is not None:
            scenario.assumptions = assumptions
        if results is not None:
            scenario.results = results
        if status is not None:
            scenario.status = status

        await self.session.flush()
        return scenario

    async def delete_scenario(self, scenario: Scenario) -> None:
        """Delete a scenario and associated runs."""
        await self.session.delete(scenario)
        await self.session.flush()

    async def save_simulation_run(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        scenario_id: Optional[uuid.UUID],
        simulation_type: str,
        parameters: Dict[str, Any],
        iterations_count: int,
        random_seed: Optional[int],
        statistics_output: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> SimulationRun:
        """Record an executed Monte Carlo simulation run in the audit ledger."""
        run = SimulationRun(
            organization_id=organization_id,
            deal_id=deal_id,
            scenario_id=scenario_id,
            simulation_type=simulation_type,
            parameters=parameters,
            iterations_count=iterations_count,
            random_seed=random_seed,
            statistics_output=statistics_output,
            status="COMPLETED",
            created_by_id=user_id,
        )
        self.session.add(run)
        await self.session.flush()
        return run
