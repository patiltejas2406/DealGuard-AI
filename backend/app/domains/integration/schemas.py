"""Pydantic Schemas for 100-Day Post-Acquisition Integration Execution APIs."""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IntegrationProgramCreateRequest(BaseModel):
    """Payload to initialize 100-day integration program."""
    name: str = Field("100-Day Value Creation & Integration Plan", max_length=255)
    close_date: Optional[date] = None
    day_0_date: Optional[date] = None
    day_100_date: Optional[date] = None
    current_day_offset: int = Field(1, ge=0, le=365)
    executive_sponsor: Optional[str] = Field(None, max_length=100)
    objectives: Optional[Dict[str, Any]] = None


class IntegrationProgramUpdateRequest(BaseModel):
    """Payload to update program parameters."""
    name: Optional[str] = None
    status: Optional[str] = None
    close_date: Optional[date] = None
    current_day_offset: Optional[int] = None
    executive_sponsor: Optional[str] = None
    objectives: Optional[Dict[str, Any]] = None


class WorkstreamCreateRequest(BaseModel):
    """Payload to register a new integration workstream."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: str = Field(..., description="17-category taxonomy code (e.g. FINANCE_ACCOUNTING, TECHNOLOGY_IT)")
    owner: Optional[str] = None
    executive_sponsor: Optional[str] = None
    priority: str = Field("MEDIUM", description="CRITICAL, HIGH, MEDIUM, LOW")
    start_day: int = Field(0, ge=0, le=100)
    target_day: int = Field(100, ge=0, le=100)
    risk_level: str = Field("LOW", description="HIGH, MEDIUM, LOW")
    linked_synergy_ids: Optional[List[str]] = Field(default_factory=list)
    linked_risk_ids: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class WorkstreamUpdateRequest(BaseModel):
    """Payload to update a workstream."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    executive_sponsor: Optional[str] = None
    priority: Optional[str] = None
    start_day: Optional[int] = None
    target_day: Optional[int] = None
    progress_pct: Optional[float] = None
    risk_level: Optional[str] = None
    linked_synergy_ids: Optional[List[str]] = None
    linked_risk_ids: Optional[List[str]] = None
    notes: Optional[str] = None


class WorkstreamStatusUpdateRequest(BaseModel):
    """Payload to transition workstream lifecycle status."""
    status: str = Field(..., description="NOT_STARTED, PLANNED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, CANCELLED")
    notes: Optional[str] = None


class MilestoneCreateRequest(BaseModel):
    """Payload to add a milestone to a workstream."""
    workstream_id: uuid.UUID
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    target_day: int = Field(30, ge=0, le=100)
    target_date: Optional[date] = None
    priority: str = Field("MEDIUM", description="CRITICAL, HIGH, MEDIUM, LOW")
    owner: Optional[str] = None
    linked_synergy_id: Optional[uuid.UUID] = None
    deliverable: Optional[str] = None
    evidence_citation_ids: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class MilestoneUpdateRequest(BaseModel):
    """Payload to update milestone attributes."""
    name: Optional[str] = None
    description: Optional[str] = None
    target_day: Optional[int] = None
    target_date: Optional[date] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    completion_pct: Optional[float] = None
    linked_synergy_id: Optional[uuid.UUID] = None
    deliverable: Optional[str] = None
    evidence_citation_ids: Optional[List[str]] = None
    notes: Optional[str] = None


class MilestoneStatusUpdateRequest(BaseModel):
    """Payload to update milestone status & completion."""
    status: str = Field(..., description="NOT_STARTED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, OVERDUE")
    completion_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None


class DependencyCreateRequest(BaseModel):
    """Payload to link predecessor and successor milestones in DAG."""
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    dependency_type: str = Field("FINISH_TO_START", description="FINISH_TO_START, START_TO_START, FINISH_TO_FINISH")
    is_blocking: bool = True


class BlockerCreateRequest(BaseModel):
    """Payload to report an operational/strategic blocker."""
    workstream_id: uuid.UUID
    milestone_id: Optional[uuid.UUID] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    severity: str = Field("HIGH", description="CRITICAL, HIGH, MEDIUM")
    owner: Optional[str] = None


class BlockerResolveRequest(BaseModel):
    """Payload to resolve a blocker."""
    resolution_notes: str = Field(..., min_length=1)


# ==========================================
# Response Models
# ==========================================

class MilestoneResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    program_id: uuid.UUID
    workstream_id: uuid.UUID
    name: str
    description: Optional[str] = None
    target_day: int
    target_date: Optional[date] = None
    stage: str = "DAYS_1_30_STABILIZE"
    status: str
    priority: str
    owner: Optional[str] = None
    completion_pct: float
    is_critical_path: bool
    linked_synergy_id: Optional[uuid.UUID] = None
    deliverable: Optional[str] = None
    evidence_citation_ids: Optional[List[str]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkstreamResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    program_id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: str
    owner: Optional[str] = None
    executive_sponsor: Optional[str] = None
    status: str
    priority: str
    start_day: int
    target_day: int
    progress_pct: float
    risk_level: str
    linked_synergy_ids: Optional[List[str]] = None
    linked_risk_ids: Optional[List[str]] = None
    notes: Optional[str] = None
    milestones_count: int = 0
    completed_milestones_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DependencyResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    program_id: uuid.UUID
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    dependency_type: str
    is_blocking: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockerResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    program_id: uuid.UUID
    workstream_id: uuid.UUID
    milestone_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    owner: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntegrationProgramResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    name: str
    status: str
    close_date: Optional[date] = None
    day_0_date: Optional[date] = None
    day_100_date: Optional[date] = None
    current_day_offset: int
    executive_sponsor: Optional[str] = None
    objectives: Optional[Dict[str, Any]] = None
    health_score: float
    health_band: str
    total_workstreams: int = 0
    total_milestones: int = 0
    completed_milestones: int = 0
    overdue_milestones: int = 0
    open_blockers: int = 0
    critical_path_duration_days: int = 0
    overall_progress_pct: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineStageResponse(BaseModel):
    deal_id: uuid.UUID
    current_day_offset: int
    stages: Dict[str, List[MilestoneResponse]]


class CriticalPathResponse(BaseModel):
    deal_id: uuid.UUID
    critical_path_milestone_ids: List[str]
    critical_path_duration_days: int
    longest_chain_length: int
    critical_milestones: List[Dict[str, Any]]


class IntegrationHealthResponse(BaseModel):
    deal_id: uuid.UUID
    health_score: float
    health_band: str
    penalties: Dict[str, Any]
    metrics: Dict[str, Any]


class ExecutiveAttentionResponse(BaseModel):
    deal_id: uuid.UUID
    critical_count: int
    high_count: int
    medium_count: int
    total_attention_items: int
    critical_items: List[Dict[str, Any]]
    high_items: List[Dict[str, Any]]
    medium_items: List[Dict[str, Any]]
