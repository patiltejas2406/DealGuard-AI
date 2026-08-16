"""Deal Management Domain Service."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.common.context import TenantContext
from app.domains.deals.models import Deal, TargetCompany
from app.domains.deals.repository import DealRepository


class DealService:
    """Business operations for Deal Management and Gating."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DealRepository(session)

    async def list_deals(
        self, context: TenantContext, stage: Optional[str] = None, status: Optional[str] = None
    ) -> List[Deal]:
        return await self.repo.list_deals(context.organization_id, stage=stage, status=status)

    async def get_deal(self, context: TenantContext, deal_id: uuid.UUID) -> Deal:
        deal = await self.repo.get_deal_by_id(context.organization_id, deal_id)
        if not deal:
            raise NotFoundException("Deal", deal_id)
        return deal

    async def create_deal_with_target(
        self,
        context: TenantContext,
        company_name: str,
        company_industry: str,
        deal_title: str,
        code_name: Optional[str] = None,
        deal_type: str = "M_AND_A_BUY_SIDE",
        stage: str = "PRE_DILIGENCE",
        target_ev: Optional[float] = None,
        currency: str = "USD",
    ) -> Deal:
        target = await self.repo.create_target_company(
            organization_id=context.organization_id,
            name=company_name,
            industry=company_industry,
        )
        deal = await self.repo.create_deal(
            organization_id=context.organization_id,
            target_company_id=target.id,
            title=deal_title,
            code_name=code_name,
            deal_type=deal_type,
            stage=stage,
            target_ev=target_ev,
            currency=currency,
            created_by_id=context.user_id,
        )
        # Assign creator as DEAL LEAD
        await self.repo.add_deal_member(
            organization_id=context.organization_id,
            deal_id=deal.id,
            user_id=context.user_id,
            deal_role="LEAD",
            can_edit=True,
        )
        await self.session.commit()
        return await self.get_deal(context, deal.id)
