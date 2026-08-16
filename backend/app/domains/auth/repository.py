"""Auth and Organization Repository Layer with Session Management."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.auth.models import AuthSession, Organization, OrganizationMembership, Role, User
from app.domains.common.models import utc_now


class AuthRepository:
    """Persistence operations for Organizations, Users, Roles, Memberships and Auth Sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_organization_by_id(self, org_id: uuid.UUID) -> Optional[Organization]:
        stmt = (
            select(Organization)
            .where(Organization.id == org_id)
            .options(selectinload(Organization.memberships))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_organization(self, name: str, slug: str, tier: str = "ENTERPRISE") -> Organization:
        org = Organization(name=name, slug=slug, tier=tier)
        self.session.add(org)
        await self.session.flush()
        return org

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.memberships).selectinload(OrganizationMembership.role))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.email == email.lower())
            .options(
                selectinload(User.memberships).selectinload(OrganizationMembership.role),
                selectinload(User.memberships).selectinload(OrganizationMembership.organization),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, email: str, hashed_password: str, full_name: str, is_superuser: bool = False
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_role(self, name: str, description: Optional[str] = None, permissions: Optional[dict] = None) -> Role:
        role = Role(name=name, description=description, permissions=permissions or {})
        self.session.add(role)
        await self.session.flush()
        return role

    async def add_user_to_organization(
        self, organization_id: uuid.UUID, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role_id=role_id,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def get_user_membership(
        self, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[OrganizationMembership]:
        stmt = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_active == True,
            )
            .options(
                selectinload(OrganizationMembership.role),
                selectinload(OrganizationMembership.organization),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_memberships(self, user_id: uuid.UUID) -> List[OrganizationMembership]:
        stmt = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active == True,
            )
            .options(
                selectinload(OrganizationMembership.role),
                selectinload(OrganizationMembership.organization),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Session Management ---

    async def create_auth_session(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        refresh_token_hash: str,
        token_family_id: uuid.UUID,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthSession:
        auth_session = AuthSession(
            user_id=user_id,
            organization_id=organization_id,
            refresh_token_hash=refresh_token_hash,
            token_family_id=token_family_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            last_used_at=utc_now(),
        )
        self.session.add(auth_session)
        await self.session.flush()
        return auth_session

    async def get_session_by_refresh_hash(self, refresh_token_hash: str) -> Optional[AuthSession]:
        stmt = (
            select(AuthSession)
            .where(AuthSession.refresh_token_hash == refresh_token_hash)
            .options(
                selectinload(AuthSession.user),
                selectinload(AuthSession.organization),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session(self, auth_session: AuthSession) -> None:
        auth_session.revoked_at = utc_now()
        await self.session.flush()

    async def revoke_token_family(self, token_family_id: uuid.UUID) -> None:
        """Revoke all sessions in a token family upon reuse anomaly detection."""
        now = utc_now()
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.token_family_id == token_family_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self.session.execute(stmt)
        await self.session.flush()
