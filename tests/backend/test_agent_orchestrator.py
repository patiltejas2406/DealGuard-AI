"""Comprehensive Test Suite for Phase 15A: Agentic Intelligence Orchestration Foundation."""

import uuid
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
)
from app.domains.agents.orchestrator import AgentOrchestrator
from app.domains.agents.service import AgentOrchestrationService
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.integration.models import (
    IntegrationProgram,
    IntegrationMilestone,
    IntegrationWorkstream,
)
from app.domains.legal.models import ContractClause, ContractRecord, LegalFinding
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.synergy.models import SynergyOpportunity
from app.domains.technology.models import TechnologyFinding


@pytest_asyncio.fixture
async def seed_agents_env(db_session: AsyncSession):
    """Seed complete multi-domain enterprise deal test fixtures for agent orchestration."""
    org = Organization(name="Acutus Capital Global", slug=f"acutus-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    await db_session.flush()

    role_q = select(Role).where(Role.name == "ADMIN")
    role_res = await db_session.execute(role_q)
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(
            name="ADMIN",
            description="Senior Investment Partner",
            permissions={"all": True},
        )
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"partner-{uuid.uuid4().hex[:6]}@acutus.com",
        hashed_password=hash_password("PartnerPassword123!"),
        full_name="Victoria Sterling",
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
        name="NovaCloud Enterprise Inc.",
        lifecycle_stage="DILIGENCE",
        industry="Cloud Infrastructure",
        sector="Software",
    )
    db_session.add(company)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=company.id,
        title="Project Nova: Cloud Infrastructure Buyout",
        code_name="Project Nova",
        deal_type="M_AND_A_BUY_SIDE",
        stage="DILIGENCE",
        target_ev=75000000.0,
        currency="USD",
        decision_score=78.5,
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

    # 1. Financials
    rev_metric = FinancialMetric(
        organization_id=org.id,
        deal_id=deal.id,
        metric_name="REVENUE",
        period="FY2023",
        value=52000000.0,
        unit="CURRENCY",
    )
    margin_metric = FinancialMetric(
        organization_id=org.id,
        deal_id=deal.id,
        metric_name="EBITDA_MARGIN",
        period="FY2023",
        value=0.22,
        unit="PERCENTAGE",
    )
    qoe = QoEAdjustment(
        organization_id=org.id,
        deal_id=deal.id,
        category="ONE_TIME_EXPENSE",
        description="Non-recurring data center migration costs",
        amount=1800000.0,
        period="FY2023",
        treatment="ADD_BACK",
        status="APPROVED",
    )
    db_session.add_all([rev_metric, margin_metric, qoe])

    # 2. Risk & Evidence
    doc = Document(
        organization_id=org.id,
        deal_id=deal.id,
        name="NovaCloud_FY23_Diligence_Report.pdf",
        file_type="PDF",
        mime_type="application/pdf",
        size_bytes=2400000,
        storage_path="/files/NovaCloud_FY23_Diligence_Report.pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status="PROCESSED",
    )
    db_session.add(doc)
    await db_session.flush()

    cit = Citation(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        page_number=14,
        exact_quote="Customer concentration indicates Top 2 customers generate 34% of consolidated recurring revenue.",
        confidence_score=0.96,
    )
    db_session.add(cit)
    await db_session.flush()

    risk1 = Risk(
        organization_id=org.id,
        deal_id=deal.id,
        company_id=company.id,
        category="CUSTOMER_CONCENTRATION",
        title="Top 2 Customer Revenue Concentration (34%)",
        description="Top two enterprise clients represent $17.6M in ARR.",
        severity=4,
        likelihood=3,
        score=12,
        risk_level="HIGH",
        status="REVIEWED",
    )
    db_session.add(risk1)
    await db_session.flush()

    risk_ev = RiskEvidence(
        organization_id=org.id,
        deal_id=deal.id,
        risk_id=risk1.id,
        citation_id=cit.id,
        relevance_explanation="Direct 10-K Customer Concentration Note 5.",
    )
    db_session.add(risk_ev)

    # 3. Legal
    clause = ContractClause(
        organization_id=org.id,
        deal_id=deal.id,
        category="CHANGE_OF_CONTROL",
        clause_title="Section 8.2 Change of Control Consent",
        clause_text="Assignment requires prior written consent from customer within 30 days.",
        requires_consent=True,
        fingerprint="novacloud_legal_coc_01",
    )
    db_session.add(clause)

    # 4. Tech
    tech = TechnologyFinding(
        organization_id=org.id,
        deal_id=deal.id,
        category="CLOUD_HOSTING_COST",
        title="AWS Reserved Instance Under-Utilization",
        technical_fact="On-demand instances represent 48% of monthly compute spend without savings plans.",
        recommendation="Transition on-demand compute to 3-year Compute Savings Plans.",
        severity="MEDIUM",
        fingerprint="novacloud_tech_01",
    )
    db_session.add(tech)

    # 5. Integration
    prog = IntegrationProgram(
        organization_id=org.id,
        deal_id=deal.id,
        name="Project Nova 100-Day Integration",
        status="ACTIVE",
    )
    db_session.add(prog)
    await db_session.flush()

    ws = IntegrationWorkstream(
        organization_id=org.id,
        deal_id=deal.id,
        program_id=prog.id,
        name="Cloud Infrastructure & Security",
        category="TECHNOLOGY_INFRASTRUCTURE",
        owner="Marcus Vance",
    )
    db_session.add(ws)
    await db_session.flush()

    ms = IntegrationMilestone(
        organization_id=org.id,
        deal_id=deal.id,
        program_id=prog.id,
        workstream_id=ws.id,
        name="KMS Key Envelope Rotation & SOC 2 Certification",
        target_day=30,
        status="IN_PROGRESS",
        is_critical_path=True,
    )
    db_session.add(ms)

    # 6. Synergy
    syn = SynergyOpportunity(
        organization_id=org.id,
        deal_id=deal.id,
        synergy_type="COST",
        category="PROCUREMENT",
        name="Unified AWS Enterprise Discount Program",
        potential_annual_value=3200000.0,
        expected_annual_value=3200000.0,
    )
    db_session.add(syn)

    # 7. Document Chunk
    chunk = DocumentChunk(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        chunk_index=0,
        page_number=14,
        content="Customer concentration indicates Top 2 customers generate 34% of consolidated recurring revenue under contracts renewing in 2025.",
        token_count=35,
    )
    db_session.add(chunk)

    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ADMIN")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "doc": doc,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_list_agents_and_metadata_api(seed_agents_env, async_client: AsyncClient):
    """Verify listing all 18 registered institutional agents with metadata."""
    env = seed_agents_env
    headers = env["headers"]

    res = await async_client.get("/api/v1/agents", headers=headers)
    assert res.status_code == 200
    agents = res.json()
    assert len(agents) >= 9  # 8 specialists + 1 decision agent + extensions

    agent_ids = [a["agent_id"] for a in agents]
    assert "deal_decision_agent" in agent_ids
    assert "finance_intelligence_agent" in agent_ids
    assert "valuation_intelligence_agent" in agent_ids
    assert "risk_intelligence_agent" in agent_ids
    assert "legal_intelligence_agent" in agent_ids
    assert "technology_operations_agent" in agent_ids
    assert "scenario_simulation_agent" in agent_ids
    assert "integration_intelligence_agent" in agent_ids
    assert "synergy_value_creation_agent" in agent_ids

    # Check individual agent metadata
    fin_res = await async_client.get("/api/v1/agents/finance_intelligence_agent", headers=headers)
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["domain"] == "FINANCIALS"
    assert "financial_metrics_tool" in fin_data["allowed_tools"]


@pytest.mark.asyncio
async def test_full_deal_decision_orchestration_api(seed_agents_env, async_client: AsyncClient):
    """Verify complete multi-agent orchestration across all 8 domains and explainable decision synthesis."""
    env = seed_agents_env
    deal_id = env["deal"].id
    headers = env["headers"]

    payload = {
        "orchestration_mode": "FULL_DEAL_DECISION",
        "query": "Synthesize comprehensive institutional acquisition assessment for Project Nova.",
    }

    orch_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/orchestrate",
        headers=headers,
        json=payload,
    )
    assert orch_res.status_code == 200
    result = orch_res.json()

    assert "execution_id" in result
    assert result["deal_id"] == str(deal_id)
    assert len(result["selected_agents"]) == 8

    # Verify all 8 specialist assessments generated
    specs = result["specialist_assessments"]
    assert "finance_intelligence_agent" in specs
    assert "valuation_intelligence_agent" in specs
    assert "risk_intelligence_agent" in specs
    assert "legal_intelligence_agent" in specs
    assert "technology_operations_agent" in specs
    assert "scenario_simulation_agent" in specs
    assert "integration_intelligence_agent" in specs
    assert "synergy_value_creation_agent" in specs

    # Verify Decision Assessment Synthesis
    decision = result["decision_assessment"]
    assert decision["recommendation"] in ["BUY", "BUY_WITH_CONDITIONS", "RENEGOTIATE", "HOLD"]
    assert decision["confidence"] in ["HIGH", "MEDIUM"]
    assert decision["deterministic_decision_score"] is not None
    assert len(decision["positive_drivers"]) > 0
    assert len(decision["negative_drivers"]) > 0
    assert "executive_rationale" in decision
    assert len(decision["citations"]) >= 1

    # Verify citations contain exact text from data room
    cit_quotes = [c["exact_quote"] for c in decision["citations"]]
    assert any("Top 2 customers" in q for q in cit_quotes)


@pytest.mark.asyncio
async def test_selective_mode_orchestration_api(seed_agents_env, async_client: AsyncClient):
    """Verify selective routing (e.g. TECH_AND_INTEGRATION_RISK) invokes only required specialist agents."""
    env = seed_agents_env
    deal_id = env["deal"].id
    headers = env["headers"]

    payload = {
        "orchestration_mode": "TECH_AND_INTEGRATION_RISK",
        "query": "Focus on cloud debt, SPOFs, and 100-day execution bottlenecks.",
    }

    orch_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/orchestrate",
        headers=headers,
        json=payload,
    )
    assert orch_res.status_code == 200
    result = orch_res.json()

    selected = result["selected_agents"]
    assert "technology_operations_agent" in selected
    assert "integration_intelligence_agent" in selected
    assert "risk_intelligence_agent" in selected
    assert "finance_intelligence_agent" not in selected


@pytest.mark.asyncio
async def test_standalone_specialist_agent_run_api(seed_agents_env, async_client: AsyncClient):
    """Verify invoking a single specialist agent directly returns its structured domain assessment."""
    env = seed_agents_env
    deal_id = env["deal"].id
    headers = env["headers"]

    res = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/finance_intelligence_agent/run",
        headers=headers,
        json={"query": "Analyze EBITDA bridge"},
    )
    assert res.status_code == 200
    fin_assess = res.json()
    assert fin_assess["agent_id"] == "finance_intelligence_agent"
    assert fin_assess["status"] == "SUCCESS"
    assert fin_assess["normalized_ebitda"] is not None
    assert fin_assess["deterministic_references"]["reported_revenue_usd"] == 52000000.0


@pytest.mark.asyncio
async def test_agent_executions_history_and_details_api(seed_agents_env, async_client: AsyncClient):
    """Verify listing past orchestration executions and retrieving full execution graph with child assessments."""
    env = seed_agents_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Run Orchestration
    orch_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/orchestrate",
        headers=headers,
        json={"orchestration_mode": "FINANCIAL_AND_VALUATION"},
    )
    assert orch_res.status_code == 200
    exec_id = orch_res.json()["execution_id"]

    # 2. List Executions
    list_res = await async_client.get(f"/api/v1/deals/{deal_id}/agents/executions", headers=headers)
    assert list_res.status_code == 200
    history = list_res.json()
    assert len(history) >= 1
    assert any(e["id"] == exec_id for e in history)

    # 3. Get Full Details
    detail_res = await async_client.get(
        f"/api/v1/deals/{deal_id}/agents/executions/{exec_id}", headers=headers
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == exec_id
    assert len(detail["assessments"]) >= 3


@pytest.mark.asyncio
async def test_agent_orchestration_tenant_isolation(seed_agents_env, async_client: AsyncClient):
    """Verify that unauthorized cross-tenant requests to orchestrate agents on foreign deals are rejected."""
    env = seed_agents_env
    deal_id = env["deal"].id

    foreign_org_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()
    foreign_token = create_access_token(
        subject=str(foreign_user_id), org_id=str(foreign_org_id), role="ADMIN"
    )
    foreign_headers = {
        "Authorization": f"Bearer {foreign_token}",
        "X-Organization-ID": str(foreign_org_id),
    }

    res = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/orchestrate",
        headers=foreign_headers,
        json={"orchestration_mode": "FULL_DEAL_DECISION"},
    )
    assert res.status_code in [401, 403, 404]
