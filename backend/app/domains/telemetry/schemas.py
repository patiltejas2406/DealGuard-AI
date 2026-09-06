"""Pydantic Schemas and Enums for External Connectors and Canonical Business Telemetry."""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectorProvider(str, Enum):
    """Supported external business system providers."""
    SALESFORCE = "SALESFORCE"
    QUICKBOOKS = "QUICKBOOKS"
    HUBSPOT = "HUBSPOT"
    NETSUITE = "NETSUITE"
    JIRA = "JIRA"
    ASANA = "ASANA"


class ConnectionStatus(str, Enum):
    """Operational status of an external system connection."""
    CONNECTED = "CONNECTED"
    ACTIVE = "ACTIVE"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    SYNCING = "SYNCING"
    AUTH_EXPIRED = "AUTH_EXPIRED"


class AuthStatus(str, Enum):
    """Authentication and token lifecycle status."""
    AUTHENTICATED = "AUTHENTICATED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"


class SyncStatus(str, Enum):
    """Execution status of an incremental or initial sync run."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


class DataFreshnessStatus(str, Enum):
    """Categorization of data age and reliability."""
    LIVE = "LIVE"            # < 1 hour old
    RECENT = "RECENT"        # < 24 hours old
    STALE = "STALE"          # >= 24 hours old
    NOT_SYNCED = "NOT_SYNCED"


class TelemetryChangeSeverity(str, Enum):
    """Significance level of detected metric drift."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# --- Connection Management Schemas ---

class ConnectorMetadata(BaseModel):
    """Metadata catalog entry for an available integration provider."""
    provider: ConnectorProvider
    name: str
    category: str
    status: str
    auth_type: str
    capabilities: List[str] = Field(default_factory=list)
    description: str


class ConnectionCredentials(BaseModel):
    """Input credentials or OAuth tokens (encrypted at rest, never stored or returned plaintext)."""
    client_id: Optional[str] = Field(default=None, description="OAuth Client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth Client Secret")
    access_token: Optional[str] = Field(default=None, description="Active Access Token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth Refresh Token")
    instance_url: Optional[str] = Field(default=None, description="Instance/Endpoint URL (e.g. Salesforce instance or QBO realm)")
    realm_id: Optional[str] = Field(default=None, description="QuickBooks Company/Realm ID")
    api_key: Optional[str] = Field(default=None, description="API Key for token-based authentication")
    extra_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional non-secret provider options")


class ExternalConnectionCreate(BaseModel):
    """Request payload to establish an external system connection."""
    provider: ConnectorProvider = Field(..., description="External system provider")
    connection_name: str = Field(..., max_length=255, description="Human-readable connection label")
    credentials: ConnectionCredentials = Field(..., description="Credentials to be encrypted at rest")
    auto_sync_interval_hours: int = Field(default=6, ge=1, le=168, description="Scheduled sync interval")


class ExternalConnectionUpdate(BaseModel):
    """Update connection settings or rotate credentials."""
    connection_name: Optional[str] = Field(default=None, max_length=255)
    credentials: Optional[ConnectionCredentials] = None
    auto_sync_interval_hours: Optional[int] = Field(default=None, ge=1, le=168)
    is_active: Optional[bool] = None


class ExternalConnectionResponse(BaseModel):
    """Safe connection representation returned to the API (secrets are completely masked)."""
    id: uuid.UUID
    organization_id: uuid.UUID
    deal_id: Optional[uuid.UUID]
    provider: ConnectorProvider
    connection_name: str
    connection_status: ConnectionStatus
    auth_status: AuthStatus
    last_successful_sync: Optional[datetime]
    last_attempted_sync: Optional[datetime]
    data_freshness_status: DataFreshnessStatus
    capabilities: List[str] = Field(default_factory=list)
    auto_sync_interval_hours: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    masked_instance_url: Optional[str] = None

    class Config:
        from_attributes = True

    @property
    def status(self) -> ConnectionStatus:
        return self.connection_status


class ConnectionValidationResult(BaseModel):
    """Result of an active connection health and authentication probe."""
    is_valid: bool
    status: ConnectionStatus
    provider: ConnectorProvider
    message: str
    discovered_capabilities: List[str] = Field(default_factory=list)
    latency_ms: float
    probed_at: datetime = Field(default_factory=datetime.utcnow)

    def __iter__(self):
        yield self.is_valid
        yield (None if self.is_valid else self.message)


# --- Sync Execution Schemas ---

class SyncTriggerRequest(BaseModel):
    """Request to initiate a synchronization job."""
    is_full_sync: bool = Field(default=False, description="Force a full sync instead of incremental checkpoint")
    entity_types: Optional[List[str]] = Field(default=None, description="Specific entities to synchronize")


class SyncRunResponse(BaseModel):
    """Tracking record for a synchronization run."""
    id: uuid.UUID
    connection_id: uuid.UUID
    status: SyncStatus
    is_full_sync: bool
    records_fetched: int
    records_normalized: int
    records_upserted: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str] = None
    entity_breakdown: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# --- Canonical Telemetry Domain Objects ---

class CanonicalCustomer(BaseModel):
    """Normalized customer account across CRM and ERP systems."""
    external_id: str
    provider: ConnectorProvider
    account_name: str
    segment: str = "MID_MARKET"
    arr_usd: float = 0.0
    mrr_usd: float = 0.0
    churn_risk_score: float = 0.15
    health_status: str = "HEALTHY"
    renewal_date: Optional[date] = None
    is_churned: bool = False
    industry: Optional[str] = None
    expansion_potential_usd: float = 0.0
    synced_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def name(self) -> str:
        return self.account_name

    @property
    def arr(self) -> float:
        return self.arr_usd

    @property
    def source_provider(self) -> ConnectorProvider:
        return self.provider

    @property
    def churn_risk_level(self) -> str:
        if self.churn_risk_score >= 0.40:
            return "HIGH"
        elif self.churn_risk_score >= 0.25:
            return "MEDIUM"
        return "LOW"

    @property
    def currency(self) -> str:
        return "USD"


class CanonicalOpportunity(BaseModel):
    """Normalized commercial opportunity / deal pipeline event."""
    external_id: str
    provider: ConnectorProvider
    opportunity_name: str
    customer_external_id: Optional[str] = None
    amount_usd: float = 0.0
    stage: str
    probability_pct: float = 50.0
    expected_revenue_usd: float = 0.0
    close_date: Optional[date] = None
    is_closed: bool = False
    is_won: bool = False
    synced_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def name(self) -> str:
        return self.opportunity_name

    @property
    def amount(self) -> float:
        return self.amount_usd

    @property
    def source_provider(self) -> ConnectorProvider:
        return self.provider


class CanonicalRevenueEvent(BaseModel):
    """Normalized realized income / invoice event."""
    external_id: str
    provider: ConnectorProvider
    customer_external_id: Optional[str] = None
    invoice_number: Optional[str] = None
    event_date: date
    fiscal_period: str
    amount_usd: float
    status: str = "PAID"  # PAID, PENDING, OVERDUE, CANCELLED
    synced_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def amount(self) -> float:
        return self.amount_usd

    @property
    def source_provider(self) -> ConnectorProvider:
        return self.provider

    @property
    def is_recurring(self) -> bool:
        return True


class CanonicalExpense(BaseModel):
    """Normalized operational or capital expenditure event."""
    external_id: str
    provider: ConnectorProvider
    expense_date: date
    fiscal_period: str
    category: str  # COGS, R&D, S&M, G&A, CLOUD, PAYROLL
    vendor_name: Optional[str] = None
    amount_usd: float
    synced_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def amount(self) -> float:
        return self.amount_usd

    @property
    def source_provider(self) -> ConnectorProvider:
        return self.provider

    @property
    def is_recurring(self) -> bool:
        return True


# --- Telemetry Aggregates and Change Detection ---

class TelemetrySummaryResponse(BaseModel):
    """Consolidated business telemetry posture for an acquired entity or deal."""
    deal_id: uuid.UUID
    active_connections_count: int
    connected_providers: List[str]
    overall_freshness: DataFreshnessStatus
    last_synced_at: Optional[datetime]
    customer_count: int
    total_pipeline_arr: float
    total_realized_revenue: float
    total_realized_expenses: float
    detected_ebitda_runrate: float
    unresolved_telemetry_changes: int

    @property
    def active_connections(self) -> int:
        return self.active_connections_count

    @property
    def total_customers(self) -> int:
        return self.customer_count

    @property
    def total_arr(self) -> float:
        return self.total_pipeline_arr

    @property
    def total_pipeline_value(self) -> float:
        return self.total_pipeline_arr

    @property
    def freshness(self) -> DataFreshnessStatus:
        return self.overall_freshness


class TelemetryChangeResponse(BaseModel):
    """Change detection record highlighting significant metric drift."""
    id: uuid.UUID
    deal_id: uuid.UUID
    metric_name: str
    previous_value: float
    new_value: float
    delta_value: float
    delta_percentage: float
    severity: TelemetryChangeSeverity
    affected_kpi: str
    affected_thesis_pillar: Optional[str]
    affected_initiatives: List[str] = Field(default_factory=list)
    suggested_agent_id: str
    detected_at: datetime
    evidence_source: str
    is_resolved: bool

    class Config:
        from_attributes = True


# Alias for backward compatibility & naming consistency
BusinessTelemetryChangeResponse = TelemetryChangeResponse
