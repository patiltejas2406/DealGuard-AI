"""Comprehensive Test Suite for Phase 10: Synergy Realization & Value Creation Intelligence Engine."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.financials.models import FinancialStatement
from app.domains.synergy.config import (
    SynergyCategory,
    SynergyStatus,
    SynergyType,
    calculate_expected_value,
    calculate_potential_value,
    calculate_value_capture_rate,
    validate_status_transition,
)
from app.domains.synergy.engine import (
    aggregate_synergy_portfolio,
    compute_synergy_5yr_schedule,
    compute_synergy_value_bridge,
)


# ==========================================
# 1. Deterministic Synergy Math & Taxonomy Tests
# ==========================================

def test_potential_and_expected_value_math():
    """Verify potential, expected, and capture rate calculations."""
    # Cost synergy: current spend $10M, target spend $7M -> potential $3M
    pot_cost = calculate_potential_value(10000000.0, 7000000.0, SynergyType.COST.value)
    assert pot_cost == 3000000.0

    # Revenue synergy: baseline $40M, target $48M -> potential $8M
    pot_rev = calculate_potential_value(40000000.0, 48000000.0, SynergyType.REVENUE.value)
    assert pot_rev == 8000000.0

    # Expected value = 3M * 80% realization * 90% probability = 2.16M
    exp_val = calculate_expected_value(3000000.0, 80.0, 90.0)
    assert exp_val == 2160000.0

    # Capture rate = 1.5M realized / 3M potential = 50.0%
    capture_rate = calculate_value_capture_rate(1500000.0, 3000000.0)
    assert capture_rate == 50.0

    # Zero denominator safety
    assert calculate_value_capture_rate(0.0, 0.0) == 0.0


def test_lifecycle_state_machine():
    """Verify valid and invalid state transitions."""
    # Valid transitions
    validate_status_transition(SynergyStatus.IDENTIFIED.value, SynergyStatus.VALIDATED.value)
    validate_status_transition(SynergyStatus.VALIDATED.value, SynergyStatus.PLANNED.value)
    validate_status_transition(SynergyStatus.PLANNED.value, SynergyStatus.IN_PROGRESS.value)
    validate_status_transition(SynergyStatus.IN_PROGRESS.value, SynergyStatus.REALIZED.value)

    # Invalid transitions
    with pytest.raises(ValueError, match="Illegal status transition"):
        validate_status_transition(SynergyStatus.IDENTIFIED.value, SynergyStatus.REALIZED.value)

    with pytest.raises(ValueError, match="Illegal status transition"):
        validate_status_transition(SynergyStatus.IDENTIFIED.value, SynergyStatus.IN_PROGRESS.value)


def test_5yr_phasing_and_margin_propagation():
    """Verify 5-year phasing trajectory and gross margin propagation to incremental EBITDA."""
    class MockSynergy:
        def __init__(self, stype, pot, prob=80.0, real_rate=100.0, int_cost=500000.0):
            self.synergy_type = stype
            self.potential_annual_value = pot
            self.realized_annual_value = 0.0
            self.probability_pct = prob
            self.realization_rate_pct = real_rate
            self.one_time_integration_cost = int_cost
            self.realization_curve = {"year_1": 20.0, "year_2": 50.0, "year_3": 80.0, "year_4": 100.0, "year_5": 100.0}

    synergies = [
        MockSynergy(SynergyType.REVENUE.value, 10000000.0),  # 10M potential rev
        MockSynergy(SynergyType.COST.value, 4000000.0),      # 4M potential cost
    ]

    schedule_data = compute_synergy_5yr_schedule(synergies, base_revenue=50000000.0, base_ebitda=15000000.0, gross_margin_pct=70.0)
    sched = schedule_data["schedule"]
    assert len(sched) == 5

    # Year 1: 20% ramp -> expected rev = 10M * 0.20 * 0.80 = 1.6M, expected cost = 4M * 0.20 * 0.80 = 0.64M
    # EBITDA impact = (1.6M * 0.70) + 0.64M = 1.12M + 0.64M = 1.76M
    assert sched[0]["expected_revenue_synergy"] == 1600000.0
    assert sched[0]["expected_cost_synergy"] == 640000.0
    assert sched[0]["ebitda_impact"] == pytest.approx(1760000.0, abs=1.0)
    assert sched[0]["integration_cost"] > 0  # Allocated upfront


def test_value_creation_waterfall_bridge():
    """Verify Value Creation Waterfall Bridge and positive Decision Score accretion."""
    class MockDeal:
        target_ev = 70000000.0
        currency = "USD"

    class MockStatement:
        statement_type = "INCOME_STATEMENT"
        line_items = {"revenue": 50000000.0, "ebitda": 15000000.0, "gross_profit": 35000000.0}
        is_audited = True

    class MockSynergy:
        def __init__(self, stype, pot, exp):
            self.synergy_type = stype
            self.potential_annual_value = pot
            self.expected_annual_value = exp
            self.realized_annual_value = 0.0
            self.probability_pct = 80.0
            self.realization_rate_pct = 100.0
            self.one_time_integration_cost = 400000.0
            self.realization_curve = {"year_1": 20.0, "year_2": 50.0, "year_3": 80.0, "year_4": 100.0, "year_5": 100.0}

    synergies = [
        MockSynergy(SynergyType.REVENUE.value, 6000000.0, 4800000.0),
        MockSynergy(SynergyType.COST.value, 3000000.0, 2400000.0),
    ]

    bridge = compute_synergy_value_bridge(
        deal=MockDeal(),
        statements=[MockStatement()],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        synergies=synergies,
        wacc_pct=10.0,
    )

    assert bridge["synergy_adjusted_ev"] > bridge["standalone_ev"]
    assert bridge["net_value_created"] > 0
    assert len(bridge["waterfall_steps"]) == 6
    assert bridge["score_delta"] >= 0  # Value creation improves decision score


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_synergy_env(db_session: AsyncSession):
    """Seed deal workspace with target company and authorized lead analyst."""
    org = Organization(name="KKR Flagship Fund", slug="kkr-flagship", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Deal Analyst", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="synergy.lead@kkr.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Henry Kravis",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(membership)
    await db_session.flush()

    target = TargetCompany(
        organization_id=org.id,
        name="Apex Cloud Services",
        industry="Enterprise SaaS",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project Apex Value Creation",
        target_ev=75000000.0,
        currency="USD",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    db_session.add(DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD",
    ))

    # Add Income Statement
    stmt = FinancialStatement(
        organization_id=org.id,
        deal_id=deal.id,
        statement_type="INCOME_STATEMENT",
        period_type="ANNUAL",
        fiscal_year=2023,
        fiscal_period="FY2023",
        source_currency="USD",
        is_audited=True,
        line_items={"revenue": 55000000.0, "ebitda": 16000000.0, "gross_profit": 40000000.0},
    )
    db_session.add(stmt)
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ANALYST")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_synergies_api_workflow(seed_synergy_env, async_client: AsyncClient):
    """Verify complete CRUD, status transitions, waterfall bridge, and actual realization logging."""
    env = seed_synergy_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Create Synergy Opportunity via POST
    create_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/synergies",
        headers=headers,
        json={
            "name": "Cloud Infrastructure Rationalization",
            "description": "Migrate on-prem workloads to consolidated AWS enterprise agreement",
            "synergy_type": "COST",
            "category": "INFRASTRUCTURE",
            "confidence": "HIGH",
            "baseline_value": 8000000.0,
            "target_value": 5500000.0,
            "realization_rate_pct": 90.0,
            "probability_pct": 85.0,
            "one_time_integration_cost": 400000.0,
            "owner": "Sarah Jenkins (CTO)",
        },
    )
    assert create_res.status_code == 201
    syn_data = create_res.json()
    synergy_id = syn_data["id"]
    assert syn_data["potential_annual_value"] == 2500000.0  # 8M - 5.5M
    assert syn_data["expected_annual_value"] == pytest.approx(1912500.0, abs=1.0)  # 2.5M * 0.90 * 0.85
    assert syn_data["status"] == "IDENTIFIED"

    # 2. List Synergies via GET
    list_res = await async_client.get(f"/api/v1/deals/{deal_id}/synergies", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Retrieve Summary via GET
    sum_res = await async_client.get(f"/api/v1/deals/{deal_id}/synergies/summary", headers=headers)
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_opportunities_count"] >= 1
    assert sum_data["total_potential_annual_value"] == 2500000.0

    # 4. Advance Status via PATCH
    status_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/synergies/{synergy_id}/status",
        headers=headers,
        json={"status": "VALIDATED", "notes": "Approved by Infrastructure Diligence Committee"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "VALIDATED"

    # 5. Log Actual Realization via POST
    actual_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/synergies/{synergy_id}/actual",
        headers=headers,
        json={
            "fiscal_period": "Q1-2024",
            "planned_value": 500000.0,
            "actual_value": 620000.0,
            "notes": "Faster migration delivered additional savings",
        },
    )
    assert actual_res.status_code == 200
    act_data = actual_res.json()
    assert act_data["realized_annual_value"] == 620000.0
    assert act_data["value_capture_rate_pct"] > 0

    # 6. Retrieve Value Waterfall Bridge via GET
    bridge_res = await async_client.get(f"/api/v1/deals/{deal_id}/synergies/value-bridge", headers=headers)
    assert bridge_res.status_code == 200
    bridge_data = bridge_res.json()
    assert "waterfall_steps" in bridge_data
    assert bridge_data["synergy_adjusted_ev"] > 0

    # 7. Retrieve 5-Year Realization Schedule via GET
    sched_res = await async_client.get(f"/api/v1/deals/{deal_id}/synergies/realization", headers=headers)
    assert sched_res.status_code == 200
    assert len(sched_res.json()["schedule"]) == 5

    # 8. Delete Synergy via DELETE
    del_res = await async_client.delete(f"/api/v1/deals/{deal_id}/synergies/{synergy_id}", headers=headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_synergies_tenant_isolation(seed_synergy_env, async_client: AsyncClient):
    """Verify strict tenant isolation prevents unauthorized cross-tenant synergy access."""
    env = seed_synergy_env
    deal_id = env["deal"].id

    foreign_org_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()

    foreign_token = create_access_token(
        subject=str(foreign_user_id), org_id=str(foreign_org_id), role="ANALYST"
    )
    foreign_headers = {
        "Authorization": f"Bearer {foreign_token}",
        "X-Organization-ID": str(foreign_org_id),
    }

    # Attempt to list or create synergies from unauthorized tenant
    res = await async_client.get(f"/api/v1/deals/{deal_id}/synergies", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    post_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/synergies",
        headers=foreign_headers,
        json={"name": "Hacked Synergy", "synergy_type": "COST", "category": "HEADCOUNT", "target_value": 1000000.0},
    )
    assert post_res.status_code in [401, 403, 404]
