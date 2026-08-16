"""Authentication and Session Management REST Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_tenant_context
from app.api.v1.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
)
from app.core.database import get_db
from app.domains.auth.models import User
from app.domains.auth.service import AuthService
from app.domains.common.context import TenantContext

router = APIRouter(prefix="/auth", tags=["Authentication & Session Management"])


@router.post(
    "/login",
    summary="Authenticate User and Create Active Session",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user credentials with Argon2id, establish tenant context,
    generate signed JWT access token, and return rotated refresh token.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service = AuthService(db)
    result = await service.login(
        email=payload.email,
        password=payload.password,
        organization_id=payload.organization_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Set secure HTTP-only cookie for web clients
    response.set_cookie(
        key="dealguard_refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,  # Set True in production SSL
        samesite="lax",
        max_age=7 * 24 * 3600,
    )

    return LoginResponse.model_validate(result)


@router.post(
    "/refresh",
    summary="Rotate Refresh Token and Obtain New Access Token",
    status_code=status.HTTP_200_OK,
    response_model=RefreshResponse,
)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """
    Validate refresh token against active database session, issue rotated token pair,
    and invalidate previous session with token family reuse detection.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service = AuthService(db)
    result = await service.refresh_session(
        refresh_token_str=payload.refresh_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    response.set_cookie(
        key="dealguard_refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )

    return RefreshResponse.model_validate(result)


@router.post(
    "/logout",
    summary="Revoke Active Refresh Session",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
)
async def logout(
    payload: LogoutRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Revoke refresh session in database and clear client authentication cookies."""
    client_ip = request.client.host if request.client else None
    service = AuthService(db)
    await service.logout(refresh_token_str=payload.refresh_token, ip_address=client_ip)

    response.delete_cookie("dealguard_refresh_token")
    return {"success": True, "message": "Session successfully revoked."}


@router.get(
    "/me",
    summary="Get Authenticated User Profile and Active Tenant Permissions",
    status_code=status.HTTP_200_OK,
    response_model=CurrentUserResponse,
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> CurrentUserResponse:
    """Fetch current user identity, organization context, resolved role, and granted permissions."""
    service = AuthService(db)
    profile = await service.get_user_profile(
        user_id=current_user.id,
        organization_id=context.organization_id,
    )
    return CurrentUserResponse.model_validate(profile)
