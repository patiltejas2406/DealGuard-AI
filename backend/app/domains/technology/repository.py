"""Async Database Repository for Technology, Operational & Product Diligence."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.technology.models import (
    OperationalMetric,
    TechnologyDependency,
    TechnologyFinding,
)


class TechnologyRepository:
    """Encapsulates all database operations for technology findings, operational metrics, and dependencies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==========================================
    # Findings
    # ==========================================

    async def list_findings(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        category: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[TechnologyFinding]:
        query = select(TechnologyFinding).where(
            TechnologyFinding.organization_id == organization_id,
            TechnologyFinding.deal_id == deal_id,
        )
        if category:
            query = query.where(TechnologyFinding.category == category)
        if severity:
            query = query.where(TechnologyFinding.severity == severity)
        query = query.order_by(TechnologyFinding.monetary_exposure.desc(), TechnologyFinding.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_finding(
        self, organization_id: uuid.UUID, finding_id: uuid.UUID
    ) -> Optional[TechnologyFinding]:
        query = select(TechnologyFinding).where(
            TechnologyFinding.organization_id == organization_id,
            TechnologyFinding.id == finding_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_finding(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID],
    ) -> TechnologyFinding:
        finding = TechnologyFinding(
            organization_id=organization_id,
            deal_id=deal_id,
            category=data["category"],
            title=data["title"],
            technical_fact=data["technical_fact"],
            business_impact=data.get("business_impact"),
            recommendation=data.get("recommendation"),
            severity=data.get("severity", "MEDIUM"),
            likelihood=data.get("likelihood", "MEDIUM"),
            confidence=data.get("confidence", "HIGH"),
            monetary_exposure=data.get("monetary_exposure", 0.0),
            status=data.get("status", "IDENTIFIED"),
            fingerprint=data.get("fingerprint", uuid.uuid4().hex),
            created_by_id=user_id,
        )
        self.session.add(finding)
        await self.session.flush()
        return finding

    async def upsert_finding_by_fingerprint(
        self, data: Dict[str, Any]
    ) -> TechnologyFinding:
        query = select(TechnologyFinding).where(
            TechnologyFinding.deal_id == data["deal_id"],
            TechnologyFinding.fingerprint == data["fingerprint"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        finding = TechnologyFinding(**data)
        self.session.add(finding)
        await self.session.flush()
        return finding

    # ==========================================
    # Operational Metrics
    # ==========================================

    async def list_metrics(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        metric_category: Optional[str] = None,
    ) -> List[OperationalMetric]:
        query = select(OperationalMetric).where(
            OperationalMetric.organization_id == organization_id,
            OperationalMetric.deal_id == deal_id,
        )
        if metric_category:
            query = query.where(OperationalMetric.metric_category == metric_category)
        query = query.order_by(OperationalMetric.created_at.asc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def upsert_metric_by_fingerprint(
        self, data: Dict[str, Any]
    ) -> OperationalMetric:
        query = select(OperationalMetric).where(
            OperationalMetric.deal_id == data["deal_id"],
            OperationalMetric.fingerprint == data["fingerprint"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        metric = OperationalMetric(**data)
        self.session.add(metric)
        await self.session.flush()
        return metric

    # ==========================================
    # Technology Dependencies
    # ==========================================

    async def list_dependencies(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        criticality: Optional[str] = None,
    ) -> List[TechnologyDependency]:
        query = select(TechnologyDependency).where(
            TechnologyDependency.organization_id == organization_id,
            TechnologyDependency.deal_id == deal_id,
        )
        if criticality:
            query = query.where(TechnologyDependency.criticality == criticality)
        query = query.order_by(TechnologyDependency.annual_cost.desc(), TechnologyDependency.created_at.asc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def upsert_dependency_by_fingerprint(
        self, data: Dict[str, Any]
    ) -> TechnologyDependency:
        query = select(TechnologyDependency).where(
            TechnologyDependency.deal_id == data["deal_id"],
            TechnologyDependency.fingerprint == data["fingerprint"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        dep = TechnologyDependency(**data)
        self.session.add(dep)
        await self.session.flush()
        return dep
