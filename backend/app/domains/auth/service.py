"""Authentication, Session Management & RBAC Domain Services."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.domains.audit.service import AuditService
from app.domains.auth.models import AuthSession, Organization, OrganizationMembership, Role, User
from app.domains.auth.permissions import resolve_permissions_for_role
from app.domains.auth.repository import AuthRepository
from app.domains.common.models import ensure_utc, utc_now



class AuthService:
    """Business operations for User Authentication, Session Rotation, and RBAC."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuthRepository(session)
        self.audit_service = AuditService(session)

    async def register_organization_with_admin(
        self, org_name: str, org_slug: str, admin_email: str, admin_password: str, admin_full_name: str
    ) -> Tuple[Organization, User]:
        existing_org = await self.repo.get_organization_by_slug(org_slug)
        if existing_org:
            raise ConflictException(f"Organization slug '{org_slug}' is already taken.")

        existing_user = await self.repo.get_user_by_email(admin_email)
        if existing_user:
            raise ConflictException(f"User with email '{admin_email}' already exists.")

        admin_role = await self.repo.get_role_by_name("ADMIN")
        if not admin_role:
            admin_role = await self.repo.create_role(
                name="ADMIN",
                description="Institutional Organization Administrator",
                permissions={"all": True},
            )

        org = await self.repo.create_organization(name=org_name, slug=org_slug)
        hashed_pwd = hash_password(admin_password)
        user = await self.repo.create_user(
            email=admin_email,
            hashed_password=hashed_pwd,
            full_name=admin_full_name,
        )
        await self.repo.add_user_to_organization(
            organization_id=org.id,
            user_id=user.id,
            role_id=admin_role.id,
        )
        await self.session.commit()
        return org, user

    async def login(
        self,
        email: str,
        password: str,
        organization_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Authenticate user credentials, establish tenant session, and issue tokens."""
        user = await self.repo.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            # Log failed attempt if user exists (without revealing existence to caller)
            if user:
                await self.audit_service.log_event(
                    organization_id=user.memberships[0].organization_id if user.memberships else uuid.uuid4(),
                    action="LOGIN_FAILURE",
                    entity_type="User",
                    actor_user_id=user.id,
                    ip_address=ip_address,
                    details={"reason": "INVALID_PASSWORD", "email": email.lower()},
                )
                await self.session.commit()
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive. Please contact your organization administrator.")

        # Determine target organization
        memberships = await self.repo.list_user_memberships(user.id)
        if not memberships and not user.is_superuser:
            raise ForbiddenException("User has no active organization memberships.")

        target_membership: Optional[OrganizationMembership] = None
        if organization_id:
            for m in memberships:
                if m.organization_id == organization_id:
                    target_membership = m
                    break
            if not target_membership and not user.is_superuser:
                raise ForbiddenException("User is not an active member of the requested organization.")
        else:
            target_membership = memberships[0] if memberships else None

        active_org = target_membership.organization if target_membership else None
        active_org_id = target_membership.organization_id if target_membership else uuid.uuid4()
        active_role_name = target_membership.role.name if target_membership else "SUPERUSER"

        permissions = resolve_permissions_for_role(active_role_name)

        # Session & Token Generation
        token_family_id = uuid.uuid4()
        expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_str = create_refresh_token(
            subject=str(user.id),
            org_id=str(active_org_id),
            family_id=str(token_family_id),
        )
        refresh_hash = hash_token(refresh_token_str)

        auth_session = await self.repo.create_auth_session(
            user_id=user.id,
            organization_id=active_org_id,
            refresh_token_hash=refresh_hash,
            token_family_id=token_family_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        access_token_str = create_access_token(
            subject=str(user.id),
            org_id=str(active_org_id),
            role=active_role_name,
            session_id=str(auth_session.id),
        )

        # Audit login success
        await self.audit_service.log_event(
            organization_id=active_org_id,
            action="LOGIN_SUCCESS",
            entity_type="User",
            actor_user_id=user.id,
            ip_address=ip_address,
            details={"role": active_role_name, "session_id": str(auth_session.id)},
        )
        await self.session.commit()

        return {
            "access_token": access_token_str,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_superuser": user.is_superuser,
            },
            "organization": {
                "id": str(active_org.id) if active_org else str(active_org_id),
                "name": active_org.name if active_org else "System Admin",
                "slug": active_org.slug if active_org else "system-admin",
            },
            "role": active_role_name,
            "permissions": list(permissions),
        }

    async def refresh_session(
        self,
        refresh_token_str: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotate refresh token and issue a fresh access token with reuse detection."""
        try:
            payload = decode_token(refresh_token_str)
        except Exception:
            raise UnauthorizedException("Invalid refresh token signature or format.")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Token is not a valid refresh token.")

        refresh_hash = hash_token(refresh_token_str)
        auth_session = await self.repo.get_session_by_refresh_hash(refresh_hash)

        # REUSE DETECTION: If session is already revoked, revoke the entire token family!
        if auth_session and auth_session.revoked_at is not None:
            await self.repo.revoke_token_family(auth_session.token_family_id)
            await self.audit_service.log_event(
                organization_id=auth_session.organization_id,
                action="REFRESH_REUSE_DETECTED",
                entity_type="AuthSession",
                actor_user_id=auth_session.user_id,
                ip_address=ip_address,
                details={"token_family_id": str(auth_session.token_family_id)},
            )
            await self.session.commit()
            raise UnauthorizedException("Compromised session token reuse detected. All sessions in this family revoked.")

        if not auth_session:
            raise UnauthorizedException("Session not found or has expired.")

        if ensure_utc(auth_session.expires_at) < utc_now():
            await self.repo.revoke_session(auth_session)
            await self.session.commit()
            raise UnauthorizedException("Refresh session has expired. Please log in again.")


        user = auth_session.user
        if not user or not user.is_active:
            raise UnauthorizedException("User account is inactive.")

        # Invalidate old session
        await self.repo.revoke_session(auth_session)

        # Issue new rotated refresh token in the same token family
        new_expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token_str = create_refresh_token(
            subject=str(user.id),
            org_id=str(auth_session.organization_id),
            family_id=str(auth_session.token_family_id),
        )
        new_refresh_hash = hash_token(new_refresh_token_str)

        new_session = await self.repo.create_auth_session(
            user_id=user.id,
            organization_id=auth_session.organization_id,
            refresh_token_hash=new_refresh_hash,
            token_family_id=auth_session.token_family_id,
            expires_at=new_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Resolve role
        membership = await self.repo.get_user_membership(user.id, auth_session.organization_id)
        role_name = membership.role.name if membership else "MEMBER"
        permissions = resolve_permissions_for_role(role_name)

        new_access_token_str = create_access_token(
            subject=str(user.id),
            org_id=str(auth_session.organization_id),
            role=role_name,
            session_id=str(new_session.id),
        )

        await self.audit_service.log_event(
            organization_id=auth_session.organization_id,
            action="REFRESH",
            entity_type="AuthSession",
            actor_user_id=user.id,
            ip_address=ip_address,
            details={"session_id": str(new_session.id)},
        )
        await self.session.commit()

        return {
            "access_token": new_access_token_str,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": role_name,
            "permissions": list(permissions),
        }

    async def logout(self, refresh_token_str: str, ip_address: Optional[str] = None) -> None:
        """Revoke active refresh session."""
        refresh_hash = hash_token(refresh_token_str)
        auth_session = await self.repo.get_session_by_refresh_hash(refresh_hash)
        if auth_session and auth_session.revoked_at is None:
            await self.repo.revoke_session(auth_session)
            await self.audit_service.log_event(
                organization_id=auth_session.organization_id,
                action="LOGOUT",
                entity_type="AuthSession",
                actor_user_id=auth_session.user_id,
                ip_address=ip_address,
                details={"session_id": str(auth_session.id)},
            )
            await self.session.commit()

    async def get_user_profile(
        self, user_id: uuid.UUID, organization_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Fetch current user identity, active tenant membership, and resolved permissions."""
        user = await self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise NotFoundException("User", user_id)

        memberships = await self.repo.list_user_memberships(user.id)
        if not memberships and not user.is_superuser:
            raise ForbiddenException("User has no active organization memberships.")

        active_membership: Optional[OrganizationMembership] = None
        if organization_id:
            for m in memberships:
                if m.organization_id == organization_id:
                    active_membership = m
                    break
            if not active_membership and not user.is_superuser:
                raise ForbiddenException("User is not an active member of this organization.")
        else:
            active_membership = memberships[0] if memberships else None

        active_org = active_membership.organization if active_membership else None
        active_role_name = active_membership.role.name if active_membership else "SUPERUSER"
        permissions = resolve_permissions_for_role(active_role_name)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_superuser": user.is_superuser,
            },
            "organization": {
                "id": str(active_org.id) if active_org else None,
                "name": active_org.name if active_org else "System",
                "slug": active_org.slug if active_org else "system",
            },
            "role": active_role_name,
            "permissions": list(permissions),
            "accessible_organizations": [
                {
                    "id": str(m.organization_id),
                    "name": m.organization.name,
                    "slug": m.organization.slug,
                    "role": m.role.name,
                }
                for m in memberships
            ],
        }

    async def get_organization(self, org_id: uuid.UUID) -> Organization:
        org = await self.repo.get_organization_by_id(org_id)
        if not org:
            raise NotFoundException("Organization", org_id)
        return org
