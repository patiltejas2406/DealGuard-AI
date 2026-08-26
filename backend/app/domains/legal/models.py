"""Legal, Contract & Compliance Diligence Domain Models."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal, TargetCompany
    from app.domains.documents.models import Citation, Document
    from app.domains.integration.models import IntegrationMilestone, IntegrationWorkstream
    from app.domains.risk.models import Risk
    from app.domains.synergy.models import SynergyOpportunity


class ContractRecord(TenantScopedModel):
    """Core contract metadata and counterparty terms."""
    __tablename__ = "contract_records"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(100), default="CUSTOMER_MSA", nullable=False)
    counterparty: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    annual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    governing_law: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRING_SOON, EXPIRED, TERMINATED
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="contracts")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    document: Mapped[Optional["Document"]] = relationship("Document")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")
    clauses: Mapped[List["ContractClause"]] = relationship(
        "ContractClause", back_populates="contract", cascade="all, delete-orphan"
    )
    findings: Mapped[List["LegalFinding"]] = relationship(
        "LegalFinding", back_populates="contract", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_contracts_org_deal", "organization_id", "deal_id"),
        Index("ix_contracts_deal_type", "deal_id", "contract_type"),
    )


class ContractClause(TenantScopedModel):
    """Extracted contractual clause with evidence citation and change-of-control triggers."""
    __tablename__ = "contract_clauses"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract_records.id", ondelete="CASCADE"), nullable=True, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # 32 categories
    clause_title: Mapped[str] = mapped_column(String(255), nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    requires_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_notice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notice_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)   # HIGH, MEDIUM, LOW
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    contract: Mapped[Optional["ContractRecord"]] = relationship("ContractRecord", back_populates="clauses")
    document: Mapped[Optional["Document"]] = relationship("Document")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")

    __table_args__ = (
        Index("ix_clauses_deal_category", "deal_id", "category"),
        Index("ix_clauses_fingerprint", "deal_id", "fingerprint", unique=True),
    )


class LegalFinding(TenantScopedModel):
    """Actionable legal/compliance finding with business impact and cross-layer linkages."""
    __tablename__ = "legal_findings"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    clause_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract_clauses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    finding_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legal_fact: Mapped[str] = mapped_column(Text, nullable=False)
    business_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status: Mapped[str] = mapped_column(String(50), default="IDENTIFIED", nullable=False)  # IDENTIFIED, REQUIRES_REVIEW, ACTION_PLANNED, CONSENT_OBTAINED, MITIGATED, ACCEPTED
    monetary_exposure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    linked_risk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risks.id", ondelete="SET NULL"), nullable=True
    )
    linked_synergy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("synergy_opportunities.id", ondelete="SET NULL"), nullable=True
    )
    linked_workstream_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_workstreams.id", ondelete="SET NULL"), nullable=True
    )
    linked_milestone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_milestones.id", ondelete="SET NULL"), nullable=True
    )
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    contract: Mapped[Optional["ContractRecord"]] = relationship("ContractRecord", back_populates="findings")
    clause: Mapped[Optional["ContractClause"]] = relationship("ContractClause")
    linked_risk: Mapped[Optional["Risk"]] = relationship("Risk")
    linked_synergy: Mapped[Optional["SynergyOpportunity"]] = relationship("SynergyOpportunity")
    linked_workstream: Mapped[Optional["IntegrationWorkstream"]] = relationship("IntegrationWorkstream")
    linked_milestone: Mapped[Optional["IntegrationMilestone"]] = relationship("IntegrationMilestone")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")

    __table_args__ = (
        Index("ix_findings_deal_type", "deal_id", "finding_type"),
        Index("ix_findings_fingerprint", "deal_id", "fingerprint", unique=True),
    )


class ComplianceRequirement(TenantScopedModel):
    """Compliance framework matrix item (GDPR, SOC2, HIPAA, Licenses) with verified evidence status."""
    __tablename__ = "compliance_requirements"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    framework: Mapped[str] = mapped_column(String(100), nullable=False)  # GDPR, SOC2, HIPAA, CCPA, etc.
    requirement_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="REQUIRES_REVIEW", nullable=False)  # EVIDENCE_PRESENT, EVIDENCE_MISSING, POTENTIAL_GAP, REQUIRES_REVIEW, COMPLIANT
    confidence: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)      # HIGH, MEDIUM, LOW
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_ids: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    remediation_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="compliance_requirements")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")

    __table_args__ = (
        Index("ix_compliance_deal_framework", "deal_id", "framework"),
    )
