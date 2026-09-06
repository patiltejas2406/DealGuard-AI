"""Post-Acquisition Intelligence Repository Layer."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.post_deal.models import (
    AcquisitionThesis,
    CustomerAccount,
    PostAcquisitionMetric,
    ValueCreationInitiative,
)
from app.domains.post_deal.schemas import (
    AcquisitionThesisCreate,
    CustomerAccountCreate,
    PostAcquisitionMetricCreate,
    ValueCreationInitiativeCreate,
)


class PostDealRepository:
    """Tenant-scoped database access layer for post-acquisition entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Customer Accounts
    async def create_customer_account(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: CustomerAccountCreate,
    ) -> CustomerAccount:
        account = CustomerAccount(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=payload.company_id,
            account_name=payload.account_name,
            segment=payload.segment,
            arr=payload.arr,
            mrr=payload.mrr,
            contract_start_date=payload.contract_start_date,
            contract_end_date=payload.contract_end_date,
            churn_risk_score=payload.churn_risk_score,
            health_status=payload.health_status,
            nps=payload.nps,
            is_churned=payload.is_churned,
            expansion_potential_usd=payload.expansion_potential_usd,
            industry=payload.industry,
            products_used=payload.products_used,
            notes=payload.notes,
        )
        self.session.add(account)
        await self.session.flush()
        return account

    async def list_customer_accounts(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[CustomerAccount]:
        q = select(CustomerAccount).where(
            CustomerAccount.organization_id == organization_id,
            CustomerAccount.deal_id == deal_id,
        ).order_by(CustomerAccount.arr.desc())
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # 2. Post-Acquisition Operating Metrics
    async def create_post_acquisition_metric(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: PostAcquisitionMetricCreate,
    ) -> PostAcquisitionMetric:
        metric = PostAcquisitionMetric(
            organization_id=organization_id,
            deal_id=deal_id,
            fiscal_period=payload.fiscal_period,
            metric_category=payload.metric_category,
            metric_name=payload.metric_name,
            baseline_value=payload.baseline_value,
            target_value=payload.target_value,
            actual_value=payload.actual_value,
            variance_pct=payload.variance_pct,
            unit=payload.unit,
            notes=payload.notes,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def list_post_acquisition_metrics(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[PostAcquisitionMetric]:
        q = select(PostAcquisitionMetric).where(
            PostAcquisitionMetric.organization_id == organization_id,
            PostAcquisitionMetric.deal_id == deal_id,
        ).order_by(PostAcquisitionMetric.fiscal_period.asc(), PostAcquisitionMetric.metric_name.asc())
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # 3. Acquisition Theses
    async def create_acquisition_thesis(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: AcquisitionThesisCreate,
    ) -> AcquisitionThesis:
        thesis = AcquisitionThesis(
            organization_id=organization_id,
            deal_id=deal_id,
            thesis_pillar=payload.thesis_pillar,
            target_metric=payload.target_metric,
            baseline_value=payload.baseline_value,
            target_value=payload.target_value,
            actual_value=payload.actual_value,
            variance_pct=payload.variance_pct,
            status=payload.status,
            rationale=payload.rationale,
            citations=payload.citations,
        )
        self.session.add(thesis)
        await self.session.flush()
        return thesis

    async def list_acquisition_theses(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[AcquisitionThesis]:
        q = select(AcquisitionThesis).where(
            AcquisitionThesis.organization_id == organization_id,
            AcquisitionThesis.deal_id == deal_id,
        ).order_by(AcquisitionThesis.thesis_pillar.asc())
        res = await self.session.execute(q)
        return list(res.scalars().all())

    # 4. Value Creation Initiatives
    async def create_value_creation_initiative(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: ValueCreationInitiativeCreate,
    ) -> ValueCreationInitiative:
        initiative = ValueCreationInitiative(
            organization_id=organization_id,
            deal_id=deal_id,
            pillar=payload.pillar,
            title=payload.title,
            description=payload.description,
            owner=payload.owner,
            target_ebitda_impact=payload.target_ebitda_impact,
            realized_ebitda_impact=payload.realized_ebitda_impact,
            status=payload.status,
            timeline_quarter=payload.timeline_quarter,
            notes=payload.notes,
        )
        self.session.add(initiative)
        await self.session.flush()
        return initiative

    async def list_value_creation_initiatives(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[ValueCreationInitiative]:
        q = select(ValueCreationInitiative).where(
            ValueCreationInitiative.organization_id == organization_id,
            ValueCreationInitiative.deal_id == deal_id,
        ).order_by(ValueCreationInitiative.target_ebitda_impact.desc())
        res = await self.session.execute(q)
        return list(res.scalars().all())
