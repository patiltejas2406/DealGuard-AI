"""Financial Statement, Quality of Earnings & Metric Calculation Service."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ValidationException
from app.domains.common.context import TenantContext
from app.domains.financials.engine.metrics import MetricCalculationEngine
from app.domains.financials.engine.qoe import QoEEngine
from app.domains.financials.engine.statements import StatementCalculationEngine
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.financials.repository import FinancialRepository


class FinancialService:
    """High-level domain service for 3-Statement Modeling, QoE Normalization, and Ratio Engine."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FinancialRepository(session)

    # -------------------------------------------------------------
    # 1. Statement Operations & Calculations
    # -------------------------------------------------------------
    async def list_statements(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[FinancialStatement]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_statements_for_deal(context.organization_id, deal_id)

    async def upsert_statement(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        statement_type: str,
        fiscal_year: int,
        fiscal_period: str,
        line_items: Dict[str, Any],
        source_currency: str = "USD",
        period_type: str = "ANNUAL",
        is_audited: bool = False,
        is_normalized: bool = False,
        source_document_id: Optional[uuid.UUID] = None,
    ) -> FinancialStatement:
        context.validate_deal_access(deal_id)

        # Run deterministic derived calculation
        st_upper = statement_type.upper()
        if st_upper == "INCOME_STATEMENT":
            calculated_items = StatementCalculationEngine.calculate_income_statement(line_items)
        elif st_upper == "BALANCE_SHEET":
            calculated_items = StatementCalculationEngine.calculate_balance_sheet(line_items)
        elif st_upper == "CASH_FLOW":
            calculated_items = StatementCalculationEngine.calculate_cash_flow(line_items)
        else:
            raise ValidationException(f"Invalid statement type: {statement_type}")

        # Preserve any non-empty source items alongside calculated fields
        merged_items = {**line_items, **{k: v for k, v in calculated_items.items() if v is not None}}

        stmt = await self.repo.upsert_statement(
            organization_id=context.organization_id,
            deal_id=deal_id,
            statement_type=st_upper,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            line_items=merged_items,
            source_currency=source_currency,
            period_type=period_type,
            is_audited=is_audited,
            is_normalized=is_normalized,
            source_document_id=source_document_id,
        )

        # Synchronize key period metrics
        await self._sync_period_metrics(context, deal_id, stmt)
        await self.session.commit()
        return stmt

    async def _sync_period_metrics(
        self, context: TenantContext, deal_id: uuid.UUID, stmt: FinancialStatement
    ) -> None:
        """Derive standard ratios for statement and store into financial_metrics table."""
        items = stmt.line_items or {}
        period = stmt.fiscal_period
        currency = stmt.source_currency

        if stmt.statement_type == "INCOME_STATEMENT":
            rev = items.get("revenue")
            if rev is not None:
                await self.repo.upsert_metric(
                    context.organization_id, deal_id, "REVENUE", period, rev, "CURRENCY", currency, False, stmt.id
                )

            gp = items.get("gross_profit")
            if gp is not None and rev:
                gm_calc = MetricCalculationEngine.calculate_margin(gp, rev, "GROSS_MARGIN")
                if gm_calc["value"] is not None:
                    await self.repo.upsert_metric(
                        context.organization_id, deal_id, "GROSS_MARGIN", period, gm_calc["value"], "PERCENTAGE", currency, False, stmt.id, calculation_formula=gm_calc["formula"]
                    )

            ebitda = items.get("ebitda")
            if ebitda is not None:
                await self.repo.upsert_metric(
                    context.organization_id, deal_id, "EBITDA", period, ebitda, "CURRENCY", currency, False, stmt.id
                )
                if rev:
                    em_calc = MetricCalculationEngine.calculate_margin(ebitda, rev, "EBITDA_MARGIN")
                    if em_calc["value"] is not None:
                        await self.repo.upsert_metric(
                            context.organization_id, deal_id, "EBITDA_MARGIN", period, em_calc["value"], "PERCENTAGE", currency, False, stmt.id, calculation_formula=em_calc["formula"]
                        )

            net_inc = items.get("net_income")
            if net_inc is not None and rev:
                nm_calc = MetricCalculationEngine.calculate_margin(net_inc, rev, "NET_MARGIN")
                if nm_calc["value"] is not None:
                    await self.repo.upsert_metric(
                        context.organization_id, deal_id, "NET_MARGIN", period, nm_calc["value"], "PERCENTAGE", currency, False, stmt.id, calculation_formula=nm_calc["formula"]
                    )

        elif stmt.statement_type == "BALANCE_SHEET":
            ca = items.get("total_current_assets")
            cl = items.get("total_current_liabilities")
            if ca is not None and cl is not None:
                wc_calc = MetricCalculationEngine.calculate_working_capital(ca, cl)
                if wc_calc["working_capital"] is not None:
                    await self.repo.upsert_metric(
                        context.organization_id, deal_id, "WORKING_CAPITAL", period, wc_calc["working_capital"], "CURRENCY", currency, False, stmt.id, calculation_formula=wc_calc["formula"]
                    )

            cash = items.get("cash_and_equivalents") or 0.0
            debt = items.get("long_term_debt") or 0.0
            short_debt = items.get("short_term_debt") or 0.0
            total_debt = debt + short_debt
            nd_calc = MetricCalculationEngine.calculate_net_debt(total_debt, cash)
            if nd_calc["net_debt"] is not None:
                await self.repo.upsert_metric(
                    context.organization_id, deal_id, "NET_DEBT", period, nd_calc["net_debt"], "CURRENCY", currency, False, stmt.id, calculation_formula="Total Debt - Cash"
                )

    # -------------------------------------------------------------
    # 2. Metrics & Multi-Year CAGR Analysis
    # -------------------------------------------------------------
    async def list_metrics(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[FinancialMetric]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_metrics_for_deal(context.organization_id, deal_id)

    async def compute_cagr_analysis(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compute multi-period CAGR across historical annual statements."""
        context.validate_deal_access(deal_id)
        stmts = await self.repo.list_statements_for_deal(context.organization_id, deal_id)
        income_stmts = [s for s in stmts if s.statement_type == "INCOME_STATEMENT" and s.period_type == "ANNUAL"]
        income_stmts.sort(key=lambda x: x.fiscal_year)

        if len(income_stmts) < 2:
            return {
                "revenue_cagr": None,
                "ebitda_cagr": None,
                "periods_analyzed": [s.fiscal_period for s in income_stmts],
                "message": "At least two annual periods are required for CAGR calculation.",
            }

        start_stmt = income_stmts[0]
        end_stmt = income_stmts[-1]
        years = end_stmt.fiscal_year - start_stmt.fiscal_year

        rev_start = start_stmt.line_items.get("revenue")
        rev_end = end_stmt.line_items.get("revenue")
        rev_cagr = MetricCalculationEngine.calculate_cagr(rev_start, rev_end, years)

        ebitda_start = start_stmt.line_items.get("ebitda")
        ebitda_end = end_stmt.line_items.get("ebitda")
        ebitda_cagr = MetricCalculationEngine.calculate_cagr(ebitda_start, ebitda_end, years)

        return {
            "start_period": start_stmt.fiscal_period,
            "end_period": end_stmt.fiscal_period,
            "years": years,
            "revenue_start": rev_start,
            "revenue_end": rev_end,
            "revenue_cagr": rev_cagr,
            "ebitda_start": ebitda_start,
            "ebitda_end": ebitda_end,
            "ebitda_cagr": ebitda_cagr,
        }

    # -------------------------------------------------------------
    # 3. Quality of Earnings (QoE) Operations
    # -------------------------------------------------------------
    async def list_qoe_adjustments(
        self, context: TenantContext, deal_id: uuid.UUID, period: Optional[str] = None
    ) -> List[QoEAdjustment]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_qoe_adjustments(context.organization_id, deal_id, period)

    async def create_qoe_adjustment(
        self,
        context: TenantContext,
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
    ) -> QoEAdjustment:
        context.validate_deal_access(deal_id)
        adj = await self.repo.create_qoe_adjustment(
            organization_id=context.organization_id,
            deal_id=deal_id,
            category=category,
            description=description,
            amount=amount,
            currency=currency,
            period=period,
            treatment=treatment,
            status=status,
            notes=notes,
            citation_id=citation_id,
            created_by_id=context.user_id,
        )
        await self.session.commit()
        return adj

    async def update_qoe_adjustment(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        adjustment_id: uuid.UUID,
        **kwargs: Any,
    ) -> QoEAdjustment:
        context.validate_deal_access(deal_id)
        adj = await self.repo.update_qoe_adjustment(
            context.organization_id, deal_id, adjustment_id, **kwargs
        )
        if not adj:
            raise NotFoundException("QoEAdjustment", adjustment_id)
        await self.session.commit()
        return adj

    async def delete_qoe_adjustment(
        self, context: TenantContext, deal_id: uuid.UUID, adjustment_id: uuid.UUID
    ) -> bool:
        context.validate_deal_access(deal_id)
        deleted = await self.repo.delete_qoe_adjustment(context.organization_id, deal_id, adjustment_id)
        if not deleted:
            raise NotFoundException("QoEAdjustment", adjustment_id)
        await self.session.commit()
        return True

    async def get_qoe_bridge(
        self, context: TenantContext, deal_id: uuid.UUID, period: str = "FY2023"
    ) -> Dict[str, Any]:
        """Compute full Quality of Earnings EBITDA bridge for a given fiscal period."""
        context.validate_deal_access(deal_id)
        stmt = await self.repo.get_statement_by_period(
            context.organization_id, deal_id, "INCOME_STATEMENT", period
        )
        reported_ebitda = None
        if stmt and stmt.line_items:
            reported_ebitda = stmt.line_items.get("ebitda") or stmt.line_items.get("operating_income")

        adjustments = await self.repo.list_qoe_adjustments(context.organization_id, deal_id, period)
        adj_dicts = [
            {
                "id": str(a.id),
                "category": a.category,
                "description": a.description,
                "amount": a.amount,
                "treatment": a.treatment,
                "status": a.status,
                "citation_id": str(a.citation_id) if a.citation_id else None,
            }
            for a in adjustments
        ]

        bridge = QoEEngine.calculate_adjusted_ebitda(reported_ebitda, adj_dicts, only_approved=False)
        return {
            "deal_id": str(deal_id),
            "period": period,
            "bridge": bridge,
            "adjustments": adj_dicts,
        }

    # -------------------------------------------------------------
    # 4. Model Accounting Validation
    # -------------------------------------------------------------
    async def validate_deal_financials(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Run complete 3-statement reconciliation and balance checks across all periods."""
        context.validate_deal_access(deal_id)
        stmts = await self.repo.list_statements_for_deal(context.organization_id, deal_id)

        validation_results: List[Dict[str, Any]] = []
        has_errors = False

        for s in stmts:
            items = s.line_items or {}
            period = s.fiscal_period
            st_type = s.statement_type

            if st_type == "BALANCE_SHEET":
                is_balanced = items.get("is_balanced")
                discrepancy = items.get("balance_discrepancy")
                if is_balanced is False:
                    has_errors = True
                    validation_results.append(
                        {
                            "statement_type": st_type,
                            "period": period,
                            "check_name": "BALANCE_SHEET_BALANCING",
                            "passed": False,
                            "severity": "CRITICAL",
                            "message": f"Balance sheet does not balance for {period}. Discrepancy: ${discrepancy:,.2f}",
                        }
                    )
                else:
                    validation_results.append(
                        {
                            "statement_type": st_type,
                            "period": period,
                            "check_name": "BALANCE_SHEET_BALANCING",
                            "passed": True,
                            "severity": "INFO",
                            "message": f"Assets equal Liabilities + Equity for {period}.",
                        }
                    )

            elif st_type == "INCOME_STATEMENT":
                rev = items.get("revenue")
                cogs = items.get("cogs")
                gp = items.get("gross_profit")
                if rev is not None and cogs is not None and gp is not None:
                    expected_gp = rev - cogs
                    if abs(expected_gp - gp) > 0.05:
                        has_errors = True
                        validation_results.append(
                            {
                                "statement_type": st_type,
                                "period": period,
                                "check_name": "GROSS_PROFIT_CONSISTENCY",
                                "passed": False,
                                "severity": "WARNING",
                                "message": f"Gross profit (${gp:,.2f}) does not equal Revenue (${rev:,.2f}) - COGS (${cogs:,.2f}).",
                            }
                        )

        return {
            "deal_id": str(deal_id),
            "status": "DISCREPANCIES_FOUND" if has_errors else "HEALTHY",
            "total_statements_checked": len(stmts),
            "checks": validation_results,
        }
