"""Financial Statements & Metrics Repository Layer."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.financials.models import FinancialMetric, FinancialStatement


class FinancialRepository:
    """Tenant-scoped persistence operations for Financial Statements & Metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_statements_for_deal(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[FinancialStatement]:
        stmt = (
            select(FinancialStatement)
            .where(
                FinancialStatement.organization_id == organization_id,
                FinancialStatement.deal_id == deal_id,
            )
            .options(selectinload(FinancialStatement.metrics))
            .order_by(FinancialStatement.fiscal_year.asc(), FinancialStatement.fiscal_period.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_statement(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        statement_type: str,
        fiscal_year: int,
        fiscal_period: str,
        line_items: dict,
        source_currency: str = "USD",
        period_type: str = "ANNUAL",
        is_audited: bool = False,
        is_normalized: bool = False,
        source_document_id: Optional[uuid.UUID] = None,
    ) -> FinancialStatement:
        stmt = FinancialStatement(
            organization_id=organization_id,
            deal_id=deal_id,
            statement_type=statement_type.upper(),
            period_type=period_type.upper(),
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            line_items=line_items,
            source_currency=source_currency.upper(),
            is_audited=is_audited,
            is_normalized=is_normalized,
            source_document_id=source_document_id,
        )
        self.session.add(stmt)
        await self.session.flush()
        return stmt

    async def create_metric(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        metric_name: str,
        period: str,
        value: float,
        unit: str = "CURRENCY",
        source_currency: str = "USD",
        is_normalized: bool = False,
        statement_id: Optional[uuid.UUID] = None,
        citation_id: Optional[uuid.UUID] = None,
        calculation_formula: Optional[str] = None,
    ) -> FinancialMetric:
        metric = FinancialMetric(
            organization_id=organization_id,
            deal_id=deal_id,
            metric_name=metric_name.upper(),
            period=period,
            value=value,
            unit=unit.upper(),
            source_currency=source_currency.upper(),
            is_normalized=is_normalized,
            statement_id=statement_id,
            citation_id=citation_id,
            calculation_formula=calculation_formula,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def list_metrics_for_deal(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[FinancialMetric]:
        stmt = (
            select(FinancialMetric)
            .where(
                FinancialMetric.organization_id == organization_id,
                FinancialMetric.deal_id == deal_id,
            )
            .options(selectinload(FinancialMetric.citation))
            .order_by(FinancialMetric.period.asc(), FinancialMetric.metric_name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
