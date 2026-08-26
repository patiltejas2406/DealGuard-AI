"""Legal, Contract & Compliance Diligence Domain Package."""

from app.domains.legal.models import (
    ComplianceRequirement,
    ContractClause,
    ContractRecord,
    LegalFinding,
)
from app.domains.legal.service import LegalService

__all__ = [
    "ContractRecord",
    "ContractClause",
    "LegalFinding",
    "ComplianceRequirement",
    "LegalService",
]
