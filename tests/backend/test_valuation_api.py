"""REST API Integration Tests for Valuation Intelligence Engine."""

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
    org = Organization(name="Blackstone Capital", slug="blackstone-cap", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="M_AND_A_LEAD", description="Lead", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="valuation.lead@blackstone.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Stephen Schwarzman",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role_id=role.id))

    target = TargetCompany(organization_id=org.id, name="CloudGuard Systems", industry="Security Software")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project CloudGuard Acquisition",
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
async def test_valuation_project_lifecycle_and_dcf_api(deal_context, async_client: AsyncClient):
    """Verify valuation initialization, WACC analysis, DCF calculation, and Football Field Summary."""
    deal_id = deal_context["deal"].id
    headers = deal_context["headers"]

    # 1. Initialize Valuation Project
    init_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation", headers=headers)
    assert init_res.status_code == 200
    val_id = init_res.json()["id"]

    # 2. Add Assumption
    ass_payload = {
        "name": "RISK_FREE_RATE",
        "value": 4.25,
        "unit": "PERCENTAGE",
        "category": "WACC",
        "source_type": "MARKET_DATA",
    }
    ass_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/valuation/assumptions",
        json=ass_payload,
        headers=headers,
    )
    assert ass_res.status_code == 201

    # 3. Get WACC Analysis
    wacc_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation/wacc", headers=headers)
    assert wacc_res.status_code == 200
    assert wacc_res.json()["is_calculable"] is True
    assert wacc_res.json()["wacc"] > 0

    # 4. Get DCF Valuation
    dcf_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation/dcf", headers=headers)
    assert dcf_res.status_code == 200
    dcf_data = dcf_res.json()["dcf"]
    assert dcf_data["implied_enterprise_value"] > 0
    assert len(dcf_data["schedule"]) == 5

    # 5. Add Comparable Company
    comp_payload = {
        "company_name": "Datadog Inc",
        "ticker": "DDOG",
        "revenue": 2000000000.0,
        "ebitda": 450000000.0,
        "enterprise_value": 36000000000.0,
        "status": "INCLUDED",
    }
    comp_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/valuation/comparables",
        json=comp_payload,
        headers=headers,
    )
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]
    assert comp_res.json()["ev_to_revenue"] == 18.0

    # 6. Add Precedent Transaction
    tx_payload = {
        "target_name": "Splunk Inc",
        "acquirer_name": "Cisco",
        "transaction_value": 28000000000.0,
        "revenue": 3800000000.0,
        "ebitda": 800000000.0,
        "status": "INCLUDED",
    }
    tx_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/valuation/precedents",
        json=tx_payload,
        headers=headers,
    )
    assert tx_res.status_code == 201

    # 7. Get Sensitivity Matrix
    sens_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation/sensitivity", headers=headers)
    assert sens_res.status_code == 200
    assert len(sens_res.json()["enterprise_value_matrix"]) == 5

    # 8. Get Valuation Summary / Football Field Range
    sum_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation/summary", headers=headers)
    assert sum_res.status_code == 200
    methods = sum_res.json()["methodologies"]
    assert len(methods) >= 2

    # 9. Model Validation Check
    val_res = await async_client.get(f"/api/v1/deals/{deal_id}/valuation/validation", headers=headers)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "HEALTHY"

    # 10. Delete Comparable Company
    del_res = await async_client.delete(f"/api/v1/deals/{deal_id}/valuation/comparables/{comp_id}", headers=headers)
    assert del_res.status_code == 200
