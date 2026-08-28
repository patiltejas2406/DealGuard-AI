"""Comprehensive Test Suite for DealGuard AI — Phase 18 Multi-Agent Intelligence Architecture."""

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
    GroundedFinding,
)
from app.domains.agents.orchestrator import AgentOrchestrator
from app.domains.agents.service import AgentOrchestrationService
from app.domains.agents.specialists.finance import FinanceIntelligenceAgent
from app.domains.agents.specialists.legal import LegalIntelligenceAgent
from app.domains.agents.specialists.valuation import ValuationAgent
from app.domains.agents.specialists.risk import RiskIntelligenceAgent
from app.domains.agents.specialists.technology import TechnologyOperationsAgent
from app.domains.agents.specialists.synergy import SynergyValueCreationAgent
from app.domains.agents.specialists.integration import IntegrationIntelligenceAgent
from app.domains.agents.specialists.scenario import ScenarioSimulationAgent
from app.domains.agents.decision_agent import DealDecisionAgent
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Document, DocumentChunk
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.integration.models import IntegrationMilestone, IntegrationProgram, IntegrationWorkstream
from app.domains.legal.models import ContractClause, ContractRecord, LegalFinding
from app.domains.risk.models import Risk
from app.domains.synergy.models import SynergyOpportunity
from app.domains.technology.models import TechnologyFinding


@pytest_asyncio.fixture
async def phase18_seed_data(db_session: AsyncSession):
    """Seed comprehensive test workspace with rich multi-domain deal data."""
    org = Organization(name="Apollo Horizon Capital", slug=f"apollo-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    await db_session.flush()

    role_q = select(Role).where(Role.name == "ADMIN")
    role_res = await db_session.execute(role_q)
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(name="ADMIN", description="Partner", permissions={"all": True})
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"ic-member-{uuid.uuid4().hex[:6]}@apollo.com",
        hashed_password=hash_password("ApolloSecret123!"),
        full_name="Alexander Vance",
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

    target = TargetCompany(
        organization_id=org.id,
        name="AeroByte Cloud Systems",
        lifecycle_stage="DILIGENCE",
        industry="Enterprise SaaS",
        sector="Technology",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project AeroByte Buyout",
        code_name="Project AeroByte",
        deal_type="M_AND_A_BUY_SIDE",
        stage="DILIGENCE",
        target_ev=60000000.0,
        currency="USD",
        decision_score=82.0,
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    deal_mem = DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD_PARTNER",
    )
    db_session.add(deal_mem)

    # Financials
    stmt = FinancialStatement(
        organization_id=org.id,
        deal_id=deal.id,
        statement_type="INCOME_STATEMENT",
        period_type="ANNUAL",
        fiscal_year=2025,
        fiscal_period="FY2025",
        source_currency="USD",
        line_items={
            "revenue": 32000000.0,
            "gross_profit": 25600000.0,
            "ebitda": 9600000.0,
            "net_income": 6400000.0,
        },
    )
    db_session.add(stmt)
    await db_session.flush()

    met_rev = FinancialMetric(
        organization_id=org.id,
        deal_id=deal.id,
        statement_id=stmt.id,
        metric_name="REVENUE",
        value=32000000.0,
        unit="CURRENCY",
        period="FY2025",
    )
    met_ebitda = FinancialMetric(
        organization_id=org.id,
        deal_id=deal.id,
        statement_id=stmt.id,
        metric_name="EBITDA_MARGIN",
        value=0.30,
        unit="PERCENTAGE",
        period="FY2025",
    )
    db_session.add_all([met_rev, met_ebitda])

    qoe = QoEAdjustment(
        organization_id=org.id,
        deal_id=deal.id,
        category="ONE_TIME_EXPENSE",
        description="One-time legacy platform migration costs",
        amount=450000.0,
        period="FY2025",
        treatment="ADD_BACK",
        status="APPROVED",
    )
    db_session.add(qoe)

    # Risks
    risk1 = Risk(
        organization_id=org.id,
        deal_id=deal.id,
        category="CUSTOMER_CONCENTRATION",
        title="Top customer accounts for 34% of ARR",
        description="Loss of key client would impact gross margins significantly.",
        severity=4,
        likelihood=3,
        score=12.0,
        risk_level="HIGH",
        mitigation_strategy="Structure 15% revenue earnout holdback.",
    )
    db_session.add(risk1)

    # Legal
    contract = ContractRecord(
        organization_id=org.id,
        deal_id=deal.id,
        title="Tier-1 Enterprise Master Service Agreement",
        contract_type="CUSTOMER_MSA",
        counterparty="Global Corp",
    )
    db_session.add(contract)
    await db_session.flush()

    clause = ContractClause(
        organization_id=org.id,
        deal_id=deal.id,
        contract_id=contract.id,
        clause_title="Section 14.2 Change of Control Consent",
        clause_text="Assignment or change of control requires 30 days advance written consent.",
        category="CHANGE_OF_CONTROL",
        requires_consent=True,
        fingerprint=f"clause-fp-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(clause)

    # Technology
    tech_find = TechnologyFinding(
        organization_id=org.id,
        deal_id=deal.id,
        category="ARCHITECTURAL",
        title="Single Availability Zone Core Postgres Database",
        technical_fact="Primary production DB lacks multi-region failover automation.",
        severity="HIGH",
        fingerprint=f"tech-fp-{uuid.uuid4().hex[:8]}",
        recommendation="Migrate to AWS Aurora Multi-AZ prior to full traffic cutover.",
    )
    db_session.add(tech_find)

    # Synergies
    syn = SynergyOpportunity(
        organization_id=org.id,
        deal_id=deal.id,
        name="Procurement and Hosting Infrastructure Consolidation",
        synergy_type="COST",
        category="INFRASTRUCTURE",
        potential_annual_value=1200000.0,
        expected_annual_value=1100000.0,
        one_time_integration_cost=300000.0,
        realization_rate_pct=100.0,
    )
    db_session.add(syn)

    # Integration
    program = IntegrationProgram(
        organization_id=org.id,
        deal_id=deal.id,
        name="Project AeroByte 100-Day Integration Program",
    )
    db_session.add(program)
    await db_session.flush()

    workstream = IntegrationWorkstream(
        organization_id=org.id,
        deal_id=deal.id,
        program_id=program.id,
        name="Technology & Infrastructure",
        category="TECHNOLOGY",
        owner="CTO Team",
    )
    db_session.add(workstream)
    await db_session.flush()

    milestone = IntegrationMilestone(
        organization_id=org.id,
        deal_id=deal.id,
        program_id=program.id,
        workstream_id=workstream.id,
        name="Day 30: Multi-AZ Database Migration",
        is_critical_path=True,
        status="NOT_STARTED",
    )
    db_session.add(milestone)

    await db_session.commit()

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "company": target,
    }


@pytest.mark.asyncio
async def test_phase18_orchestrator_dynamic_intent_routing_english(db_session: AsyncSession, phase18_seed_data):
    """Verify AgentOrchestrator routes natural language English intents to specific specialist agents."""
    orchestrator = AgentOrchestrator(db_session)

    # Financial Query
    fin_agents = orchestrator.select_agents_for_request(None, "What is the normalized EBITDA and revenue growth?")
    assert AgentId.FINANCE in fin_agents

    # Risk Query
    risk_agents = orchestrator.select_agents_for_request(None, "What are the key downside risks and threats?")
    assert AgentId.RISK in risk_agents

    # Legal Query
    legal_agents = orchestrator.select_agents_for_request(None, "Are there any change of control consent clauses?")
    assert AgentId.LEGAL in legal_agents

    # Tech Query
    tech_agents = orchestrator.select_agents_for_request(None, "Is there any tech debt, SPOF, or cloud architecture issue?")
    assert AgentId.TECHNOLOGY in tech_agents

    # Synergy Query
    syn_agents = orchestrator.select_agents_for_request(None, "What are the cost savings and synergy opportunities?")
    assert AgentId.SYNERGY in syn_agents


@pytest.mark.asyncio
async def test_phase18_orchestrator_dynamic_intent_routing_hinglish(db_session: AsyncSession, phase18_seed_data):
    """Verify AgentOrchestrator accurately routes Hinglish queries to specific specialist agents."""
    orchestrator = AgentOrchestrator(db_session)

    # Hinglish Risk
    risk_agents = orchestrator.select_agents_for_request(None, "bhai is deal mein sabse bada risk kya hai?")
    assert AgentId.RISK in risk_agents

    # Hinglish Finance
    fin_agents = orchestrator.select_agents_for_request(None, "financials ka scene kya hai? revenue kitna hai?")
    assert AgentId.FINANCE in fin_agents

    # Hinglish Valuation
    val_agents = orchestrator.select_agents_for_request(None, "valuation sahi hai kya? DCF multiple kya bolta hai?")
    assert AgentId.VALUATION in val_agents

    # Hinglish Full Decision
    full_agents = orchestrator.select_agents_for_request(None, "deal Karen ya nahi? Final investment decision kya hai?")
    assert len(full_agents) >= 6


@pytest.mark.asyncio
async def test_phase18_finance_specialist_agent(db_session: AsyncSession, phase18_seed_data):
    """Verify FinanceIntelligenceAgent produces deterministic QoE, revenue, EBITDA, and FACT-tagged findings."""
    agent = FinanceIntelligenceAgent(db_session)
    request = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )
    assessment = await agent.execute(request)

    assert assessment.status == AgentStatus.SUCCESS
    assert assessment.confidence == AgentConfidence.HIGH
    assert assessment.normalized_ebitda is not None
    assert assessment.metrics.get("revenue") == 32000000.0
    assert len(assessment.key_findings) > 0
    assert assessment.key_findings[0].finding_type == "FACT"
    assert assessment.key_findings[0].is_deterministic_calculation is True


@pytest.mark.asyncio
async def test_phase18_legal_specialist_agent(db_session: AsyncSession, phase18_seed_data):
    """Verify LegalIntelligenceAgent analyzes contracts, identifies CoC clauses, and populates data_gaps."""
    agent = LegalIntelligenceAgent(db_session)
    request = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )
    assessment = await agent.execute(request)

    assert assessment.status == AgentStatus.SUCCESS
    assert assessment.change_of_control_clauses_count == 1
    assert assessment.contracts_analyzed_count >= 1
    assert len(assessment.unresolved_issues) >= 1
    assert "written counterparty consents" in assessment.unresolved_issues[0].lower() or "consent" in assessment.unresolved_issues[0].lower()


@pytest.mark.asyncio
async def test_phase18_risk_specialist_agent_with_ml(db_session: AsyncSession, phase18_seed_data):
    """Verify RiskIntelligenceAgent processes deterministic 17-pillar risks and invokes ML downside model."""
    agent = RiskIntelligenceAgent(db_session)
    request = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )
    assessment = await agent.execute(request)

    assert assessment.status == AgentStatus.SUCCESS
    assert assessment.total_risks_identified >= 1
    assert assessment.critical_risks_count >= 0
    assert len(assessment.risks) >= 1
    assert "CUSTOMER_CONCENTRATION" in [r["category"] for r in assessment.risks]


@pytest.mark.asyncio
async def test_phase18_technology_specialist_agent(db_session: AsyncSession, phase18_seed_data):
    """Verify TechnologyOperationsAgent evaluates technical findings, tech debt, and cloud architecture."""
    agent = TechnologyOperationsAgent(db_session)
    request = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )
    assessment = await agent.execute(request)

    assert assessment.status == AgentStatus.SUCCESS
    assert assessment.spof_count >= 0
    assert assessment.cloud_architecture_score > 0.0
    assert len(assessment.key_findings) > 0


@pytest.mark.asyncio
async def test_phase18_synergy_and_integration_specialists(db_session: AsyncSession, phase18_seed_data):
    """Verify Synergy and Integration specialists execute deterministic models."""
    syn_agent = SynergyValueCreationAgent(db_session)
    int_agent = IntegrationIntelligenceAgent(db_session)
    request = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )

    syn_assess = await syn_agent.execute(request)
    assert syn_assess.status == AgentStatus.SUCCESS
    assert syn_assess.annual_run_rate_synergy_usd >= 1000000.0

    int_assess = await int_agent.execute(request)
    assert int_assess.status == AgentStatus.SUCCESS
    assert int_assess.total_milestones >= 1
    assert int_assess.critical_path_milestones_count >= 1


@pytest.mark.asyncio
async def test_phase18_insufficient_evidence_and_data_gaps(db_session: AsyncSession, phase18_seed_data):
    """Verify empty deal records produce INSUFFICIENT_EVIDENCE with explicit data gaps."""
    # Create empty deal with no statements or documents
    empty_deal = Deal(
        organization_id=phase18_seed_data["org"].id,
        target_company_id=phase18_seed_data["company"].id,
        title="Empty Pipeline Deal",
        code_name="Project Ghost",
        deal_type="M_AND_A_BUY_SIDE",
        stage="SCREENING",
        target_ev=0.0,
        currency="USD",
        created_by_id=phase18_seed_data["user"].id,
    )
    db_session.add(empty_deal)
    await db_session.flush()

    req = AgentExecutionRequest(
        deal_id=empty_deal.id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )

    # Test Finance Agent on empty data
    fin_agent = FinanceIntelligenceAgent(db_session)
    fin_res = await fin_agent.execute(req)
    assert fin_res.status == AgentStatus.INSUFFICIENT_EVIDENCE
    assert fin_res.confidence == AgentConfidence.INSUFFICIENT_EVIDENCE
    assert len(fin_res.data_gaps) >= 2

    # Test Legal Agent on empty data
    leg_agent = LegalIntelligenceAgent(db_session)
    leg_res = await leg_agent.execute(req)
    assert leg_res.status == AgentStatus.INSUFFICIENT_EVIDENCE
    assert len(leg_res.data_gaps) >= 2


@pytest.mark.asyncio
async def test_phase18_deal_decision_agent_synthesis(db_session: AsyncSession, phase18_seed_data):
    """Verify DealDecisionAgent synthesizes multi-domain specialist outputs, domain views, and mitigations."""
    decision_agent = DealDecisionAgent(db_session)
    req = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )

    # Run specialist agents
    fin_res = await FinanceIntelligenceAgent(db_session).execute(req)
    risk_res = await RiskIntelligenceAgent(db_session).execute(req)
    leg_res = await LegalIntelligenceAgent(db_session).execute(req)
    tech_res = await TechnologyOperationsAgent(db_session).execute(req)
    val_res = await ValuationAgent(db_session).execute(req)
    syn_res = await SynergyValueCreationAgent(db_session).execute(req)
    int_res = await IntegrationIntelligenceAgent(db_session).execute(req)

    specialist_assessments = {
        AgentId.FINANCE: fin_res,
        AgentId.RISK: risk_res,
        AgentId.LEGAL: leg_res,
        AgentId.TECHNOLOGY: tech_res,
        AgentId.VALUATION: val_res,
        AgentId.SYNERGY: syn_res,
        AgentId.INTEGRATION: int_res,
    }

    decision = await decision_agent.synthesize_decision(req, specialist_assessments)

    assert decision.status == AgentStatus.SUCCESS
    assert decision.recommendation in [
        DecisionRecommendation.BUY,
        DecisionRecommendation.BUY_WITH_CONDITIONS,
        DecisionRecommendation.RENEGOTIATE,
        DecisionRecommendation.HOLD,
    ]
    assert decision.financial_view is not None
    assert decision.risk_view is not None
    assert decision.legal_view is not None
    assert decision.technology_view is not None
    assert decision.valuation_view is not None
    assert len(decision.key_decision_drivers) > 0
    assert len(decision.required_conditions) > 0


@pytest.mark.asyncio
async def test_phase18_failure_containment_and_unavailable_agent(db_session: AsyncSession, phase18_seed_data):
    """Verify that failed/unavailable specialists are contained and noted in the decision synthesis."""
    decision_agent = DealDecisionAgent(db_session)
    req = AgentExecutionRequest(
        deal_id=phase18_seed_data["deal"].id,
        organization_id=phase18_seed_data["org"].id,
        user_id=phase18_seed_data["user"].id,
    )

    fin_res = await FinanceIntelligenceAgent(db_session).execute(req)
    # Simulate failed legal agent
    from app.domains.agents.contract import BaseAgentAssessment
    failed_legal = BaseAgentAssessment(
        agent_id=AgentId.LEGAL,
        domain="LEGAL_CONTRACTS",
        status=AgentStatus.AGENT_UNAVAILABLE,
        summary="Legal parsing service temporarily unavailable.",
        confidence=AgentConfidence.LOW,
        confidence_score=0.0,
    )

    specialist_assessments = {
        AgentId.FINANCE: fin_res,
        AgentId.LEGAL: failed_legal,
    }

    decision = await decision_agent.synthesize_decision(req, specialist_assessments)
    assert decision.status == AgentStatus.SUCCESS
    # Should include conditional note about missing/unavailable legal diligence
    assert any("legal" in c.lower() for c in decision.required_conditions)


@pytest.mark.asyncio
async def test_phase18_api_endpoints(async_client: AsyncClient, phase18_seed_data):
    """Verify Phase 18 REST endpoints for agent analysis, investment decision, and runs."""
    token = create_access_token(
        subject=str(phase18_seed_data["user"].id),
        org_id=str(phase18_seed_data["org"].id),
        role="ADMIN",
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": str(phase18_seed_data["org"].id),
    }
    deal_id = str(phase18_seed_data["deal"].id)

    # 1. POST /deals/{deal_id}/agents/analyze
    analyze_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/analyze",
        headers=headers,
        json={"orchestration_mode": "FINANCIAL_AND_VALUATION", "query": "Check financials and DCF valuation"},
    )
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.json()
    assert "execution_id" in analyze_data
    assert "decision_assessment" in analyze_data

    # 2. POST /deals/{deal_id}/agents/investment-decision
    ic_resp = await async_client.post(
        f"/api/v1/deals/{deal_id}/agents/investment-decision",
        headers=headers,
        json={"orchestration_mode": "FULL_DEAL_DECISION"},
    )
    assert ic_resp.status_code == 200
    ic_data = ic_resp.json()
    exec_id = ic_data["execution_id"]
    assert "recommendation" in ic_data["decision_assessment"]
    assert "financial_view" in ic_data["decision_assessment"]

    # 3. GET /deals/{deal_id}/agents/runs/{run_id}
    run_resp = await async_client.get(
        f"/api/v1/deals/{deal_id}/agents/runs/{exec_id}",
        headers=headers,
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["id"] == exec_id
    assert len(run_data["assessments"]) > 0

    # 4. GET /deals/{deal_id}/agents/runs/{run_id}/agents
    agents_resp = await async_client.get(
        f"/api/v1/deals/{deal_id}/agents/runs/{exec_id}/agents",
        headers=headers,
    )
    assert agents_resp.status_code == 200
    agents_list = agents_resp.json()
    assert isinstance(agents_list, list)
    assert len(agents_list) > 0
