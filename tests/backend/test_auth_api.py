import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.audit.models import AuditEvent
from app.domains.auth.models import AuthSession, Organization, OrganizationMembership, Role, User


@pytest_asyncio.fixture
async def seeded_auth_user(db_session: AsyncSession):

    """Seed an organization, admin role, and user for auth testing."""
    org = Organization(name="Sequoia Capital", slug="sequoia-cap", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ADMIN", description="Tenant Admin", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="partner@sequoia.demo",
        hashed_password=hash_password("SuperSecret123!"),
        full_name="Roelof Botha",
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
    await db_session.commit()

    return {"org": org, "user": user, "role": role}


@pytest.mark.asyncio
async def test_login_success(seeded_auth_user, async_client: AsyncClient, db_session: AsyncSession):
    """Verify valid login returns tokens, establishes session, and records audit event."""
    payload = {
        "email": "partner@sequoia.demo",
        "password": "SuperSecret123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "partner@sequoia.demo"
    assert data["organization"]["slug"] == "sequoia-cap"
    assert data["role"] == "ADMIN"
    assert "deals:create" in data["permissions"]

    # Verify Audit Event recorded
    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.action == "LOGIN_SUCCESS",
            AuditEvent.actor_user_id == seeded_auth_user["user"].id,
        )
    )
    res = await db_session.execute(stmt)
    event = res.scalar_one_or_none()
    assert event is not None


@pytest.mark.asyncio
async def test_login_invalid_password(seeded_auth_user, async_client: AsyncClient, db_session: AsyncSession):
    """Verify login failure on wrong password with generic error and audit logging."""
    payload = {
        "email": "partner@sequoia.demo",
        "password": "WrongPassword999!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["error"]["message"]

    # Verify Audit Event recorded
    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.action == "LOGIN_FAILURE",
            AuditEvent.actor_user_id == seeded_auth_user["user"].id,
        )
    )
    res = await db_session.execute(stmt)
    event = res.scalar_one_or_none()
    assert event is not None


@pytest.mark.asyncio
async def test_login_unknown_user(async_client: AsyncClient):
    """Verify login failure on non-existent account."""
    payload = {
        "email": "ghost@doesnotexist.demo",
        "password": "AnyPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_refresh_token_lifecycle_and_rotation(seeded_auth_user, async_client: AsyncClient):
    """Verify refresh token rotation and access token renewal."""
    # 1. Initial login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "partner@sequoia.demo", "password": "SuperSecret123!"},
    )
    assert login_res.status_code == 200
    first_refresh = login_res.json()["refresh_token"]

    # 2. Rotate refresh token
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    second_refresh = refresh_data["refresh_token"]
    assert second_refresh != first_refresh
    assert "access_token" in refresh_data


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(seeded_auth_user, async_client: AsyncClient):
    """Verify that replaying a rotated/invalidated refresh token revokes all sessions."""
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "partner@sequoia.demo", "password": "SuperSecret123!"},
    )
    first_refresh = login_res.json()["refresh_token"]

    # 2. Legitimate rotation -> first_refresh is now revoked
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_res.status_code == 200
    second_refresh = refresh_res.json()["refresh_token"]

    # 3. Attacker replays first_refresh (reuse anomaly)
    replay_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert replay_res.status_code == 401
    assert "reuse detected" in replay_res.json()["error"]["message"].lower()

    # 4. Even the second legitimate token should now be invalidated because the family was revoked
    second_replay = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": second_refresh},
    )
    assert second_replay.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_session(seeded_auth_user, async_client: AsyncClient):
    """Verify that logout explicitly revokes the active session."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "partner@sequoia.demo", "password": "SuperSecret123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Subsequent refresh attempt must fail
    subsequent_refresh = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert subsequent_refresh.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_profile(seeded_auth_user, async_client: AsyncClient):
    """Verify /auth/me returns authenticated user, org, and permissions."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "partner@sequoia.demo", "password": "SuperSecret123!"},
    )
    access_token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["user"]["email"] == "partner@sequoia.demo"
    assert profile["organization"]["name"] == "Sequoia Capital"
    assert profile["role"] == "ADMIN"
    assert len(profile["accessible_organizations"]) >= 1
