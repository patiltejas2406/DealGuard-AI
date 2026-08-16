# ADR-006: LangGraph for Controlled AI Orchestration

## Context
Multi-step due diligence analysis requires controlled execution paths (e.g. document parsing $\rightarrow$ structured fact extraction $\rightarrow$ deterministic metric computation $\rightarrow$ 17-pillar risk synthesis $\rightarrow$ citation binding). Unconstrained agent loops can diverge or hallucinate.

## Decision
Use **LangGraph** as a state machine workflow orchestrator for complex multi-step AI tasks, with strict node transitions and citation-validation gates. LlamaIndex is used specifically for document data-connectors and hierarchical chunk retrieval.

## Alternatives Considered
- **Unconstrained ReAct / AutoGPT-style agent loops**: Rejected due to non-deterministic divergence and lack of auditability.
- **Pure custom prompt chaining without graph abstractions**: Rejected for complex cyclic workflows requiring human-in-the-loop review nodes.

## Consequences
- **Positive**: Auditable, step-by-step stateful workflows with checkpointing and deterministic transitions.
- **Negative**: Adds LangGraph as a workflow dependency.
- **Status**: APPROVED & FROZEN
