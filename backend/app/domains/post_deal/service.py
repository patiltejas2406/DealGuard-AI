"""Post-Acquisition Intelligence Business Service."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.context import TenantContext
from app.domains.deals.models import Deal, TargetCompany
from app.domains.integration.models import (
    IntegrationBlocker,
    IntegrationMilestone,
    IntegrationProgram,
    IntegrationWorkstream,
)
from app.domains.post_deal.kpi_engine import PostDealKPIEngine, ThesisStatus
from app.domains.post_deal.models import (
    AcquisitionThesis,
    CustomerAccount,
    PostAcquisitionMetric,
    ValueCreationInitiative,
)
from app.domains.post_deal.repository import PostDealRepository
from app.domains.post_deal.schemas import (
    AcquisitionThesisCreate,
    AcquisitionThesisResponse,
    CustomerAccountCreate,
    CustomerAccountResponse,
    PostAcquisitionCustomersResponse,
    PostAcquisitionIntegrationResponse,
    PostAcquisitionMetricCreate,
    PostAcquisitionMetricResponse,
    PostAcquisitionOverviewResponse,
    PostAcquisitionPerformanceResponse,
    PostAcquisitionRisksResponse,
    PostAcquisitionSynergiesResponse,
    PostAcquisitionThesisResponse,
    ValueCreationInitiativeCreate,
    ValueCreationInitiativeResponse,
)
from app.domains.risk.models import Risk
from app.domains.synergy.models import SynergyOpportunity, SynergyRealizationLog


class PostDealService:
    """Service governing post-acquisition performance calculations, customer analytics, and thesis tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PostDealRepository(session)

    async def get_overview(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionOverviewResponse:
        """Aggregate high-level executive post-acquisition dashboard."""
        context.validate_deal_access(deal_id)

        # 1. Deal & Target
        deal_q = (
            select(Deal, TargetCompany)
            .outerjoin(TargetCompany, Deal.target_company_id == TargetCompany.id)
            .where(Deal.id == deal_id, Deal.organization_id == context.organization_id)
        )
        deal_res = await self.session.execute(deal_q)
        deal_row = deal_res.first()
        deal_title = deal_row[0].title if deal_row else "Acquisition Deal"
        company_name = deal_row[1].name if (deal_row and deal_row[1]) else "Acquired Company"

        # 2. Customers
        accounts = await self.repo.list_customer_accounts(context.organization_id, deal_id)
        total_arr = sum(a.arr for a in accounts)
        at_risk_accounts = [a for a in accounts if a.health_status in ["AT_RISK", "CRITICAL", "CHURNED"]]
        at_risk_count = len(at_risk_accounts)

        # Compute NRR
        starting_arr = total_arr
        expansion_arr = sum(a.expansion_potential_usd for a in accounts if a.health_status == "EXPANDING")
        churned_arr = sum(a.arr for a in accounts if a.is_churned)
        nrr_pct = PostDealKPIEngine.compute_net_revenue_retention_pct(
            starting_arr=starting_arr, expansion_arr=expansion_arr, churned_arr=churned_arr
        ) if total_arr > 0 else None

        # 3. Synergies
        syn_q = select(SynergyOpportunity).where(
            SynergyOpportunity.deal_id == deal_id,
            SynergyOpportunity.organization_id == context.organization_id,
        )
        syn_res = await self.session.execute(syn_q)
        synergies = list(syn_res.scalars().all())
        expected_syn = sum(s.expected_annual_value for s in synergies)
        realized_syn = sum(s.realized_annual_value for s in synergies)
        syn_pct = PostDealKPIEngine.compute_synergy_realization_pct(realized_syn, expected_syn)

        # 4. Integration
        ms_q = select(IntegrationMilestone).where(
            IntegrationMilestone.deal_id == deal_id,
            IntegrationMilestone.organization_id == context.organization_id,
        )
        ms_res = await self.session.execute(ms_q)
        milestones = list(ms_res.scalars().all())
        completed_ms = len([m for m in milestones if m.status == "COMPLETED"])
        integration_completion_pct = PostDealKPIEngine.compute_integration_completion_pct(
            completed_ms, len(milestones)
        )

        blockers_q = select(IntegrationBlocker).where(
            IntegrationBlocker.deal_id == deal_id,
            IntegrationBlocker.organization_id == context.organization_id,
            IntegrationBlocker.status == "OPEN",
        )
        blockers_res = await self.session.execute(blockers_q)
        open_blockers = list(blockers_res.scalars().all())
        open_blockers_count = len(open_blockers)

        # 5. Financial Metrics
        metrics = await self.repo.list_post_acquisition_metrics(context.organization_id, deal_id)
        rev_m = next((m for m in metrics if m.metric_name == "REVENUE"), None)
        ebitda_m = next((m for m in metrics if m.metric_name == "EBITDA"), None)
        rev_actual = rev_m.actual_value if rev_m else None
        rev_target = rev_m.target_value if rev_m else None
        ebitda_actual = ebitda_m.actual_value if ebitda_m else None
        ebitda_target = ebitda_m.target_value if ebitda_m else None

        # 6. Value Creation Summary
        summary = PostDealKPIEngine.compute_executive_value_creation_summary(
            revenue_actual=rev_actual,
            revenue_target=rev_target,
            ebitda_actual=ebitda_actual,
            ebitda_target=ebitda_target,
            synergy_realized=realized_syn,
            synergy_expected=expected_syn,
            integration_completion_pct=integration_completion_pct,
            open_blockers_count=open_blockers_count,
            customer_nrr_pct=nrr_pct,
        )

        initiatives = await self.repo.list_value_creation_initiatives(context.organization_id, deal_id)

        # Health score (0 - 100)
        health_base = 85.0
        if open_blockers_count > 0:
            health_base -= min(30.0, open_blockers_count * 10.0)
        if at_risk_count > 0:
            health_base -= min(20.0, at_risk_count * 5.0)
        if syn_pct is not None and syn_pct < 50.0:
            health_base -= 15.0
        health_score = max(0.0, min(100.0, round(health_base, 1)))

        highlights = []
        if integration_completion_pct > 0:
            highlights.append(f"Integration {integration_completion_pct:.1f}% complete across {len(milestones)} milestones.")
        if syn_pct is not None:
            highlights.append(f"Synergies tracking at {syn_pct:.1f}% realization (${realized_syn:,.0f} / ${expected_syn:,.0f}).")
        if total_arr > 0:
            highlights.append(f"Customer base ARR: ${total_arr:,.0f} across {len(accounts)} accounts.")

        top_risks = []
        if open_blockers_count > 0:
            top_risks.append(f"{open_blockers_count} open integration blocker(s) require executive intervention.")
        if at_risk_count > 0:
            top_risks.append(f"{at_risk_count} customer account(s) flagged with elevated churn risk.")

        return PostAcquisitionOverviewResponse(
            deal_id=deal_id,
            deal_title=deal_title,
            company_name=company_name,
            overall_thesis_status=summary["overall_status"],
            health_score=health_score,
            total_arr=total_arr,
            nrr_pct=nrr_pct,
            synergy_realization_pct=syn_pct,
            integration_completion_pct=integration_completion_pct,
            open_blockers_count=open_blockers_count,
            at_risk_customers_count=at_risk_count,
            active_initiatives_count=len(initiatives),
            pillars=summary["pillars"],
            key_highlights=highlights,
            top_risks=top_risks,
        )

    async def get_performance(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionPerformanceResponse:
        """Retrieve post-close financial performance metrics and variances."""
        context.validate_deal_access(deal_id)
        metrics = await self.repo.list_post_acquisition_metrics(context.organization_id, deal_id)

        data_gaps = []
        if not metrics:
            data_gaps.append("Post-acquisition quarterly financial statements and actual P&L ledger feeds.")

        rev_m = next((m for m in metrics if m.metric_name == "REVENUE"), None)
        ebitda_m = next((m for m in metrics if m.metric_name == "EBITDA"), None)

        rev_growth = None
        if rev_m and rev_m.baseline_value > 0:
            rev_growth = PostDealKPIEngine.compute_revenue_growth_pct(rev_m.actual_value, rev_m.baseline_value)

        ebitda_margin = None
        if ebitda_m and rev_m and rev_m.actual_value > 0:
            ebitda_margin = PostDealKPIEngine.compute_ebitda_margin_pct(ebitda_m.actual_value, rev_m.actual_value)

        periods = sorted(list({m.fiscal_period for m in metrics}))

        return PostAcquisitionPerformanceResponse(
            deal_id=deal_id,
            metrics=[PostAcquisitionMetricResponse.model_validate(m) for m in metrics],
            revenue_growth_pct=rev_growth,
            ebitda_margin_pct=ebitda_margin,
            historical_periods=periods,
            data_gaps=data_gaps,
        )

    async def get_integration(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionIntegrationResponse:
        """Retrieve 100-day integration program execution telemetry."""
        context.validate_deal_access(deal_id)

        prog_q = select(IntegrationProgram).where(
            IntegrationProgram.deal_id == deal_id,
            IntegrationProgram.organization_id == context.organization_id,
        )
        prog_res = await self.session.execute(prog_q)
        prog = prog_res.scalar_one_or_none()

        ws_q = select(IntegrationWorkstream).where(
            IntegrationWorkstream.deal_id == deal_id,
            IntegrationWorkstream.organization_id == context.organization_id,
        )
        ws_res = await self.session.execute(ws_q)
        workstreams = list(ws_res.scalars().all())

        ms_q = select(IntegrationMilestone).where(
            IntegrationMilestone.deal_id == deal_id,
            IntegrationMilestone.organization_id == context.organization_id,
        )
        ms_res = await self.session.execute(ms_q)
        milestones = list(ms_res.scalars().all())

        blockers_q = select(IntegrationBlocker).where(
            IntegrationBlocker.deal_id == deal_id,
            IntegrationBlocker.organization_id == context.organization_id,
            IntegrationBlocker.status == "OPEN",
        )
        blockers_res = await self.session.execute(blockers_q)
        open_blockers = list(blockers_res.scalars().all())

        total_ms = len(milestones)
        completed_ms = len([m for m in milestones if m.status == "COMPLETED"])
        overdue_ms = len([m for m in milestones if m.status == "OVERDUE"])
        critical_ms = len([m for m in milestones if m.is_critical_path])
        completion_pct = PostDealKPIEngine.compute_integration_completion_pct(completed_ms, total_ms)

        health_score = 90.0
        if len(open_blockers) > 0:
            health_score -= min(40.0, len(open_blockers) * 15.0)
        if overdue_ms > 0:
            health_score -= min(25.0, overdue_ms * 8.0)
        health_score = max(0.0, min(100.0, health_score))

        data_gaps = []
        if total_ms == 0:
            data_gaps.append("100-Day Integration Workstream Charters and Milestone Dependency Graph.")

        return PostAcquisitionIntegrationResponse(
            deal_id=deal_id,
            program_name=prog.name if prog else "100-Day Integration Program",
            total_milestones=total_ms,
            completed_milestones=completed_ms,
            overdue_milestones=overdue_ms,
            critical_path_milestones=critical_ms,
            completion_pct=completion_pct,
            health_score=round(health_score, 1),
            open_blockers=[
                {"id": str(b.id), "title": b.title, "severity": b.severity, "impact": b.impact_description}
                for b in open_blockers
            ],
            workstreams=[
                {"id": str(w.id), "name": w.name, "category": w.category, "progress_pct": w.progress_percentage}
                for w in workstreams
            ],
            data_gaps=data_gaps,
        )

    async def get_synergies(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionSynergiesResponse:
        """Retrieve expected vs realized synergy performance."""
        context.validate_deal_access(deal_id)

        syn_q = select(SynergyOpportunity).where(
            SynergyOpportunity.deal_id == deal_id,
            SynergyOpportunity.organization_id == context.organization_id,
        )
        syn_res = await self.session.execute(syn_q)
        synergies = list(syn_res.scalars().all())

        logs_q = select(SynergyRealizationLog).where(
            SynergyRealizationLog.deal_id == deal_id,
            SynergyRealizationLog.organization_id == context.organization_id,
        )
        logs_res = await self.session.execute(logs_q)
        logs = list(logs_res.scalars().all())

        expected_total = sum(s.expected_annual_value for s in synergies)
        realized_total = sum(s.realized_annual_value for s in synergies)
        cost_realized = sum(s.realized_annual_value for s in synergies if s.synergy_type == "COST")
        rev_realized = sum(s.realized_annual_value for s in synergies if s.synergy_type == "REVENUE")

        realization_pct = PostDealKPIEngine.compute_synergy_realization_pct(realized_total, expected_total)

        data_gaps = []
        if not synergies:
            data_gaps.append("Pre-deal synergy model and value creation roadmap.")
        if not logs and synergies:
            data_gaps.append("Post-close actual synergy realization logs and accounting audit reports.")

        return PostAcquisitionSynergiesResponse(
            deal_id=deal_id,
            total_expected_annual_synergy=expected_total,
            total_realized_annual_synergy=realized_total,
            realization_rate_pct=realization_pct,
            cost_synergies_realized=cost_realized,
            revenue_synergies_realized=rev_realized,
            opportunities_count=len(synergies),
            realization_logs=[
                {
                    "fiscal_period": l.fiscal_period,
                    "planned_value": l.planned_value,
                    "actual_value": l.actual_value,
                    "variance": l.variance,
                }
                for l in logs
            ],
            data_gaps=data_gaps,
        )

    async def get_customers(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionCustomersResponse:
        """Retrieve customer account intelligence, cohort retention, and churn risk analytics."""
        context.validate_deal_access(deal_id)
        accounts = await self.repo.list_customer_accounts(context.organization_id, deal_id)

        data_gaps = []
        if not accounts:
            data_gaps.append("Customer subscription contracts, ARR ledger, and CRM account health data.")

        total_arr = sum(a.arr for a in accounts)
        avg_churn_risk = (sum(a.churn_risk_score for a in accounts) / len(accounts)) if accounts else 0.0
        at_risk = [a for a in accounts if a.health_status in ["AT_RISK", "CRITICAL"] or a.churn_risk_score > 0.40]
        at_risk_arr = sum(a.arr for a in at_risk)
        expansion_usd = sum(a.expansion_potential_usd for a in accounts)

        # NRR
        expansion_arr = sum(a.expansion_potential_usd for a in accounts if a.health_status == "EXPANDING")
        churned_arr = sum(a.arr for a in accounts if a.is_churned)
        nrr_pct = PostDealKPIEngine.compute_net_revenue_retention_pct(
            starting_arr=total_arr, expansion_arr=expansion_arr, churned_arr=churned_arr
        ) if total_arr > 0 else None

        churn_rate = PostDealKPIEngine.compute_churn_rate_pct(churned_arr, total_arr) if total_arr > 0 else None

        return PostAcquisitionCustomersResponse(
            deal_id=deal_id,
            total_accounts=len(accounts),
            total_arr=total_arr,
            average_churn_risk=round(avg_churn_risk, 3),
            at_risk_arr=at_risk_arr,
            at_risk_accounts=[CustomerAccountResponse.model_validate(a) for a in at_risk],
            expansion_pipeline_usd=expansion_usd,
            nrr_pct=nrr_pct,
            churn_rate_pct=churn_rate,
            data_gaps=data_gaps,
        )

    async def get_risks(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionRisksResponse:
        """Retrieve emerging post-close operational, technology, customer, and integration risks."""
        context.validate_deal_access(deal_id)

        q = select(Risk).where(
            Risk.deal_id == deal_id,
            Risk.organization_id == context.organization_id,
        ).order_by(Risk.score.desc())
        res = await self.session.execute(q)
        risks = list(res.scalars().all())

        data_gaps = []
        if not risks:
            data_gaps.append("Post-close operational risk log and compliance monitoring audit.")

        crit_count = len([r for r in risks if r.severity == "CRITICAL"])
        high_count = len([r for r in risks if r.severity == "HIGH"])

        return PostAcquisitionRisksResponse(
            deal_id=deal_id,
            total_risks_count=len(risks),
            critical_risks_count=crit_count,
            high_risks_count=high_count,
            emerging_post_close_risks=[
                {
                    "id": str(r.id),
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "severity": r.severity,
                    "score": r.score,
                    "mitigation": r.mitigation_strategy,
                }
                for r in risks
            ],
            data_gaps=data_gaps,
        )

    async def get_theses(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> PostAcquisitionThesisResponse:
        """Retrieve Acquisition Thesis targets vs actual results."""
        context.validate_deal_access(deal_id)
        theses = await self.repo.list_acquisition_theses(context.organization_id, deal_id)
        initiatives = await self.repo.list_value_creation_initiatives(context.organization_id, deal_id)

        data_gaps = []
        if not theses:
            data_gaps.append("Acquisition investment thesis and target financial/synergy milestones.")

        # Evaluate overall thesis status
        statuses = [t.status for t in theses if t.status != "INSUFFICIENT_DATA"]
        if not statuses:
            overall = "INSUFFICIENT_DATA"
        elif "OFF_TRACK" in statuses:
            overall = "OFF_TRACK"
        elif "AT_RISK" in statuses:
            overall = "AT_RISK"
        else:
            overall = "ON_TRACK"

        return PostAcquisitionThesisResponse(
            deal_id=deal_id,
            overall_status=overall,
            theses=[AcquisitionThesisResponse.model_validate(t) for t in theses],
            initiatives=[ValueCreationInitiativeResponse.model_validate(i) for i in initiatives],
            data_gaps=data_gaps,
        )
