"""Abstract Base Connector Interface for External Business Telemetry Ingestion."""

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.domains.telemetry.schemas import (
    CanonicalCustomer,
    CanonicalExpense,
    CanonicalOpportunity,
    CanonicalRevenueEvent,
    ConnectionCredentials,
    ConnectionStatus,
    ConnectionValidationResult,
    ConnectorProvider,
)


@dataclass
class SyncBatchResult:
    """Normalized payload output produced by a connector sync cycle."""
    customers: List[CanonicalCustomer] = field(default_factory=list)
    opportunities: List[CanonicalOpportunity] = field(default_factory=list)
    revenue_events: List[CanonicalRevenueEvent] = field(default_factory=list)
    expenses: List[CanonicalExpense] = field(default_factory=list)
    new_checkpoints: Dict[str, str] = field(default_factory=dict)
    records_fetched: int = 0
    records_failed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def record_count(self) -> int:
        return len(self.customers) + len(self.opportunities) + len(self.revenue_events) + len(self.expenses)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def new_cursors(self) -> Dict[str, str]:
        return self.new_checkpoints


class BaseConnector(abc.ABC):
    """Abstract interface defining the lifecycle and contract for business system connectors.
    
    All vendor-specific implementations (Salesforce, QuickBooks, HubSpot, NetSuite, Jira, Asana)
    must implement these lifecycle hooks. Agents and downstream engines only consume normalized
    DealGuard canonical telemetry.
    """

    def __init__(
        self,
        provider: ConnectorProvider,
        credentials: Optional[ConnectionCredentials] = None,
        deal_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.credentials = credentials or ConnectionCredentials()
        self.deal_id = deal_id
        self.organization_id = organization_id

    @abc.abstractmethod
    async def authenticate(self) -> bool:
        """Validate or refresh OAuth credentials."""
        pass

    @abc.abstractmethod
    async def validate_connection(self) -> ConnectionValidationResult:
        """Probe connectivity and check authorization health against the vendor API."""
        pass

    @abc.abstractmethod
    async def discover_capabilities(self) -> List[str]:
        """Inspect and return available external objects/endpoints (e.g. ['Accounts', 'Opportunities'])."""
        pass

    @abc.abstractmethod
    async def initial_sync(self, batch_size: int = 200) -> SyncBatchResult:
        """Perform initial complete baseline ingestion."""
        pass

    @abc.abstractmethod
    async def incremental_sync(
        self,
        checkpoints: Dict[str, str],
        batch_size: int = 200,
    ) -> SyncBatchResult:
        """Perform delta synchronization using high-water-mark cursor checkpoints."""
        pass

    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """Revoke active tokens and terminate connection session."""
        pass
