"""Role-Based Access Control (RBAC) Permission Matrix & Definitions."""

from typing import Dict, List, Set

# Standard Platform Permissions
PERM_ORG_READ = "organization:read"
PERM_ORG_MANAGE = "organization:manage"

PERM_USERS_READ = "users:read"
PERM_USERS_MANAGE = "users:manage"

PERM_DEALS_READ = "deals:read"
PERM_DEALS_CREATE = "deals:create"
PERM_DEALS_UPDATE = "deals:update"
PERM_DEALS_DELETE = "deals:delete"
PERM_DEALS_MANAGE_MEMBERS = "deals:manage_members"

PERM_DOCS_READ = "documents:read"
PERM_DOCS_UPLOAD = "documents:upload"
PERM_DOCS_DELETE = "documents:delete"

PERM_FINANCIALS_READ = "financials:read"
PERM_FINANCIALS_WRITE = "financials:write"

PERM_VALUATION_READ = "valuation:read"
PERM_VALUATION_WRITE = "valuation:write"

PERM_RISKS_READ = "risks:read"
PERM_RISKS_WRITE = "risks:write"
PERM_RISKS_REVIEW = "risks:review"

PERM_AUDIT_READ = "audit:read"

PERM_ANALYSIS_RUN = "analysis:run"
PERM_ANALYSIS_REVIEW = "analysis:review"

ALL_PERMISSIONS: List[str] = [
    PERM_ORG_READ,
    PERM_ORG_MANAGE,
    PERM_USERS_READ,
    PERM_USERS_MANAGE,
    PERM_DEALS_READ,
    PERM_DEALS_CREATE,
    PERM_DEALS_UPDATE,
    PERM_DEALS_DELETE,
    PERM_DEALS_MANAGE_MEMBERS,
    PERM_DOCS_READ,
    PERM_DOCS_UPLOAD,
    PERM_DOCS_DELETE,
    PERM_FINANCIALS_READ,
    PERM_FINANCIALS_WRITE,
    PERM_VALUATION_READ,
    PERM_VALUATION_WRITE,
    PERM_RISKS_READ,
    PERM_RISKS_WRITE,
    PERM_RISKS_REVIEW,
    PERM_AUDIT_READ,
    PERM_ANALYSIS_RUN,
    PERM_ANALYSIS_REVIEW,
]

# Canonical Default Role-to-Permissions Mapping
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "ADMIN": ["*"],  # Super-admin access across all tenant operations
    "M_AND_A_LEAD": [
        PERM_ORG_READ,
        PERM_USERS_READ,
        PERM_DEALS_READ,
        PERM_DEALS_CREATE,
        PERM_DEALS_UPDATE,
        PERM_DEALS_DELETE,
        PERM_DEALS_MANAGE_MEMBERS,
        PERM_DOCS_READ,
        PERM_DOCS_UPLOAD,
        PERM_DOCS_DELETE,
        PERM_FINANCIALS_READ,
        PERM_FINANCIALS_WRITE,
        PERM_VALUATION_READ,
        PERM_VALUATION_WRITE,
        PERM_RISKS_READ,
        PERM_RISKS_WRITE,
        PERM_RISKS_REVIEW,
        PERM_AUDIT_READ,
        PERM_ANALYSIS_RUN,
        PERM_ANALYSIS_REVIEW,
    ],
    "LEAD": [
        PERM_ORG_READ,
        PERM_USERS_READ,
        PERM_DEALS_READ,
        PERM_DEALS_CREATE,
        PERM_DEALS_UPDATE,
        PERM_DEALS_DELETE,
        PERM_DEALS_MANAGE_MEMBERS,
        PERM_DOCS_READ,
        PERM_DOCS_UPLOAD,
        PERM_DOCS_DELETE,
        PERM_FINANCIALS_READ,
        PERM_FINANCIALS_WRITE,
        PERM_VALUATION_READ,
        PERM_VALUATION_WRITE,
        PERM_RISKS_READ,
        PERM_RISKS_WRITE,
        PERM_RISKS_REVIEW,
        PERM_AUDIT_READ,
        PERM_ANALYSIS_RUN,
        PERM_ANALYSIS_REVIEW,
    ],
    "FINANCIAL_ANALYST": [
        PERM_ORG_READ,
        PERM_DEALS_READ,
        PERM_DEALS_CREATE,
        PERM_DEALS_UPDATE,
        PERM_DOCS_READ,
        PERM_DOCS_UPLOAD,
        PERM_FINANCIALS_READ,
        PERM_FINANCIALS_WRITE,
        PERM_VALUATION_READ,
        PERM_VALUATION_WRITE,
        PERM_RISKS_READ,
        PERM_RISKS_WRITE,
        PERM_ANALYSIS_RUN,
    ],
    "ANALYST": [
        PERM_ORG_READ,
        PERM_DEALS_READ,
        PERM_DEALS_CREATE,
        PERM_DEALS_UPDATE,
        PERM_DOCS_READ,
        PERM_DOCS_UPLOAD,
        PERM_FINANCIALS_READ,
        PERM_FINANCIALS_WRITE,
        PERM_VALUATION_READ,
        PERM_VALUATION_WRITE,
        PERM_RISKS_READ,
        PERM_RISKS_WRITE,
        PERM_ANALYSIS_RUN,
    ],
    "REVIEWER": [
        PERM_ORG_READ,
        PERM_DEALS_READ,
        PERM_DOCS_READ,
        PERM_FINANCIALS_READ,
        PERM_VALUATION_READ,
        PERM_RISKS_READ,
        PERM_RISKS_REVIEW,
        PERM_AUDIT_READ,
        PERM_ANALYSIS_REVIEW,
    ],
    "AUDITOR": [
        PERM_ORG_READ,
        PERM_DEALS_READ,
        PERM_DOCS_READ,
        PERM_FINANCIALS_READ,
        PERM_VALUATION_READ,
        PERM_RISKS_READ,
        PERM_AUDIT_READ,
    ],
}



def resolve_permissions_for_role(role_name: str, custom_permissions: List[str] | None = None) -> Set[str]:
    """Resolve active permission set for a given role name and optional custom permissions."""
    role_key = role_name.upper()
    perms: Set[str] = set(ROLE_PERMISSIONS.get(role_key, []))
    if "*" in perms:
        return set(ALL_PERMISSIONS)
    if custom_permissions:
        perms.update(custom_permissions)
    return perms
