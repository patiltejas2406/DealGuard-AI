"""Integration Tests for Telemetry Sync Engine, KPI Engine, and Post-Deal Agents."""

import uuid
from datetime import date, datetime, timezone
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.models import *
from app.domains.agents.contract import AgentExecutionRequest, AgentId, AgentStatus
from app.domains.agents.post_deal.extensibility import (
    GrowthIntelligenceAgent,
    RevenueOptimizationAgent,
    CustomerRetentionAgent,
    CostOptimizationAgent,
    OperationsIntelligenceAgent,
    FPandAAgent,
    CorporateStrategyAgent,
    PerformanceMonitoringAgent,
    MarketingIntelligenceAgent,
)
from app.domains.auth.models import Organization, Role, User, OrganizationMembership
from app.domains.deals.models import Deal, TargetCompany
from app.domains.post_deal.kpi_engine import PostDealKPIEngine
from app.domains.telemetry.models import (
    BusinessCustomer,
    BusinessExpense,
    BusinessOpportunity,
    BusinessRevenueEvent,
    ExternalConnection,
)
from app.domains.telemetry.schemas import (
    ConnectorProvider,
    ConnectionStatus,
    DataFreshnessStatus,
    ExternalConnectionCreate,
)
from app.domains.telemetry.service import TelemetryService
from app.domains.telemetry.sync_engine import TelemetrySyncEngine


async def create_test_env(db_session: AsyncSession, org_slug: str = "test-org"):
    """Helper to seed tenant org, company, user, and deal for foreign key integrity."""
    org = Organization(name="Test Org", slug=f"{org_slug}-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    await db_session.flush()

    user = User(
        email=f"user-{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="hash",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    company = TargetCompany(
        organization_id=org.id,
        name="Target Co",
        lifecycle_stage="POST_CLOSE",
        industry="Enterprise Software",
        sector="B2B SaaS",
    )
    db_session.add(company)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=company.id,
        title="Project Apollo",
        code_name="Apollo",
        deal_type="M_AND_A_BUY_SIDE",
        stage="POST_ACQUISITION",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.commit()

    return org, user, deal


@pytest.mark.asyncio
async def test_telemetry_sync_engine_and_idempotency(db_session: AsyncSession):
    """Verify sync engine execution, checkpoint creation, and idempotency on duplicate runs."""
    org, user, deal = await create_test_env(db_session)

    service = TelemetryService(db_session)

    # 1. Register Salesforce connection
    payload = ExternalConnectionCreate(
        provider=ConnectorProvider.SALESFORCE,
        connection_name="Production Salesforce CRM",
        credentials={
            "instance_url": "https://na139.salesforce.com",
            "access_token": "00D50000000Ixxxx!ARsAQ_test",
        },
    )
    conn_resp = await service.create_connection(
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
        payload=payload,
    )
    assert conn_resp.status == ConnectionStatus.ACTIVE

    # 2. Run initial sync
    sync_engine = TelemetrySyncEngine(db_session)
    run_result = await sync_engine.execute_sync(
        connection_id=conn_resp.id,
        incremental=False,
    )
    assert run_result.status in ("COMPLETED", "SUCCESS")
    assert run_result.records_upserted == 6

    # 3. Idempotency test: Re-run initial sync with same records
    second_result = await sync_engine.execute_sync(
        connection_id=conn_resp.id,
        incremental=False,
    )
    assert second_result.status in ("COMPLETED", "SUCCESS")
    assert second_result.records_upserted == 6

    # 4. Check summary
    summary = await service.get_telemetry_summary(deal_id=deal.id, organization_id=org.id)
    assert summary.active_connections == 1
    assert summary.total_customers == 3
    assert summary.total_arr == 2120000.0  # Total pipeline ARR from Salesforce opportunities (1.2M + 640k + 280k)
    assert summary.total_pipeline_value > 0
    assert summary.freshness == DataFreshnessStatus.LIVE


def test_kpi_engine_calculation_from_telemetry():
    """Verify deterministic KPI calculations directly from canonical telemetry entities."""
    deal_id = uuid.uuid4()
    org_id = uuid.uuid4()

    customers = [
        BusinessCustomer(
            deal_id=deal_id,
            organization_id=org_id,
            source_provider=ConnectorProvider.SALESFORCE.value,
            external_id="CUST-1",
            account_name="Alpha Corp",
            arr_usd=100000.0,
            expansion_potential_usd=10000.0,
            is_churned=False,
            churn_risk_score=0.1,
            health_status="HEALTHY",
        ),
        BusinessCustomer(
            deal_id=deal_id,
            organization_id=org_id,
            source_provider=ConnectorProvider.SALESFORCE.value,
            external_id="CUST-2",
            account_name="Beta Corp",
            arr_usd=50000.0,
            expansion_potential_usd=5000.0,
            is_churned=False,
            churn_risk_score=0.8,
            health_status="AT_RISK",
        ),
    ]

    revenue_events = [
        BusinessRevenueEvent(
            deal_id=deal_id,
            organization_id=org_id,
            source_provider=ConnectorProvider.QUICKBOOKS.value,
            external_id="INV-1",
            amount_usd=200000.0,
            event_date=date(2025, 1, 15),
            fiscal_period="2025-Q1",
            status="PAID",
        ),
    ]

    expenses = [
        BusinessExpense(
            deal_id=deal_id,
            organization_id=org_id,
            source_provider=ConnectorProvider.QUICKBOOKS.value,
            external_id="BILL-1",
            amount_usd=140000.0,
            expense_date=date(2025, 1, 20),
            fiscal_period="2025-Q1",
            category="Hosting",
        ),
    ]

    opportunities = [
        BusinessOpportunity(
            deal_id=deal_id,
            organization_id=org_id,
            source_provider=ConnectorProvider.SALESFORCE.value,
            external_id="OPP-1",
            opportunity_name="Expansion Deal",
            amount_usd=75000.0,
            expected_revenue_usd=37500.0,
            stage="Proposal",
            is_closed=False,
            is_won=False,
        ),
    ]

    kpis = PostDealKPIEngine.compute_kpis_from_telemetry(
        customers=customers,
        opportunities=opportunities,
        revenue_events=revenue_events,
        expenses=expenses,
    )

    assert kpis["total_customers"] == 2
    assert kpis["retained_customers"] == 2
    assert kpis["total_contractual_arr"] == 150000.0
    assert kpis["realized_revenue_usd"] == 200000.0
    assert kpis["realized_expenses_usd"] == 140000.0
    assert kpis["realized_ebitda_usd"] == 60000.0  # 200k - 140k
    assert kpis["ebitda_margin_pct"] == 30.0  # 60k / 200k
    assert kpis["total_pipeline_value_usd"] == 75000.0
    assert kpis["is_deterministic"] is True


@pytest.mark.asyncio
async def test_specialist_agents_with_canonical_telemetry(db_session: AsyncSession):
    """Verify post-deal agents leverage telemetry and generate grounded citations."""
    org, user, deal = await create_test_env(db_session)

    # Create & Sync Salesforce Connection
    service = TelemetryService(db_session)
    sf_conn = await service.create_connection(
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
        payload=ExternalConnectionCreate(
            provider=ConnectorProvider.SALESFORCE,
            connection_name="Salesforce CRM",
            credentials={"instance_url": "https://na139.salesforce.com", "access_token": "tok"},
        ),
    )
    # Create & Sync QuickBooks Connection
    qbo_conn = await service.create_connection(
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
        payload=ExternalConnectionCreate(
            provider=ConnectorProvider.QUICKBOOKS,
            connection_name="QuickBooks Online",
            credentials={"realm_id": "123456", "access_token": "tok"},
        ),
    )

    sync_engine = TelemetrySyncEngine(db_session)
    await sync_engine.execute_sync(sf_conn.id, incremental=False)
    await sync_engine.execute_sync(qbo_conn.id, incremental=False)

    req = AgentExecutionRequest(
        agent_id=AgentId.GROWTH,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )

    # 1. Growth Intelligence Agent
    growth_agent = GrowthIntelligenceAgent(db_session)
    growth_res = await growth_agent.execute(req)
    assert growth_res.status == AgentStatus.SUCCESS
    assert growth_res.metrics["total_arr"] == 21100000.0
    assert growth_res.metrics["telemetry_customers_count"] == 6
    # Verifiable citation
    assert len(growth_res.key_findings[0].citations) >= 1
    assert "Salesforce" in growth_res.key_findings[0].citations[0].document_name

    # 2. Revenue Optimization Agent
    rev_agent = RevenueOptimizationAgent(db_session)
    rev_req = AgentExecutionRequest(
        agent_id=AgentId.REVENUE,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    rev_res = await rev_agent.execute(rev_req)
    assert rev_res.status == AgentStatus.SUCCESS
    assert rev_res.metrics["actual_revenue"] == 2110000.0  # 1.25M + 620k + 240k from contract fixtures
    assert len(rev_res.key_findings[0].citations) >= 1
    assert "QuickBooks" in rev_res.key_findings[0].citations[0].document_name

    # 3. Customer Retention Agent
    ret_agent = CustomerRetentionAgent(db_session)
    ret_req = AgentExecutionRequest(
        agent_id=AgentId.CUSTOMER,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    ret_res = await ret_agent.execute(ret_req)
    assert ret_res.status == AgentStatus.SUCCESS
    assert ret_res.metrics["total_accounts"] == 6
    assert ret_res.metrics["total_arr"] == 21100000.0

    # 4. FP&A Intelligence Agent
    fpa_agent = FPandAAgent(db_session)
    fpa_req = AgentExecutionRequest(
        agent_id=AgentId.FP_AND_A,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    fpa_res = await fpa_agent.execute(fpa_req)
    assert fpa_res.status == AgentStatus.SUCCESS
    assert fpa_res.metrics["actual_ebitda"] > 0
    assert len(fpa_res.key_findings[0].citations) >= 1

    # 5. Performance Monitoring Agent
    mon_agent = PerformanceMonitoringAgent(db_session)
    mon_req = AgentExecutionRequest(
        agent_id=AgentId.MONITORING,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    mon_res = await mon_agent.execute(mon_req)
    assert mon_res.status == AgentStatus.SUCCESS
    assert mon_res.metrics["active_connections_count"] == 2
    assert mon_res.metrics["recent_sync_runs_count"] == 2

    # 6. Cost Optimization Agent
    cost_agent = CostOptimizationAgent(db_session)
    cost_req = AgentExecutionRequest(
        agent_id=AgentId.COST_OPT,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    cost_res = await cost_agent.execute(cost_req)
    assert cost_res.status == AgentStatus.SUCCESS
    assert len(cost_res.key_findings[0].citations) >= 1
    assert "QuickBooks" in cost_res.key_findings[0].citations[0].document_name

    # 7. Operations Intelligence Agent
    ops_agent = OperationsIntelligenceAgent(db_session)
    ops_req = AgentExecutionRequest(
        agent_id=AgentId.OPERATIONS,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    ops_res = await ops_agent.execute(ops_req)
    assert ops_res.status == AgentStatus.SUCCESS
    assert ops_res.metrics["active_connections_count"] == 2
    assert len(ops_res.key_findings[0].citations) >= 1
    assert "Operational Telemetry Connection" in ops_res.key_findings[0].citations[0].document_name

    # 8. Corporate Strategy Agent
    strat_agent = CorporateStrategyAgent(db_session)
    strat_req = AgentExecutionRequest(
        agent_id=AgentId.STRATEGY,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    strat_res = await strat_agent.execute(strat_req)
    assert strat_res.status == AgentStatus.SUCCESS, strat_res.summary
    assert strat_res.metrics["telemetry_revenue_actuals_usd"] == 2110000.0
    assert len(strat_res.key_findings[0].citations) >= 1

    # 9. Marketing Intelligence Agent
    mkt_agent = MarketingIntelligenceAgent(db_session)
    mkt_req = AgentExecutionRequest(
        agent_id=AgentId.MARKETING,
        deal_id=deal.id,
        organization_id=org.id,
        user_id=user.id,
    )
    mkt_res = await mkt_agent.execute(mkt_req)
    assert mkt_res.status == AgentStatus.SUCCESS
    assert mkt_res.metrics["total_accounts"] == 6
    assert mkt_res.metrics["marketing_spend_usd"] > 0
    assert len(mkt_res.key_findings[0].citations) >= 1


@pytest.mark.asyncio
async def test_tenant_and_deal_isolation(db_session: AsyncSession):
    """Verify strict tenant and deal boundary isolation for telemetry data."""
    org_a, user_a, deal_a = await create_test_env(db_session, org_slug="org-a")
    org_b, user_b, deal_b = await create_test_env(db_session, org_slug="org-b")

    service = TelemetryService(db_session)

    # Ingest for Deal A / Org A
    await service.create_connection(
        deal_id=deal_a.id,
        organization_id=org_a.id,
        user_id=user_a.id,
        payload=ExternalConnectionCreate(
            provider=ConnectorProvider.SALESFORCE,
            connection_name="Deal A CRM",
            credentials={"instance_url": "https://na1.sf.com", "access_token": "tok"},
        ),
    )

    # Ingest for Deal B / Org B
    await service.create_connection(
        deal_id=deal_b.id,
        organization_id=org_b.id,
        user_id=user_b.id,
        payload=ExternalConnectionCreate(
            provider=ConnectorProvider.QUICKBOOKS,
            connection_name="Deal B QBO",
            credentials={"realm_id": "999", "access_token": "tok"},
        ),
    )

    # Query Deal A from Org A
    conns_a = await service.list_connections(deal_id=deal_a.id, organization_id=org_a.id)
    assert len(conns_a) == 1
    assert conns_a[0].provider == ConnectorProvider.SALESFORCE

    # Query Deal A from Org B -> Must be isolated (0 results)
    conns_isolated = await service.list_connections(deal_id=deal_a.id, organization_id=org_b.id)
    assert len(conns_isolated) == 0

    # Query Deal B from Org A -> Must be isolated (0 results)
    conns_b_isolated = await service.list_connections(deal_id=deal_b.id, organization_id=org_a.id)
    assert len(conns_b_isolated) == 0
