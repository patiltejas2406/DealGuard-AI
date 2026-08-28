"""Unit Tests for Agent Contracts, Tool Registry Authorization & HITL Governance."""

import pytest
import uuid
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentLifecyclePhase,
    AgentMetadata,
    AgentStatus,
    BaseAgentAssessment,
    DecisionAssessment,
    DecisionRecommendation,
    FinanceAssessment,
    RiskAssessment,
    ValuationAssessment,
)
from app.domains.agents.human_review import (
    EscalationSeverity,
    HumanReviewEscalation,
    HumanReviewEvaluator,
    HumanReviewTrigger,
)
from app.domains.agents.tools import (
    AgentToolRegistry,
    ToolDefinition,
    UnauthorizedToolAccessError,
)
from app.domains.ai.guardrails import AIGuardrailError, AIGuardrailValidator
from app.domains.ai.schemas import CitationRef, GroundedFinding


def test_agent_contract_schemas_and_metadata():
    """Verify that agent metadata adheres to production schema boundaries."""
    meta = AgentMetadata(
        agent_id=AgentId.FINANCE,
        name="Finance Intelligence Specialist",
        purpose="Analyze financial statements and QoE adjustments.",
        domain="FINANCIALS",
        lifecycle_phase=AgentLifecyclePhase.PRE_DEAL_ACQUISITION,
        allowed_tools=["financial_metrics_tool", "qoe_bridge_tool"],
        evidence_requirements=["Audited Financials"],
        confidence_policy="Requires verified 3-statement data.",
    )
    assert meta.agent_id == AgentId.FINANCE
    assert meta.domain == "FINANCIALS"
    assert "financial_metrics_tool" in meta.allowed_tools
    assert meta.version == "1.0.0"


def test_tool_registry_authorization_enforcement():
    """Verify that agents are blocked from invoking tools outside their whitelist."""
    # Finance agent should be allowed to use financial_metrics_tool
    AgentToolRegistry.verify_tool_access(AgentId.FINANCE, "financial_metrics_tool")

    # Finance agent should be blocked from calling risk_matrix_17_pillar_tool
    with pytest.raises(UnauthorizedToolAccessError) as exc_info:
        AgentToolRegistry.verify_tool_access(AgentId.FINANCE, "risk_matrix_17_pillar_tool")
    assert "NOT authorized" in str(exc_info.value)


def test_tool_registry_custom_registration_and_execution():
    """Verify registering a custom tool and checking execution security."""
    test_tool = ToolDefinition(
        name="test_math_tool",
        domain="TEST",
        description="Deterministic multiplier",
        is_deterministic=True,
        execute_fn=lambda x: x * 2,
    )
    AgentToolRegistry.register_tool(test_tool)
    assert AgentToolRegistry.get_tool("test_math_tool") is not None


def test_human_review_evaluator_triggers():
    """Verify that HumanReviewEvaluator properly identifies escalation requirements."""
    # High confidence, 0 critical risks -> No review needed
    is_req, reasons, action = HumanReviewEvaluator.evaluate_escalation_needed(
        confidence_score=0.92,
        critical_issues_count=0,
        unresolved_issues=[],
        has_insufficient_evidence=False,
    )
    assert not is_req
    assert len(reasons) == 0

    # Low confidence -> Escalation required
    is_req, reasons, action = HumanReviewEvaluator.evaluate_escalation_needed(
        confidence_score=0.62,
        critical_issues_count=0,
        unresolved_issues=[],
        has_insufficient_evidence=False,
    )
    assert is_req
    assert any("confidence" in r.lower() for r in reasons)

    # Critical risks -> Escalation required
    is_req, reasons, action = HumanReviewEvaluator.evaluate_escalation_needed(
        confidence_score=0.90,
        critical_issues_count=2,
        unresolved_issues=[],
        has_insufficient_evidence=False,
    )
    assert is_req
    assert any("critical severity" in r.lower() for r in reasons)


def test_grounded_finding_and_guardrail_validation():
    """Verify that grounded findings with citations pass AI guardrails."""
    cit = CitationRef(
        document_id=uuid.uuid4(),
        page_number=4,
        exact_quote="Revenue grew by 24% year over year to $45.2M in FY2023.",
        confidence_score=0.95,
    )
    finding = GroundedFinding(
        domain_pillar="FINANCIAL",
        category="REVENUE_GROWTH",
        headline="Strong Top-Line Revenue Acceleration",
        detailed_reasoning="Audited financials confirm 24% revenue expansion.",
        severity_level="LOW",
        confidence_score=0.94,
        is_deterministic_calculation=False,
        citations=[cit],
    )
    is_valid, violations = AIGuardrailValidator.validate_finding_grounding(finding)
    assert is_valid
    assert len(violations) == 0
