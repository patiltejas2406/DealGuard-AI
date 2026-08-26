"""Pydantic Request and Response Schemas for Legal, Contract & Compliance Engine."""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# 1. Contract Schemas
# ==========================================

class ContractRecordCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    contract_type: str = Field(default="CUSTOMER_MSA")
    counterparty: str = Field(..., max_length=255)
    document_id: Optional[uuid.UUID] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    auto_renewal: bool = False
    annual_value: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", max_length=10)
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: str = Field(default="ACTIVE")


class ContractRecordUpdateRequest(BaseModel):
    title: Optional[str] = None
    contract_type: Optional[str] = None
    counterparty: Optional[str] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    annual_value: Optional[float] = None
    currency: Optional[str] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None


class ContractClauseResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    contract_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    category: str
    clause_title: str
    clause_text: str
    normalized_summary: Optional[str] = None
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    requires_consent: bool
    requires_notice: bool
    notice_period_days: Optional[int] = None
    severity: str
    confidence: str
    citation_id: Optional[uuid.UUID] = None
    fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractRecordResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    title: str
    contract_type: str
    counterparty: str
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    auto_renewal: bool
    annual_value: float
    currency: str
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: str
    citation_id: Optional[uuid.UUID] = None
    clauses_count: int = 0
    findings_count: int = 0
    has_change_of_control: bool = False
    requires_consent: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Legal Finding Schemas
# ==========================================

class LegalFindingStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="IDENTIFIED, REQUIRES_REVIEW, ACTION_PLANNED, CONSENT_OBTAINED, MITIGATED, ACCEPTED")
    notes: Optional[str] = None


class LegalFindingResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    contract_id: Optional[uuid.UUID] = None
    clause_id: Optional[uuid.UUID] = None
    finding_type: str
    title: str
    description: Optional[str] = None
    legal_fact: str
    business_impact: Optional[str] = None
    recommendation: Optional[str] = None
    severity: str
    status: str
    monetary_exposure: float
    currency: str
    linked_risk_id: Optional[uuid.UUID] = None
    linked_synergy_id: Optional[uuid.UUID] = None
    linked_workstream_id: Optional[uuid.UUID] = None
    linked_milestone_id: Optional[uuid.UUID] = None
    citation_id: Optional[uuid.UUID] = None
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Compliance Schemas
# ==========================================

class ComplianceRequirementResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    framework: str
    requirement_name: str
    description: Optional[str] = None
    status: str
    confidence: str
    evidence_summary: Optional[str] = None
    citation_ids: Optional[List[Any]] = None
    remediation_action: Optional[str] = None
    remediation_deadline: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Aggregation & Analytical Schemas
# ==========================================

class ChangeOfControlItem(BaseModel):
    contract_id: uuid.UUID
    contract_title: str
    counterparty: str
    contract_type: str
    annual_value: float
    currency: str
    requires_consent: bool
    requires_notice: bool
    notice_period_days: Optional[int] = None
    clause_summary: str
    severity: str
    confidence: str
    status: str
    citation_id: Optional[uuid.UUID] = None
    page_number: Optional[int] = None


class ChangeOfControlConsoleResponse(BaseModel):
    deal_id: uuid.UUID
    total_change_of_control_contracts: int
    total_consents_required: int
    total_revenue_exposed: float
    currency: str = "USD"
    contracts: List[ChangeOfControlItem]


class LegalSummaryResponse(BaseModel):
    deal_id: uuid.UUID
    total_annual_contract_value: float
    revenue_at_risk: float
    revenue_at_risk_pct: float
    total_contracts_reviewed: int
    contracts_at_risk_count: int
    change_of_control_contracts_count: int
    consents_required_count: int
    total_clauses_extracted: int
    total_findings_count: int
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    compliance_total_requirements: int
    compliance_evidence_present: int
    compliance_evidence_missing: int
    compliance_potential_gaps: int
    confidence_distribution: Dict[str, int]


class LegalScanResponse(BaseModel):
    deal_id: uuid.UUID
    contracts_scanned: int
    clauses_extracted: int
    findings_generated: int
    compliance_requirements_checked: int
    message: str
