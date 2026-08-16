# ADR-003: Pure-Python Deterministic Financial Engine

## Context
Financial analysts, investment committees, and corporate buyers make multi-million-dollar decisions based on financial indicators (EBITDA, Net Debt, CAGR, WACC, DCF, IRR). Large Language Models are stochastic and prone to arithmetic hallucinations, inconsistent rounding, and non-deterministic behavior.

## Decision
All financial metrics, normalizations, ratios, DCF valuations, multiples calculations, sensitivity heatmaps, and scenario deltas MUST be computed exclusively by **pure-Python deterministic domain services** using verified formulas. LLMs are strictly prohibited from performing authoritative arithmetic. LLMs are restricted to extracting raw cell figures and explaining pre-computed results.

## Alternatives Considered
- **LLM-generated calculations / Code Interpreter**: Rejected as unreliable, non-reproducible, and un-auditable for financial governance.

## Consequences
- **Positive**: 100% mathematical precision, verifiable unit tests, deterministic repeatability, full auditability.
- **Negative**: Requires writing and maintaining comprehensive financial domain code in Python.
- **Status**: APPROVED & FROZEN
