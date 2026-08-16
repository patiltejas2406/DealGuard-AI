"""Aggregated Domain Models Registry for Alembic and Application Core."""

from app.core.database import Base
from app.domains.common.models import BaseModel, TenantScopedModel
from app.domains.auth.models import Organization, User, Role, OrganizationMembership, AuthSession
from app.domains.deals.models import TargetCompany, Deal, DealMember
from app.domains.documents.models import Document, DocumentVersion, DocumentChunk, Citation
from app.domains.financials.models import FinancialStatement, FinancialMetric, QoEAdjustment
from app.domains.valuation.models import (
    Valuation,
    ValuationAssumption,
    ComparableCompany,
    PrecedentTransaction,
    ValuationOutput,
)
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.audit.models import AuditEvent, HumanReview
from app.domains.jobs.models import JobExecution

__all__ = [
    "Base",
    "BaseModel",
    "TenantScopedModel",
    "Organization",
    "User",
    "Role",
    "OrganizationMembership",
    "AuthSession",
    "TargetCompany",
    "Deal",
    "DealMember",
    "Document",
    "DocumentVersion",
    "DocumentChunk",
    "Citation",
    "FinancialStatement",
    "FinancialMetric",
    "QoEAdjustment",
    "Valuation",
    "ValuationAssumption",
    "ComparableCompany",
    "PrecedentTransaction",
    "ValuationOutput",
    "Risk",
    "RiskEvidence",
    "AuditEvent",
    "HumanReview",
    "JobExecution",
]



