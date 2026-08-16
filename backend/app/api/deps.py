"""FastAPI Security Dependencies for JWT Authentication, Tenant Context & RBAC."""

import uuid
from typing import Callable, Optional
from fastapi import Depends, Header, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.security import decode_token
from app.domains.auth.models import OrganizationMembership, User
from app.domains.auth.permissions import resolve_permissions_for_role
from app.domains.auth.repository import AuthRepository
from app.domains.common.context import TenantContext
from app.domains.deals.models import Deal, DealMember

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT access token and return the authenticated User entity."""
    if not auth or not auth.credentials:
        raise UnauthorizedException("Authentication required. Please provide a valid Bearer token.")

    payload = decode_token(auth.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedException("Provided token is not a valid access token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Access token missing subject identity.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in token.")

    repo = AuthRepository(db)
    user = await repo.get_user_by_id(user_uuid)
    if not user:
        raise UnauthorizedException("User associated with this token no longer exists.")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive.")

    return user


async def get_tenant_context(
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    x_deal_id: Optional[str] = Header(None, alias="X-Deal-ID"),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """
    Resolve and validate tenant membership for the authenticated user,
    constructing an authoritative TenantContext with active role and permissions.
    """
    repo = AuthRepository(db)
    memberships = await repo.list_user_memberships(current_user.id)

    if not memberships and not current_user.is_superuser:
        raise ForbiddenException("User has no active organization memberships.")

    target_org_id: Optional[uuid.UUID] = None
    if x_organization_id:
        try:
            target_org_id = uuid.UUID(x_organization_id)
        except ValueError:
            raise UnauthorizedException("Invalid X-Organization-ID header format.")
    elif memberships:
        target_org_id = memberships[0].organization_id

    # Verify membership in the target organization
    active_membership: Optional[OrganizationMembership] = None
    if target_org_id:
        for m in memberships:
            if m.organization_id == target_org_id:
                active_membership = m
                break

    if not active_membership and not current_user.is_superuser:
        raise ForbiddenException("User is not authorized for the requested organization.")

    active_org_id = active_membership.organization_id if active_membership else (target_org_id or uuid.uuid4())
    active_role_name = active_membership.role.name if active_membership else "SUPERUSER"
    permissions = resolve_permissions_for_role(active_role_name)

    deal_uuid = uuid.UUID(x_deal_id) if x_deal_id else None

    return TenantContext(
        organization_id=active_org_id,
        user_id=current_user.id,
        roles=[active_role_name],
        permissions=permissions,
        deal_id=deal_uuid,
        is_superuser=current_user.is_superuser,
    )


def require_permission(permission: str) -> Callable:
    """Dependency factory checking if the active TenantContext possesses a required permission."""
    async def permission_checker(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        context.require_permission(permission)
        return context
    return permission_checker


def require_role(role_name: str) -> Callable:
    """Dependency factory checking if the active TenantContext possesses a required role."""
    async def role_checker(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        context.require_role(role_name)
        return context
    return role_checker


async def validate_deal_membership(
    deal_id: uuid.UUID = Path(..., description="Target Deal UUID"),
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """
    Validate that the authenticated user has explicit deal membership,
    or holds organization ADMIN / superuser privileges.
    """
    if context.is_superuser or context.has_role("ADMIN"):
        return context

    stmt = (
        select(DealMember)
        .where(
            DealMember.organization_id == context.organization_id,
            DealMember.deal_id == deal_id,
            DealMember.user_id == context.user_id,
        )
    )
    result = await db.execute(stmt)
    deal_member = result.scalar_one_or_none()

    if not deal_member:
        # Check if deal actually exists in this organization to return safe 403 vs 404
        deal_stmt = select(Deal).where(
            Deal.organization_id == context.organization_id,
            Deal.id == deal_id,
        )
        deal_res = await db.execute(deal_stmt)
        if not deal_res.scalar_one_or_none():
            raise NotFoundException("Deal", deal_id)
        raise ForbiddenException("User is not an authorized team member for this deal workspace.")

    return TenantContext(
        organization_id=context.organization_id,
        user_id=context.user_id,
        roles=context.roles,
        permissions=context.permissions,
        deal_id=deal_id,
        deal_role=deal_member.deal_role,
        is_superuser=context.is_superuser,
    )
