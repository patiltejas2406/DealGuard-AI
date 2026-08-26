"""Comprehensive Test Suite for Phase 9: What-If Deal Simulation, Sensitivity Surfaces, and Monte Carlo Analysis."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.financials.models import FinancialStatement
from app.domains.risk.models import Risk
from app.domains.simulation.config import (
    DistributionType,
    validate_variable_value,
)
from app.domains.simulation.monte_carlo import run_monte_carlo_simulation
from app.domains.simulation.sensitivity import compute_1d_sensitivity, compute_2d_sensitivity_matrix
from app.domains.simulation.whatif import evaluate_whatif_scenario
from app.domains.valuation.models import Valuation, ValuationOutput


# ==========================================
# 1. Deterministic What-If & Whitelist Tests
# ==========================================

def test_variable_whitelist_and_validation():
    """Verify whitelisted variables validate correctly and unauthorized variables raise errors."""
    assert validate_variable_value("revenue_growth_pct", 15.0) == 15.0
    assert validate_variable_value("ebitda_margin_pct", 22.5) == 22.5
    assert validate_variable_value("wacc_pct", 10.0) == 10.0
    assert validate_variable_value("churn_rate_pct", 5.0) == 5.0

    # Unauthorized variable name
    with pytest.raises(ValueError, match="not in the supported simulation whitelist"):
        validate_variable_value("arbitrary_python_code", 100.0)

    # Out of bounds value
    with pytest.raises(ValueError, match="out of permitted range"):
        validate_variable_value("churn_rate_pct", 150.0)  # Max is 100.0


def test_whatif_deterministic_math_and_immutability():
    """Verify What-If scenario computes exact financial/valuation deltas while leaving base data immutable."""
    class MockDeal:
        target_ev = 80000000.0
        currency = "USD"

    class MockStatement:
        statement_type = "INCOME_STATEMENT"
        line_items = {"revenue": 60000000.0, "ebitda": 18000000.0, "gross_profit": 45000000.0}
        is_audited = True

    base_deal = MockDeal()
    base_stmts = [MockStatement()]

    # Run Downside Scenario (Revenue -10%, EBITDA Margin -400 bps)
    scenario_res = evaluate_whatif_scenario(
        deal=base_deal,
        statements=base_stmts,
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        assumptions_overlay={
            "revenue_growth_pct": -10.0,
            "ebitda_margin_pct": 26.0,  # Base was 30%
            "purchase_price": 80000000.0,
        },
    )

    # Verify Base Immutability
    assert base_deal.target_ev == 80000000.0
    assert base_stmts[0].line_items["revenue"] == 60000000.0
    assert base_stmts[0].line_items["ebitda"] == 18000000.0

    # Verify Scenario Calculations
    assert scenario_res["scenario_case"]["revenue"] == 54000000.0  # 60M * 0.90
    assert scenario_res["deltas"]["revenue_delta_pct"] == -10.0
    assert scenario_res["scenario_case"]["ebitda_margin_pct"] == 26.0
    assert scenario_res["deltas"]["decision_score_delta"] < 0  # Score degraded


# ==========================================
# 2. 1D & 2D Sensitivity Tests
# ==========================================

def test_sensitivity_1d_and_2d_matrices():
    """Verify 1D sweep curves and 2D cross-variable matrices compute valid ranges."""
    class MockDeal:
        target_ev = 70000000.0
        currency = "USD"

    class MockStatement:
        statement_type = "INCOME_STATEMENT"
        line_items = {"revenue": 50000000.0, "ebitda": 15000000.0, "gross_profit": 35000000.0}
        is_audited = True

    # 1D Sweep
    sweep = compute_1d_sensitivity(
        deal=MockDeal(),
        statements=[MockStatement()],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        variable_name="revenue_growth_pct",
        steps=[-10.0, 0.0, 10.0],
    )
    assert sweep["steps_count"] == 3
    assert sweep["curve"][0]["decision_score"] < sweep["curve"][2]["decision_score"]

    # 2D Matrix
    matrix = compute_2d_sensitivity_matrix(
        deal=MockDeal(),
        statements=[MockStatement()],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        row_variable="revenue_growth_pct",
        row_steps=[-10.0, 10.0],
        col_variable="ebitda_margin_pct",
        col_steps=[20.0, 30.0],
    )
    assert len(matrix["matrix_grid"]) == 2
    assert len(matrix["matrix_grid"][0]) == 2
    assert matrix["matrix_grid"][1][1]["implied_ev"] > matrix["matrix_grid"][0][0]["implied_ev"]


# ==========================================
# 3. Monte Carlo Reproducibility & Distributions
# ==========================================

def test_monte_carlo_reproducibility_with_seed():
    """Verify deterministic seed produces identical outputs across simulation runs."""
    class MockDeal:
        target_ev = 75000000.0
        currency = "USD"

    class MockStatement:
        statement_type = "INCOME_STATEMENT"
        line_items = {"revenue": 50000000.0, "ebitda": 15000000.0, "gross_profit": 35000000.0}
        is_audited = True

    dists = {
        "revenue_growth_pct": {
            "distribution_type": "TRIANGULAR",
            "min_val": -10.0,
            "mode_val": 8.0,
            "max_val": 20.0,
        },
        "ebitda_margin_pct": {
            "distribution_type": "NORMAL",
            "mean": 28.0,
            "std_dev": 3.0,
        },
    }

    # Run 1 with Seed 42
    run1 = run_monte_carlo_simulation(
        deal=MockDeal(),
        statements=[MockStatement()],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        variable_distributions=dists,
        iterations=500,
        random_seed=42,
    )

    # Run 2 with Seed 42
    run2 = run_monte_carlo_simulation(
        deal=MockDeal(),
        statements=[MockStatement()],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
        variable_distributions=dists,
        iterations=500,
        random_seed=42,
    )

    # Assert exact deterministic equality
    assert run1["valuation_statistics"]["median"] == run2["valuation_statistics"]["median"]
    assert run1["valuation_statistics"]["percentiles"]["p5"] == run2["valuation_statistics"]["percentiles"]["p5"]
    assert run1["valuation_statistics"]["percentiles"]["p95"] == run2["valuation_statistics"]["percentiles"]["p95"]
    assert run1["decision_score_statistics"]["mean"] == run2["decision_score_statistics"]["mean"]

    # Verify Percentiles Ordering: p5 <= p25 <= p50 <= p75 <= p95
    p = run1["valuation_statistics"]["percentiles"]
    assert p["p5"] <= p["p10"] <= p["p25"] <= p["p50"] <= p["p75"] <= p["p90"] <= p["p95"]


# ==========================================
# 4. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_simulation_env(db_session: AsyncSession):
    """Seed deal workspace with financial statements and lead analyst."""
    org = Organization(name="Blackstone Strategic Growth", slug="blackstone-growth", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Deal Analyst", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="sim.lead@blackstone.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Stephen Schwarzman",
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
        name="DataNexus AI",
        industry="Enterprise Infrastructure",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project DataNexus Acquisition",
        target_ev=65000000.0,
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
        line_items={"revenue": 48000000.0, "ebitda": 14500000.0, "gross_profit": 36000000.0},
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
async def test_simulation_api_workflow(seed_simulation_env, async_client: AsyncClient):
    """Verify complete CRUD for What-If scenarios, sensitivity matrices, and Monte Carlo runs."""
    env = seed_simulation_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Create What-If Scenario via POST
    create_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/scenarios",
        headers=headers,
        json={
            "name": "Management Conservative Case",
            "description": "Lower growth and modest margin compression",
            "scenario_type": "DOWNSIDE",
            "assumptions": {
                "revenue_growth_pct": -5.0,
                "ebitda_margin_pct": 25.0,
            },
        },
    )
    assert create_res.status_code == 201
    scen_data = create_res.json()
    scenario_id = scen_data["id"]
    assert scen_data["name"] == "Management Conservative Case"
    assert "results" in scen_data
    assert scen_data["results"]["scenario_case"]["revenue"] > 0

    # 2. List Scenarios via GET
    list_res = await async_client.get(f"/api/v1/deals/{deal_id}/scenarios", headers=headers)
    assert list_res.status_code == 200
    scenarios_list = list_res.json()
    assert len(scenarios_list) >= 1

    # 3. Retrieve Scenario by ID
    get_res = await async_client.get(f"/api/v1/deals/{deal_id}/scenarios/{scenario_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == scenario_id

    # 4. Re-run Scenario via POST
    run_res = await async_client.post(f"/api/v1/deals/{deal_id}/scenarios/{scenario_id}/run", headers=headers)
    assert run_res.status_code == 200

    # 5. Execute 2D Sensitivity Matrix via POST
    sens_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/scenarios/sensitivity",
        headers=headers,
        json={
            "row_variable": "revenue_growth_pct",
            "row_steps": [-10.0, 0.0, 10.0],
            "col_variable": "ebitda_margin_pct",
            "col_steps": [20.0, 30.0],
        },
    )
    assert sens_res.status_code == 200
    sens_data = sens_res.json()
    assert sens_data["type"] == "2D_MATRIX"
    assert len(sens_data["data"]["matrix_grid"]) == 3

    # 6. Execute Monte Carlo Simulation via POST
    mc_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/scenarios/monte-carlo",
        headers=headers,
        json={
            "iterations": 200,
            "random_seed": 42,
            "variable_distributions": {
                "revenue_growth_pct": {
                    "distribution_type": "TRIANGULAR",
                    "min_val": -15.0,
                    "mode_val": 5.0,
                    "max_val": 20.0,
                },
                "ebitda_margin_pct": {
                    "distribution_type": "NORMAL",
                    "mean": 28.0,
                    "std_dev": 2.5,
                },
            },
        },
    )
    assert mc_res.status_code == 200
    mc_data = mc_res.json()
    assert mc_data["iterations_completed"] == 200
    assert "percentiles" in mc_data["valuation_statistics"]
    assert "band_probabilities" in mc_data

    # 7. Delete Scenario via DELETE
    del_res = await async_client.delete(f"/api/v1/deals/{deal_id}/scenarios/{scenario_id}", headers=headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_simulation_tenant_isolation(seed_simulation_env, async_client: AsyncClient):
    """Verify strict tenant isolation prevents cross-tenant access to scenarios."""
    env = seed_simulation_env
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

    # Attempt to list or create scenarios from unauthorized tenant
    res = await async_client.get(f"/api/v1/deals/{deal_id}/scenarios", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    post_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/scenarios",
        headers=foreign_headers,
        json={"name": "Hacked Case", "assumptions": {"revenue_growth_pct": 5.0}},
    )
    assert post_res.status_code in [401, 403, 404]
