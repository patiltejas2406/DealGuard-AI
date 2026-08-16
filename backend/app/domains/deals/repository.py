"""Deal Workspace & Target Company Repository Layer with Strict Tenancy Enforced."""

import uuid
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.deals.models import Deal, DealMember, TargetCompany


class DealRepository:
    """Tenant-scoped persistence operations for Deals and Target Companies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_target_company_by_id(
        self, organization_id: uuid.UUID, company_id: uuid.UUID
    ) -> Optional[TargetCompany]:
        stmt = (
            select(TargetCompany)
            .where(
                TargetCompany.organization_id == organization_id,
                TargetCompany.id == company_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_target_company(
        self,
        organization_id: uuid.UUID,
        name: str,
        industry: str,
        sector: Optional[str] = None,
        headquarters: Optional[str] = None,
        website: Optional[str] = None,
        founding_year: Optional[int] = None,
        employee_count: Optional[int] = None,
        description: Optional[str] = None,
    ) -> TargetCompany:
        company = TargetCompany(
            organization_id=organization_id,
            name=name,
            industry=industry,
            sector=sector,
            headquarters=headquarters,
            website=website,
            founding_year=founding_year,
            employee_count=employee_count,
            description=description,
        )
        self.session.add(company)
        await self.session.flush()
        return company

    async def list_deals(
        self, organization_id: uuid.UUID, stage: Optional[str] = None, status: Optional[str] = None
    ) -> List[Deal]:
        stmt = (
            select(Deal)
            .where(Deal.organization_id == organization_id)
            .options(
                selectinload(Deal.target_company),
                selectinload(Deal.members),
            )
            .order_by(Deal.created_at.desc())
        )
        if stage:
            stmt = stmt.where(Deal.stage == stage)
        if status:
            stmt = stmt.where(Deal.status == status)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_deal_by_id(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[Deal]:
        stmt = (
            select(Deal)
            .where(
                Deal.organization_id == organization_id,
                Deal.id == deal_id,
            )
            .options(
                selectinload(Deal.target_company),
                selectinload(Deal.members),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_deal(
        self,
        organization_id: uuid.UUID,
        target_company_id: uuid.UUID,
        title: str,
        code_name: Optional[str] = None,
        deal_type: str = "M_AND_A_BUY_SIDE",
        stage: str = "PRE_DILIGENCE",
        target_ev: Optional[float] = None,
        currency: str = "USD",
        created_by_id: Optional[uuid.UUID] = None,
    ) -> Deal:
        deal = Deal(
            organization_id=organization_id,
            target_company_id=target_company_id,
            title=title,
            code_name=code_name,
            deal_type=deal_type,
            stage=stage,
            target_ev=target_ev,
            currency=currency,
            created_by_id=created_by_id,
        )
        self.session.add(deal)
        await self.session.flush()
        return deal

    async def add_deal_member(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        user_id: uuid.UUID,
        deal_role: str = "ANALYST",
        can_edit: bool = True,
    ) -> DealMember:
        member = DealMember(
            organization_id=organization_id,
            deal_id=deal_id,
            user_id=user_id,
            deal_role=deal_role,
            can_edit=can_edit,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def delete_deal(self, organization_id: uuid.UUID, deal_id: uuid.UUID) -> bool:
        stmt = delete(Deal).where(
            Deal.organization_id == organization_id,
            Deal.id == deal_id,
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
