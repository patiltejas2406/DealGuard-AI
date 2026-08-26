"""Technology, Operational & Product Diligence Domain Models."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal, TargetCompany
    from app.domains.documents.models import Citation, Document
    from app.domains.integration.models import IntegrationMilestone, IntegrationWorkstream
    from app.domains.legal.models import ContractRecord
    from app.domains.risk.models import Risk


class TechnologyFinding(TenantScopedModel):
    """Grounded technological, architectural, or technical debt finding."""
    __tablename__ = "technology_findings"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # 30 categories
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    technical_fact: Mapped[str] = mapped_column(Text, nullable=False)
    business_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    likelihood: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False) # HIGH, MEDIUM, LOW
    confidence: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)   # HIGH, MEDIUM, LOW
    monetary_exposure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="IDENTIFIED", nullable=False)  # IDENTIFIED, REQUIRES_REVIEW, REMEDIATION_PLANNED, MITIGATED, ACCEPTED
    linked_risk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risks.id", ondelete="SET NULL"), nullable=True
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
    deal: Mapped["Deal"] = relationship("Deal", backref="technology_findings")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    document: Mapped[Optional["Document"]] = relationship("Document")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")
    linked_risk: Mapped[Optional["Risk"]] = relationship("Risk")
    linked_workstream: Mapped[Optional["IntegrationWorkstream"]] = relationship("IntegrationWorkstream")
    linked_milestone: Mapped[Optional["IntegrationMilestone"]] = relationship("IntegrationMilestone")

    __table_args__ = (
        Index("ix_tech_findings_org_deal", "organization_id", "deal_id"),
        Index("ix_tech_findings_deal_cat", "deal_id", "category"),
        Index("ix_tech_findings_fingerprint", "deal_id", "fingerprint", unique=True),
    )


class OperationalMetric(TenantScopedModel):
    """Deterministic operational KPI, SLA measurement, or cloud cost point."""
    __tablename__ = "operational_metrics"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metric_category: Mapped[str] = mapped_column(String(100), nullable=False)  # UPTIME_SLA, INCIDENT_MTTR, CLOUD_SPEND, BACKUP_RECOVERY
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="%", nullable=False)
    deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ON_TARGET", nullable=False)  # ON_TARGET, DEVIATION, CRITICAL_BREACH
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="operational_metrics")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")

    __table_args__ = (
        Index("ix_op_metrics_deal_cat", "deal_id", "metric_category"),
        Index("ix_op_metrics_fingerprint", "deal_id", "fingerprint", unique=True),
    )


class TechnologyDependency(TenantScopedModel):
    """External API, Cloud Vendor, or Critical Single Point of Failure (SPOF) component."""
    __tablename__ = "technology_dependencies"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(100), nullable=False)  # CLOUD_PROVIDER, SAAS_API, DATABASE, EXTERNAL_SERVICE
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criticality: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    failure_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replacement_difficulty: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW
    is_single_point_of_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    annual_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract_records.id", ondelete="SET NULL"), nullable=True
    )
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="technology_dependencies")
    contract: Mapped[Optional["ContractRecord"]] = relationship("ContractRecord")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")

    __table_args__ = (
        Index("ix_tech_deps_deal_criticality", "deal_id", "criticality"),
        Index("ix_tech_deps_fingerprint", "deal_id", "fingerprint", unique=True),
    )
