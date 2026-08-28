"""Standardized Agent Contracts, Schemas & Intelligence Assessment Protocols."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.domains.ai.schemas import CitationRef, GroundedFinding


class AgentLifecyclePhase(str, Enum):
    """Lifecycle phase alignment for agentic intelligence."""
    PRE_DEAL_ACQUISITION = "PRE_DEAL_ACQUISITION"
    POST_DEAL_VALUE_CREATION = "POST_DEAL_VALUE_CREATION"
    CROSS_LIFECYCLE = "CROSS_LIFECYCLE"


class AgentId(str, Enum):
    """Standardized Agent Identifiers across the platform."""
    # Pre-Deal Diligence Specialists
    FINANCE = "finance_intelligence_agent"
    VALUATION = "valuation_intelligence_agent"
    RISK = "risk_intelligence_agent"
    LEGAL = "legal_intelligence_agent"
    TECHNOLOGY = "technology_operations_agent"
    SCENARIO = "scenario_simulation_agent"
    INTEGRATION = "integration_intelligence_agent"
    SYNERGY = "synergy_value_creation_agent"
    
    # Meta Decision Agent
    DECISION = "deal_decision_agent"
    
    # Post-Deal Value Creation Specialists (Extensible)
    GROWTH = "growth_intelligence_agent"
    REVENUE = "revenue_optimization_agent"
    MARKETING = "marketing_intelligence_agent"
    CUSTOMER = "customer_retention_agent"
    COST_OPT = "cost_optimization_agent"
    OPERATIONS = "operations_intelligence_agent"
    FP_AND_A = "fp_and_a_agent"
    STRATEGY = "corporate_strategy_agent"
    MONITORING = "performance_monitoring_agent"


class AgentStatus(str, Enum):
    """Execution status of an agent assessment."""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AgentConfidence(str, Enum):
    """Confidence level of agent findings and assessments."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DecisionRecommendation(str, Enum):
    """Standardized investment and acquisition decision recommendations."""
    BUY = "BUY"
    BUY_WITH_CONDITIONS = "BUY_WITH_CONDITIONS"
    RENEGOTIATE = "RENEGOTIATE"
    HOLD = "HOLD"
    AVOID = "AVOID"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AgentMetadata(BaseModel):
    """Production contract metadata describing an agent's capability boundary."""
    agent_id: AgentId
    name: str
    version: str = "1.0.0"
    purpose: str
    domain: str
    lifecycle_phase: AgentLifecyclePhase = AgentLifecyclePhase.PRE_DEAL_ACQUISITION
    allowed_tools: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    confidence_policy: str
    limitations: List[str] = Field(default_factory=list)
    handoff_targets: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionRequest(BaseModel):
    """Standardized payload for invoking a specialist or decision agent."""
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    query: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_evidence: bool = True
    parent_execution_id: Optional[uuid.UUID] = None


class BaseAgentAssessment(BaseModel):
    """Base output contract for all specialized agents."""
    agent_id: AgentId
    domain: str
    status: AgentStatus = AgentStatus.SUCCESS
    summary: str
    confidence: AgentConfidence = AgentConfidence.HIGH
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.90)
    
    # Structured Insights
    key_findings: List[GroundedFinding] = Field(default_factory=list)
    positive_drivers: List[str] = Field(default_factory=list)
    negative_drivers: List[str] = Field(default_factory=list)
    unresolved_issues: List[str] = Field(default_factory=list)
    required_diligence: List[str] = Field(default_factory=list)
    
    # Provenance and Traceability
    citations: List[CitationRef] = Field(default_factory=list)
    deterministic_references: Dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable arithmetic or metrics output directly by deterministic calculation engines."
    )
    tools_invoked: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Specialized Domain Assessments
class FinanceAssessment(BaseAgentAssessment):
    """Structured assessment from Finance Intelligence Agent."""
    revenue_trend: Optional[str] = None
    normalized_ebitda: Optional[float] = None
    ebitda_margin: Optional[float] = None
    qoe_net_adjustments: Optional[float] = None
    revenue_cagr_3yr: Optional[float] = None


class ValuationAssessment(BaseAgentAssessment):
    """Structured assessment from Valuation Intelligence Agent."""
    implied_ev_dcf: Optional[float] = None
    implied_ev_comps: Optional[float] = None
    implied_ev_precedents: Optional[float] = None
    blended_valuation_mid: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    wacc_used: Optional[float] = None


class RiskAssessment(BaseAgentAssessment):
    """Structured assessment from Risk Intelligence Agent."""
    total_risks_identified: int = 0
    critical_risks_count: int = 0
    high_risks_count: int = 0
    composite_risk_score: Optional[float] = None
    top_risk_categories: List[str] = Field(default_factory=list)


class LegalAssessment(BaseAgentAssessment):
    """Structured assessment from Legal Intelligence Agent."""
    contracts_analyzed_count: int = 0
    change_of_control_clauses_count: int = 0
    value_at_risk_usd: Optional[float] = None
    non_compete_blockers_count: int = 0
    regulatory_compliance_status: Optional[str] = None


class TechnologyAssessment(BaseAgentAssessment):
    """Structured assessment from Technology & Operations Agent."""
    tech_debt_level: Optional[str] = None
    cloud_architecture_score: Optional[float] = None
    spof_count: int = 0
    sla_compliance_rate: Optional[float] = None
    cybersecurity_exceptions_count: int = 0


class ScenarioAssessment(BaseAgentAssessment):
    """Structured assessment from Scenario & Simulation Agent."""
    base_case_irr: Optional[float] = None
    downside_case_irr: Optional[float] = None
    upside_case_irr: Optional[float] = None
    monte_carlo_var_95: Optional[float] = None
    recession_resilience_rating: Optional[str] = None


class IntegrationAssessment(BaseAgentAssessment):
    """Structured assessment from 100-Day Integration Intelligence Agent."""
    total_milestones: int = 0
    critical_path_milestones_count: int = 0
    integration_health_score: Optional[float] = None
    day_100_synergy_readiness_pct: Optional[float] = None
    identified_blockers_count: int = 0


class SynergyAssessment(BaseAgentAssessment):
    """Structured assessment from Synergy & Value Creation Agent."""
    annual_run_rate_synergy_usd: Optional[float] = None
    net_present_value_synergy_usd: Optional[float] = None
    cost_synergies_pct: Optional[float] = None
    revenue_synergies_pct: Optional[float] = None
    phasing_period_years: int = 5


class DecisionAssessment(BaseAgentAssessment):
    """Synthesized holistic deal decision assessment from Deal Decision Agent."""
    recommendation: DecisionRecommendation = DecisionRecommendation.HOLD
    deterministic_decision_score: Optional[float] = Field(
        None,
        description="Immutable 0-100 composite score from the authoritative DecisionScore engine."
    )
    executive_rationale: str
    required_conditions: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    escalation_reasons: List[str] = Field(default_factory=list)
    recommended_human_action: str
    specialist_contributions: Dict[str, Any] = Field(default_factory=dict)
