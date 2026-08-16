"""REST API Integration Tests for Financial Statements, Metrics, CAGR & QoE."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany


@pytest_asyncio.fixture
async def deal_context(db_session: AsyncSession):
    """Seed authenticated organization, deal workspace, and lead analyst."""
    org = Organization(name="Vista Equity", slug="vista-equity", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="M_AND_A_LEAD", description="Lead", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="lead@vista.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Robert Smith",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role_id=role.id))

    target = TargetCompany(organization_id=org.id, name="SaaSScale Corp", industry="Software")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project SaaSScale Acquisition",
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
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="M_AND_A_LEAD")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_financial_statements_crud_and_metrics_sync(deal_context, async_client: AsyncClient):
    """Verify statement creation, auto-metric synchronization, and validation reporting."""
    deal_id = deal_context["deal"].id
    headers = deal_context["headers"]

    # 1. Post FY2022 Income Statement
    payload_2022 = {
        "statement_type": "INCOME_STATEMENT",
        "fiscal_year": 2022,
        "fiscal_period": "FY2022",
        "line_items": {
            "revenue": 30000000.0,
            "cogs": 9000000.0,
            "operating_expenses": 15000000.0,
            "depreciation_amortization": 2000000.0,
            "ebitda": 6000000.0,
        },
    }
    res_2022 = await async_client.post(
        f"/api/v1/deals/{deal_id}/financials/statements",
        json=payload_2022,
        headers=headers,
    )
    assert res_2022.status_code == 201

    # 2. Post FY2023 Income Statement
    payload_2023 = {
        "statement_type": "INCOME_STATEMENT",
        "fiscal_year": 2023,
        "fiscal_period": "FY2023",
        "line_items": {
            "revenue": 45000000.0,
            "cogs": 12000000.0,
            "operating_expenses": 21000000.0,
            "depreciation_amortization": 3000000.0,
            "ebitda": 12000000.0,
        },
    }
    res_2023 = await async_client.post(
        f"/api/v1/deals/{deal_id}/financials/statements",
        json=payload_2023,
        headers=headers,
    )
    assert res_2023.status_code == 201
    assert res_2023.json()["line_items"]["gross_profit"] == 33000000.0  # 45M - 12M

    # 3. List Statements
    stmts_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials/statements", headers=headers)
    assert stmts_res.status_code == 200
    assert len(stmts_res.json()) == 2

    # 4. Check Synced Metrics
    metrics_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    metric_names = [m["metric_name"] for m in metrics]
    assert "REVENUE" in metric_names
    assert "GROSS_MARGIN" in metric_names
    assert "EBITDA_MARGIN" in metric_names

    # 5. Compute CAGR ($30M -> $45M over 1 year = 50.0%)
    cagr_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials/cagr", headers=headers)
    assert cagr_res.status_code == 200
    assert cagr_res.json()["revenue_cagr"] == 50.0

    # 6. Post Balance Sheet
    bs_payload = {
        "statement_type": "BALANCE_SHEET",
        "fiscal_year": 2023,
        "fiscal_period": "FY2023",
        "line_items": {
            "cash": 8000000.0,
            "accounts_receivable": 5000000.0,
            "inventory": 2000000.0,
            "ppe": 15000000.0,
            "accounts_payable": 4000000.0,
            "long_term_debt": 10000000.0,
            "equity": 16000000.0,
        },
    }
    bs_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/financials/statements",
        json=bs_payload,
        headers=headers,
    )
    assert bs_res.status_code == 201
    assert bs_res.json()["line_items"]["is_balanced"] is True

    # 7. Model Validation Report
    val_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials/validation", headers=headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_qoe_adjustment_lifecycle_and_bridge_api(deal_context, async_client: AsyncClient):
    """Verify QoE adjustment creation, approval, and EBITDA bridge calculation."""
    deal_id = deal_context["deal"].id
    headers = deal_context["headers"]

    # 1. Post Income Statement for reported EBITDA
    await async_client.post(
        f"/api/v1/deals/{deal_id}/financials/statements",
        json={
            "statement_type": "INCOME_STATEMENT",
            "fiscal_year": 2023,
            "fiscal_period": "FY2023",
            "line_items": {"revenue": 45000000.0, "ebitda": 10000000.0},
        },
        headers=headers,
    )

    # 2. Create QoE Add-Back
    adj_payload = {
        "category": "LEGAL_NON_RECURRING",
        "description": "Settlement fees for patent dispute",
        "amount": 750000.0,
        "period": "FY2023",
        "treatment": "ADD_BACK",
        "status": "APPROVED",
    }
    create_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/financials/qoe",
        json=adj_payload,
        headers=headers,
    )
    assert create_res.status_code == 201
    adj_id = create_res.json()["id"]

    # 3. Get QoE Bridge
    bridge_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials/qoe?period=FY2023", headers=headers)
    assert bridge_res.status_code == 200
    bridge = bridge_res.json()["bridge"]
    assert bridge["reported_ebitda"] == 10000000.0
    assert bridge["total_add_backs"] == 750000.0
    assert bridge["adjusted_ebitda"] == 10750000.0

    # 4. Update QoE Adjustment to Rejected
    patch_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/financials/qoe/{adj_id}",
        json={"status": "REJECTED"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "REJECTED"

    # 5. Delete QoE Adjustment
    del_res = await async_client.delete(f"/api/v1/deals/{deal_id}/financials/qoe/{adj_id}", headers=headers)
    assert del_res.status_code == 200
