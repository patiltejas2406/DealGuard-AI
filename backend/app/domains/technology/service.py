"""Technology, Operational & Product Diligence Business Service."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.documents.models import DocumentChunk
from app.domains.technology.analytics import compute_technology_summary_metrics
from app.domains.technology.config import validate_tech_transition
from app.domains.technology.models import (
    OperationalMetric,
    TechnologyDependency,
    TechnologyFinding,
)
from app.domains.technology.repository import TechnologyRepository
from app.domains.technology.scanner import extract_technology_findings_from_chunks
from app.domains.technology.schemas import (
    OperationalMetricResponse,
    TechnologyDependencyResponse,
    TechnologyFindingCreateRequest,
    TechnologyFindingResponse,
    TechnologyFindingStatusUpdateRequest,
    TechnologyScanResponse,
    TechnologySummaryResponse,
)


class TechnologyService:
    """Business service orchestrating technology diligence, cloud cost analysis, and operational reliability tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TechnologyRepository(session)

    # ==========================================
    # Scanning Pipeline
    # ==========================================

    async def scan_deal_documents(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> TechnologyScanResponse:
        """Scan data room document chunks for technological debt, single points of failure, and infrastructure metrics."""
        context.validate_deal_access(deal_id)

        chunk_query = select(DocumentChunk).where(
            DocumentChunk.deal_id == deal_id,
            DocumentChunk.organization_id == context.organization_id,
        )
        chunk_res = await self.session.execute(chunk_query)
        chunks = list(chunk_res.scalars().all())

        raw_findings, raw_metrics, raw_dependencies = extract_technology_findings_from_chunks(
            chunks=chunks,
            deal_id=deal_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
        )

        saved_findings = []
        for f_data in raw_findings:
            f = await self.repo.upsert_finding_by_fingerprint(f_data)
            saved_findings.append(f)

        saved_metrics = []
        for m_data in raw_metrics:
            m = await self.repo.upsert_metric_by_fingerprint(m_data)
            saved_metrics.append(m)

        saved_deps = []
        for d_data in raw_dependencies:
            d = await self.repo.upsert_dependency_by_fingerprint(d_data)
            saved_deps.append(d)

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="TECHNOLOGY_DILIGENCE_SCAN_COMPLETED",
                entity_type="Deal",
                entity_id=deal_id,
                details={
                    "findings_extracted": len(saved_findings),
                    "metrics_recorded": len(saved_metrics),
                    "dependencies_identified": len(saved_deps),
                },
            )
        )
        await self.session.commit()

        return TechnologyScanResponse(
            deal_id=deal_id,
            findings_extracted=len(saved_findings),
            metrics_recorded=len(saved_metrics),
            dependencies_identified=len(saved_deps),
            message=f"Extracted {len(saved_findings)} technology findings and {len(saved_deps)} critical dependencies.",
        )

    # ==========================================
    # Findings Operations
    # ==========================================

    async def list_findings(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        category: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[TechnologyFindingResponse]:
        context.validate_deal_access(deal_id)
        findings = await self.repo.list_findings(context.organization_id, deal_id, category, severity)
        return [TechnologyFindingResponse.model_validate(f) for f in findings]

    async def create_finding(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        payload: TechnologyFindingCreateRequest,
    ) -> TechnologyFindingResponse:
        context.validate_deal_access(deal_id)
        finding = await self.repo.create_finding(
            organization_id=context.organization_id,
            deal_id=deal_id,
            data=payload.model_dump(),
            user_id=context.user_id,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="TECHNOLOGY_FINDING_CREATED",
                entity_type="TechnologyFinding",
                entity_id=finding.id,
                details={"title": finding.title, "category": finding.category},
            )
        )
        await self.session.commit()
        return TechnologyFindingResponse.model_validate(finding)

    async def update_finding_status(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        finding_id: uuid.UUID,
        payload: TechnologyFindingStatusUpdateRequest,
    ) -> TechnologyFindingResponse:
        context.validate_deal_access(deal_id)
        finding = await self.repo.get_finding(context.organization_id, finding_id)
        if not finding:
            raise NotFoundException("TechnologyFinding", finding_id)

        validate_tech_transition(finding.status, payload.status)
        old_status = finding.status
        finding.status = payload.status

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="TECHNOLOGY_FINDING_STATUS_UPDATED",
                entity_type="TechnologyFinding",
                entity_id=finding.id,
                details={"old_status": old_status, "new_status": payload.status, "notes": payload.notes},
            )
        )
        await self.session.commit()
        return TechnologyFindingResponse.model_validate(finding)

    # ==========================================
    # Operational Metrics & Dependencies
    # ==========================================

    async def list_metrics(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        metric_category: Optional[str] = None,
    ) -> List[OperationalMetricResponse]:
        context.validate_deal_access(deal_id)
        metrics = await self.repo.list_metrics(context.organization_id, deal_id, metric_category)
        return [OperationalMetricResponse.model_validate(m) for m in metrics]

    async def list_dependencies(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        criticality: Optional[str] = None,
    ) -> List[TechnologyDependencyResponse]:
        context.validate_deal_access(deal_id)
        deps = await self.repo.list_dependencies(context.organization_id, deal_id, criticality)
        return [TechnologyDependencyResponse.model_validate(d) for d in deps]

    # ==========================================
    # Executive Technology Summary
    # ==========================================

    async def get_technology_summary(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> TechnologySummaryResponse:
        context.validate_deal_access(deal_id)
        findings = await self.repo.list_findings(context.organization_id, deal_id)
        metrics = await self.repo.list_metrics(context.organization_id, deal_id)
        dependencies = await self.repo.list_dependencies(context.organization_id, deal_id)

        summary_data = compute_technology_summary_metrics(findings, metrics, dependencies)
        return TechnologySummaryResponse(deal_id=deal_id, **summary_data)
