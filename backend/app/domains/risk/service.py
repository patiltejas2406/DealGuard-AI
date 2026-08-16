"""Deal Risk Intelligence Domain Service."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.common.context import TenantContext
from app.domains.risk.models import Risk
from app.domains.risk.repository import RiskRepository


class RiskService:
    """Business operations for Risk Register and Evidence Attribution."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RiskRepository(session)

    async def list_risks(
        self, context: TenantContext, deal_id: uuid.UUID, category: Optional[str] = None
    ) -> List[Risk]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_risks_for_deal(context.organization_id, deal_id, category=category)
