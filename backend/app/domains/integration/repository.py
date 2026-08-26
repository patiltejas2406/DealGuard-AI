"""Async Database Repository for 100-Day Integration Execution Engine."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.integration.models import (
    IntegrationBlocker,
    IntegrationDependency,
    IntegrationMilestone,
    IntegrationProgram,
    IntegrationWorkstream,
)


class IntegrationRepository:
    """Async repository for integration programs, workstreams, milestones, dependencies, and blockers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==========================================
    # Program Operations
    # ==========================================

    async def get_program(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[IntegrationProgram]:
        """Fetch integration program for a deal."""
        query = select(IntegrationProgram).where(
            IntegrationProgram.organization_id == organization_id,
            IntegrationProgram.deal_id == deal_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_program(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        company_id: Optional[uuid.UUID],
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> IntegrationProgram:
        """Initialize new integration program."""
        program = IntegrationProgram(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=company_id,
            name=data.get("name", "100-Day Value Creation & Integration Plan"),
            status="ACTIVE",
            close_date=data.get("close_date"),
            day_0_date=data.get("day_0_date"),
            day_100_date=data.get("day_100_date"),
            current_day_offset=data.get("current_day_offset", 1),
            executive_sponsor=data.get("executive_sponsor"),
            objectives=data.get("objectives", {}),
            health_score=100.0,
            health_band="HEALTHY",
            created_by_id=user_id,
        )
        self.session.add(program)
        await self.session.flush()
        return program

    async def update_program(
        self, program: IntegrationProgram, updates: Dict[str, Any]
    ) -> IntegrationProgram:
        """Update program parameters."""
        for k, v in updates.items():
            if v is not None and hasattr(program, k):
                setattr(program, k, v)
        await self.session.flush()
        return program

    # ==========================================
    # Workstream Operations
    # ==========================================

    async def list_workstreams(
        self, organization_id: uuid.UUID, program_id: uuid.UUID, category: Optional[str] = None
    ) -> List[IntegrationWorkstream]:
        """List all workstreams in an integration program."""
        query = (
            select(IntegrationWorkstream)
            .where(
                IntegrationWorkstream.organization_id == organization_id,
                IntegrationWorkstream.program_id == program_id,
            )
            .order_by(IntegrationWorkstream.start_day.asc(), IntegrationWorkstream.name.asc())
        )
        if category:
            query = query.where(IntegrationWorkstream.category == category)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_workstream(
        self, organization_id: uuid.UUID, workstream_id: uuid.UUID
    ) -> Optional[IntegrationWorkstream]:
        """Get single workstream."""
        query = select(IntegrationWorkstream).where(
            IntegrationWorkstream.organization_id == organization_id,
            IntegrationWorkstream.id == workstream_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_workstream(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        program_id: uuid.UUID,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> IntegrationWorkstream:
        """Create and persist workstream."""
        ws = IntegrationWorkstream(
            organization_id=organization_id,
            deal_id=deal_id,
            program_id=program_id,
            name=data["name"],
            description=data.get("description"),
            category=data["category"],
            owner=data.get("owner"),
            executive_sponsor=data.get("executive_sponsor"),
            status="NOT_STARTED",
            priority=data.get("priority", "MEDIUM"),
            start_day=data.get("start_day", 0),
            target_day=data.get("target_day", 100),
            progress_pct=0.0,
            risk_level=data.get("risk_level", "LOW"),
            linked_synergy_ids=data.get("linked_synergy_ids", []),
            linked_risk_ids=data.get("linked_risk_ids", []),
            notes=data.get("notes"),
            created_by_id=user_id,
        )
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def update_workstream(
        self, ws: IntegrationWorkstream, updates: Dict[str, Any]
    ) -> IntegrationWorkstream:
        """Update workstream attributes."""
        for k, v in updates.items():
            if v is not None and hasattr(ws, k):
                setattr(ws, k, v)
        await self.session.flush()
        return ws

    async def delete_workstream(self, ws: IntegrationWorkstream) -> None:
        """Delete workstream."""
        await self.session.delete(ws)
        await self.session.flush()

    # ==========================================
    # Milestone Operations
    # ==========================================

    async def list_milestones(
        self,
        organization_id: uuid.UUID,
        program_id: uuid.UUID,
        workstream_id: Optional[uuid.UUID] = None,
    ) -> List[IntegrationMilestone]:
        """List all milestones for program or workstream."""
        query = (
            select(IntegrationMilestone)
            .where(
                IntegrationMilestone.organization_id == organization_id,
                IntegrationMilestone.program_id == program_id,
            )
            .order_by(IntegrationMilestone.target_day.asc(), IntegrationMilestone.name.asc())
        )
        if workstream_id:
            query = query.where(IntegrationMilestone.workstream_id == workstream_id)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_milestone(
        self, organization_id: uuid.UUID, milestone_id: uuid.UUID
    ) -> Optional[IntegrationMilestone]:
        """Get single milestone."""
        query = select(IntegrationMilestone).where(
            IntegrationMilestone.organization_id == organization_id,
            IntegrationMilestone.id == milestone_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_milestone(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        program_id: uuid.UUID,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> IntegrationMilestone:
        """Create and persist milestone."""
        milestone = IntegrationMilestone(
            organization_id=organization_id,
            deal_id=deal_id,
            program_id=program_id,
            workstream_id=data["workstream_id"],
            name=data["name"],
            description=data.get("description"),
            target_day=data.get("target_day", 30),
            target_date=data.get("target_date"),
            status="NOT_STARTED",
            priority=data.get("priority", "MEDIUM"),
            owner=data.get("owner"),
            completion_pct=0.0,
            is_critical_path=False,
            linked_synergy_id=data.get("linked_synergy_id"),
            deliverable=data.get("deliverable"),
            evidence_citation_ids=data.get("evidence_citation_ids", []),
            notes=data.get("notes"),
            created_by_id=user_id,
        )
        self.session.add(milestone)
        await self.session.flush()
        return milestone

    async def update_milestone(
        self, milestone: IntegrationMilestone, updates: Dict[str, Any]
    ) -> IntegrationMilestone:
        """Update milestone attributes."""
        for k, v in updates.items():
            if v is not None and hasattr(milestone, k):
                setattr(milestone, k, v)
        if getattr(milestone, "completion_pct", 0.0) >= 100.0 and milestone.status != "COMPLETED":
            milestone.status = "COMPLETED"
            milestone.completed_at = datetime.utcnow()
        await self.session.flush()
        return milestone

    async def delete_milestone(self, milestone: IntegrationMilestone) -> None:
        """Delete milestone."""
        await self.session.delete(milestone)
        await self.session.flush()

    # ==========================================
    # Dependency Operations
    # ==========================================

    async def list_dependencies(
        self, organization_id: uuid.UUID, program_id: uuid.UUID
    ) -> List[IntegrationDependency]:
        """List all dependencies in a program."""
        query = select(IntegrationDependency).where(
            IntegrationDependency.organization_id == organization_id,
            IntegrationDependency.program_id == program_id,
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def create_dependency(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        program_id: uuid.UUID,
        predecessor_id: uuid.UUID,
        successor_id: uuid.UUID,
        dep_type: str = "FINISH_TO_START",
    ) -> IntegrationDependency:
        """Create dependency link."""
        dep = IntegrationDependency(
            organization_id=organization_id,
            deal_id=deal_id,
            program_id=program_id,
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=dep_type,
            is_blocking=True,
        )
        self.session.add(dep)
        await self.session.flush()
        return dep

    async def delete_dependency(
        self, organization_id: uuid.UUID, dep_id: uuid.UUID
    ) -> Optional[IntegrationDependency]:
        """Delete dependency."""
        query = select(IntegrationDependency).where(
            IntegrationDependency.organization_id == organization_id,
            IntegrationDependency.id == dep_id,
        )
        res = await self.session.execute(query)
        dep = res.scalar_one_or_none()
        if dep:
            await self.session.delete(dep)
            await self.session.flush()
        return dep

    # ==========================================
    # Blocker Operations
    # ==========================================

    async def list_blockers(
        self, organization_id: uuid.UUID, program_id: uuid.UUID
    ) -> List[IntegrationBlocker]:
        """List all blockers."""
        query = (
            select(IntegrationBlocker)
            .where(
                IntegrationBlocker.organization_id == organization_id,
                IntegrationBlocker.program_id == program_id,
            )
            .order_by(desc(IntegrationBlocker.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_blocker(
        self, organization_id: uuid.UUID, blocker_id: uuid.UUID
    ) -> Optional[IntegrationBlocker]:
        """Get single blocker."""
        query = select(IntegrationBlocker).where(
            IntegrationBlocker.organization_id == organization_id,
            IntegrationBlocker.id == blocker_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_blocker(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        program_id: uuid.UUID,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> IntegrationBlocker:
        """Create and persist blocker."""
        blocker = IntegrationBlocker(
            organization_id=organization_id,
            deal_id=deal_id,
            program_id=program_id,
            workstream_id=data["workstream_id"],
            milestone_id=data.get("milestone_id"),
            title=data["title"],
            description=data.get("description"),
            severity=data.get("severity", "HIGH"),
            status="OPEN",
            owner=data.get("owner"),
            created_by_id=user_id,
        )
        self.session.add(blocker)
        await self.session.flush()
        return blocker

    async def resolve_blocker(
        self, blocker: IntegrationBlocker, resolution_notes: str
    ) -> IntegrationBlocker:
        """Mark blocker resolved."""
        blocker.status = "RESOLVED"
        blocker.resolution_notes = resolution_notes
        blocker.resolved_at = datetime.utcnow()
        await self.session.flush()
        return blocker
