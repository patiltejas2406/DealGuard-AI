"""Deal Risk Intelligence Domain Service."""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ValidationException
from app.domains.audit.service import AuditService
from app.domains.common.context import TenantContext
from app.domains.risk.models import Risk
from app.domains.risk.repository import RiskRepository
from app.domains.risk.scanner import DocumentRiskScanner
from app.domains.risk.scoring import compute_risk_matrix
from app.domains.risk.taxonomy import (
    CATEGORY_METADATA,
    CategoryInfo,
    DetectionSource,
    RiskCategory,
    RiskStatus,
)


class RiskService:
    """Business operations for Risk Register, Evidence Provenance, and Automated Scans."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RiskRepository(session)
        self.audit_service = AuditService(session)
        self.scanner = DocumentRiskScanner(session)

    async def list_risks(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        min_severity: Optional[int] = None,
        min_likelihood: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "score",
        sort_desc: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Risk], int]:
        """List risks for a deal with tenant validation, filtering, and pagination."""
        context.validate_deal_access(deal_id)
        return await self.repo.list_risks_for_deal(
            organization_id=context.organization_id,
            deal_id=deal_id,
            category=category,
            risk_level=risk_level,
            status=status,
            min_severity=min_severity,
            min_likelihood=min_likelihood,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
            offset=offset,
            limit=limit,
        )

    async def get_risk(
        self, context: TenantContext, deal_id: uuid.UUID, risk_id: uuid.UUID
    ) -> Risk:
        """Fetch a single risk item with evidence citations."""
        context.validate_deal_access(deal_id)
        risk = await self.repo.get_risk_by_id(context.organization_id, deal_id, risk_id)
        if not risk:
            raise NotFoundException("Risk", risk_id)
        return risk

    async def create_risk(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        category: RiskCategory,
        title: str,
        description: str,
        severity: int,
        likelihood: int,
        status: RiskStatus = RiskStatus.IDENTIFIED,
        detection_source: DetectionSource = DetectionSource.MANUAL_ENTRY,
        confidence_score: Optional[float] = None,
        mitigation_strategy: Optional[str] = None,
        recommendation: Optional[str] = None,
        company_id: Optional[uuid.UUID] = None,
        citation_ids: Optional[List[uuid.UUID]] = None,
    ) -> Risk:
        """Create a new risk item and record audit log."""
        context.validate_deal_access(deal_id)

        meta = CATEGORY_METADATA.get(category)
        if not recommendation and meta:
            recommendation = f"Targeted review for {meta.name}. {meta.default_mitigation}"

        risk = await self.repo.create_risk(
            organization_id=context.organization_id,
            deal_id=deal_id,
            category=category.value,
            title=title,
            description=description,
            severity=severity,
            likelihood=likelihood,
            status=status.value,
            detection_source=detection_source.value,
            confidence_score=confidence_score,
            mitigation_strategy=mitigation_strategy or (meta.default_mitigation if meta else None),
            recommendation=recommendation,
            company_id=company_id,
            owner_id=context.user_id,
        )

        if citation_ids:
            for cit_id in citation_ids:
                await self.repo.link_evidence_to_risk(
                    organization_id=context.organization_id,
                    deal_id=deal_id,
                    risk_id=risk.id,
                    citation_id=cit_id,
                    relevance_explanation="Manual citation attachment",
                )

        await self.audit_service.log_event(
            organization_id=context.organization_id,
            deal_id=deal_id,
            actor_user_id=context.user_id,
            action="RISK_CREATED",
            entity_type="Risk",
            entity_id=risk.id,
            details={
                "category": risk.category,
                "score": risk.score,
                "risk_level": risk.risk_level,
                "source": risk.detection_source,
            },
        )

        return await self.get_risk(context, deal_id, risk.id)

    async def update_risk(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        risk_id: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[RiskCategory] = None,
        severity: Optional[int] = None,
        likelihood: Optional[int] = None,
        status: Optional[RiskStatus] = None,
        mitigation_strategy: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> Risk:
        """Update risk item attributes and log audit modification."""
        risk = await self.get_risk(context, deal_id, risk_id)

        old_score = risk.score
        old_level = risk.risk_level

        updated = await self.repo.update_risk(
            risk=risk,
            title=title,
            description=description,
            category=category.value if category else None,
            severity=severity,
            likelihood=likelihood,
            status=status.value if status else None,
            mitigation_strategy=mitigation_strategy,
            recommendation=recommendation,
        )

        await self.audit_service.log_event(
            organization_id=context.organization_id,
            deal_id=deal_id,
            actor_user_id=context.user_id,
            action="RISK_UPDATED",
            entity_type="Risk",
            entity_id=risk.id,
            details={
                "old_score": old_score,
                "new_score": updated.score,
                "old_level": old_level,
                "new_level": updated.risk_level,
            },
        )

        return updated

    async def update_risk_status(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        risk_id: uuid.UUID,
        new_status: RiskStatus,
        rationale: Optional[str] = None,
    ) -> Risk:
        """Update risk lifecycle status (REVIEWED, ACCEPTED, MITIGATED, REJECTED) with audit trail."""
        risk = await self.get_risk(context, deal_id, risk_id)
        old_status = risk.status

        risk.status = new_status.value
        await self.session.flush()

        await self.audit_service.log_event(
            organization_id=context.organization_id,
            deal_id=deal_id,
            actor_user_id=context.user_id,
            action="RISK_STATUS_CHANGED",
            entity_type="Risk",
            entity_id=risk.id,
            details={
                "old_status": old_status,
                "new_status": new_status.value,
                "rationale": rationale or "No rationale provided",
            },
        )

        return risk

    async def delete_risk(
        self, context: TenantContext, deal_id: uuid.UUID, risk_id: uuid.UUID
    ) -> None:
        """Delete a risk item and record audit event."""
        risk = await self.get_risk(context, deal_id, risk_id)
        await self.repo.delete_risk(risk)

        await self.audit_service.log_event(
            organization_id=context.organization_id,
            deal_id=deal_id,
            actor_user_id=context.user_id,
            action="RISK_DELETED",
            entity_type="Risk",
            entity_id=risk_id,
            details={"title": risk.title, "category": risk.category},
        )

    async def get_risk_matrix(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compute the 5x5 Likelihood x Severity matrix and summary metrics."""
        context.validate_deal_access(deal_id)
        risks, _ = await self.repo.list_risks_for_deal(
            organization_id=context.organization_id,
            deal_id=deal_id,
            limit=500,
        )
        return compute_risk_matrix(risks)

    def get_categories_metadata(self) -> List[CategoryInfo]:
        """Return full taxonomy metadata for all 17 risk categories."""
        return list(CATEGORY_METADATA.values())

    async def run_automated_risk_scan(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        categories: Optional[List[RiskCategory]] = None,
        min_confidence: float = 0.60,
    ) -> Tuple[List[Risk], int, int, int]:
        """
        Execute automated document risk scanner across all data room files for the deal.
        """
        context.validate_deal_access(deal_id)

        created_risks, scanned_chunks, detected_count, duplicates_skipped = (
            await self.scanner.scan_deal_documents(
                organization_id=context.organization_id,
                deal_id=deal_id,
                categories=categories,
                min_confidence=min_confidence,
            )
        )

        await self.audit_service.log_event(
            organization_id=context.organization_id,
            deal_id=deal_id,
            actor_user_id=context.user_id,
            action="RISK_SCAN_EXECUTED",
            entity_type="Deal",
            entity_id=deal_id,
            details={
                "scanned_chunks": scanned_chunks,
                "detected_count": detected_count,
                "created_count": len(created_risks),
                "duplicates_skipped": duplicates_skipped,
            },
        )

        # Reload created risks with citations
        reloaded_risks: List[Risk] = []
        for r in created_risks:
            reloaded = await self.repo.get_risk_by_id(context.organization_id, deal_id, r.id)
            if reloaded:
                reloaded_risks.append(reloaded)

        return reloaded_risks, scanned_chunks, detected_count, duplicates_skipped
