"""Role-Based Access Control (RBAC) Permission Enforcement Tests."""

import uuid
from typing import Tuple
import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User


async def create_user_with_role(
    session: AsyncSession, org: Organization, email: str, role_name: str
) -> Tuple[User, str]:
    """Helper to seed a user with a specific role and return access token."""
    role = await session.execute(Role.__table__.select().where(Role.name == role_name))
    role_obj = role.first()
    if not role_obj:
        role_record = Role(name=role_name, description=f"{role_name} Role")
        session.add(role_record)
        await session.flush()
        role_id = role_record.id
    else:
        role_id = role_obj.id

    user = User(
        email=email,
        hashed_password=hash_password("Pass123!"),
        full_name=f"User {role_name}",
        is_active=True,
    )
    session.add(user)
    await session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role_id,
    )
    session.add(membership)
    await session.commit()

    token = create_access_token(
        subject=str(user.id),
        org_id=str(org.id),
        role=role_name,
    )
    return user, token


from typing import Tuple


@pytest.mark.asyncio
async def test_rbac_analyst_can_create_deals(db_session: AsyncSession, async_client: AsyncClient):
    """Verify FINANCIAL_ANALYST can create a deal."""
    org = Organization(name="Carlyle Group", slug="carlyle-group", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_with_role(
        db_session, org, "analyst@carlyle.demo", "FINANCIAL_ANALYST"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id),
    }

    payload = {
        "company_name": "SaaS Target Inc",
        "company_industry": "Software",
        "deal_title": "Project Alpha",
        "target_ev": 45000000.0,
    }

    res = await async_client.post("/api/v1/deals", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["title"] == "Project Alpha"


@pytest.mark.asyncio
async def test_rbac_reviewer_cannot_create_deals(db_session: AsyncSession, async_client: AsyncClient):
    """Verify REVIEWER is denied when attempting to create a deal (403 Forbidden)."""
    org = Organization(name="General Atlantic", slug="ga-fund", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_with_role(
        db_session, org, "reviewer@ga.demo", "REVIEWER"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id),
    }

    payload = {
        "company_name": "Unauthorized Target",
        "company_industry": "Software",
        "deal_title": "Project Unauthorized",
        "target_ev": 50000000.0,
    }

    res = await async_client.post("/api/v1/deals", json=payload, headers=headers)
    assert res.status_code == 403
    assert "Missing required permission" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_rbac_auditor_cannot_create_deals(db_session: AsyncSession, async_client: AsyncClient):
    """Verify AUDITOR role is read-only and denied on mutation (403 Forbidden)."""
    org = Organization(name="Audit Firm", slug="audit-firm", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    user, token = await create_user_with_role(
        db_session, org, "auditor@audit.demo", "AUDITOR"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id),
    }

    payload = {
        "company_name": "Audit Target",
        "company_industry": "Industrial",
        "deal_title": "Project Audit Block",
    }

    res = await async_client.post("/api/v1/deals", json=payload, headers=headers)
    assert res.status_code == 403
