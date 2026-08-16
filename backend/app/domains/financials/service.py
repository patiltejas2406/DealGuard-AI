"""Financial Statement & Metric Domain Service."""

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.common.context import TenantContext
from app.domains.financials.models import FinancialMetric, FinancialStatement
from app.domains.financials.repository import FinancialRepository


class FinancialService:
    """Business operations for 3-Statement Diligence and Metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FinancialRepository(session)

    async def list_statements(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[FinancialStatement]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_statements_for_deal(context.organization_id, deal_id)

    async def list_metrics(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[FinancialMetric]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_metrics_for_deal(context.organization_id, deal_id)
