"""Connector Registry & Factory for External Business Systems."""

from typing import Any, Dict, List, Optional, Type
from app.domains.telemetry.connectors.base import BaseConnector
from app.domains.telemetry.connectors.quickbooks import QuickBooksConnector
from app.domains.telemetry.connectors.salesforce import SalesforceConnector
from app.domains.telemetry.schemas import ConnectionCredentials, ConnectorProvider


class ConnectorRegistry:
    """Central factory for instantiating vendor-specific connector instances."""

    _REGISTRY: Dict[ConnectorProvider, Type[BaseConnector]] = {
        ConnectorProvider.SALESFORCE: SalesforceConnector,
        ConnectorProvider.QUICKBOOKS: QuickBooksConnector,
    }

    _PROVIDER_METADATA: Dict[ConnectorProvider, Dict[str, Any]] = {
        ConnectorProvider.SALESFORCE: {
            "name": "Salesforce Sales Cloud",
            "category": "CRM & Commercial Pipeline",
            "status": "ACTIVE",
            "auth_type": "OAuth 2.0 Web Server / Refresh Token",
            "capabilities": ["Account", "Opportunity", "Contact", "Lead"],
            "description": "Continuously ingests customer account expansion and enterprise sales pipeline opportunities.",
        },
        ConnectorProvider.QUICKBOOKS: {
            "name": "Intuit QuickBooks Online",
            "category": "Accounting & Financial Telemetry",
            "status": "ACTIVE",
            "auth_type": "OAuth 2.0 / Realm Connection",
            "capabilities": ["Customer", "Invoice", "Payment", "Bill", "Purchase", "Account"],
            "description": "Ingests realized revenue invoices and operating expenses to feed deterministic post-close KPIs.",
        },
        ConnectorProvider.HUBSPOT: {
            "name": "HubSpot CRM",
            "category": "Marketing & Inbound Pipeline",
            "status": "PLANNED",
            "auth_type": "OAuth 2.0 / Private App Token",
            "capabilities": ["Contacts", "Deals", "Companies", "Engagements"],
            "description": "Future connector for marketing attribution and inbound pipeline velocity.",
        },
        ConnectorProvider.NETSUITE: {
            "name": "Oracle NetSuite ERP",
            "category": "Enterprise ERP & General Ledger",
            "status": "PLANNED",
            "auth_type": "TBA / OAuth 2.0",
            "capabilities": ["General Ledger", "Invoices", "Vendors", "Revenue Recognition"],
            "description": "Future connector for enterprise mid-market ERP consolidation.",
        },
        ConnectorProvider.JIRA: {
            "name": "Atlassian Jira Software",
            "category": "Engineering & Technology Telemetry",
            "status": "PLANNED",
            "auth_type": "OAuth 2.0 / API Token",
            "capabilities": ["Issues", "Sprints", "Velocity", "Tech Debt"],
            "description": "Future connector for post-close technology integration and release velocity.",
        },
        ConnectorProvider.ASANA: {
            "name": "Asana Work Management",
            "category": "PMI Workstreams & Project Milestones",
            "status": "PLANNED",
            "auth_type": "OAuth 2.0 / Personal Access Token",
            "capabilities": ["Tasks", "Projects", "Milestones"],
            "description": "Future connector for 100-day integration milestone synchronization.",
        },
    }

    @classmethod
    def get_connector(cls, provider: ConnectorProvider) -> BaseConnector:
        """Instantiate a connector instance for the given provider."""
        connector_cls = cls._REGISTRY.get(provider)
        if not connector_cls:
            raise ValueError(f"Provider '{provider}' is not yet supported in the active connector registry.")
        return connector_cls()

    @classmethod
    def create_connector(
        cls,
        provider: ConnectorProvider,
        credentials: ConnectionCredentials,
        deal_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> BaseConnector:
        """Instantiate a connector instance for the given provider."""
        connector_cls = cls._REGISTRY.get(provider)
        if not connector_cls:
            raise ValueError(f"Provider '{provider}' is not yet supported in the active connector registry.")
        return connector_cls(
            credentials=credentials,
            deal_id=deal_id,
            organization_id=organization_id,
        )

    @classmethod
    def get_all_providers(cls) -> List[Any]:
        """Return catalog of supported and upcoming connector providers as schemas."""
        from app.domains.telemetry.schemas import ConnectorMetadata
        return [
            ConnectorMetadata(
                provider=provider,
                name=meta["name"],
                category=meta["category"],
                status=meta["status"],
                auth_type=meta["auth_type"],
                capabilities=meta["capabilities"],
                description=meta["description"],
            )
            for provider, meta in cls._PROVIDER_METADATA.items()
        ]

    @classmethod
    def list_supported_providers(cls) -> List[Dict[str, Any]]:
        """Return catalog of supported and upcoming connector providers."""
        return [
            {"provider_id": provider.value, **meta}
            for provider, meta in cls._PROVIDER_METADATA.items()
        ]
