"""AI Intelligence, RAG Grounding & Evidence Schema Contracts."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CitationRef(BaseModel):
    """Verifiable reference linking an AI extraction or finding to raw evidence."""
    citation_id: Optional[uuid.UUID] = None
    document_id: uuid.UUID
    chunk_id: Optional[uuid.UUID] = None
    document_name: Optional[str] = None
    page_number: int = Field(ge=1, default=1)
    section_title: Optional[str] = None
    exact_quote: str = Field(min_length=1)
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)


class GroundedFinding(BaseModel):
    """Institutional intelligence finding with mandatory evidence citations."""
    finding_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    domain_pillar: str = Field(description="Diligence or corporate pillar: FINANCIAL, RISK, LEGAL, OPERATIONAL, TECH")
    category: str
    headline: str
    detailed_reasoning: str
    finding_type: str = Field(
        default="FACT",
        description="Categorization of finding: FACT (verified data room evidence/calculation), PREDICTION (statistical/ML inference), RECOMMENDATION (expert diligence guidance)"
    )
    severity_level: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.90)
    is_deterministic_calculation: bool = False
    calculation_source_engine: Optional[str] = None
    citations: List[CitationRef] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)



class GroundedRecommendation(BaseModel):
    """Actionable recommendation linked to findings, evidence, and value impact."""
    recommendation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    deal_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    workstream: str  # INTEGRATION, RISK_MITIGATION, SYNERGY_CAPTURE, POST_DEAL_100_DAY
    title: str
    action_item: str
    expected_value_impact: Optional[str] = None
    implementation_timeframe_days: Optional[int] = None
    associated_finding_ids: List[uuid.UUID] = Field(default_factory=list)
    citations: List[CitationRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
