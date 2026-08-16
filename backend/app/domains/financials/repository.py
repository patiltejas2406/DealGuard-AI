"""Financial Statements, Metrics & QoE Adjustments Repository Layer."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.common.models import utc_now
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment


class FinancialRepository:
    """Tenant-scoped persistence operations for Financial Statements, Metrics, and QoE."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Statements
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

    async def get_statement_by_period(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, statement_type: str, fiscal_period: str
    ) -> Optional[FinancialStatement]:
        stmt = (
            select(FinancialStatement)
            .where(
                FinancialStatement.organization_id == organization_id,
                FinancialStatement.deal_id == deal_id,
                FinancialStatement.statement_type == statement_type.upper(),
                FinancialStatement.fiscal_period == fiscal_period,
            )
            .options(selectinload(FinancialStatement.metrics))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_statement(
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
        existing = await self.get_statement_by_period(
            organization_id, deal_id, statement_type, fiscal_period
        )
        if existing:
            existing.line_items = line_items
            existing.is_audited = is_audited
            existing.is_normalized = is_normalized
            existing.source_currency = source_currency.upper()
            existing.period_type = period_type.upper()
            existing.updated_at = utc_now()
            await self.session.flush()
            return existing

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

    # Metrics
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

    async def upsert_metric(
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
        stmt = (
            select(FinancialMetric)
            .where(
                FinancialMetric.organization_id == organization_id,
                FinancialMetric.deal_id == deal_id,
                FinancialMetric.metric_name == metric_name.upper(),
                FinancialMetric.period == period,
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.unit = unit.upper()
            existing.source_currency = source_currency.upper()
            existing.is_normalized = is_normalized
            existing.calculation_formula = calculation_formula
            existing.citation_id = citation_id or existing.citation_id
            existing.statement_id = statement_id or existing.statement_id
            existing.updated_at = utc_now()
            await self.session.flush()
            return existing

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

    # QoE Adjustments
    async def list_qoe_adjustments(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, period: Optional[str] = None
    ) -> List[QoEAdjustment]:
        stmt = (
            select(QoEAdjustment)
            .where(
                QoEAdjustment.organization_id == organization_id,
                QoEAdjustment.deal_id == deal_id,
            )
            .options(
                selectinload(QoEAdjustment.citation),
                selectinload(QoEAdjustment.created_by),
            )
        )
        if period:
            stmt = stmt.where(QoEAdjustment.period == period)
        stmt = stmt.order_by(QoEAdjustment.period.asc(), QoEAdjustment.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_qoe_adjustment(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, adjustment_id: uuid.UUID
    ) -> Optional[QoEAdjustment]:
        stmt = (
            select(QoEAdjustment)
            .where(
                QoEAdjustment.organization_id == organization_id,
                QoEAdjustment.deal_id == deal_id,
                QoEAdjustment.id == adjustment_id,
            )
            .options(
                selectinload(QoEAdjustment.citation),
                selectinload(QoEAdjustment.created_by),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_qoe_adjustment(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        category: str,
        description: str,
        amount: float,
        currency: str = "USD",
        period: str = "FY2023",
        treatment: str = "ADD_BACK",
        status: str = "PROPOSED",
        notes: Optional[str] = None,
        citation_id: Optional[uuid.UUID] = None,
        created_by_id: Optional[uuid.UUID] = None,
    ) -> QoEAdjustment:
        adj = QoEAdjustment(
            organization_id=organization_id,
            deal_id=deal_id,
            category=category.upper(),
            description=description,
            amount=amount,
            currency=currency.upper(),
            period=period,
            treatment=treatment.upper(),
            status=status.upper(),
            notes=notes,
            citation_id=citation_id,
            created_by_id=created_by_id,
        )
        self.session.add(adj)
        await self.session.flush()
        return adj

    async def update_qoe_adjustment(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        adjustment_id: uuid.UUID,
        **kwargs: Any,
    ) -> Optional[QoEAdjustment]:
        adj = await self.get_qoe_adjustment(organization_id, deal_id, adjustment_id)
        if not adj:
            return None
        for k, v in kwargs.items():
            if hasattr(adj, k) and v is not None:
                setattr(adj, k, v)
        adj.updated_at = utc_now()
        await self.session.flush()
        return adj

    async def delete_qoe_adjustment(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, adjustment_id: uuid.UUID
    ) -> bool:
        stmt = delete(QoEAdjustment).where(
            QoEAdjustment.organization_id == organization_id,
            QoEAdjustment.deal_id == deal_id,
            QoEAdjustment.id == adjustment_id,
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
