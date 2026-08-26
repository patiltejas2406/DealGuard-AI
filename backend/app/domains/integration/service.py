"""100-Day Integration Execution Business Service."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.integration.config import (
    get_100day_stage,
    validate_workstream_transition,
)
from app.domains.integration.dag import compute_critical_path, validate_dependency_graph
from app.domains.integration.executive_attention import generate_executive_attention_queue
from app.domains.integration.health import calculate_integration_health_score
from app.domains.integration.models import (
    IntegrationBlocker,
    IntegrationDependency,
    IntegrationMilestone,
    IntegrationProgram,
    IntegrationWorkstream,
)
from app.domains.integration.repository import IntegrationRepository
from app.domains.integration.schemas import (
    BlockerCreateRequest,
    BlockerResolveRequest,
    BlockerResponse,
    CriticalPathResponse,
    DependencyCreateRequest,
    DependencyResponse,
    ExecutiveAttentionResponse,
    IntegrationHealthResponse,
    IntegrationProgramCreateRequest,
    IntegrationProgramResponse,
    IntegrationProgramUpdateRequest,
    MilestoneCreateRequest,
    MilestoneResponse,
    MilestoneStatusUpdateRequest,
    MilestoneUpdateRequest,
    TimelineStageResponse,
    WorkstreamCreateRequest,
    WorkstreamResponse,
    WorkstreamStatusUpdateRequest,
    WorkstreamUpdateRequest,
)


class IntegrationService:
    """Business service orchestrating 100-Day Integration Programs, DAGs, and Health Tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IntegrationRepository(session)

    # ==========================================
    # Program Operations
    # ==========================================

    async def get_or_create_program(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> IntegrationProgramResponse:
        """Fetch or automatically initialize the 100-day integration program for a deal."""
        context.validate_deal_access(deal_id)
        prog = await self.repo.get_program(context.organization_id, deal_id)
        if not prog:
            prog = await self.repo.create_program(
                organization_id=context.organization_id,
                deal_id=deal_id,
                company_id=None,
                data={"name": "100-Day Value Creation & Integration Plan"},
                user_id=context.user_id,
            )
            await self.session.commit()

        return await self._format_program(prog)

    async def create_program(
        self, context: TenantContext, deal_id: uuid.UUID, payload: IntegrationProgramCreateRequest
    ) -> IntegrationProgramResponse:
        """Create a new 100-day integration program."""
        context.validate_deal_access(deal_id)
        existing = await self.repo.get_program(context.organization_id, deal_id)
        if existing:
            return await self._format_program(existing)

        prog = await self.repo.create_program(
            organization_id=context.organization_id,
            deal_id=deal_id,
            company_id=None,
            data=payload.model_dump(),
            user_id=context.user_id,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="INTEGRATION_PROGRAM_INITIALIZED",
                entity_type="IntegrationProgram",
                entity_id=prog.id,
                details={"name": prog.name},
            )
        )
        await self.session.commit()
        return await self._format_program(prog)

    async def update_program(
        self, context: TenantContext, deal_id: uuid.UUID, payload: IntegrationProgramUpdateRequest
    ) -> IntegrationProgramResponse:
        """Update program attributes."""
        context.validate_deal_access(deal_id)
        prog = await self.repo.get_program(context.organization_id, deal_id)
        if not prog:
            raise NotFoundException("IntegrationProgram", deal_id)

        updated = await self.repo.update_program(prog, payload.model_dump(exclude_unset=True))
        await self.session.commit()
        return await self._format_program(updated)

    # ==========================================
    # Workstream Operations
    # ==========================================

    async def list_workstreams(
        self, context: TenantContext, deal_id: uuid.UUID, category: Optional[str] = None
    ) -> List[WorkstreamResponse]:
        """List workstreams for a deal program."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        workstreams = await self.repo.list_workstreams(context.organization_id, prog.id, category)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id)

        ws_milestone_counts = {}
        ws_completed_counts = {}
        for m in milestones:
            ws_milestone_counts[m.workstream_id] = ws_milestone_counts.get(m.workstream_id, 0) + 1
            if m.status == "COMPLETED" or m.completion_pct >= 100.0:
                ws_completed_counts[m.workstream_id] = ws_completed_counts.get(m.workstream_id, 0) + 1

        return [
            self._format_workstream(
                ws,
                ws_milestone_counts.get(ws.id, 0),
                ws_completed_counts.get(ws.id, 0),
            )
            for ws in workstreams
        ]

    async def create_workstream(
        self, context: TenantContext, deal_id: uuid.UUID, payload: WorkstreamCreateRequest
    ) -> WorkstreamResponse:
        """Create an integration workstream."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)

        ws = await self.repo.create_workstream(
            organization_id=context.organization_id,
            deal_id=deal_id,
            program_id=prog.id,
            data=payload.model_dump(),
            user_id=context.user_id,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="WORKSTREAM_CREATED",
                entity_type="IntegrationWorkstream",
                entity_id=ws.id,
                details={"name": ws.name, "category": ws.category},
            )
        )
        await self._sync_program_health(prog.id)
        await self.session.commit()
        return self._format_workstream(ws, 0, 0)

    async def update_workstream_status(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        workstream_id: uuid.UUID,
        payload: WorkstreamStatusUpdateRequest,
    ) -> WorkstreamResponse:
        """Transition workstream lifecycle status with state machine enforcement."""
        context.validate_deal_access(deal_id)
        ws = await self.repo.get_workstream(context.organization_id, workstream_id)
        if not ws:
            raise NotFoundException("IntegrationWorkstream", workstream_id)

        validate_workstream_transition(ws.status, payload.status)
        old_status = ws.status
        ws.status = payload.status
        if payload.notes:
            ws.notes = f"{ws.notes or ''}\n[Status {old_status} -> {payload.status}]: {payload.notes}".strip()

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="WORKSTREAM_STATUS_UPDATED",
                entity_type="IntegrationWorkstream",
                entity_id=ws.id,
                details={"old_status": old_status, "new_status": payload.status},
            )
        )
        await self._sync_program_health(ws.program_id)
        await self.session.commit()
        return self._format_workstream(ws, 0, 0)

    # ==========================================
    # Milestone Operations
    # ==========================================

    async def list_milestones(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        workstream_id: Optional[uuid.UUID] = None,
    ) -> List[MilestoneResponse]:
        """List all milestones for a deal."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id, workstream_id)
        return [self._format_milestone(m) for m in milestones]

    async def create_milestone(
        self, context: TenantContext, deal_id: uuid.UUID, payload: MilestoneCreateRequest
    ) -> MilestoneResponse:
        """Add a milestone to a workstream."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        ws = await self.repo.get_workstream(context.organization_id, payload.workstream_id)
        if not ws:
            raise NotFoundException("IntegrationWorkstream", payload.workstream_id)

        milestone = await self.repo.create_milestone(
            organization_id=context.organization_id,
            deal_id=deal_id,
            program_id=prog.id,
            data=payload.model_dump(),
            user_id=context.user_id,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="MILESTONE_CREATED",
                entity_type="IntegrationMilestone",
                entity_id=milestone.id,
                details={"name": milestone.name, "target_day": milestone.target_day},
            )
        )
        await self._recompute_workstream_progress(ws)
        await self._sync_program_health(prog.id)
        await self.session.commit()
        return self._format_milestone(milestone)

    async def update_milestone_status(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        milestone_id: uuid.UUID,
        payload: MilestoneStatusUpdateRequest,
    ) -> MilestoneResponse:
        """Update milestone status and completion percentage."""
        context.validate_deal_access(deal_id)
        milestone = await self.repo.get_milestone(context.organization_id, milestone_id)
        if not milestone:
            raise NotFoundException("IntegrationMilestone", milestone_id)

        milestone.status = payload.status
        if payload.completion_pct is not None:
            milestone.completion_pct = payload.completion_pct
        if payload.status == "COMPLETED" and milestone.completion_pct < 100.0:
            milestone.completion_pct = 100.0

        if payload.notes:
            milestone.notes = f"{milestone.notes or ''}\n[Status: {payload.status}]: {payload.notes}".strip()

        ws = await self.repo.get_workstream(context.organization_id, milestone.workstream_id)
        if ws:
            await self._recompute_workstream_progress(ws)

        await self._sync_program_health(milestone.program_id)
        await self.session.commit()
        return self._format_milestone(milestone)

    # ==========================================
    # Dependency & DAG Operations
    # ==========================================

    async def create_dependency(
        self, context: TenantContext, deal_id: uuid.UUID, payload: DependencyCreateRequest
    ) -> DependencyResponse:
        """Add dependency link after verifying DAG acyclicity."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)

        # 1. Fetch existing dependencies to check for cycles
        existing_deps = await self.repo.list_dependencies(context.organization_id, prog.id)
        validate_dependency_graph(existing_deps, payload.predecessor_id, payload.successor_id)

        dep = await self.repo.create_dependency(
            organization_id=context.organization_id,
            deal_id=deal_id,
            program_id=prog.id,
            predecessor_id=payload.predecessor_id,
            successor_id=payload.successor_id,
            dep_type=payload.dependency_type,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="INTEGRATION_DEPENDENCY_CREATED",
                entity_type="IntegrationDependency",
                entity_id=dep.id,
                details={
                    "pred": str(payload.predecessor_id),
                    "succ": str(payload.successor_id),
                },
            )
        )
        await self._sync_program_health(prog.id)
        await self.session.commit()
        return DependencyResponse.model_validate(dep)

    async def delete_dependency(
        self, context: TenantContext, deal_id: uuid.UUID, dependency_id: uuid.UUID
    ) -> None:
        """Delete dependency link."""
        context.validate_deal_access(deal_id)
        await self.repo.delete_dependency(context.organization_id, dependency_id)
        await self.session.commit()

    # ==========================================
    # Blocker Operations
    # ==========================================

    async def list_blockers(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[BlockerResponse]:
        """List blockers."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        blockers = await self.repo.list_blockers(context.organization_id, prog.id)
        return [BlockerResponse.model_validate(b) for b in blockers]

    async def create_blocker(
        self, context: TenantContext, deal_id: uuid.UUID, payload: BlockerCreateRequest
    ) -> BlockerResponse:
        """Report an operational blocker."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)

        blocker = await self.repo.create_blocker(
            organization_id=context.organization_id,
            deal_id=deal_id,
            program_id=prog.id,
            data=payload.model_dump(),
            user_id=context.user_id,
        )

        # If high/critical blocker, transition associated workstream to BLOCKED
        ws = await self.repo.get_workstream(context.organization_id, payload.workstream_id)
        if ws and payload.severity in ["CRITICAL", "HIGH"] and ws.status != "BLOCKED":
            ws.status = "BLOCKED"

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="INTEGRATION_BLOCKER_REPORTED",
                entity_type="IntegrationBlocker",
                entity_id=blocker.id,
                details={"title": blocker.title, "severity": blocker.severity},
            )
        )
        await self._sync_program_health(prog.id)
        await self.session.commit()
        return BlockerResponse.model_validate(blocker)

    async def resolve_blocker(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        blocker_id: uuid.UUID,
        payload: BlockerResolveRequest,
    ) -> BlockerResponse:
        """Resolve a blocker."""
        context.validate_deal_access(deal_id)
        blocker = await self.repo.get_blocker(context.organization_id, blocker_id)
        if not blocker:
            raise NotFoundException("IntegrationBlocker", blocker_id)

        resolved = await self.repo.resolve_blocker(blocker, payload.resolution_notes)

        # Check if workstream can return to IN_PROGRESS
        ws = await self.repo.get_workstream(context.organization_id, blocker.workstream_id)
        if ws and ws.status == "BLOCKED":
            ws.status = "IN_PROGRESS"

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="INTEGRATION_BLOCKER_RESOLVED",
                entity_type="IntegrationBlocker",
                entity_id=blocker.id,
                details={"resolution": payload.resolution_notes},
            )
        )
        await self._sync_program_health(blocker.program_id)
        await self.session.commit()
        return BlockerResponse.model_validate(resolved)

    # ==========================================
    # Analytics & Timeline Views
    # ==========================================

    async def get_timeline(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> TimelineStageResponse:
        """Retrieve 100-Day Timeline grouped into Day 0, Days 1-30, Days 31-60, Days 61-100."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id)

        stages: Dict[str, List[MilestoneResponse]] = {
            "DAY_0_CLOSE": [],
            "DAYS_1_30_STABILIZE": [],
            "DAYS_31_60_INTEGRATE": [],
            "DAYS_61_100_OPTIMIZE": [],
        }

        for m in milestones:
            stg = get_100day_stage(m.target_day)
            stages[stg].append(self._format_milestone(m))

        return TimelineStageResponse(
            deal_id=deal_id,
            current_day_offset=prog.current_day_offset,
            stages=stages,
        )

    async def get_critical_path(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> CriticalPathResponse:
        """Compute critical path across milestones."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id)
        dependencies = await self.repo.list_dependencies(context.organization_id, prog.id)

        cp_data = compute_critical_path(milestones, dependencies)
        return CriticalPathResponse(deal_id=deal_id, **cp_data)

    async def get_health(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> IntegrationHealthResponse:
        """Compute deterministic integration health score."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        workstreams = await self.repo.list_workstreams(context.organization_id, prog.id)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id)
        blockers = await self.repo.list_blockers(context.organization_id, prog.id)

        health_data = calculate_integration_health_score(
            workstreams, milestones, blockers, prog.current_day_offset
        )
        return IntegrationHealthResponse(deal_id=deal_id, **health_data)

    async def get_executive_attention(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> ExecutiveAttentionResponse:
        """Fetch prioritized executive escalations."""
        context.validate_deal_access(deal_id)
        prog = await self._ensure_program(context, deal_id)
        workstreams = await self.repo.list_workstreams(context.organization_id, prog.id)
        milestones = await self.repo.list_milestones(context.organization_id, prog.id)
        dependencies = await self.repo.list_dependencies(context.organization_id, prog.id)
        blockers = await self.repo.list_blockers(context.organization_id, prog.id)

        cp_data = compute_critical_path(milestones, dependencies)
        att_data = generate_executive_attention_queue(
            workstreams=workstreams,
            milestones=milestones,
            blockers=blockers,
            critical_path_milestone_ids=cp_data["critical_path_milestone_ids"],
            current_day_offset=prog.current_day_offset,
        )
        return ExecutiveAttentionResponse(deal_id=deal_id, **att_data)

    # ==========================================
    # Helper & Aggregation Methods
    # ==========================================

    async def _ensure_program(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> IntegrationProgram:
        """Fetch or initialize program."""
        prog = await self.repo.get_program(context.organization_id, deal_id)
        if not prog:
            prog = await self.repo.create_program(
                organization_id=context.organization_id,
                deal_id=deal_id,
                company_id=None,
                data={"name": "100-Day Value Creation & Integration Plan"},
                user_id=context.user_id,
            )
            await self.session.flush()
        return prog

    async def _recompute_workstream_progress(self, ws: IntegrationWorkstream) -> None:
        """Update workstream progress based on milestone completion."""
        milestones = await self.repo.list_milestones(
            ws.organization_id, ws.program_id, workstream_id=ws.id
        )
        if milestones:
            avg_progress = sum(float(m.completion_pct or 0.0) for m in milestones) / len(milestones)
            ws.progress_pct = round(avg_progress, 1)
            if ws.progress_pct >= 100.0 and ws.status != "COMPLETED":
                ws.status = "COMPLETED"
            elif ws.progress_pct > 0.0 and ws.status == "NOT_STARTED":
                ws.status = "IN_PROGRESS"
            await self.session.flush()

    async def _sync_program_health(self, program_id: uuid.UUID) -> None:
        """Recalculate and persist program health score."""
        # Find program org and deal
        query = select(IntegrationProgram).where(IntegrationProgram.id == program_id)
        res = await self.session.execute(query)
        prog = res.scalar_one_or_none()
        if not prog:
            return

        workstreams = await self.repo.list_workstreams(prog.organization_id, prog.id)
        milestones = await self.repo.list_milestones(prog.organization_id, prog.id)
        blockers = await self.repo.list_blockers(prog.organization_id, prog.id)

        health_data = calculate_integration_health_score(
            workstreams, milestones, blockers, prog.current_day_offset
        )
        prog.health_score = health_data["health_score"]
        prog.health_band = health_data["health_band"]
        await self.session.flush()

    async def _format_program(self, prog: IntegrationProgram) -> IntegrationProgramResponse:
        """Format program with aggregate summary statistics."""
        workstreams = await self.repo.list_workstreams(prog.organization_id, prog.id)
        milestones = await self.repo.list_milestones(prog.organization_id, prog.id)
        dependencies = await self.repo.list_dependencies(prog.organization_id, prog.id)
        blockers = await self.repo.list_blockers(prog.organization_id, prog.id)

        cp_data = compute_critical_path(milestones, dependencies)
        health_data = calculate_integration_health_score(
            workstreams, milestones, blockers, prog.current_day_offset
        )

        completed_count = sum(1 for m in milestones if m.status == "COMPLETED" or m.completion_pct >= 100.0)
        overdue_count = sum(
            1 for m in milestones if (m.target_day < prog.current_day_offset and m.completion_pct < 100.0) or m.status == "OVERDUE"
        )
        open_blockers_count = sum(1 for b in blockers if b.status == "OPEN")

        overall_progress = (
            round(sum(float(m.completion_pct or 0.0) for m in milestones) / len(milestones), 1)
            if milestones
            else 0.0
        )

        return IntegrationProgramResponse(
            id=prog.id,
            deal_id=prog.deal_id,
            company_id=prog.company_id,
            organization_id=prog.organization_id,
            name=prog.name,
            status=prog.status,
            close_date=prog.close_date,
            day_0_date=prog.day_0_date,
            day_100_date=prog.day_100_date,
            current_day_offset=prog.current_day_offset,
            executive_sponsor=prog.executive_sponsor,
            objectives=prog.objectives or {},
            health_score=health_data["health_score"],
            health_band=health_data["health_band"],
            total_workstreams=len(workstreams),
            total_milestones=len(milestones),
            completed_milestones=completed_count,
            overdue_milestones=overdue_count,
            open_blockers=open_blockers_count,
            critical_path_duration_days=cp_data["critical_path_duration_days"],
            overall_progress_pct=overall_progress,
            created_at=prog.created_at,
            updated_at=prog.updated_at,
        )

    def _format_workstream(
        self, ws: IntegrationWorkstream, milestones_count: int, completed_count: int
    ) -> WorkstreamResponse:
        return WorkstreamResponse(
            id=ws.id,
            deal_id=ws.deal_id,
            program_id=ws.program_id,
            name=ws.name,
            description=ws.description,
            category=ws.category,
            owner=ws.owner,
            executive_sponsor=ws.executive_sponsor,
            status=ws.status,
            priority=ws.priority,
            start_day=ws.start_day,
            target_day=ws.target_day,
            progress_pct=ws.progress_pct,
            risk_level=ws.risk_level,
            linked_synergy_ids=ws.linked_synergy_ids or [],
            linked_risk_ids=ws.linked_risk_ids or [],
            notes=ws.notes,
            milestones_count=milestones_count,
            completed_milestones_count=completed_count,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        )

    def _format_milestone(self, m: IntegrationMilestone) -> MilestoneResponse:
        return MilestoneResponse(
            id=m.id,
            deal_id=m.deal_id,
            program_id=m.program_id,
            workstream_id=m.workstream_id,
            name=m.name,
            description=m.description,
            target_day=m.target_day,
            target_date=m.target_date,
            stage=get_100day_stage(m.target_day),
            status=m.status,
            priority=m.priority,
            owner=m.owner,
            completion_pct=m.completion_pct,
            is_critical_path=m.is_critical_path,
            linked_synergy_id=m.linked_synergy_id,
            deliverable=m.deliverable,
            evidence_citation_ids=m.evidence_citation_ids or [],
            notes=m.notes,
            completed_at=m.completed_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
