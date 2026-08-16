"""Valuation Intelligence Repository Layer for Multi-Tenant Persistence."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.common.models import utc_now
from app.domains.valuation.models import (
    ComparableCompany,
    PrecedentTransaction,
    Valuation,
    ValuationAssumption,
    ValuationOutput,
)


class ValuationRepository:
    """Tenant-scoped persistence operations for Valuations, Assumptions, Comps, Precedents & Outputs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -------------------------------------------------------------
    # 1. Valuations
    # -------------------------------------------------------------
    async def get_or_create_default_valuation(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Valuation:
        stmt = (
            select(Valuation)
            .where(Valuation.organization_id == organization_id, Valuation.deal_id == deal_id)
            .order_by(Valuation.created_at.asc())
        )
        res = await self.session.execute(stmt)
        val = res.scalar_one_or_none()
        if val:
            return val

        val = Valuation(
            organization_id=organization_id,
            deal_id=deal_id,
            title="Base Case Valuation",
            status="ACTIVE",
            selected_method="MULTI_METHOD",
            created_by_id=user_id,
        )
        self.session.add(val)
        await self.session.flush()
        return val

    async def get_valuation(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: uuid.UUID
    ) -> Optional[Valuation]:
        stmt = (
            select(Valuation)
            .where(
                Valuation.organization_id == organization_id,
                Valuation.deal_id == deal_id,
                Valuation.id == valuation_id,
            )
            .options(
                selectinload(Valuation.assumptions),
                selectinload(Valuation.comparables),
                selectinload(Valuation.precedents),
                selectinload(Valuation.outputs),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_valuation(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: uuid.UUID, **kwargs: Any
    ) -> Optional[Valuation]:
        val = await self.get_valuation(organization_id, deal_id, valuation_id)
        if not val:
            return None
        for k, v in kwargs.items():
            if hasattr(val, k) and v is not None:
                setattr(val, k, v)
        val.updated_at = utc_now()
        await self.session.flush()
        return val

    # -------------------------------------------------------------
    # 2. Assumptions
    # -------------------------------------------------------------
    async def list_assumptions(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[ValuationAssumption]:
        stmt = (
            select(ValuationAssumption)
            .where(
                ValuationAssumption.organization_id == organization_id,
                ValuationAssumption.deal_id == deal_id,
            )
            .options(selectinload(ValuationAssumption.citation))
        )
        if valuation_id:
            stmt = stmt.where(ValuationAssumption.valuation_id == valuation_id)
        stmt = stmt.order_by(ValuationAssumption.category.asc(), ValuationAssumption.name.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def upsert_assumption(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        name: str,
        value: float,
        unit: str = "PERCENTAGE",
        category: str = "WACC",
        period: Optional[str] = None,
        source_type: str = "ANALYST_INPUT",
        is_analyst_entered: bool = True,
        confidence_score: Optional[float] = None,
        citation_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        valuation_id: Optional[uuid.UUID] = None,
    ) -> ValuationAssumption:
        stmt = select(ValuationAssumption).where(
            ValuationAssumption.organization_id == organization_id,
            ValuationAssumption.deal_id == deal_id,
            ValuationAssumption.name == name.upper(),
        )
        if valuation_id:
            stmt = stmt.where(ValuationAssumption.valuation_id == valuation_id)
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.unit = unit.upper()
            existing.category = category.upper()
            existing.period = period
            existing.source_type = source_type.upper()
            existing.is_analyst_entered = is_analyst_entered
            existing.confidence_score = confidence_score
            existing.citation_id = citation_id or existing.citation_id
            existing.notes = notes or existing.notes
            existing.updated_at = utc_now()
            await self.session.flush()
            return existing

        ass = ValuationAssumption(
            organization_id=organization_id,
            deal_id=deal_id,
            valuation_id=valuation_id,
            name=name.upper(),
            category=category.upper(),
            value=value,
            unit=unit.upper(),
            period=period,
            source_type=source_type.upper(),
            is_analyst_entered=is_analyst_entered,
            confidence_score=confidence_score,
            citation_id=citation_id,
            notes=notes,
        )
        self.session.add(ass)
        await self.session.flush()
        return ass

    # -------------------------------------------------------------
    # 3. Comparable Companies
    # -------------------------------------------------------------
    async def list_comparables(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[ComparableCompany]:
        stmt = (
            select(ComparableCompany)
            .where(
                ComparableCompany.organization_id == organization_id,
                ComparableCompany.deal_id == deal_id,
            )
            .options(selectinload(ComparableCompany.citation))
            .order_by(ComparableCompany.company_name.asc())
        )
        if valuation_id:
            stmt = stmt.where(ComparableCompany.valuation_id == valuation_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_comparable(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, comp_id: uuid.UUID
    ) -> Optional[ComparableCompany]:
        stmt = (
            select(ComparableCompany)
            .where(
                ComparableCompany.organization_id == organization_id,
                ComparableCompany.deal_id == deal_id,
                ComparableCompany.id == comp_id,
            )
            .options(selectinload(ComparableCompany.citation))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_comparable(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        company_name: str,
        ticker: Optional[str] = None,
        industry: Optional[str] = None,
        geography: Optional[str] = None,
        revenue: Optional[float] = None,
        ebitda: Optional[float] = None,
        ebit: Optional[float] = None,
        net_income: Optional[float] = None,
        enterprise_value: Optional[float] = None,
        equity_value: Optional[float] = None,
        ev_to_revenue: Optional[float] = None,
        ev_to_ebitda: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        revenue_growth: Optional[float] = None,
        status: str = "INCLUDED",
        source: str = "ANALYST_INPUT",
        notes: Optional[str] = None,
        citation_id: Optional[uuid.UUID] = None,
        valuation_id: Optional[uuid.UUID] = None,
    ) -> ComparableCompany:
        comp = ComparableCompany(
            organization_id=organization_id,
            deal_id=deal_id,
            valuation_id=valuation_id,
            company_name=company_name,
            ticker=ticker,
            industry=industry,
            geography=geography,
            revenue=revenue,
            ebitda=ebitda,
            ebit=ebit,
            net_income=net_income,
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            ev_to_revenue=ev_to_revenue,
            ev_to_ebitda=ev_to_ebitda,
            pe_ratio=pe_ratio,
            revenue_growth=revenue_growth,
            status=status.upper(),
            source=source,
            notes=notes,
            citation_id=citation_id,
        )
        self.session.add(comp)
        await self.session.flush()
        return comp

    async def update_comparable(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, comp_id: uuid.UUID, **kwargs: Any
    ) -> Optional[ComparableCompany]:
        comp = await self.get_comparable(organization_id, deal_id, comp_id)
        if not comp:
            return None
        for k, v in kwargs.items():
            if hasattr(comp, k) and v is not None:
                setattr(comp, k, v)
        comp.updated_at = utc_now()
        await self.session.flush()
        return comp

    async def delete_comparable(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, comp_id: uuid.UUID
    ) -> bool:
        stmt = delete(ComparableCompany).where(
            ComparableCompany.organization_id == organization_id,
            ComparableCompany.deal_id == deal_id,
            ComparableCompany.id == comp_id,
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    # -------------------------------------------------------------
    # 4. Precedent Transactions
    # -------------------------------------------------------------
    async def list_precedents(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[PrecedentTransaction]:
        stmt = (
            select(PrecedentTransaction)
            .where(
                PrecedentTransaction.organization_id == organization_id,
                PrecedentTransaction.deal_id == deal_id,
            )
            .options(selectinload(PrecedentTransaction.citation))
            .order_by(PrecedentTransaction.announcement_date.desc(), PrecedentTransaction.target_name.asc())
        )
        if valuation_id:
            stmt = stmt.where(PrecedentTransaction.valuation_id == valuation_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_precedent(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, tx_id: uuid.UUID
    ) -> Optional[PrecedentTransaction]:
        stmt = (
            select(PrecedentTransaction)
            .where(
                PrecedentTransaction.organization_id == organization_id,
                PrecedentTransaction.deal_id == deal_id,
                PrecedentTransaction.id == tx_id,
            )
            .options(selectinload(PrecedentTransaction.citation))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_precedent(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        target_name: str,
        acquirer_name: Optional[str] = None,
        announcement_date: Optional[str] = None,
        transaction_value: Optional[float] = None,
        enterprise_value: Optional[float] = None,
        revenue: Optional[float] = None,
        ebitda: Optional[float] = None,
        ev_to_revenue: Optional[float] = None,
        ev_to_ebitda: Optional[float] = None,
        transaction_type: str = "100%_ACQUISITION",
        industry: Optional[str] = None,
        geography: Optional[str] = None,
        status: str = "INCLUDED",
        source: str = "ANALYST_INPUT",
        notes: Optional[str] = None,
        citation_id: Optional[uuid.UUID] = None,
        valuation_id: Optional[uuid.UUID] = None,
    ) -> PrecedentTransaction:
        tx = PrecedentTransaction(
            organization_id=organization_id,
            deal_id=deal_id,
            valuation_id=valuation_id,
            target_name=target_name,
            acquirer_name=acquirer_name,
            announcement_date=announcement_date,
            transaction_value=transaction_value,
            enterprise_value=enterprise_value,
            revenue=revenue,
            ebitda=ebitda,
            ev_to_revenue=ev_to_revenue,
            ev_to_ebitda=ev_to_ebitda,
            transaction_type=transaction_type,
            industry=industry,
            geography=geography,
            status=status.upper(),
            source=source,
            notes=notes,
            citation_id=citation_id,
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def update_precedent(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, tx_id: uuid.UUID, **kwargs: Any
    ) -> Optional[PrecedentTransaction]:
        tx = await self.get_precedent(organization_id, deal_id, tx_id)
        if not tx:
            return None
        for k, v in kwargs.items():
            if hasattr(tx, k) and v is not None:
                setattr(tx, k, v)
        tx.updated_at = utc_now()
        await self.session.flush()
        return tx

    async def delete_precedent(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, tx_id: uuid.UUID
    ) -> bool:
        stmt = delete(PrecedentTransaction).where(
            PrecedentTransaction.organization_id == organization_id,
            PrecedentTransaction.deal_id == deal_id,
            PrecedentTransaction.id == tx_id,
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    # -------------------------------------------------------------
    # 5. Outputs
    # -------------------------------------------------------------
    async def list_outputs(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, valuation_id: uuid.UUID
    ) -> List[ValuationOutput]:
        stmt = (
            select(ValuationOutput)
            .where(
                ValuationOutput.organization_id == organization_id,
                ValuationOutput.deal_id == deal_id,
                ValuationOutput.valuation_id == valuation_id,
            )
            .order_by(ValuationOutput.methodology.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def upsert_output(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        valuation_id: uuid.UUID,
        methodology: str,
        enterprise_value_low: Optional[float] = None,
        enterprise_value_base: Optional[float] = None,
        enterprise_value_high: Optional[float] = None,
        equity_value_low: Optional[float] = None,
        equity_value_base: Optional[float] = None,
        equity_value_high: Optional[float] = None,
        implied_ev: Optional[float] = None,
        implied_equity_value: Optional[float] = None,
        calculation_details: Optional[dict] = None,
    ) -> ValuationOutput:
        stmt = select(ValuationOutput).where(
            ValuationOutput.organization_id == organization_id,
            ValuationOutput.deal_id == deal_id,
            ValuationOutput.valuation_id == valuation_id,
            ValuationOutput.methodology == methodology.upper(),
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.enterprise_value_low = enterprise_value_low
            existing.enterprise_value_base = enterprise_value_base
            existing.enterprise_value_high = enterprise_value_high
            existing.equity_value_low = equity_value_low
            existing.equity_value_base = equity_value_base
            existing.equity_value_high = equity_value_high
            existing.implied_ev = implied_ev
            existing.implied_equity_value = implied_equity_value
            existing.calculation_details = calculation_details
            existing.updated_at = utc_now()
            await self.session.flush()
            return existing

        out = ValuationOutput(
            organization_id=organization_id,
            deal_id=deal_id,
            valuation_id=valuation_id,
            methodology=methodology.upper(),
            enterprise_value_low=enterprise_value_low,
            enterprise_value_base=enterprise_value_base,
            enterprise_value_high=enterprise_value_high,
            equity_value_low=equity_value_low,
            equity_value_base=equity_value_base,
            equity_value_high=equity_value_high,
            implied_ev=implied_ev,
            implied_equity_value=implied_equity_value,
            calculation_details=calculation_details,
        )
        self.session.add(out)
        await self.session.flush()
        return out
