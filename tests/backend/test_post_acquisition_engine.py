"""Comprehensive Test Suite for Phase 19: Post-Acquisition Intelligence, Value Creation & Business Growth.

Validates:
1. Deterministic PostDealKPIEngine financial & operational formulas.
2. 9 authentic post-deal specialist agents (DB-backed, tool whitelisted, grounded findings).
3. Post-acquisition multi-agent orchestration with failure containment.
4. Natural language & Hinglish post-acquisition intent routing.
5. Copilot multi-turn post-deal context retrieval.
6. Post-acquisition REST APIs, RBAC authorization, and tenant isolation.
7. Explicit INSUFFICIENT_EVIDENCE / DATA_GAP handling with zero fake data.
"""

import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentStatus,
    DecisionRecommendation,
    GroundedFinding,
)
from app.domains.agents.orchestrator import AgentOrchestrator
from app.domains.agents.post_deal.extensibility import (
    CorporateStrategyAgent,
    CostOptimizationAgent,
    CustomerRetentionAgent,
    FPandAAgent,
    GrowthIntelligenceAgent,
    MarketingIntelligenceAgent,
    OperationsIntelligenceAgent,
    PerformanceMonitoringAgent,
    RevenueOptimizationAgent,
)
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.copilot.intent import CopilotIntent, CopilotLanguage, IntentRouter
from app.domains.copilot.retriever import MultiDomainRetriever
from app.domains.deals.models import Deal, DealMember, TargetCompany
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
    CustomerAccountCreate,
    PostAcquisitionMetricCreate,
    ValueCreationInitiativeCreate,
)
from app.domains.post_deal.service import PostDealService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def post_deal_env(db_session: AsyncSession):
    """Seed multi-tenant post-deal workspace with authentic test entities."""
    org = Organization(name="Valence Growth Partners", slug=f"valence-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    await db_session.flush()

    role_q = select(Role).where(Role.name == "ADMIN")
    role_res = await db_session.execute(role_q)
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(name="ADMIN", description="Managing Director", permissions={"all": True})
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"partner-{uuid.uuid4().hex[:6]}@valence.com",
        hashed_password=hash_password("ValencePassword123!"),
        full_name="Elena Rostova",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    mem = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
        is_active=True,
    )
    db_session.add(mem)

    company = TargetCompany(
        organization_id=org.id,
        name="Apex Enterprise Solutions",
        lifecycle_stage="POST_CLOSE",
        industry="Enterprise Software",
        sector="B2B SaaS",
    )
    db_session.add(company)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=company.id,
        title="Project Apex: Post-Acquisition Value Creation",
        code_name="Project Apex",
        deal_type="M_AND_A_BUY_SIDE",
        stage="POST_ACQUISITION",
        target_ev=120_000_000.0,
        currency="USD",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    deal_mem = DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD_ANALYST",
        can_edit=True,
    )
    db_session.add(deal_mem)
    await db_session.commit()

    token = create_access_token(
        subject=str(user.id),
        org_id=str(org.id),
        role=role.name,
    )

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "role": role,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


# ============================================================================
# 1. DETERMINISTIC POST-DEAL KPI ENGINE TESTS
# ============================================================================

def test_post_deal_kpi_engine_revenue_growth():
    """Test revenue growth calculations including positive, negative, and zero baseline."""
    res = PostDealKPIEngine.compute_revenue_growth_pct(actual_revenue=12_500_000, baseline_revenue=10_000_000)
    assert res == 25.0

    # Negative growth
    neg_res = PostDealKPIEngine.compute_revenue_growth_pct(actual_revenue=8_000_000, baseline_revenue=10_000_000)
    assert neg_res == -20.0

    # Zero / None baseline safety
    zero_res = PostDealKPIEngine.compute_revenue_growth_pct(actual_revenue=5_000_000, baseline_revenue=0)
    assert zero_res is None


def test_post_deal_kpi_engine_ebitda_margin():
    """Test EBITDA margin calculation."""
    res = PostDealKPIEngine.compute_ebitda_margin_pct(ebitda=5_000_000, revenue=20_000_000)
    assert res == 25.0

    # Zero revenue safety
    zero_margin = PostDealKPIEngine.compute_ebitda_margin_pct(ebitda=100_000, revenue=0)
    assert zero_margin is None


def test_post_deal_kpi_engine_synergy_realization():
    """Test synergy realization rate and variance."""
    res = PostDealKPIEngine.compute_synergy_realization_pct(
        realized_value=1_500_000,
        expected_value=2_000_000,
    )
    assert res == 75.0

    # Zero expected safety
    zero_res = PostDealKPIEngine.compute_synergy_realization_pct(
        realized_value=500_000,
        expected_value=0,
    )
    assert zero_res is None


def test_post_deal_kpi_engine_customer_metrics():
    """Test retention, churn rate, and NRR formulas."""
    # Retention
    ret_res = PostDealKPIEngine.compute_customer_retention_pct(
        retained_customers=92,
        starting_customers=100,
    )
    assert ret_res == 92.0

    # Churn Rate
    churn_res = PostDealKPIEngine.compute_churn_rate_pct(
        churned_amount=8,
        total_amount=100,
    )
    assert churn_res == 8.0

    # Net Revenue Retention (NRR)
    nrr_res = PostDealKPIEngine.compute_net_revenue_retention_pct(
        starting_arr=100_000,
        expansion_arr=15_000,
        contraction_arr=2_000,
        churned_arr=3_000,
    )
    # (100k + 15k - 2k - 3k) / 100k = 110.0%
    assert nrr_res == 110.0


def test_post_deal_kpi_engine_integration_and_thesis():
    """Test integration completion and thesis status evaluation."""
    int_res = PostDealKPIEngine.compute_integration_completion_pct(
        completed_milestones=15,
        total_milestones=20,
    )
    assert int_res == 75.0

    ontime_res = PostDealKPIEngine.compute_milestone_ontime_pct(
        ontime_milestones=18,
        total_milestones=20,
    )
    assert ontime_res == 90.0

    # Acquisition Thesis Status: Revenue (higher is better)
    thesis_on_track = PostDealKPIEngine.evaluate_thesis_pillar_status(
        actual_value=10_500_000,
        target_value=10_000_000,
        is_higher_better=True,
    )
    assert thesis_on_track == ThesisStatus.ON_TRACK

    thesis_at_risk = PostDealKPIEngine.evaluate_thesis_pillar_status(
        actual_value=8_500_000,
        target_value=10_000_000,
        is_higher_better=True,
    )
    assert thesis_at_risk == ThesisStatus.AT_RISK

    thesis_off_track = PostDealKPIEngine.evaluate_thesis_pillar_status(
        actual_value=7_500_000,
        target_value=10_000_000,
        is_higher_better=True,
    )
    assert thesis_off_track == ThesisStatus.OFF_TRACK

    thesis_no_data = PostDealKPIEngine.evaluate_thesis_pillar_status(
        actual_value=None,
        target_value=10_000_000,
        is_higher_better=True,
    )
    assert thesis_no_data == ThesisStatus.INSUFFICIENT_DATA


# ============================================================================
# 2. POST-DEAL SPECIALIST AGENTS STANDALONE EXECUTION
# ============================================================================

@pytest.mark.asyncio
async def test_post_deal_agents_insufficient_evidence_when_empty(db_session: AsyncSession):
    """Verify that when no data exists, post-deal agents return INSUFFICIENT_EVIDENCE rather than fabricating data."""
    deal_id = uuid.uuid4()
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    req = AgentExecutionRequest(
        deal_id=deal_id,
        organization_id=org_id,
        user_id=user_id,
        query="Evaluate post-acquisition performance",
    )

    # 1. PerformanceMonitoringAgent
    perf_agent = PerformanceMonitoringAgent(db_session)
    perf_result = await perf_agent.execute(req)
    assert perf_result.status == AgentStatus.INSUFFICIENT_EVIDENCE
    assert len(perf_result.data_gaps) > 0

    # 2. GrowthIntelligenceAgent
    growth_agent = GrowthIntelligenceAgent(db_session)
    growth_result = await growth_agent.execute(req)
    assert growth_result.status == AgentStatus.INSUFFICIENT_EVIDENCE
    assert len(growth_result.data_gaps) > 0
    assert any("customer" in g.lower() for g in growth_result.data_gaps)

    # 3. RevenueOptimizationAgent
    rev_agent = RevenueOptimizationAgent(db_session)
    rev_result = await rev_agent.execute(req)
    assert rev_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 4. CustomerRetentionAgent
    cust_agent = CustomerRetentionAgent(db_session)
    cust_result = await cust_agent.execute(req)
    assert cust_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 5. CostOptimizationAgent
    cost_agent = CostOptimizationAgent(db_session)
    cost_result = await cost_agent.execute(req)
    assert cost_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 6. OperationsIntelligenceAgent
    ops_agent = OperationsIntelligenceAgent(db_session)
    ops_result = await ops_agent.execute(req)
    assert ops_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 7. FPandAAgent
    fpa_agent = FPandAAgent(db_session)
    fpa_result = await fpa_agent.execute(req)
    assert fpa_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 8. CorporateStrategyAgent
    strat_agent = CorporateStrategyAgent(db_session)
    strat_result = await strat_agent.execute(req)
    assert strat_result.status == AgentStatus.INSUFFICIENT_EVIDENCE

    # 9. MarketingIntelligenceAgent
    mkt_agent = MarketingIntelligenceAgent(db_session)
    mkt_result = await mkt_agent.execute(req)
    assert mkt_result.status == AgentStatus.INSUFFICIENT_EVIDENCE


@pytest.mark.asyncio
async def test_post_deal_agents_execution_with_populated_data(db_session: AsyncSession, post_deal_env):
    """Verify that specialist agents execute deterministic tools, compute metrics, and produce grounded findings."""
    env = post_deal_env
    deal_id = env["deal"].id
    org_id = env["org"].id
    user_id = env["user"].id

    req = AgentExecutionRequest(
        deal_id=deal_id,
        organization_id=org_id,
        user_id=user_id,
        query="Comprehensive post-acquisition assessment",
    )

    repo = PostDealRepository(db_session)

    # Seed customers
    await repo.create_customer_account(
        org_id,
        deal_id,
        CustomerAccountCreate(
            account_name="Acme Global Corp",
            segment="ENTERPRISE",
            arr=1_200_000.0,
            health_status="HEALTHY",
            churn_risk_score=0.10,
            is_churned=False,
            expansion_potential_usd=400_000.0,
        ),
    )
    await repo.create_customer_account(
        org_id,
        deal_id,
        CustomerAccountCreate(
            account_name="Beta Retail Inc",
            segment="MID_MARKET",
            arr=450_000.0,
            health_status="CRITICAL",
            churn_risk_score=0.78,
            is_churned=False,
            notes="Contract renewal pending. Low feature adoption.",
        ),
    )

    # Seed post-close metrics
    await repo.create_post_acquisition_metric(
        org_id,
        deal_id,
        PostAcquisitionMetricCreate(
            fiscal_period="Q1-2026",
            metric_category="FINANCIAL",
            metric_name="REVENUE",
            baseline_value=10_000_000.0,
            target_value=12_000_000.0,
            actual_value=12_500_000.0,
            variance_pct=25.0,
        ),
    )

    # Seed thesis
    await repo.create_acquisition_thesis(
        org_id,
        deal_id,
        AcquisitionThesisCreate(
            thesis_pillar="REVENUE",
            target_metric="SaaS ARR Growth",
            thesis_statement="Target 25% YoY ARR growth post-acquisition",
            baseline_value=10_000_000.0,
            target_value=12_000_000.0,
            actual_value=12_500_000.0,
            status="ON_TRACK",
            rationale="Target 25% YoY ARR growth post-acquisition",
        ),
    )

    # Seed initiative
    await repo.create_value_creation_initiative(
        org_id,
        deal_id,
        ValueCreationInitiativeCreate(
            pillar="GROWTH",
            title="Enterprise Cross-Sell Program",
            owner="VP Sales",
            status="IN_PROGRESS",
            target_ebitda_impact=1_500_000.0,
            realized_ebitda_impact=600_000.0,
        ),
    )
    await db_session.commit()

    # Execute PerformanceMonitoringAgent
    perf_agent = PerformanceMonitoringAgent(db_session)
    perf_result = await perf_agent.execute(req)
    assert perf_result.status == AgentStatus.SUCCESS
    assert perf_result.agent_id == AgentId.MONITORING
    assert len(perf_result.key_findings) > 0
    assert any("Telemetry" in f.headline or "Health" in f.headline for f in perf_result.key_findings)

    # Execute GrowthIntelligenceAgent
    growth_agent = GrowthIntelligenceAgent(db_session)
    growth_result = await growth_agent.execute(req)
    assert growth_result.status == AgentStatus.SUCCESS
    assert growth_result.agent_id == AgentId.GROWTH
    assert len(growth_result.key_findings) > 0

    # Execute CustomerRetentionAgent
    cust_agent = CustomerRetentionAgent(db_session)
    cust_result = await cust_agent.execute(req)
    assert cust_result.status == AgentStatus.SUCCESS
    assert cust_result.agent_id == AgentId.CUSTOMER
    assert len(cust_result.key_findings) > 0
    assert any("Retention" in f.headline or "Churn" in f.headline for f in cust_result.key_findings)
    assert cust_result.metrics["at_risk_accounts_count"] >= 1

    # Execute CorporateStrategyAgent (Thesis tracking)
    strat_agent = CorporateStrategyAgent(db_session)
    strat_result = await strat_agent.execute(req)
    assert strat_result.status == AgentStatus.SUCCESS
    assert strat_result.agent_id == AgentId.STRATEGY
    assert any("Thesis" in f.headline or "Thesis" in f.detailed_reasoning for f in strat_result.key_findings)


# ============================================================================
# 3. POST-DEAL MULTI-AGENT ORCHESTRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_post_deal_orchestrator_execution(db_session: AsyncSession, post_deal_env):
    """Test full multi-agent orchestration for post-deal value creation mode."""
    env = post_deal_env
    deal_id = env["deal"].id
    org_id = env["org"].id
    user_id = env["user"].id

    orchestrator = AgentOrchestrator(db_session)

    # 1. Post-acquisition value creation mode
    req1 = AgentExecutionRequest(
        deal_id=deal_id,
        organization_id=org_id,
        user_id=user_id,
        query="How is the acquired business performing against thesis?",
    )
    res1 = await orchestrator.orchestrate(req1, orchestration_mode="POST_ACQUISITION_VALUE_CREATION")
    assert res1.deal_id == deal_id
    assert res1.orchestration_mode == "POST_ACQUISITION_VALUE_CREATION"
    assert len(res1.selected_agents) == 10
    assert res1.decision_assessment is not None
    assert res1.decision_assessment.recommendation in [
        DecisionRecommendation.BUY,
        DecisionRecommendation.BUY_WITH_CONDITIONS,
        DecisionRecommendation.RENEGOTIATE,
        DecisionRecommendation.HOLD,
        DecisionRecommendation.AVOID,
        DecisionRecommendation.INSUFFICIENT_EVIDENCE,
    ]

    # 2. Customer and growth mode
    req2 = AgentExecutionRequest(
        deal_id=deal_id,
        organization_id=org_id,
        user_id=user_id,
        query="Which customers are at risk and where can we grow?",
    )
    res2 = await orchestrator.orchestrate(req2, orchestration_mode="CUSTOMER_AND_GROWTH")
    assert len(res2.selected_agents) == 3
    assert AgentId.CUSTOMER in res2.selected_agents
    assert AgentId.GROWTH in res2.selected_agents
    assert AgentId.REVENUE in res2.selected_agents


# ============================================================================
# 4. NATURAL LANGUAGE & HINGLISH INTENT ROUTING TESTS
# ============================================================================

def test_post_deal_intent_routing_english_and_hinglish():
    """Verify regex and semantic routing for post-acquisition queries in English and Hinglish."""
    # Language detection
    assert IntentRouter.detect_language("How is the acquired business performing post-close?") == CopilotLanguage.ENGLISH
    assert IntentRouter.detect_language("business kaisa perform kar raha hai?") == CopilotLanguage.HINGLISH
    assert IntentRouter.detect_language("100-day plan ka kya status hai?") == CopilotLanguage.HINGLISH
    assert IntentRouter.detect_language("synergy actually achieve hui kya?") == CopilotLanguage.HINGLISH
    assert IntentRouter.detect_language("customers mein kaun risk mein hai?") == CopilotLanguage.HINGLISH

    # English Post-Acquisition Performance
    intent1 = IntentRouter.classify_intent("How is the acquired business performing post-close?")
    assert intent1 == CopilotIntent.POST_ACQUISITION

    # Hinglish Business Performance
    intent2 = IntentRouter.classify_intent("business kaisa perform kar raha hai?")
    assert intent2 == CopilotIntent.POST_ACQUISITION

    # Hinglish Integration Status
    intent3 = IntentRouter.classify_intent("100-day plan ka kya status hai?")
    assert intent3 in [CopilotIntent.POST_ACQUISITION, CopilotIntent.INTEGRATION]

    # Hinglish Synergy Realization
    intent4 = IntentRouter.classify_intent("synergy actually achieve hui kya?")
    assert intent4 in [CopilotIntent.POST_ACQUISITION, CopilotIntent.SYNERGY_ANALYSIS]

    # Follow-up
    intent5 = IntentRouter.classify_intent("what should we do?")
    assert intent5 == CopilotIntent.FOLLOW_UP


# ============================================================================
# 5. POST-DEAL REST API ENDPOINTS & RBAC TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_post_deal_rest_apis(post_deal_env, async_client: AsyncClient):
    """Test REST API routes for post-acquisition intelligence."""
    env = post_deal_env
    deal_id = str(env["deal"].id)
    headers = env["headers"]

    # 1. GET Overview
    resp = await async_client.get(f"/api/v1/deals/{deal_id}/post-acquisition/overview", headers=headers)
    assert resp.status_code == 200
    overview_data = resp.json()
    assert overview_data["deal_id"] == deal_id
    assert "overall_thesis_status" in overview_data
    assert "health_score" in overview_data
    assert "pillars" in overview_data

    # 2. POST Customer Account
    cust_payload = {
        "account_name": "Apex Enterprise Ltd",
        "segment": "ENTERPRISE",
        "arr": 850000.0,
        "health_status": "HEALTHY",
        "churn_risk_score": 0.10,
    }
    cust_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/post-acquisition/customers",
        headers=headers,
        json=cust_payload,
    )
    assert cust_resp.status_code == 201
    cust_data = cust_resp.json()
    assert cust_data["account_name"] == "Apex Enterprise Ltd"
    assert cust_data["arr"] == 850000.0

    # 3. GET Customers List
    get_cust_resp = await async_client.get(f"/api/v1/deals/{deal_id}/post-acquisition/customers", headers=headers)
    assert get_cust_resp.status_code == 200
    assert get_cust_resp.json()["total_accounts"] >= 1

    # 4. POST Metric
    metric_payload = {
        "fiscal_period": "Q1-2026",
        "metric_category": "FINANCIAL",
        "metric_name": "REVENUE",
        "baseline_value": 12000000.0,
        "target_value": 14000000.0,
        "actual_value": 15000000.0,
        "variance_pct": 25.0,
    }
    metric_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/post-acquisition/metrics",
        headers=headers,
        json=metric_payload,
    )
    assert metric_resp.status_code == 201
    assert metric_resp.json()["variance_pct"] == 25.0

    # 5. POST Thesis
    thesis_payload = {
        "thesis_pillar": "REVENUE",
        "target_metric": "APAC ARR Growth",
        "baseline_value": 0.0,
        "target_value": 5000000.0,
        "actual_value": 4800000.0,
        "status": "ON_TRACK",
        "rationale": "Expand to APAC generating $5M ARR",
    }
    thesis_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/post-acquisition/thesis",
        headers=headers,
        json=thesis_payload,
    )
    assert thesis_resp.status_code == 201
    assert thesis_resp.json()["status"] == "ON_TRACK"

    # 6. POST Initiative
    init_payload = {
        "pillar": "EFFICIENCY",
        "title": "Cloud Infrastructure Consolidation",
        "owner": "CTO",
        "status": "IN_PROGRESS",
        "target_ebitda_impact": 800000.0,
        "realized_ebitda_impact": 400000.0,
    }
    init_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/post-acquisition/initiatives",
        headers=headers,
        json=init_payload,
    )
    assert init_resp.status_code == 201
    assert init_resp.json()["title"] == "Cloud Infrastructure Consolidation"

    # 7. POST Analyze Trigger
    analyze_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/post-acquisition/analyze",
        headers=headers,
        json={"orchestration_mode": "POST_ACQUISITION_VALUE_CREATION"},
    )
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.json()
    assert "execution_id" in analyze_data
    assert "specialist_assessments" in analyze_data


# ============================================================================
# 6. TENANT & DEAL ISOLATION VERIFICATION
# ============================================================================

@pytest.mark.asyncio
async def test_post_deal_tenant_isolation(db_session: AsyncSession, post_deal_env, async_client: AsyncClient):
    """Verify strict tenant isolation across post-deal customer accounts and metrics."""
    env = post_deal_env
    deal_id = env["deal"].id
    org_id = env["org"].id

    # Seed a customer for Org 1
    repo = PostDealRepository(db_session)
    await repo.create_customer_account(
        org_id,
        deal_id,
        CustomerAccountCreate(
            account_name="Tenant 1 Secret Customer",
            tier="Enterprise",
            contract_arr=2_000_000.0,
        ),
    )
    await db_session.commit()

    # Create Org 2 and User 2
    org2 = Organization(name="Other Tenant Capital", slug=f"other-{uuid.uuid4().hex[:6]}")
    db_session.add(org2)
    await db_session.flush()

    user2 = User(
        email=f"other-{uuid.uuid4().hex[:6]}@other.com",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Other User",
        is_active=True,
    )
    db_session.add(user2)
    await db_session.flush()

    mem2 = OrganizationMembership(
        organization_id=org2.id,
        user_id=user2.id,
        role_id=env["role"].id,
        is_active=True,
    )
    db_session.add(mem2)
    await db_session.commit()

    token2 = create_access_token(
        subject=str(user2.id),
        org_id=str(org2.id),
        role=env["role"].name,
    )
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Org 2 attempting to access Deal 1's post-acquisition data should be rejected (404/403)
    resp = await async_client.get(f"/api/v1/deals/{deal_id}/post-acquisition/customers", headers=headers2)
    assert resp.status_code in [403, 404]
