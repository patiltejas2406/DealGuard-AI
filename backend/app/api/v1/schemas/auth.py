"""Authentication Request and Response Pydantic Schemas."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    organization_id: Optional[uuid.UUID] = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_superuser: bool


class OrganizationBriefResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse
    organization: OrganizationBriefResponse
    role: str
    permissions: List[str]


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    permissions: List[str]


class CurrentUserResponse(BaseModel):
    user: UserProfileResponse
    organization: OrganizationBriefResponse
    role: str
    permissions: List[str]
    accessible_organizations: List[OrganizationBriefResponse]
