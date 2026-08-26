"""Pydantic Request and Response Schemas for 17-Pillar Risk Intelligence."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.domains.risk.taxonomy import DetectionSource, RiskCategory, RiskLevel, RiskStatus


class CitationDetail(BaseModel):
    """Citation metadata for verified risk evidence."""
    id: uuid.UUID
    document_id: uuid.UUID
    document_name: Optional[str] = None
    page_number: int
    section: Optional[str] = None
    exact_quote: str
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    confidence_score: float = 1.0


class RiskEvidenceDetail(BaseModel):
    """Evidence link attached to a risk finding."""
    id: uuid.UUID
    citation_id: uuid.UUID
    citation: Optional[CitationDetail] = None
    relevance_explanation: Optional[str] = None
    weight: float = 1.0


class RiskCreateRequest(BaseModel):
    """Schema for manual or automated risk creation."""
    category: RiskCategory
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    severity: int = Field(ge=1, le=5, description="1 (Negligible) to 5 (Catastrophic)")
    likelihood: int = Field(ge=1, le=5, description="1 (Rare) to 5 (Almost Certain)")
    status: RiskStatus = RiskStatus.IDENTIFIED
    detection_source: DetectionSource = DetectionSource.MANUAL_ENTRY
    confidence_score: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    mitigation_strategy: Optional[str] = None
    recommendation: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    citation_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)


class RiskUpdateRequest(BaseModel):
    """Schema for updating risk attributes."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=5)
    category: Optional[RiskCategory] = None
    severity: Optional[int] = Field(None, ge=1, le=5)
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[RiskStatus] = None
    mitigation_strategy: Optional[str] = None
    recommendation: Optional[str] = None


class RiskStatusUpdateRequest(BaseModel):
    """Schema for updating review/workflow status with optional rationale."""
    status: RiskStatus
    rationale: Optional[str] = None


class RiskResponse(BaseModel):
    """Complete risk register item response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    category: str
    title: str
    description: str
    severity: int
    likelihood: int
    score: int
    risk_level: str
    status: str
    detection_source: str
    confidence_score: Optional[float] = None
    mitigation_strategy: Optional[str] = None
    recommendation: Optional[str] = None
    fingerprint: Optional[str] = None
    evidence_items: List[RiskEvidenceDetail] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskListResponse(BaseModel):
    """Paginated or filtered list of risk register items."""
    total: int
    items: List[RiskResponse]


class RiskMatrixCell(BaseModel):
    """Summary item inside a 5x5 heatmap cell."""
    id: str
    title: str
    category: str
    severity: int
    likelihood: int
    score: int
    risk_level: str
    status: str


class RiskMatrixResponse(BaseModel):
    """Aggregate quantitative risk heatmap and distribution metrics."""
    total_risks: int
    average_score: float
    level_counts: Dict[str, int]
    category_counts: Dict[str, int]
    status_counts: Dict[str, int]
    matrix_grid: Dict[int, Dict[int, List[RiskMatrixCell]]]


class RiskCategoryInfoResponse(BaseModel):
    """Metadata response for a risk category pillar."""
    id: str
    name: str
    description: str
    signals: List[str]
    default_mitigation: str
    typical_severity_range: str


class RiskDetectionRequest(BaseModel):
    """Configuration options for running automated document risk scanner."""
    categories: Optional[List[RiskCategory]] = None
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.60)
    auto_commit: bool = True


class RiskDetectionResultItem(BaseModel):
    """Single risk detected during document scanning."""
    category: str
    title: str
    description: str
    severity: int
    likelihood: int
    score: int
    risk_level: str
    confidence_score: float
    recommendation: str
    exact_quote: str
    document_id: uuid.UUID
    page_number: int


class RiskDetectionResponse(BaseModel):
    """Summary of automated risk scanner results."""
    deal_id: uuid.UUID
    scanned_chunks_count: int
    detected_count: int
    created_count: int
    duplicates_skipped: int
    risks: List[RiskResponse]
