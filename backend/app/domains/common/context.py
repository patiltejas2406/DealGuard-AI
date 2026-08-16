"""Tenant and Security Context for Request Scoping and Access Enforcement."""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Set
from app.core.exceptions import ForbiddenException


@dataclass(frozen=True)
class TenantContext:
    """Immutable context encapsulating the authenticated user, tenant, permissions, and deal scope."""
    organization_id: uuid.UUID
    user_id: uuid.UUID
    roles: List[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    deal_id: Optional[uuid.UUID] = None
    deal_role: Optional[str] = None
    is_superuser: bool = False

    def has_permission(self, permission: str) -> bool:
        """Check if user holds explicit or admin permission."""
        if self.is_superuser or "*" in self.permissions:
            return True
        return permission in self.permissions

    def has_role(self, role_name: str) -> bool:
        """Check if user possesses the specified role in this tenant."""
        if self.is_superuser:
            return True
        return role_name.upper() in [r.upper() for r in self.roles]

    def require_permission(self, permission: str) -> None:
        """Raise ForbiddenException if the permission is missing."""
        if not self.has_permission(permission):
            raise ForbiddenException(f"Missing required permission: '{permission}'.")

    def require_role(self, role_name: str) -> None:
        """Raise ForbiddenException if the role is missing."""
        if not self.has_role(role_name):
            raise ForbiddenException(f"Missing required role: '{role_name}'.")

    def validate_deal_access(self, target_deal_id: uuid.UUID) -> None:
        """Verify the context is authorized for the target deal."""
        if self.is_superuser or self.has_role("ADMIN"):
            return
        if self.deal_id and self.deal_id != target_deal_id:
            raise ForbiddenException("Tenant context is not authorized for this deal.")
