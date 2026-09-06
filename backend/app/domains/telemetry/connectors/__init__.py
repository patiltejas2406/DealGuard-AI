"""Connector implementations and registry."""

from app.domains.telemetry.connectors.base import BaseConnector, SyncBatchResult
from app.domains.telemetry.connectors.quickbooks import QuickBooksConnector
from app.domains.telemetry.connectors.salesforce import SalesforceConnector
from app.domains.telemetry.connectors.registry import ConnectorRegistry

__all__ = [
    "BaseConnector",
    "SyncBatchResult",
    "SalesforceConnector",
    "QuickBooksConnector",
    "ConnectorRegistry",
]
