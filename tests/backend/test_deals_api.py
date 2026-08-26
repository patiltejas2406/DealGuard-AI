"""Tests for Deal & Workspace REST Endpoints with Authentication."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User


@pytest.mark.asyncio
async def test_create_and_list_deals_api(db_session: AsyncSession, async_client: AsyncClient):
    """Verify deal creation and listing via REST API."""
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Pre-seed the organization, role and user in the DB
    org = Organization(id=org_id, name="Insight Partners", slug="insight-partners")
    role = Role(name="ADMIN", description="Tenant Admin", permissions={"all": True})
    user = User(
        id=user_id,
        email="lead@insight.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Deal Partner",
        is_active=True,
    )
    db_session.add(org)
    db_session.add(role)
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(membership)
    await db_session.commit()


    token = create_access_token(subject=str(user_id), org_id=str(org_id), role="ADMIN")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org_id),
    }

    # 1. Create Deal
    payload = {
        "company_name": "CloudOps Automation",
        "company_industry": "Infrastructure Software",
        "deal_title": "Project Velocity: CloudOps Buyout",
        "code_name": "Project Velocity",
        "deal_type": "MAJORITY_ACQUISITION",
        "stage": "PRE_DILIGENCE",
        "target_ev": 85000000.0,
        "currency": "USD",
    }

    response = await async_client.post("/api/v1/deals", json=payload, headers=headers)
    assert response.status_code == 201
    created_deal = response.json()
    assert created_deal["title"] == "Project Velocity: CloudOps Buyout"
    assert created_deal["target_ev"] == 85000000.0
    assert created_deal["target_company"]["name"] == "CloudOps Automation"
    deal_id = created_deal["id"]

    # 2. List Deals
    list_res = await async_client.get("/api/v1/deals", headers=headers)
    assert list_res.status_code == 200
    deals = list_res.json()
    assert len(deals) == 1
    assert deals[0]["id"] == deal_id

    # 3. Get Deal by ID
    get_res = await async_client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == deal_id

    # 4. Check Deal Sub-resources (Documents, Risks, Financials)
    docs_res = await async_client.get(f"/api/v1/deals/{deal_id}/documents", headers=headers)
    assert docs_res.status_code == 200
    assert isinstance(docs_res.json(), list)

    risks_res = await async_client.get(f"/api/v1/deals/{deal_id}/risks", headers=headers)
    assert risks_res.status_code == 200
    risks_json = risks_res.json()
    assert "items" in risks_json and isinstance(risks_json["items"], list)

    fin_res = await async_client.get(f"/api/v1/deals/{deal_id}/financials", headers=headers)
    assert fin_res.status_code == 200
    assert isinstance(fin_res.json(), list)
