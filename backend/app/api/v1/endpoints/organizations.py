"""Organization Governance Endpoints."""

import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_tenant_context
from app.api.v1.schemas.common import OrganizationCreateRequest, OrganizationResponse
from app.core.database import get_db
from app.domains.auth.service import AuthService
from app.domains.common.context import TenantContext

router = APIRouter(prefix="/organizations", tags=["Organizations & Tenancy"])


@router.post(
    "",
    summary="Register New Organization Tenant with Admin Account",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
)
async def register_organization(
    payload: OrganizationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = AuthService(db)
    org, admin_user = await service.register_organization_with_admin(
        org_name=payload.name,
        org_slug=payload.slug,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        admin_full_name=payload.admin_full_name,
    )
    return {
        "success": True,
        "organization": OrganizationResponse.model_validate(org),
        "admin_user_id": str(admin_user.id),
    }


@router.get(
    "/{org_id}",
    summary="Get Organization Details by ID",
    status_code=status.HTTP_200_OK,
    response_model=OrganizationResponse,
)
async def get_organization_details(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(get_tenant_context),
) -> OrganizationResponse:
    if not context.is_superuser and context.organization_id != org_id:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("User is not authorized to access details of this organization.")
    service = AuthService(db)
    org = await service.get_organization(org_id)
    return OrganizationResponse.model_validate(org)

