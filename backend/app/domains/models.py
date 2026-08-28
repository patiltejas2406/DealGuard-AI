"""Aggregated Domain Models Registry for Alembic and Application Core."""

from app.core.database import Base
from app.domains.common.models import BaseModel, TenantScopedModel
from app.domains.auth.models import Organization, User, Role, OrganizationMembership, AuthSession
from app.domains.deals.models import TargetCompany, Deal, DealMember
from app.domains.documents.models import Document, DocumentVersion, DocumentChunk, Citation
from app.domains.financials.models import FinancialStatement, FinancialMetric, QoEAdjustment
from app.domains.valuation.models import (
    Valuation,
    ValuationAssumption,
    ComparableCompany,
    PrecedentTransaction,
    ValuationOutput,
)
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.decision.models import DecisionScore
from app.domains.simulation.models import Scenario, SimulationRun
from app.domains.synergy.models import SynergyOpportunity, SynergyRealizationLog
from app.domains.integration.models import (
    IntegrationProgram,
    IntegrationWorkstream,
    IntegrationMilestone,
    IntegrationDependency,
    IntegrationBlocker,
)
from app.domains.legal.models import (
    ContractRecord,
    ContractClause,
    LegalFinding,
    ComplianceRequirement,
)
from app.domains.technology.models import (
    TechnologyFinding,
    OperationalMetric,
    TechnologyDependency,
)
from app.domains.copilot.models import (
    CopilotConversation,
    CopilotMessage,
)
from app.domains.audit.models import AuditEvent, HumanReview
from app.domains.jobs.models import JobExecution
from app.domains.agents.models import AgentExecution, AgentAssessmentRecord
from app.domains.ml.models import MLModelRecord, MLPredictionRecord

__all__ = [
    "Base",
    "BaseModel",
    "TenantScopedModel",
    "Organization",
    "User",
    "Role",
    "OrganizationMembership",
    "AuthSession",
    "TargetCompany",
    "Deal",
    "DealMember",
    "Document",
    "DocumentVersion",
    "DocumentChunk",
    "Citation",
    "FinancialStatement",
    "FinancialMetric",
    "QoEAdjustment",
    "Valuation",
    "ValuationAssumption",
    "ComparableCompany",
    "PrecedentTransaction",
    "ValuationOutput",
    "Risk",
    "RiskEvidence",
    "DecisionScore",
    "Scenario",
    "SimulationRun",
    "SynergyOpportunity",
    "SynergyRealizationLog",
    "IntegrationProgram",
    "IntegrationWorkstream",
    "IntegrationMilestone",
    "IntegrationDependency",
    "IntegrationBlocker",
    "ContractRecord",
    "ContractClause",
    "LegalFinding",
    "ComplianceRequirement",
    "TechnologyFinding",
    "OperationalMetric",
    "TechnologyDependency",
    "CopilotConversation",
    "CopilotMessage",
    "AuditEvent",
    "HumanReview",
    "JobExecution",
    "AgentExecution",
    "AgentAssessmentRecord",
    "MLModelRecord",
    "MLPredictionRecord",
]



