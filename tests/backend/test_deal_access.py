"""Deal-Level Authorization & Member Scoping Tests."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany


@pytest.mark.asyncio
async def test_deal_member_access_enforcement(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify that a user who belongs to the organization but is NOT a member of a deal
    is denied access (403 Forbidden), while assigned members and admins succeed.
    """
    org = Organization(name="TPG Capital", slug="tpg-cap", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role_analyst = Role(name="FINANCIAL_ANALYST", description="Analyst")
    role_admin = Role(name="ADMIN", description="Admin")
    db_session.add(role_analyst)
    db_session.add(role_admin)
    await db_session.flush()

    # User 1: Assigned Analyst
    user_assigned = User(
        email="assigned@tpg.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Assigned Analyst",
        is_active=True,
    )
    # User 2: Unassigned Analyst
    user_unassigned = User(
        email="unassigned@tpg.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Unassigned Analyst",
        is_active=True,
    )
    # User 3: Org Admin
    user_admin = User(
        email="admin@tpg.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Org Admin",
        is_active=True,
    )
    db_session.add(user_assigned)
    db_session.add(user_unassigned)
    db_session.add(user_admin)
    await db_session.flush()

    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user_assigned.id, role_id=role_analyst.id))
    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user_unassigned.id, role_id=role_analyst.id))
    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user_admin.id, role_id=role_admin.id))
    await db_session.flush()

    # Create confidential target company and deal
    target = TargetCompany(organization_id=org.id, name="Secret Unicorn Corp", industry="Fintech")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project Unicorn M&A",
        created_by_id=user_assigned.id,
    )
    db_session.add(deal)
    await db_session.flush()

    # Assign ONLY user_assigned to the deal
    db_session.add(DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user_assigned.id,
        deal_role="ANALYST",
    ))
    await db_session.commit()

    token_assigned = create_access_token(subject=str(user_assigned.id), org_id=str(org.id), role="FINANCIAL_ANALYST")
    token_unassigned = create_access_token(subject=str(user_unassigned.id), org_id=str(org.id), role="FINANCIAL_ANALYST")
    token_admin = create_access_token(subject=str(user_admin.id), org_id=str(org.id), role="ADMIN")

    headers_assigned = {"Authorization": f"Bearer {token_assigned}", "X-Organization-ID": str(org.id)}
    headers_unassigned = {"Authorization": f"Bearer {token_unassigned}", "X-Organization-ID": str(org.id)}
    headers_admin = {"Authorization": f"Bearer {token_admin}", "X-Organization-ID": str(org.id)}

    # 1. Assigned member requests deal -> 200 OK
    res_assigned = await async_client.get(f"/api/v1/deals/{deal.id}", headers=headers_assigned)
    assert res_assigned.status_code == 200
    assert res_assigned.json()["id"] == str(deal.id)

    # 2. Unassigned member from same org requests deal -> 403 Forbidden
    res_unassigned = await async_client.get(f"/api/v1/deals/{deal.id}", headers=headers_unassigned)
    assert res_unassigned.status_code == 403
    assert "not an authorized team member" in res_unassigned.json()["error"]["message"]

    # 3. Org Admin requests deal -> 200 OK (Admin override)
    res_admin = await async_client.get(f"/api/v1/deals/{deal.id}", headers=headers_admin)
    assert res_admin.status_code == 200
