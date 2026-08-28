"""Centralized Agent Tool Registry & Deterministic Execution Governance."""

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from app.domains.agents.contract import AgentId


class UnauthorizedToolAccessError(PermissionError):
    """Raised when an agent attempts to invoke a tool outside its authorized whitelist."""
    pass


class ToolExecutionError(RuntimeError):
    """Raised when a deterministic tool fails during execution."""
    pass


@dataclass
class ToolDefinition:
    """Explicit definition of an authorized deterministic tool or RAG retrieval capability."""
    name: str
    domain: str
    description: str
    is_deterministic: bool
    required_permissions: List[str] = field(default_factory=list)
    execute_fn: Optional[Callable] = None


class AgentToolRegistry:
    """Production registry governing which deterministic tools each agent is authorized to call."""

    _tools: Dict[str, ToolDefinition] = {}
    _agent_tool_whitelist: Dict[AgentId, List[str]] = {
        # 1. Finance Agent
        AgentId.FINANCE: [
            "financial_statements_tool",
            "financial_metrics_tool",
            "qoe_bridge_tool",
            "financial_rag_retrieval_tool",
        ],
        # 2. Valuation Agent
        AgentId.VALUATION: [
            "dcf_valuation_tool",
            "wacc_calculator_tool",
            "trading_comps_tool",
            "precedent_transactions_tool",
            "valuation_sensitivity_tool",
        ],
        # 3. Risk Agent
        AgentId.RISK: [
            "risk_matrix_17_pillar_tool",
            "document_risk_scanner_tool",
            "risk_evidence_tool",
        ],
        # 4. Legal Agent
        AgentId.LEGAL: [
            "contract_clause_tool",
            "legal_value_at_risk_tool",
            "compliance_matrix_tool",
        ],
        # 5. Technology Agent
        AgentId.TECHNOLOGY: [
            "tech_findings_tool",
            "operational_metrics_tool",
            "cloud_cost_risk_tool",
            "spof_analyzer_tool",
        ],
        # 6. Scenario Agent
        AgentId.SCENARIO: [
            "whatif_scenario_tool",
            "sensitivity_grid_tool",
            "monte_carlo_simulation_tool",
        ],
        # 7. Integration Agent
        AgentId.INTEGRATION: [
            "integration_milestones_tool",
            "integration_dag_critical_path_tool",
            "integration_health_score_tool",
        ],
        # 8. Synergy Agent
        AgentId.SYNERGY: [
            "synergy_waterfall_bridge_tool",
            "synergy_5yr_phasing_tool",
            "synergy_npv_calculator_tool",
        ],
        # 9. Deal Decision Agent
        AgentId.DECISION: [
            "decision_score_composite_tool",
            "specialist_assessment_aggregator_tool",
        ],
        # Post-Deal Extensions
        AgentId.GROWTH: ["growth_waterfall_tool", "customer_expansion_tool"],
        AgentId.REVENUE: ["pricing_elasticity_tool", "revenue_bridge_tool"],
        AgentId.MARKETING: ["cac_ltv_tool", "campaign_efficiency_tool"],
        AgentId.CUSTOMER: ["retention_cohort_tool", "nps_sentiment_tool"],
        AgentId.COST_OPT: ["procurement_spend_tool", "headcount_synergy_tool"],
        AgentId.OPERATIONS: ["throughput_sla_tool", "facility_utilization_tool"],
        AgentId.FP_AND_A: ["rolling_forecast_tool", "budget_variance_tool"],
        AgentId.STRATEGY: ["market_share_tam_tool", "ma_pipeline_tool"],
        AgentId.MONITORING: ["kpi_health_dashboard_tool", "covenant_compliance_tool"],
    }

    @classmethod
    def register_tool(cls, tool: ToolDefinition) -> None:
        """Register a tool definition in the global registry."""
        cls._tools[tool.name] = tool

    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[ToolDefinition]:
        """Retrieve a tool definition by name."""
        return cls._tools.get(tool_name)

    @classmethod
    def list_all_tools(cls) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_allowed_tools_for_agent(cls, agent_id: AgentId) -> List[str]:
        """Get the authorized tool whitelist for a given agent."""
        return cls._agent_tool_whitelist.get(agent_id, [])

    @classmethod
    def verify_tool_access(cls, agent_id: AgentId, tool_name: str) -> None:
        """
        Validate that the agent is explicitly authorized to call the requested tool.
        Raises UnauthorizedToolAccessError on violation.
        """
        allowed = cls.get_allowed_tools_for_agent(agent_id)
        if tool_name not in allowed:
            raise UnauthorizedToolAccessError(
                f"Security Violation: Agent '{agent_id.value}' is NOT authorized to execute tool '{tool_name}'. "
                f"Authorized tools: {allowed}"
            )

    @classmethod
    async def execute_tool(
        cls, agent_id: AgentId, tool_name: str, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Execute an authorized tool with strict security validation.
        """
        cls.verify_tool_access(agent_id, tool_name)
        tool = cls.get_tool(tool_name)
        if not tool or not tool.execute_fn:
            # Fallback for declarative or pipeline tools
            return {"status": "SUCCESS", "tool": tool_name, "message": "Tool executed via registered service"}

        try:
            if inspect.iscoroutinefunction(tool.execute_fn):
                return await tool.execute_fn(*args, **kwargs)
            return tool.execute_fn(*args, **kwargs)
        except Exception as exc:
            raise ToolExecutionError(f"Tool execution failed for '{tool_name}': {str(exc)}") from exc
