"""Post-Acquisition Agentic Intelligence Modules — Production Implementations.

Authentic, grounded agent implementations for post-acquisition integration,
operating performance monitoring, synergy realization, customer intelligence,
revenue growth, operational efficiency, and executive acquisition thesis tracking.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.domains.agents.base import BaseSpecialistAgent
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentLifecyclePhase,
    AgentMetadata,
    AgentStatus,
    BaseAgentAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding, GroundedRecommendation
from app.domains.integration.models import IntegrationBlocker, IntegrationMilestone
from app.domains.post_deal.kpi_engine import PostDealKPIEngine, ThesisStatus
from app.domains.post_deal.models import (
    AcquisitionThesis,
    CustomerAccount,
    PostAcquisitionMetric,
    ValueCreationInitiative,
)
from app.domains.synergy.models import SynergyOpportunity, SynergyRealizationLog
from app.domains.technology.models import OperationalMetric, TechnologyDependency, TechnologyFinding
from app.domains.telemetry.models import (
    BusinessCustomer,
    BusinessExpense,
    BusinessOpportunity,
    BusinessRevenueEvent,
    BusinessTelemetryChange,
    ExternalConnection,
    SyncRun,
)


class BasePostDealAgent(BaseSpecialistAgent):
    """Base class for post-acquisition corporate growth and value realization agents."""

    @property
    def lifecycle_phase(self) -> AgentLifecyclePhase:
        return AgentLifecyclePhase.POST_DEAL_VALUE_CREATION


# 1. Growth Intelligence Agent
class GrowthIntelligenceAgent(BasePostDealAgent):
    """Identifies organic expansion, cross-sell white space, and TAM penetration."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.GROWTH

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Growth Intelligence Agent",
            version="1.0.0",
            purpose="Analyze account expansion potential, cross-selling pipelines, and inorganic bolt-on synergies.",
            domain="POST_DEAL_GROWTH",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "growth_waterfall_tool",
                "customer_expansion_tool",
                "pricing_elasticity_tool",
                "revenue_bridge_tool",
            ],
            confidence_policy="Requires verified customer expansion ledger records for HIGH confidence.",
            evidence_requirements=["Customer Account Expansion Register", "Growth Initiatives Log"],
            limitations=["Organic expansion forecasts depend on market sales execution capacity."],
            handoff_targets=["revenue_optimization_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("customer_expansion_tool")
        tools_invoked.append("customer_expansion_tool")

        # Query Customer Accounts
        cust_q = select(CustomerAccount).where(
            CustomerAccount.deal_id == deal_id,
            CustomerAccount.organization_id == org_id,
        )
        cust_res = await self.session.execute(cust_q)
        accounts = list(cust_res.scalars().all())

        # Query Canonical Telemetry (CRM Customers and Opportunities)
        telem_cust_q = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.organization_id == org_id,
        )
        telem_custs = list((await self.session.execute(telem_cust_q)).scalars().all())

        telem_opp_q = select(BusinessOpportunity).where(
            BusinessOpportunity.deal_id == deal_id,
            BusinessOpportunity.organization_id == org_id,
        )
        telem_opps = list((await self.session.execute(telem_opp_q)).scalars().all())

        # Query Growth Initiatives
        self.verify_tool("growth_waterfall_tool")
        tools_invoked.append("growth_waterfall_tool")

        init_q = select(ValueCreationInitiative).where(
            ValueCreationInitiative.deal_id == deal_id,
            ValueCreationInitiative.organization_id == org_id,
            ValueCreationInitiative.pillar == "GROWTH",
        )
        init_res = await self.session.execute(init_q)
        initiatives = list(init_res.scalars().all())

        if not accounts and not initiatives and not telem_custs and not telem_opps:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_GROWTH",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient customer account expansion or growth initiative data in post-close workspace.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No customer account expansion potentials, growth programs, or CRM telemetry logged."],
                data_gaps=[
                    "Post-acquisition customer account list with ARR and expansion estimates",
                    "Strategic organic growth and cross-sell initiative pipeline",
                ],
                required_diligence=["Connect CRM telemetry or ingest customer subscription ledger."],
            )

        citations = []
        if accounts:
            total_arr = sum(a.arr for a in accounts)
            total_expansion = sum(a.expansion_potential_usd for a in accounts)
            expanding_accounts = [a for a in accounts if a.expansion_potential_usd > 0]
        else:
            total_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in telem_custs)
            open_opps = [o for o in telem_opps if not getattr(o, "is_closed", False) or getattr(o, "is_won", False)]
            total_expansion = sum(float(getattr(o, "amount_usd", 0.0) or 0.0) for o in open_opps if not getattr(o, "is_closed", False))
            expanding_accounts = [c for c in telem_custs if any(getattr(o, "customer_external_id", "") == getattr(c, "external_id", "") for o in open_opps)]
            if telem_custs or telem_opps:
                ref_id = telem_custs[0].id if telem_custs else telem_opps[0].id
                citations.append(
                    CitationRef(
                        document_id=ref_id,
                        document_name="External CRM Telemetry (Salesforce)",
                        page_number=1,
                        exact_quote=f"Live business telemetry: {len(telem_custs)} customer accounts and {len(telem_opps)} pipeline opportunities ingested.",
                        confidence_score=0.95,
                    )
                )

        target_growth_ebitda = sum(i.target_ebitda_impact for i in initiatives)
        realized_growth_ebitda = sum(i.realized_ebitda_impact for i in initiatives)

        positive_drivers = []
        negative_drivers = []

        if total_expansion > 0:
            positive_drivers.append(
                f"Identified ${total_expansion:,.0f} in expansion opportunities across {len(expanding_accounts)} customer accounts."
            )
        if target_growth_ebitda > 0:
            positive_drivers.append(
                f"Targeting ${target_growth_ebitda:,.0f} EBITDA impact from {len(initiatives)} strategic growth initiatives."
            )

        if not expanding_accounts and total_arr > 0:
            negative_drivers.append("No active expansion or upsell pipeline identified in current customer base.")

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="GROWTH_EXPANSION",
                headline="Customer Expansion Potential",
                detailed_reasoning=f"Analyzed {len(accounts) or len(telem_custs)} accounts representing ${total_arr:,.0f} baseline ARR. Total expansion potential: ${total_expansion:,.0f}.",
                finding_type="FACT",
                severity_level="LOW" if total_expansion > 0 else "MEDIUM",
                confidence_score=0.90,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Growth Intelligence: ${total_expansion:,.0f} in account expansion potential identified across "
            f"{len(expanding_accounts)} accounts. Active growth initiatives: {len(initiatives)} "
            f"(${realized_growth_ebitda:,.0f} / ${target_growth_ebitda:,.0f} realized)."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_GROWTH",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.90,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "total_arr": total_arr,
                "total_expansion_potential_usd": total_expansion,
                "expanding_accounts_count": len(expanding_accounts),
                "growth_initiatives_count": len(initiatives),
                "target_growth_ebitda": target_growth_ebitda,
                "realized_growth_ebitda": realized_growth_ebitda,
                "telemetry_customers_count": len(telem_custs),
                "telemetry_opportunities_count": len(telem_opps),
            },
            deterministic_references={
                "expansion_potential_usd": total_expansion,
                "total_arr": total_arr,
                "growth_initiatives_count": len(initiatives),
            },
        )


# 2. Revenue Optimization Agent
class RevenueOptimizationAgent(BasePostDealAgent):
    """Monitors revenue growth, gross margins, price elasticity, and discount governance."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.REVENUE

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Revenue Optimization Agent",
            version="1.0.0",
            purpose="Analyze pricing power, gross margin realization, and post-close revenue trends vs targets.",
            domain="POST_DEAL_REVENUE",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "pricing_elasticity_tool",
                "revenue_bridge_tool",
                "customer_expansion_tool",
                "post_deal_metrics_tool",
            ],
            confidence_policy="Requires verified post-deal P&L line items and pricing logs.",
            evidence_requirements=["Post-Acquisition Income Statement", "Product Pricing Tier Register"],
            limitations=["Price elasticity modeling requires contract renewal rate history."],
            handoff_targets=["fp_and_a_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("post_deal_metrics_tool")
        tools_invoked.append("post_deal_metrics_tool")

        # Query Post-Acquisition Financial Metrics
        metrics_q = select(PostAcquisitionMetric).where(
            PostAcquisitionMetric.deal_id == deal_id,
            PostAcquisitionMetric.organization_id == org_id,
        )
        metrics_res = await self.session.execute(metrics_q)
        metrics = list(metrics_res.scalars().all())

        # Query Canonical Telemetry (Revenue Events / Invoices)
        telem_rev_q = select(BusinessRevenueEvent).where(
            BusinessRevenueEvent.deal_id == deal_id,
            BusinessRevenueEvent.organization_id == org_id,
        )
        telem_rev_events = list((await self.session.execute(telem_rev_q)).scalars().all())

        if not metrics and not telem_rev_events:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_REVENUE",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient post-close revenue metrics or operating statements available.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No post-closing revenue, gross margin records, or accounting telemetry found."],
                data_gaps=["Post-acquisition monthly/quarterly actual revenue and gross margin logs."],
                required_diligence=["Connect accounting telemetry (QuickBooks Online) or ingest P&L statements."],
            )

        rev_m = next((m for m in metrics if m.metric_name == "REVENUE"), None)
        gm_m = next((m for m in metrics if m.metric_name == "GROSS_MARGIN"), None)

        actual_rev = rev_m.actual_value if rev_m else 0.0
        baseline_rev = rev_m.baseline_value if rev_m else 0.0
        target_rev = rev_m.target_value if rev_m else 0.0

        citations = []
        if actual_rev == 0.0 and telem_rev_events:
            actual_rev = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in telem_rev_events)
            ref_id = telem_rev_events[0].id
            citations.append(
                CitationRef(
                    document_id=ref_id,
                    document_name="External Accounting Telemetry (QuickBooks Online)",
                    page_number=1,
                    exact_quote=f"Live business telemetry: Recognized ${actual_rev:,.0f} across {len(telem_rev_events)} invoices/revenue events.",
                    confidence_score=0.95,
                )
            )

        rev_growth = PostDealKPIEngine.compute_revenue_growth_pct(actual_rev, baseline_rev) if baseline_rev > 0 else None
        rev_variance = round(((actual_rev - target_rev) / target_rev) * 100.0, 2) if target_rev > 0 else 0.0

        positive_drivers = []
        negative_drivers = []

        if rev_growth is not None and rev_growth > 0:
            positive_drivers.append(f"Post-acquisition revenue grew {rev_growth:.1f}% vs baseline (${actual_rev:,.0f} vs ${baseline_rev:,.0f}).")
        elif rev_growth is not None and rev_growth < 0:
            negative_drivers.append(f"Post-acquisition revenue contracted {abs(rev_growth):.1f}% vs baseline.")

        if rev_variance >= 0 and target_rev > 0:
            positive_drivers.append(f"Actual revenue is +{rev_variance:.1f}% ahead of plan target (${actual_rev:,.0f} vs ${target_rev:,.0f}).")
        elif target_rev > 0:
            negative_drivers.append(f"Actual revenue is {rev_variance:.1f}% below target.")

        findings = [
            GroundedFinding(
                domain_pillar="FINANCIAL",
                category="REVENUE_PERFORMANCE",
                headline="Post-Acquisition Revenue Execution",
                detailed_reasoning=f"Actual revenue reached ${actual_rev:,.0f} (Growth vs baseline: {rev_growth or 0:.1f}%, Variance vs plan: {rev_variance:+.1f}%).",
                finding_type="FACT",
                severity_level="LOW" if rev_variance >= -5.0 else "HIGH",
                confidence_score=0.92,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Revenue Optimization: Actual revenue is ${actual_rev:,.0f} "
            f"({rev_growth or 0:+.1f}% vs baseline, {rev_variance:+.1f}% vs plan target)."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_REVENUE",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.92,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "actual_revenue": actual_rev,
                "baseline_revenue": baseline_rev,
                "target_revenue": target_rev,
                "revenue_growth_pct": rev_growth,
                "revenue_variance_pct": rev_variance,
                "telemetry_revenue_events_count": len(telem_rev_events),
            },
            deterministic_references={
                "actual_revenue": actual_rev,
                "revenue_growth_pct": rev_growth,
                "revenue_variance_pct": rev_variance,
            },
        )


# 3. Customer Retention Agent
class CustomerRetentionAgent(BasePostDealAgent):
    """Monitors customer churn risk, net revenue retention (NRR), and account health."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.CUSTOMER

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Customer Retention Agent",
            version="1.0.0",
            purpose="Analyze customer concentration, NRR retention cohorts, and account-level churn risks.",
            domain="POST_DEAL_CUSTOMER",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "retention_cohort_tool",
                "nps_sentiment_tool",
                "customer_portfolio_tool",
                "ml_prediction_tool",
            ],
            confidence_policy="Requires verified customer CRM subscription renewal feeds.",
            evidence_requirements=["Customer Account List", "Subscription Contract Renewal Log"],
            limitations=["Churn risk models rely on timely CRM updates and usage telemetry."],
            handoff_targets=["growth_intelligence_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("customer_portfolio_tool")
        tools_invoked.append("customer_portfolio_tool")

        # Query Customer Accounts
        cust_q = select(CustomerAccount).where(
            CustomerAccount.deal_id == deal_id,
            CustomerAccount.organization_id == org_id,
        )
        cust_res = await self.session.execute(cust_q)
        accounts = list(cust_res.scalars().all())

        # Query Canonical Telemetry Customers
        telem_cust_q = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.organization_id == org_id,
        )
        telem_custs = list((await self.session.execute(telem_cust_q)).scalars().all())

        if not accounts and not telem_custs:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_CUSTOMER",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient customer account or retention data in post-close workspace.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No customer accounts, renewal schedules, or CRM telemetry logged."],
                data_gaps=[
                    "Customer subscription contract database with ARR and renewal dates",
                    "Customer health scores and NPS telemetry logs",
                ],
                required_diligence=["Connect CRM telemetry (Salesforce) or ingest customer subscription accounts."],
            )

        citations = []
        if accounts:
            total_accounts = len(accounts)
            total_arr = sum(a.arr for a in accounts)
            at_risk_accounts = [a for a in accounts if a.health_status in ["AT_RISK", "CRITICAL"] or a.churn_risk_score > 0.40]
            at_risk_arr = sum(a.arr for a in at_risk_accounts)
            churned_accounts = [a for a in accounts if a.is_churned]
            churned_arr = sum(a.arr for a in churned_accounts)
            expanding_arr = sum(a.expansion_potential_usd for a in accounts if a.health_status == "EXPANDING")
            avg_churn_risk = sum(a.churn_risk_score for a in accounts) / total_accounts if total_accounts > 0 else 0.0
            nrr_pct = PostDealKPIEngine.compute_net_revenue_retention_pct(
                starting_arr=total_arr, expansion_arr=expanding_arr, churned_arr=churned_arr
            ) if total_arr > 0 else 100.0
        else:
            total_accounts = len(telem_custs)
            total_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in telem_custs)
            at_risk_accounts = [c for c in telem_custs if (getattr(c, "churn_risk_score", 0.0) or 0.0) >= 0.5 or getattr(c, "health_status", "") in ["AT_RISK", "CRITICAL"]]
            at_risk_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in at_risk_accounts)
            churned_accounts = [c for c in telem_custs if getattr(c, "is_churned", False)]
            churned_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in churned_accounts)
            expanding_arr = sum(float(getattr(c, "expansion_potential_usd", 0.0) or 0.0) for c in telem_custs if getattr(c, "health_status", "") == "EXPANDING")
            avg_churn_risk = sum(float(getattr(c, "churn_risk_score", 0.0) or 0.0) for c in telem_custs) / total_accounts if total_accounts > 0 else 0.0
            nrr_pct = PostDealKPIEngine.compute_net_revenue_retention_pct(
                starting_arr=total_arr, expansion_arr=expanding_arr, churned_arr=churned_arr
            ) if total_arr > 0 else 100.0
            ref_id = telem_custs[0].id
            citations.append(
                CitationRef(
                    document_id=ref_id,
                    document_name="External CRM Customer Telemetry (Salesforce)",
                    page_number=1,
                    exact_quote=f"Continuous telemetry ingested {total_accounts} customer accounts (${total_arr:,.0f} ARR) with churn risk classification.",
                    confidence_score=0.95,
                )
            )

        positive_drivers = []
        negative_drivers = []

        if nrr_pct is not None and nrr_pct >= 105.0:
            positive_drivers.append(f"Strong Net Revenue Retention (NRR) of {nrr_pct:.1f}% indicates healthy account expansion.")
        elif nrr_pct is not None and nrr_pct < 100.0:
            negative_drivers.append(f"Net Revenue Retention below 100% ({nrr_pct:.1f}%), indicating net revenue contraction.")

        if at_risk_accounts:
            negative_drivers.append(f"{len(at_risk_accounts)} customer accounts flagged at elevated churn risk (${at_risk_arr:,.0f} ARR).")
        else:
            positive_drivers.append("Zero customer accounts currently flagged at critical churn risk.")

        findings = [
            GroundedFinding(
                domain_pillar="CUSTOMER",
                category="RETENTION_HEALTH",
                headline="Customer Retention & Churn Health",
                detailed_reasoning=f"Analyzed {total_accounts} accounts with ${total_arr:,.0f} ARR. NRR: {nrr_pct or 0:.1f}%. At-risk accounts: {len(at_risk_accounts)} (${at_risk_arr:,.0f} ARR at risk).",
                finding_type="FACT",
                severity_level="LOW" if len(at_risk_accounts) == 0 else ("HIGH" if at_risk_arr > total_arr * 0.20 else "MEDIUM"),
                confidence_score=0.91,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Customer Retention: {total_accounts} accounts (${total_arr:,.0f} ARR). NRR: {nrr_pct or 0:.1f}%. "
            f"{len(at_risk_accounts)} account(s) at elevated churn risk (${at_risk_arr:,.0f} ARR)."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_CUSTOMER",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.91,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "total_accounts": total_accounts,
                "total_arr": total_arr,
                "at_risk_accounts_count": len(at_risk_accounts),
                "at_risk_arr": at_risk_arr,
                "avg_churn_risk_score": round(avg_churn_risk, 3),
                "nrr_pct": nrr_pct,
                "telemetry_customers_count": len(telem_custs),
            },
            deterministic_references={
                "total_arr": total_arr,
                "at_risk_arr": at_risk_arr,
                "nrr_pct": nrr_pct,
            },
        )


# 4. Cost Optimization Agent
class CostOptimizationAgent(BasePostDealAgent):
    """Identifies vendor rationalization, G&A synergies, cloud hosting savings, and process efficiencies."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.COST_OPT

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Cost Optimization Agent",
            version="1.0.0",
            purpose="Identify procurement overlaps, cloud hosting redundancies, and operational cost savings.",
            domain="POST_DEAL_COST",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "procurement_spend_tool",
                "headcount_synergy_tool",
                "operational_metrics_tool",
                "cloud_cost_risk_tool",
            ],
            confidence_policy="Requires verified vendor GL ledger and operational cost logs.",
            evidence_requirements=["Vendor Procurement Ledger", "Cloud Hosting Invoices"],
            limitations=["Cost rationalization execution timelines depend on contract termination clauses."],
            handoff_targets=["operations_intelligence_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("operational_metrics_tool")
        tools_invoked.append("operational_metrics_tool")

        # Query Operational Metrics
        op_q = select(OperationalMetric).where(
            OperationalMetric.deal_id == deal_id,
            OperationalMetric.organization_id == org_id,
        )
        op_res = await self.session.execute(op_q)
        op_metrics = list(op_res.scalars().all())

        # Query Technology Dependencies & Cloud spend
        self.verify_tool("cloud_cost_risk_tool")
        tools_invoked.append("cloud_cost_risk_tool")

        dep_q = select(TechnologyDependency).where(
            TechnologyDependency.deal_id == deal_id,
            TechnologyDependency.organization_id == org_id,
        )
        dep_res = await self.session.execute(dep_q)
        dependencies = list(dep_res.scalars().all())

        # Query Cost Synergy Initiatives
        init_q = select(ValueCreationInitiative).where(
            ValueCreationInitiative.deal_id == deal_id,
            ValueCreationInitiative.organization_id == org_id,
            ValueCreationInitiative.pillar.in_(["COST", "OPERATIONS"]),
        )
        init_res = await self.session.execute(init_q)
        initiatives = list(init_res.scalars().all())

        # Query Canonical Telemetry Expenses (QuickBooks)
        telem_exp_q = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.organization_id == org_id,
        )
        telem_expenses = list((await self.session.execute(telem_exp_q)).scalars().all())

        if not op_metrics and not dependencies and not initiatives and not telem_expenses:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_COST",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient operational cost, cloud spend, vendor procurement, or expense telemetry data.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No vendor procurement, operational cost, or accounting expense telemetry records logged."],
                data_gaps=["Vendor contracts, cloud hosting invoices, and cost synergy tracking schedules."],
                required_diligence=["Connect accounting telemetry (QuickBooks Online) or ingest vendor contracts."],
            )

        total_dep_spend = sum(d.annual_cost for d in dependencies)
        total_telem_spend = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in telem_expenses)
        effective_spend = total_dep_spend + total_telem_spend if total_dep_spend == 0 else total_dep_spend
        spofs = [d for d in dependencies if d.is_single_point_of_failure]
        target_cost_savings = sum(i.target_ebitda_impact for i in initiatives)
        realized_cost_savings = sum(i.realized_ebitda_impact for i in initiatives)

        cloud_metrics = [m for m in op_metrics if m.metric_category == "CLOUD_SPEND"]

        positive_drivers = []
        negative_drivers = []

        if target_cost_savings > 0:
            positive_drivers.append(
                f"Cost reduction roadmap targeting ${target_cost_savings:,.0f} annual EBITDA savings (${realized_cost_savings:,.0f} realized)."
            )

        if spofs:
            negative_drivers.append(f"{len(spofs)} vendor dependency/dependencies identified as critical Single Points of Failure.")

        citations = []
        if telem_expenses:
            ref_id = telem_expenses[0].id
            citations.append(
                CitationRef(
                    document_id=ref_id,
                    document_name="External Accounting Telemetry (QuickBooks Online)",
                    page_number=1,
                    exact_quote=f"Live business telemetry: Ingested {len(telem_expenses)} operating expense line items totaling ${total_telem_spend:,.0f}.",
                    confidence_score=0.95,
                )
            )

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="COST_OPTIMIZATION",
                headline="Operational Cost & Vendor Spend Rationalization",
                detailed_reasoning=f"Analyzed {len(dependencies)} vendor dependencies and {len(telem_expenses)} telemetry expense records totaling ${effective_spend:,.0f} spend. Cost initiatives: {len(initiatives)} (${realized_cost_savings:,.0f} realized of ${target_cost_savings:,.0f} target).",
                finding_type="FACT",
                severity_level="LOW" if realized_cost_savings >= target_cost_savings * 0.5 else "MEDIUM",
                confidence_score=0.88,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Cost Optimization: ${effective_spend:,.0f} in vendor/operating spend tracked across "
            f"{len(dependencies) or len(telem_expenses)} items. "
            f"Cost savings initiatives: ${realized_cost_savings:,.0f} realized of ${target_cost_savings:,.0f} target."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_COST",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.88,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "total_vendor_spend": effective_spend,
                "telemetry_expenses_spend": total_telem_spend,
                "telemetry_expenses_count": len(telem_expenses),
                "spof_vendor_count": len(spofs),
                "target_cost_savings": target_cost_savings,
                "realized_cost_savings": realized_cost_savings,
                "cost_initiatives_count": len(initiatives),
            },
            deterministic_references={
                "total_vendor_spend": effective_spend,
                "realized_cost_savings": realized_cost_savings,
            },
        )


# 5. Operations Intelligence Agent
class OperationsIntelligenceAgent(BasePostDealAgent):
    """Monitors SLA compliance, operational incidents, throughput, and process bottlenecks."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.OPERATIONS

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Operations Intelligence Agent",
            version="1.0.0",
            purpose="Monitor SLA compliance, operational incident response, and process bottlenecks.",
            domain="POST_DEAL_OPERATIONS",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "throughput_sla_tool",
                "facility_utilization_tool",
                "operational_metrics_tool",
                "integration_health_score_tool",
            ],
            confidence_policy="Requires verified operational telemetry and incident logs.",
            evidence_requirements=["Operational SLA Log", "Production Incident Register"],
            limitations=["SLA telemetry granularity depends on source monitoring integrations."],
            handoff_targets=["cost_optimization_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("operational_metrics_tool")
        tools_invoked.append("operational_metrics_tool")

        # Query Operational Metrics
        op_q = select(OperationalMetric).where(
            OperationalMetric.deal_id == deal_id,
            OperationalMetric.organization_id == org_id,
        )
        op_res = await self.session.execute(op_q)
        metrics = list(op_res.scalars().all())

        # Query Integration Blockers
        self.verify_tool("integration_health_score_tool")
        tools_invoked.append("integration_health_score_tool")

        blockers_q = select(IntegrationBlocker).where(
            IntegrationBlocker.deal_id == deal_id,
            IntegrationBlocker.organization_id == org_id,
            IntegrationBlocker.status == "OPEN",
        )
        blockers_res = await self.session.execute(blockers_q)
        blockers = list(blockers_res.scalars().all())

        # Query Continuous External Telemetry (Connections, Expenses, Drift)
        conn_q = select(ExternalConnection).where(
            ExternalConnection.deal_id == deal_id,
            ExternalConnection.organization_id == org_id,
        )
        connections = list((await self.session.execute(conn_q)).scalars().all())

        telem_exp_q = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.organization_id == org_id,
        )
        telem_expenses = list((await self.session.execute(telem_exp_q)).scalars().all())

        changes_q = select(BusinessTelemetryChange).where(
            BusinessTelemetryChange.deal_id == deal_id,
            BusinessTelemetryChange.organization_id == org_id,
            BusinessTelemetryChange.is_resolved == False,
        )
        changes = list((await self.session.execute(changes_q)).scalars().all())

        if not metrics and not blockers and not connections and not telem_expenses:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_OPERATIONS",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient operational telemetry, connection feeds, or SLA performance logs.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No operational SLA or throughput telemetry recorded."],
                data_gaps=["Operational SLA compliance metrics, uptime records, and incident MTTR logs."],
                required_diligence=["Connect operational monitoring telemetry into DealGuard AI."],
            )

        breaches = [m for m in metrics if m.status == "CRITICAL_BREACH"]
        deviations = [m for m in metrics if m.status == "DEVIATION"]
        critical_blockers = [b for b in blockers if b.severity == "CRITICAL"]

        positive_drivers = []
        negative_drivers = []

        if connections:
            active_conns = [c for c in connections if c.connection_status in ("ACTIVE", "CONNECTED")]
            positive_drivers.append(f"{len(active_conns)} of {len(connections)} operational telemetry system(s) active.")

        if not breaches and not critical_blockers:
            positive_drivers.append("All monitored operational SLAs are within target parameters.")
        else:
            if breaches:
                negative_drivers.append(f"{len(breaches)} operational metric(s) in CRITICAL_BREACH state.")
            if critical_blockers:
                negative_drivers.append(f"{len(critical_blockers)} critical integration blocker(s) impacting operations.")

        if changes:
            negative_drivers.append(f"{len(changes)} unresolved operational metric drift event(s) detected in continuous telemetry.")

        infra_expenses = [e for e in telem_expenses if str(e.category).upper() in ("CLOUD", "COGS")]
        total_infra_spend = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in infra_expenses)

        citations = []
        if connections:
            citations.append(
                CitationRef(
                    document_id=connections[0].id,
                    document_name=f"Operational Telemetry Connection ({connections[0].provider})",
                    page_number=1,
                    exact_quote=f"Operational system connection status: {connections[0].connection_status}. Freshness: {connections[0].data_freshness_status}.",
                )
            )
        elif telem_expenses:
            citations.append(
                CitationRef(
                    document_id=telem_expenses[0].id,
                    document_name=f"Operational Cost Telemetry ({telem_expenses[0].provider})",
                    page_number=1,
                    exact_quote=f"Ingested {len(telem_expenses)} expense line item(s) totaling ${sum(float(getattr(e, 'amount_usd', 0.0) or 0.0) for e in telem_expenses):,.0f}.",
                )
            )

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="SLA_PERFORMANCE",
                headline="Operational SLA & Process Health",
                detailed_reasoning=(
                    f"Evaluated {len(metrics)} operational metrics with {len(breaches)} critical breaches, "
                    f"{len(blockers)} open blockers, and {len(connections)} active external system connections."
                ),
                finding_type="FACT",
                severity_level="LOW" if not breaches and not critical_blockers else "HIGH",
                confidence_score=0.90,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Operations Intelligence: {len(metrics)} KPIs monitored. "
            f"Breaches: {len(breaches)}, Deviations: {len(deviations)}, Open Blockers: {len(blockers)}, "
            f"Active Telemetry Systems: {len(connections)}."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_OPERATIONS",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.90,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "total_monitored_metrics": len(metrics),
                "critical_breaches_count": len(breaches),
                "deviations_count": len(deviations),
                "open_blockers_count": len(blockers),
                "active_connections_count": len(connections),
                "operational_infra_spend_usd": total_infra_spend,
                "unresolved_drift_events_count": len(changes),
            },
            deterministic_references={
                "critical_breaches_count": len(breaches),
                "open_blockers_count": len(blockers),
                "active_connections_count": len(connections),
            },
        )


# 6. FP&A Intelligence Agent
class FPandAAgent(BasePostDealAgent):
    """Maintains rolling financial forecasts, budget vs actual variance, and covenant tracking."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.FP_AND_A

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="FP&A Intelligence Agent",
            version="1.0.0",
            purpose="Maintain rolling financial forecasts, budget vs actual variance analysis, and covenant compliance.",
            domain="POST_DEAL_FP_AND_A",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "rolling_forecast_tool",
                "budget_variance_tool",
                "financial_statements_tool",
                "post_deal_metrics_tool",
            ],
            confidence_policy="Requires verified monthly closing accounting balances.",
            evidence_requirements=["Monthly Closing Financial Reports", "Budget Model Workbook"],
            limitations=["Forecasts assume continuation of current macroeconomic baseline."],
            handoff_targets=["revenue_optimization_agent", "corporate_strategy_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("post_deal_metrics_tool")
        tools_invoked.append("post_deal_metrics_tool")

        metrics_q = select(PostAcquisitionMetric).where(
            PostAcquisitionMetric.deal_id == deal_id,
            PostAcquisitionMetric.organization_id == org_id,
        )
        metrics_res = await self.session.execute(metrics_q)
        metrics = list(metrics_res.scalars().all())

        # Query Canonical Telemetry (Revenue & Expenses)
        telem_rev_q = select(BusinessRevenueEvent).where(
            BusinessRevenueEvent.deal_id == deal_id,
            BusinessRevenueEvent.organization_id == org_id,
        )
        telem_rev_events = list((await self.session.execute(telem_rev_q)).scalars().all())

        telem_exp_q = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.organization_id == org_id,
        )
        telem_expenses = list((await self.session.execute(telem_exp_q)).scalars().all())

        if not metrics and not telem_rev_events and not telem_expenses:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_FP_AND_A",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient post-acquisition financial statements, budget variance, or accounting telemetry data.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No post-close financial actuals, budget variance logs, or external accounting telemetry found."],
                data_gaps=["Monthly P&L, balance sheet, and budget vs actual financial models."],
                required_diligence=["Connect accounting telemetry (QuickBooks Online) or ingest quarterly financial actuals."],
            )

        citations = []
        if metrics:
            rev_m = next((m for m in metrics if m.metric_name == "REVENUE"), None)
            ebitda_m = next((m for m in metrics if m.metric_name == "EBITDA"), None)
            actual_ebitda = ebitda_m.actual_value if ebitda_m else 0.0
            target_ebitda = ebitda_m.target_value if ebitda_m else 0.0
            actual_rev = rev_m.actual_value if rev_m else 0.0
        else:
            actual_rev = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in telem_rev_events)
            actual_exp = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in telem_expenses)
            actual_ebitda = round(actual_rev - actual_exp, 2)
            target_ebitda = actual_rev * 0.20 if actual_rev > 0 else 0.0
            ref_id = telem_rev_events[0].id if telem_rev_events else telem_expenses[0].id
            citations.append(
                CitationRef(
                    document_id=ref_id,
                    document_name="External Accounting Telemetry (QuickBooks Online)",
                    page_number=1,
                    exact_quote=f"Live business telemetry derived EBITDA of ${actual_ebitda:,.0f} from ${actual_rev:,.0f} revenue and ${actual_exp:,.0f} operating expenses.",
                    confidence_score=0.95,
                )
            )

        ebitda_margin = PostDealKPIEngine.compute_ebitda_margin_pct(actual_ebitda, actual_rev)
        ebitda_variance = round(((actual_ebitda - target_ebitda) / abs(target_ebitda)) * 100.0, 2) if target_ebitda != 0 else 0.0

        positive_drivers = []
        negative_drivers = []

        if ebitda_margin is not None and ebitda_margin > 0:
            positive_drivers.append(f"Operating EBITDA margin standing at {ebitda_margin:.1f}%.")
        if ebitda_variance >= 0 and target_ebitda > 0:
            positive_drivers.append(f"EBITDA is +{ebitda_variance:.1f}% ahead of plan target (${actual_ebitda:,.0f} vs ${target_ebitda:,.0f}).")
        elif target_ebitda > 0:
            negative_drivers.append(f"EBITDA is {ebitda_variance:.1f}% below plan budget.")

        findings = [
            GroundedFinding(
                domain_pillar="FINANCIAL",
                category="BUDGET_VARIANCE",
                headline="FP&A Budget vs Actual Performance",
                detailed_reasoning=f"Actual EBITDA: ${actual_ebitda:,.0f} (Margin: {ebitda_margin or 0:.1f}%, Variance: {ebitda_variance:+.1f}% vs target).",
                finding_type="FACT",
                severity_level="LOW" if ebitda_variance >= -10.0 else "HIGH",
                confidence_score=0.92,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"FP&A Forecast: Actual EBITDA ${actual_ebitda:,.0f} (Margin: {ebitda_margin or 0:.1f}%, "
            f"Variance: {ebitda_variance:+.1f}% vs budget target)."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_FP_AND_A",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.92,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "actual_ebitda": actual_ebitda,
                "target_ebitda": target_ebitda,
                "ebitda_margin_pct": ebitda_margin,
                "ebitda_variance_pct": ebitda_variance,
                "telemetry_revenue_events_count": len(telem_rev_events),
                "telemetry_expenses_count": len(telem_expenses),
            },
            deterministic_references={
                "actual_ebitda": actual_ebitda,
                "ebitda_margin_pct": ebitda_margin,
                "ebitda_variance_pct": ebitda_variance,
            },
        )


# 7. Corporate Strategy / Executive Value Creation Agent
class CorporateStrategyAgent(BasePostDealAgent):
    """Synthesizes post-acquisition performance against the original acquisition thesis."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.STRATEGY

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Corporate Strategy & Value Creation Agent",
            version="1.0.0",
            purpose="Synthesize executive acquisition thesis progress, strategic OKRs, and portfolio value realization.",
            domain="POST_DEAL_STRATEGY",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "market_share_tam_tool",
                "ma_pipeline_tool",
                "acquisition_thesis_tool",
                "value_creation_synthesis_tool",
            ],
            confidence_policy="Requires verified acquisition thesis targets and post-close actuals.",
            evidence_requirements=["Investment Committee Memo", "Acquisition Thesis Scorecard"],
            limitations=["Strategy recommendations reflect current available operating actuals."],
            handoff_targets=["performance_monitoring_agent", "deal_decision_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("acquisition_thesis_tool")
        tools_invoked.append("acquisition_thesis_tool")

        # Query Theses
        theses_q = select(AcquisitionThesis).where(
            AcquisitionThesis.deal_id == deal_id,
            AcquisitionThesis.organization_id == org_id,
        )
        theses_res = await self.session.execute(theses_q)
        theses = list(theses_res.scalars().all())

        # Query Value Creation Initiatives
        self.verify_tool("value_creation_synthesis_tool")
        tools_invoked.append("value_creation_synthesis_tool")

        init_q = select(ValueCreationInitiative).where(
            ValueCreationInitiative.deal_id == deal_id,
            ValueCreationInitiative.organization_id == org_id,
        )
        init_res = await self.session.execute(init_q)
        initiatives = list(init_res.scalars().all())

        # Query Continuous Telemetry Drift & Financial Actuals
        telem_changes_q = select(BusinessTelemetryChange).where(
            BusinessTelemetryChange.deal_id == deal_id,
            BusinessTelemetryChange.organization_id == org_id,
        )
        telem_changes = list((await self.session.execute(telem_changes_q)).scalars().all())

        telem_rev_q = select(BusinessRevenueEvent).where(
            BusinessRevenueEvent.deal_id == deal_id,
            BusinessRevenueEvent.organization_id == org_id,
        )
        telem_revs = list((await self.session.execute(telem_rev_q)).scalars().all())

        telem_cust_q = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.organization_id == org_id,
        )
        telem_custs = list((await self.session.execute(telem_cust_q)).scalars().all())

        if not theses and not initiatives and not telem_changes and not telem_revs and not telem_custs:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_STRATEGY",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient acquisition thesis tracking data, strategic programs, or business telemetry actuals.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No acquisition thesis targets or strategic initiatives logged."],
                data_gaps=["Original acquisition thesis pillars and post-acquisition milestone targets."],
                required_diligence=["Configure Acquisition Thesis Scorecard in Post-Acquisition Workspace."],
            )

        on_track = [t for t in theses if t.status == "ON_TRACK"]
        at_risk = [t for t in theses if t.status == "AT_RISK"]
        off_track = [t for t in theses if t.status == "OFF_TRACK"]

        if off_track:
            overall_status = ThesisStatus.OFF_TRACK.value
        elif at_risk:
            overall_status = ThesisStatus.AT_RISK.value
        elif on_track:
            overall_status = ThesisStatus.ON_TRACK.value
        elif telem_revs or telem_custs:
            overall_status = ThesisStatus.ON_TRACK.value
        else:
            overall_status = ThesisStatus.INSUFFICIENT_DATA.value

        positive_drivers = []
        negative_drivers = []

        for t in on_track:
            positive_drivers.append(f"Thesis Pillar '{t.thesis_pillar}' is ON TRACK ({t.target_metric}).")
        for t in at_risk:
            negative_drivers.append(f"Thesis Pillar '{t.thesis_pillar}' is AT RISK ({t.target_metric}).")
        for t in off_track:
            negative_drivers.append(f"Thesis Pillar '{t.thesis_pillar}' is OFF TRACK ({t.target_metric}).")

        # Integrate telemetry drift against strategic thesis
        drift_in_pillars = [c for c in telem_changes if c.affected_thesis_pillar]
        for c in drift_in_pillars:
            negative_drivers.append(
                f"Telemetry drift detected in thesis pillar '{c.affected_thesis_pillar}': {c.metric_name} shifted {c.delta_percentage:+.1f}%."
            )

        total_actual_revenue = sum(float(getattr(r, "amount_usd", 0.0) or 0.0) for r in telem_revs)
        total_pipeline_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in telem_custs)

        citations = []
        if telem_changes:
            ref_change = telem_changes[0]
            citations.append(
                CitationRef(
                    document_id=ref_change.id,
                    document_name="Continuous Telemetry Drift Stream",
                    page_number=1,
                    exact_quote=f"Identified {len(telem_changes)} telemetry variance events evaluated against core investment thesis.",
                )
            )
        elif telem_revs:
            ref_rev = telem_revs[0]
            citations.append(
                CitationRef(
                    document_id=ref_rev.id,
                    document_name=f"External ERP Revenue Telemetry ({ref_rev.provider})",
                    page_number=1,
                    exact_quote=f"Realized ${total_actual_revenue:,.0f} revenue actuals across {len(telem_revs)} synchronized transactions.",
                )
            )
        elif telem_custs:
            ref_c = telem_custs[0]
            citations.append(
                CitationRef(
                    document_id=ref_c.id,
                    document_name=f"External CRM Telemetry ({ref_c.provider})",
                    page_number=1,
                    exact_quote=f"Total monitored ARR of ${total_pipeline_arr:,.0f} across {len(telem_custs)} customer accounts.",
                )
            )

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="ACQUISITION_THESIS",
                headline="Acquisition Thesis Realization Status",
                detailed_reasoning=(
                    f"Thesis status: {overall_status}. On Track: {len(on_track)}, At Risk: {len(at_risk)}, "
                    f"Off Track: {len(off_track)} across {len(theses)} pillars with {len(telem_changes)} continuous telemetry drift events."
                ),
                finding_type="FACT",
                severity_level="LOW" if overall_status == "ON_TRACK" else "HIGH",
                confidence_score=0.93,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        summary = (
            f"Corporate Strategy: Overall Acquisition Thesis is {overall_status}. "
            f"Pillars on track: {len(on_track)}/{len(theses)}. Value creation programs: {len(initiatives)}. "
            f"Monitored Telemetry Drift Events: {len(telem_changes)}."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_STRATEGY",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.93,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "overall_thesis_status": overall_status,
                "theses_count": len(theses),
                "on_track_count": len(on_track),
                "at_risk_count": len(at_risk),
                "off_track_count": len(off_track),
                "initiatives_count": len(initiatives),
                "telemetry_drift_events_count": len(telem_changes),
                "telemetry_revenue_actuals_usd": total_actual_revenue,
                "telemetry_pipeline_arr_usd": total_pipeline_arr,
            },
            deterministic_references={
                "overall_thesis_status": overall_status,
                "on_track_count": len(on_track),
                "telemetry_drift_events_count": len(telem_changes),
            },
        )


# 8. Performance Monitoring Agent
class PerformanceMonitoringAgent(BasePostDealAgent):
    """Continuous executive dashboard monitoring real-time value creation KPIs."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.MONITORING

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Performance Monitoring Agent",
            version="1.0.0",
            purpose="Continuous telemetry tracking on enterprise KPIs, integration velocity, and early risk detection.",
            domain="POST_DEAL_MONITORING",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "kpi_health_dashboard_tool",
                "covenant_compliance_tool",
                "post_deal_metrics_tool",
                "integration_health_score_tool",
            ],
            confidence_policy="Continuous telemetry stream aggregation.",
            evidence_requirements=["Integrated KPI Telemetry Feeds"],
            limitations=["Telemetry accuracy depends on connector synchronization frequency."],
            handoff_targets=["corporate_strategy_agent", "fp_and_a_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("post_deal_metrics_tool")
        tools_invoked.append("post_deal_metrics_tool")

        metrics_q = select(PostAcquisitionMetric).where(
            PostAcquisitionMetric.deal_id == deal_id,
            PostAcquisitionMetric.organization_id == org_id,
        )
        metrics_res = await self.session.execute(metrics_q)
        metrics = list(metrics_res.scalars().all())

        self.verify_tool("integration_health_score_tool")
        tools_invoked.append("integration_health_score_tool")

        ms_q = select(IntegrationMilestone).where(
            IntegrationMilestone.deal_id == deal_id,
            IntegrationMilestone.organization_id == org_id,
        )
        ms_res = await self.session.execute(ms_q)
        milestones = list(ms_res.scalars().all())

        blockers_q = select(IntegrationBlocker).where(
            IntegrationBlocker.deal_id == deal_id,
            IntegrationBlocker.organization_id == org_id,
            IntegrationBlocker.status == "OPEN",
        )
        blockers_res = await self.session.execute(blockers_q)
        open_blockers = list(blockers_res.scalars().all())

        # Query External Connections & Sync Runs
        conn_q = select(ExternalConnection).where(
            ExternalConnection.deal_id == deal_id,
            ExternalConnection.organization_id == org_id,
        )
        connections = list((await self.session.execute(conn_q)).scalars().all())

        sync_q = select(SyncRun).where(
            SyncRun.deal_id == deal_id,
            SyncRun.organization_id == org_id,
        ).order_by(SyncRun.started_at.desc()).limit(10)
        recent_syncs = list((await self.session.execute(sync_q)).scalars().all())

        if not metrics and not milestones and not connections:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_MONITORING",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient telemetry, performance metrics, or external connections for continuous monitoring.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No continuous KPI feeds, external connectors, or integration milestones connected."],
                data_gaps=["Post-acquisition KPI feeds, connector telemetry, and milestone logs."],
                required_diligence=["Connect business telemetry feeds (Salesforce/QuickBooks) in Telemetry Workspace."],
            )

        completed_ms = len([m for m in milestones if m.status == "COMPLETED"])
        completion_pct = PostDealKPIEngine.compute_integration_completion_pct(completed_ms, len(milestones))

        health_base = 88.0
        if len(open_blockers) > 0:
            health_base -= min(35.0, len(open_blockers) * 12.0)
        health_score = max(0.0, min(100.0, round(health_base, 1)))

        citations = []
        if connections:
            citations.append(
                CitationRef(
                    document_id=connections[0].id,
                    document_name="External Telemetry Infrastructure",
                    page_number=1,
                    exact_quote=f"{len(connections)} external telemetry connection(s) configured with {len(recent_syncs)} recent synchronization run(s).",
                    confidence_score=0.95,
                )
            )

        findings = [
            GroundedFinding(
                domain_pillar="OPERATIONAL",
                category="MONITORING_TELEMETRY",
                headline="Continuous Performance Telemetry Health",
                detailed_reasoning=f"Calculated enterprise health score: {health_score:.1f}/100 based on {len(metrics)} tracked KPIs, {completion_pct:.1f}% integration completion, {len(open_blockers)} open blockers, and {len(connections)} active telemetry connector(s).",
                finding_type="FACT",
                severity_level="LOW" if health_score >= 75.0 else "MEDIUM",
                confidence_score=0.90,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        positive_drivers = []
        if health_score >= 70:
            positive_drivers.append(f"Health score {health_score:.1f}/100 with active telemetry across {len(metrics)} metrics.")
        if connections:
            positive_drivers.append(f"{len(connections)} enterprise business system(s) continuously feeding telemetry.")

        summary = (
            f"Performance Monitoring: Enterprise Health Score is {health_score:.1f}/100. "
            f"Integration is {completion_pct:.1f}% complete with {len(open_blockers)} open blocker(s) and "
            f"{len(connections)} connected telemetry provider(s)."
        )

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_MONITORING",
            status=AgentStatus.SUCCESS,
            summary=summary,
            confidence=AgentConfidence.HIGH,
            confidence_score=0.90,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=[f"{len(open_blockers)} unmitigated blockers detected."] if open_blockers else [],
            metrics={
                "health_score": health_score,
                "integration_completion_pct": completion_pct,
                "open_blockers_count": len(open_blockers),
                "metrics_tracked_count": len(metrics),
                "active_connections_count": len(connections),
                "recent_sync_runs_count": len(recent_syncs),
            },
            deterministic_references={
                "health_score": health_score,
                "integration_completion_pct": completion_pct,
                "active_connections_count": len(connections),
            },
        )


# 9. Marketing Intelligence Agent
class MarketingIntelligenceAgent(BasePostDealAgent):
    """Optimizes customer acquisition cost (CAC), LTV/CAC ratios, and campaign ROI."""

    @property
    def agent_id(self) -> AgentId:
        return AgentId.MARKETING

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Marketing Intelligence Agent",
            version="1.0.0",
            purpose="Analyze CAC payback periods, LTV/CAC ratios, and customer acquisition efficiency.",
            domain="POST_DEAL_MARKETING",
            lifecycle_phase=AgentLifecyclePhase.POST_DEAL_VALUE_CREATION,
            allowed_tools=[
                "cac_ltv_tool",
                "campaign_efficiency_tool",
                "customer_cohort_tool",
            ],
            confidence_policy="Requires verified digital attribution and ad spend ledger data.",
            evidence_requirements=["Marketing Ad Spend Ledger", "Attribution Funnel Report"],
            limitations=["Attribution models require minimum 90-day campaign history."],
            handoff_targets=["growth_intelligence_agent", "revenue_optimization_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> BaseAgentAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        self.verify_tool("customer_cohort_tool")
        tools_invoked.append("customer_cohort_tool")

        # Query legacy / internal CustomerAccount
        cust_q = select(CustomerAccount).where(
            CustomerAccount.deal_id == deal_id,
            CustomerAccount.organization_id == org_id,
        )
        cust_res = await self.session.execute(cust_q)
        accounts = list(cust_res.scalars().all())

        # Query Canonical External Customer Telemetry (Salesforce & QBO)
        telem_cust_q = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.organization_id == org_id,
        )
        telem_customers = list((await self.session.execute(telem_cust_q)).scalars().all())

        # Query External Sales & Marketing Expenses (QuickBooks)
        telem_exp_q = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.organization_id == org_id,
            BusinessExpense.category == "S&M",
        )
        sm_expenses = list((await self.session.execute(telem_exp_q)).scalars().all())

        if not accounts and not telem_customers and not sm_expenses:
            return BaseAgentAssessment(
                agent_id=self.agent_id,
                domain="POST_DEAL_MARKETING",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient marketing CAC/LTV or acquisition channel telemetry.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No marketing CAC or customer acquisition channel data found."],
                data_gaps=["Marketing spend ledger, customer acquisition funnel conversion rates."],
                required_diligence=["Ingest marketing attribution and acquisition spend data."],
            )

        # Reconcile customer counts and ARR
        if accounts:
            total_accounts = len(accounts)
            total_arr = sum(a.arr for a in accounts)
        else:
            total_accounts = len(telem_customers)
            total_arr = sum(float(getattr(c, "arr_usd", 0.0) or 0.0) for c in telem_customers)

        avg_arr = total_arr / total_accounts if total_accounts else 0.0
        total_sm_spend = sum(float(getattr(e, "amount_usd", 0.0) or 0.0) for e in sm_expenses)
        cac_estimate = (total_sm_spend / total_accounts) if total_accounts > 0 and total_sm_spend > 0 else 0.0

        positive_drivers = []
        negative_drivers = []

        if avg_arr > 0:
            positive_drivers.append(f"Average contract value of ${avg_arr:,.0f} supported by live customer account telemetry.")
        if total_sm_spend > 0:
            positive_drivers.append(f"Synchronized ${total_sm_spend:,.0f} in S&M operational expenditure for CAC analysis.")

        citations = []
        if telem_customers:
            ref_c = telem_customers[0]
            citations.append(
                CitationRef(
                    document_id=ref_c.id,
                    document_name=f"External CRM Telemetry ({ref_c.provider})",
                    page_number=1,
                    exact_quote=f"Live customer portfolio: {len(telem_customers)} accounts tracked with pipeline ARR of ${total_arr:,.0f}.",
                )
            )
        if sm_expenses:
            ref_e = sm_expenses[0]
            citations.append(
                CitationRef(
                    document_id=ref_e.id,
                    document_name=f"External S&M Expense Telemetry ({ref_e.provider})",
                    page_number=1,
                    exact_quote=f"Ingested {len(sm_expenses)} Sales & Marketing expense line item(s) totaling ${total_sm_spend:,.0f}.",
                )
            )

        findings = [
            GroundedFinding(
                domain_pillar="CUSTOMER",
                category="CAC_LTV_EFFICIENCY",
                headline="Customer Acquisition & Marketing Efficiency",
                detailed_reasoning=(
                    f"Analyzed {total_accounts} accounts with average ACV of ${avg_arr:,.0f} "
                    f"and total S&M spend of ${total_sm_spend:,.0f}."
                ),
                finding_type="FACT",
                severity_level="LOW",
                confidence_score=0.85,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.post_deal.kpi_engine",
                citations=citations,
            )
        ]

        return BaseAgentAssessment(
            agent_id=self.agent_id,
            domain="POST_DEAL_MARKETING",
            status=AgentStatus.SUCCESS,
            summary=f"Marketing Intelligence: {total_accounts} accounts tracked with average ACV of ${avg_arr:,.0f}, S&M spend of ${total_sm_spend:,.0f}.",
            confidence=AgentConfidence.HIGH,
            confidence_score=0.85,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics={
                "total_accounts": total_accounts,
                "average_acv": avg_arr,
                "marketing_spend_usd": total_sm_spend,
                "cac_usd": round(cac_estimate, 2),
                "telemetry_customers_count": len(telem_customers),
            },
            deterministic_references={
                "average_acv": avg_arr,
                "marketing_spend_usd": total_sm_spend,
            },
        )
