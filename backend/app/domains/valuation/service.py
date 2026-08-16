"""Valuation Intelligence Domain Service Orchestrating DCF, WACC, Comps, Precedents & Ranges."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ValidationException
from app.domains.common.context import TenantContext
from app.domains.financials.repository import FinancialRepository
from app.domains.valuation.engine.bridge import ValuationBridgeEngine
from app.domains.valuation.engine.comparables import ComparableEngine
from app.domains.valuation.engine.dcf import DCFEngine
from app.domains.valuation.engine.precedents import PrecedentEngine
from app.domains.valuation.engine.sensitivity import SensitivityEngine
from app.domains.valuation.engine.wacc import WACCEngine
from app.domains.valuation.models import (
    ComparableCompany,
    PrecedentTransaction,
    Valuation,
    ValuationAssumption,
    ValuationOutput,
)
from app.domains.valuation.repository import ValuationRepository


class ValuationService:
    """High-level service coordinating multi-methodology corporate valuations and auditability."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ValuationRepository(session)
        self.fin_repo = FinancialRepository(session)

    # -------------------------------------------------------------
    # 1. Valuation Project Management
    # -------------------------------------------------------------
    async def get_or_create_valuation(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Valuation:
        context.validate_deal_access(deal_id)
        val = await self.repo.get_or_create_default_valuation(
            context.organization_id, deal_id, user_id=context.user_id
        )
        await self.session.commit()
        return val

    async def update_valuation(
        self, context: TenantContext, deal_id: uuid.UUID, valuation_id: uuid.UUID, **kwargs: Any
    ) -> Valuation:
        context.validate_deal_access(deal_id)
        val = await self.repo.update_valuation(
            context.organization_id, deal_id, valuation_id, **kwargs
        )
        if not val:
            raise NotFoundException("Valuation", valuation_id)
        await self.session.commit()
        return val

    # -------------------------------------------------------------
    # 2. Assumptions & WACC Management
    # -------------------------------------------------------------
    async def list_assumptions(
        self, context: TenantContext, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[ValuationAssumption]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_assumptions(context.organization_id, deal_id, valuation_id)

    async def upsert_assumption(
        self,
        context: TenantContext,
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
        context.validate_deal_access(deal_id)
        ass = await self.repo.upsert_assumption(
            organization_id=context.organization_id,
            deal_id=deal_id,
            name=name,
            value=value,
            unit=unit,
            category=category,
            period=period,
            source_type=source_type,
            is_analyst_entered=is_analyst_entered,
            confidence_score=confidence_score,
            citation_id=citation_id,
            notes=notes,
            valuation_id=valuation_id,
        )
        await self.session.commit()
        return ass

    async def get_wacc_analysis(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compute WACC based on stored assumptions or default market baseline."""
        context.validate_deal_access(deal_id)
        assumptions = await self.repo.list_assumptions(context.organization_id, deal_id)
        ass_dict = {a.name: a.value for a in assumptions}

        rf = ass_dict.get("RISK_FREE_RATE", 4.5)
        erp = ass_dict.get("EQUITY_RISK_PREMIUM", 5.5)
        beta = ass_dict.get("BETA", 1.15)
        kd_pre = ass_dict.get("PRE_TAX_COST_DEBT", 6.5)
        tax_rate = ass_dict.get("TAX_RATE", 25.0)
        ew = ass_dict.get("EQUITY_WEIGHT", 80.0)
        dw = ass_dict.get("DEBT_WEIGHT", 20.0)

        return WACCEngine.calculate_wacc(
            risk_free_rate=rf,
            beta=beta,
            equity_risk_premium=erp,
            pre_tax_cost_of_debt=kd_pre,
            tax_rate=tax_rate,
            equity_weight=ew,
            debt_weight=dw,
        )

    # -------------------------------------------------------------
    # 3. Discounted Cash Flow (DCF) Operations
    # -------------------------------------------------------------
    async def compute_dcf_valuation(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        projections: Optional[List[Dict[str, Any]]] = None,
        wacc: Optional[float] = None,
        terminal_growth_rate: Optional[float] = None,
        exit_multiple: Optional[float] = None,
        terminal_method: str = "PERPETUITY_GROWTH",
    ) -> Dict[str, Any]:
        """Run DCF valuation using stored or analyst-provided projections and parameters."""
        context.validate_deal_access(deal_id)
        val = await self.get_or_create_valuation(context, deal_id)

        # Retrieve Phase 5 Financial Balance Sheet for cash & debt
        stmts = await self.fin_repo.list_statements_for_deal(context.organization_id, deal_id)
        bs_stmt = next((s for s in reversed(stmts) if s.statement_type == "BALANCE_SHEET"), None)
        cash = 0.0
        debt = 0.0
        if bs_stmt and bs_stmt.line_items:
            cash = bs_stmt.line_items.get("cash_and_equivalents") or bs_stmt.line_items.get("cash") or 0.0
            lt_debt = bs_stmt.line_items.get("long_term_debt") or 0.0
            st_debt = bs_stmt.line_items.get("short_term_debt") or 0.0
            debt = lt_debt + st_debt

        # WACC resolution
        if wacc is None:
            wacc_analysis = await self.get_wacc_analysis(context, deal_id)
            wacc = wacc_analysis.get("wacc") or 9.5

        # Projections resolution (default 5-year model if not supplied)
        if not projections:
            is_stmt = next((s for s in reversed(stmts) if s.statement_type == "INCOME_STATEMENT"), None)
            base_rev = 50000000.0
            base_ebit = 12000000.0
            base_dna = 2500000.0
            if is_stmt and is_stmt.line_items:
                base_rev = is_stmt.line_items.get("revenue") or base_rev
                base_ebit = is_stmt.line_items.get("ebit") or is_stmt.line_items.get("operating_income") or (base_rev * 0.20)
                base_dna = is_stmt.line_items.get("depreciation_amortization") or (base_rev * 0.05)

            # Build standard 5-year forecast
            projections = []
            for y in range(1, 6):
                growth_rate = max(15.0 - (y * 2.0), 5.0)  # fading growth: 13%, 11%, 9%, 7%, 5%
                rev = base_rev * ((1.0 + (growth_rate / 100.0)) ** y)
                ebit = rev * 0.22
                dna = rev * 0.04
                capex = rev * 0.05
                wc_change = (rev * 0.03)
                projections.append({
                    "period": f"FY202{3+y}",
                    "revenue": round(rev, 2),
                    "revenue_growth": round(growth_rate, 2),
                    "ebitda": round(ebit + dna, 2),
                    "ebitda_margin": round(((ebit + dna) / rev) * 100, 2),
                    "ebit": round(ebit, 2),
                    "tax_rate": 25.0,
                    "depreciation_amortization": round(dna, 2),
                    "capex": round(capex, 2),
                    "working_capital_change": round(wc_change, 2),
                })

        dcf_res = DCFEngine.calculate_dcf(
            projections=projections,
            wacc=wacc,
            terminal_growth_rate=terminal_growth_rate or 3.0,
            exit_multiple=exit_multiple or 10.0,
            terminal_method=terminal_method,
            cash=cash,
            debt=debt,
        )

        # Save output in repository
        method_key = f"DCF_{terminal_method.upper()}"
        ev_base = dcf_res["implied_enterprise_value"]
        eq_base = dcf_res["implied_equity_value"]
        await self.repo.upsert_output(
            organization_id=context.organization_id,
            deal_id=deal_id,
            valuation_id=val.id,
            methodology=method_key,
            enterprise_value_base=ev_base,
            equity_value_base=eq_base,
            implied_ev=ev_base,
            implied_equity_value=eq_base,
            calculation_details=dcf_res,
        )
        await self.session.commit()

        return {
            "valuation_id": str(val.id),
            "deal_id": str(deal_id),
            "dcf": dcf_res,
        }

    # -------------------------------------------------------------
    # 4. Trading Comparable Companies (CCA)
    # -------------------------------------------------------------
    async def list_comparables(
        self, context: TenantContext, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[ComparableCompany]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_comparables(context.organization_id, deal_id, valuation_id)

    async def create_comparable(
        self,
        context: TenantContext,
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
        revenue_growth: Optional[float] = None,
        status: str = "INCLUDED",
        source: str = "ANALYST_INPUT",
        notes: Optional[str] = None,
        citation_id: Optional[uuid.UUID] = None,
        valuation_id: Optional[uuid.UUID] = None,
    ) -> ComparableCompany:
        context.validate_deal_access(deal_id)
        # Compute multiples
        multiples = ComparableEngine.calculate_comp_multiples({
            "enterprise_value": enterprise_value,
            "equity_value": equity_value,
            "revenue": revenue,
            "ebitda": ebitda,
            "net_income": net_income,
        })
        comp = await self.repo.create_comparable(
            organization_id=context.organization_id,
            deal_id=deal_id,
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
            ev_to_revenue=multiples["ev_to_revenue"],
            ev_to_ebitda=multiples["ev_to_ebitda"],
            pe_ratio=multiples["pe_ratio"],
            revenue_growth=revenue_growth,
            status=status,
            source=source,
            notes=notes,
            citation_id=citation_id,
            valuation_id=valuation_id,
        )
        await self.session.commit()
        return comp

    async def update_comparable(
        self, context: TenantContext, deal_id: uuid.UUID, comp_id: uuid.UUID, **kwargs: Any
    ) -> ComparableCompany:
        context.validate_deal_access(deal_id)
        comp = await self.repo.update_comparable(context.organization_id, deal_id, comp_id, **kwargs)
        if not comp:
            raise NotFoundException("ComparableCompany", comp_id)
        # Re-derive multiples
        multiples = ComparableEngine.calculate_comp_multiples({
            "enterprise_value": comp.enterprise_value,
            "equity_value": comp.equity_value,
            "revenue": comp.revenue,
            "ebitda": comp.ebitda,
            "net_income": comp.net_income,
        })
        comp.ev_to_revenue = multiples["ev_to_revenue"]
        comp.ev_to_ebitda = multiples["ev_to_ebitda"]
        comp.pe_ratio = multiples["pe_ratio"]
        await self.session.commit()
        return comp

    async def delete_comparable(
        self, context: TenantContext, deal_id: uuid.UUID, comp_id: uuid.UUID
    ) -> bool:
        context.validate_deal_access(deal_id)
        deleted = await self.repo.delete_comparable(context.organization_id, deal_id, comp_id)
        if not deleted:
            raise NotFoundException("ComparableCompany", comp_id)
        await self.session.commit()
        return True

    async def get_comparable_analysis(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compute cohort statistics and implied valuation range from trading comps."""
        context.validate_deal_access(deal_id)
        val = await self.get_or_create_valuation(context, deal_id)
        comps = await self.repo.list_comparables(context.organization_id, deal_id)
        comp_dicts = [
            {
                "id": str(c.id),
                "company_name": c.company_name,
                "ticker": c.ticker,
                "revenue": c.revenue,
                "ebitda": c.ebitda,
                "enterprise_value": c.enterprise_value,
                "equity_value": c.equity_value,
                "ev_to_revenue": c.ev_to_revenue,
                "ev_to_ebitda": c.ev_to_ebitda,
                "pe_ratio": c.pe_ratio,
                "status": c.status,
            }
            for c in comps
        ]

        stats = ComparableEngine.calculate_comp_cohort_statistics(comp_dicts, only_included=True)

        # Retrieve target LTM metrics & balance sheet items
        stmts = await self.fin_repo.list_statements_for_deal(context.organization_id, deal_id)
        is_stmt = next((s for s in reversed(stmts) if s.statement_type == "INCOME_STATEMENT"), None)
        bs_stmt = next((s for s in reversed(stmts) if s.statement_type == "BALANCE_SHEET"), None)

        target_rev = is_stmt.line_items.get("revenue", 0.0) if is_stmt and is_stmt.line_items else 0.0
        target_ebitda = is_stmt.line_items.get("ebitda", 0.0) if is_stmt and is_stmt.line_items else 0.0
        cash = bs_stmt.line_items.get("cash_and_equivalents", 0.0) if bs_stmt and bs_stmt.line_items else 0.0
        debt = (bs_stmt.line_items.get("long_term_debt", 0.0) + bs_stmt.line_items.get("short_term_debt", 0.0)) if bs_stmt and bs_stmt.line_items else 0.0

        implied_rev = ComparableEngine.calculate_implied_valuation(
            target_metric_value=target_rev,
            multiple_stats=stats["ev_to_revenue_stats"],
            metric_type="REVENUE",
            cash=cash,
            debt=debt,
        )
        implied_ebitda = ComparableEngine.calculate_implied_valuation(
            target_metric_value=target_ebitda,
            multiple_stats=stats["ev_to_ebitda_stats"],
            metric_type="EBITDA",
            cash=cash,
            debt=debt,
        )

        return {
            "valuation_id": str(val.id),
            "deal_id": str(deal_id),
            "companies": comp_dicts,
            "statistics": stats,
            "implied_valuation_revenue": implied_rev,
            "implied_valuation_ebitda": implied_ebitda,
        }

    # -------------------------------------------------------------
    # 5. Precedent Transactions (PTA)
    # -------------------------------------------------------------
    async def list_precedents(
        self, context: TenantContext, deal_id: uuid.UUID, valuation_id: Optional[uuid.UUID] = None
    ) -> List[PrecedentTransaction]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_precedents(context.organization_id, deal_id, valuation_id)

    async def create_precedent(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        target_name: str,
        acquirer_name: Optional[str] = None,
        announcement_date: Optional[str] = None,
        transaction_value: Optional[float] = None,
        enterprise_value: Optional[float] = None,
        revenue: Optional[float] = None,
        ebitda: Optional[float] = None,
        transaction_type: str = "100%_ACQUISITION",
        industry: Optional[str] = None,
        geography: Optional[str] = None,
        status: str = "INCLUDED",
        source: str = "ANALYST_INPUT",
        notes: Optional[str] = None,
        citation_id: Optional[uuid.UUID] = None,
        valuation_id: Optional[uuid.UUID] = None,
    ) -> PrecedentTransaction:
        context.validate_deal_access(deal_id)
        multiples = PrecedentEngine.calculate_deal_multiples({
            "enterprise_value": enterprise_value or transaction_value,
            "revenue": revenue,
            "ebitda": ebitda,
        })
        tx = await self.repo.create_precedent(
            organization_id=context.organization_id,
            deal_id=deal_id,
            target_name=target_name,
            acquirer_name=acquirer_name,
            announcement_date=announcement_date,
            transaction_value=transaction_value,
            enterprise_value=enterprise_value,
            revenue=revenue,
            ebitda=ebitda,
            ev_to_revenue=multiples["ev_to_revenue"],
            ev_to_ebitda=multiples["ev_to_ebitda"],
            transaction_type=transaction_type,
            industry=industry,
            geography=geography,
            status=status,
            source=source,
            notes=notes,
            citation_id=citation_id,
            valuation_id=valuation_id,
        )
        await self.session.commit()
        return tx

    async def update_precedent(
        self, context: TenantContext, deal_id: uuid.UUID, tx_id: uuid.UUID, **kwargs: Any
    ) -> PrecedentTransaction:
        context.validate_deal_access(deal_id)
        tx = await self.repo.update_precedent(context.organization_id, deal_id, tx_id, **kwargs)
        if not tx:
            raise NotFoundException("PrecedentTransaction", tx_id)
        multiples = PrecedentEngine.calculate_deal_multiples({
            "enterprise_value": tx.enterprise_value or tx.transaction_value,
            "revenue": tx.revenue,
            "ebitda": tx.ebitda,
        })
        tx.ev_to_revenue = multiples["ev_to_revenue"]
        tx.ev_to_ebitda = multiples["ev_to_ebitda"]
        await self.session.commit()
        return tx

    async def delete_precedent(
        self, context: TenantContext, deal_id: uuid.UUID, tx_id: uuid.UUID
    ) -> bool:
        context.validate_deal_access(deal_id)
        deleted = await self.repo.delete_precedent(context.organization_id, deal_id, tx_id)
        if not deleted:
            raise NotFoundException("PrecedentTransaction", tx_id)
        await self.session.commit()
        return True

    async def get_precedent_analysis(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compute precedent transaction statistics and implied valuation range."""
        context.validate_deal_access(deal_id)
        val = await self.get_or_create_valuation(context, deal_id)
        txs = await self.repo.list_precedents(context.organization_id, deal_id)
        tx_dicts = [
            {
                "id": str(t.id),
                "target_name": t.target_name,
                "acquirer_name": t.acquirer_name,
                "announcement_date": t.announcement_date,
                "transaction_value": t.transaction_value,
                "enterprise_value": t.enterprise_value,
                "revenue": t.revenue,
                "ebitda": t.ebitda,
                "ev_to_revenue": t.ev_to_revenue,
                "ev_to_ebitda": t.ev_to_ebitda,
                "status": t.status,
            }
            for t in txs
        ]

        stats = PrecedentEngine.calculate_precedent_cohort_statistics(tx_dicts, only_included=True)

        stmts = await self.fin_repo.list_statements_for_deal(context.organization_id, deal_id)
        is_stmt = next((s for s in reversed(stmts) if s.statement_type == "INCOME_STATEMENT"), None)
        bs_stmt = next((s for s in reversed(stmts) if s.statement_type == "BALANCE_SHEET"), None)

        target_rev = is_stmt.line_items.get("revenue", 0.0) if is_stmt and is_stmt.line_items else 0.0
        target_ebitda = is_stmt.line_items.get("ebitda", 0.0) if is_stmt and is_stmt.line_items else 0.0
        cash = bs_stmt.line_items.get("cash_and_equivalents", 0.0) if bs_stmt and bs_stmt.line_items else 0.0
        debt = (bs_stmt.line_items.get("long_term_debt", 0.0) + bs_stmt.line_items.get("short_term_debt", 0.0)) if bs_stmt and bs_stmt.line_items else 0.0

        implied_rev = PrecedentEngine.calculate_implied_valuation(
            target_metric_value=target_rev,
            multiple_stats=stats["ev_to_revenue_stats"],
            metric_type="REVENUE",
            cash=cash,
            debt=debt,
        )
        implied_ebitda = PrecedentEngine.calculate_implied_valuation(
            target_metric_value=target_ebitda,
            multiple_stats=stats["ev_to_ebitda_stats"],
            metric_type="EBITDA",
            cash=cash,
            debt=debt,
        )

        return {
            "valuation_id": str(val.id),
            "deal_id": str(deal_id),
            "transactions": tx_dicts,
            "statistics": stats,
            "implied_valuation_revenue": implied_rev,
            "implied_valuation_ebitda": implied_ebitda,
        }

    # -------------------------------------------------------------
    # 6. Sensitivity Analysis
    # -------------------------------------------------------------
    async def get_sensitivity_matrix(
        self, context: TenantContext, deal_id: uuid.UUID, matrix_type: str = "WACC_VS_GROWTH"
    ) -> Dict[str, Any]:
        """Generate deterministic 2D valuation sensitivity grid."""
        context.validate_deal_access(deal_id)
        dcf_data = await self.compute_dcf_valuation(context, deal_id)
        schedule = dcf_data["dcf"]["schedule"]
        wacc = dcf_data["dcf"]["wacc_pct"]
        g = dcf_data["dcf"]["terminal_growth_rate_pct"] or 3.0
        cash = dcf_data["dcf"]["bridge"]["cash_and_equivalents"]
        debt = dcf_data["dcf"]["bridge"]["total_debt"]

        if matrix_type.upper() == "WACC_VS_EXIT_MULTIPLE":
            return SensitivityEngine.generate_wacc_exit_multiple_matrix(
                projections=schedule,
                base_wacc=wacc,
                base_multiple=10.0,
                cash=cash,
                debt=debt,
            )

        return SensitivityEngine.generate_wacc_terminal_growth_matrix(
            projections=schedule,
            base_wacc=wacc,
            base_growth=g,
            cash=cash,
            debt=debt,
        )

    # -------------------------------------------------------------
    # 7. Valuation Summary & Football Field Range
    # -------------------------------------------------------------
    async def get_valuation_summary(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Aggregate all valuation methodologies into a unified football field comparison."""
        context.validate_deal_access(deal_id)
        val = await self.get_or_create_valuation(context, deal_id)

        # 1. DCF Perpetuity
        dcf_perp = await self.compute_dcf_valuation(context, deal_id, terminal_method="PERPETUITY_GROWTH")
        # 2. DCF Exit Multiple
        dcf_mult = await self.compute_dcf_valuation(context, deal_id, terminal_method="EXIT_MULTIPLE", exit_multiple=10.0)
        # 3. Comps
        comps_analysis = await self.get_comparable_analysis(context, deal_id)
        # 4. Precedents
        precedents_analysis = await self.get_precedent_analysis(context, deal_id)

        methodologies = [
            {
                "methodology": "DCF_PERPETUITY",
                "label": "DCF (Perpetuity Growth 3.0%)",
                "ev_low": dcf_perp["dcf"]["implied_enterprise_value"] * 0.90,
                "ev_base": dcf_perp["dcf"]["implied_enterprise_value"],
                "ev_high": dcf_perp["dcf"]["implied_enterprise_value"] * 1.10,
                "equity_low": dcf_perp["dcf"]["implied_equity_value"] * 0.90,
                "equity_base": dcf_perp["dcf"]["implied_equity_value"],
                "equity_high": dcf_perp["dcf"]["implied_equity_value"] * 1.10,
            },
            {
                "methodology": "DCF_EXIT_MULTIPLE",
                "label": "DCF (Exit Multiple 10.0x)",
                "ev_low": dcf_mult["dcf"]["implied_enterprise_value"] * 0.90,
                "ev_base": dcf_mult["dcf"]["implied_enterprise_value"],
                "ev_high": dcf_mult["dcf"]["implied_enterprise_value"] * 1.10,
                "equity_low": dcf_mult["dcf"]["implied_equity_value"] * 0.90,
                "equity_base": dcf_mult["dcf"]["implied_equity_value"],
                "equity_high": dcf_mult["dcf"]["implied_equity_value"] * 1.10,
            },
        ]

        # Add Comps EBITDA if available
        comp_ebitda = comps_analysis["implied_valuation_ebitda"]
        if comp_ebitda.get("is_calculable"):
            methodologies.append({
                "methodology": "CCA_EBITDA",
                "label": f"Trading Comps (EV/EBITDA {comp_ebitda.get('multiple_base')}x)",
                "ev_low": comp_ebitda["implied_enterprise_value_low"],
                "ev_base": comp_ebitda["implied_enterprise_value_base"],
                "ev_high": comp_ebitda["implied_enterprise_value_high"],
                "equity_low": comp_ebitda["implied_equity_value_low"],
                "equity_base": comp_ebitda["implied_equity_value_base"],
                "equity_high": comp_ebitda["implied_equity_value_high"],
            })

        # Add Precedents EBITDA if available
        tx_ebitda = precedents_analysis["implied_valuation_ebitda"]
        if tx_ebitda.get("is_calculable"):
            methodologies.append({
                "methodology": "PRECEDENT_EBITDA",
                "label": f"Precedent Transactions ({tx_ebitda.get('multiple_base')}x)",
                "ev_low": tx_ebitda["implied_enterprise_value_low"],
                "ev_base": tx_ebitda["implied_enterprise_value_base"],
                "ev_high": tx_ebitda["implied_enterprise_value_high"],
                "equity_low": tx_ebitda["implied_equity_value_low"],
                "equity_base": tx_ebitda["implied_equity_value_base"],
                "equity_high": tx_ebitda["implied_equity_value_high"],
            })

        # Transaction Price Premium Analysis
        tx_comparison = None
        base_ev = dcf_perp["dcf"]["implied_enterprise_value"]
        if val.proposed_ev is not None:
            tx_comparison = ValuationBridgeEngine.calculate_transaction_comparison(
                proposed_ev=val.proposed_ev,
                proposed_equity_value=val.proposed_equity_value,
                benchmark_ev=base_ev,
            )

        return {
            "valuation_id": str(val.id),
            "deal_id": str(deal_id),
            "currency": val.currency,
            "proposed_ev": val.proposed_ev,
            "proposed_equity_value": val.proposed_equity_value,
            "methodologies": methodologies,
            "transaction_comparison": tx_comparison,
        }

    # -------------------------------------------------------------
    # 8. Model Validation Checks
    # -------------------------------------------------------------
    async def validate_valuation_model(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Perform validation and consistency checks on valuation inputs and assumptions."""
        context.validate_deal_access(deal_id)
        assumptions = await self.repo.list_assumptions(context.organization_id, deal_id)
        ass_dict = {a.name: a.value for a in assumptions}

        checks: List[Dict[str, Any]] = []
        has_errors = False

        # Check 1: WACC vs Terminal Growth Rate
        wacc = ass_dict.get("WACC", 9.5)
        g = ass_dict.get("TERMINAL_GROWTH_RATE", 3.0)
        if wacc <= g:
            has_errors = True
            checks.append({
                "check_name": "WACC_VS_TERMINAL_GROWTH",
                "passed": False,
                "severity": "CRITICAL",
                "message": f"WACC ({wacc}%) must be strictly greater than Terminal Growth Rate ({g}%).",
            })
        else:
            checks.append({
                "check_name": "WACC_VS_TERMINAL_GROWTH",
                "passed": True,
                "severity": "INFO",
                "message": f"WACC ({wacc}%) exceeds Terminal Growth Rate ({g}%).",
            })

        # Check 2: Beta Sanity
        beta = ass_dict.get("BETA", 1.15)
        if beta <= 0:
            has_errors = True
            checks.append({
                "check_name": "BETA_RANGE",
                "passed": False,
                "severity": "WARNING",
                "message": f"Beta ({beta}) is non-positive, which is atypical for equity valuation.",
            })
        else:
            checks.append({
                "check_name": "BETA_RANGE",
                "passed": True,
                "severity": "INFO",
                "message": f"Beta ({beta}) is within valid range.",
            })

        return {
            "deal_id": str(deal_id),
            "status": "DISCREPANCIES_FOUND" if has_errors else "HEALTHY",
            "checks": checks,
        }
