# ADR-001: Modular Monolith Backend Architecture

## Context
DealGuard AI requires high transactional consistency across deals, financial statements, contracts, risks, valuations, and audit logs. A microservices architecture at this stage would introduce significant network latency, distributed transaction complexity (2PC/Sagas), container orchestration overhead, and operational friction for due diligence workflows that inherently join relational deal data with financial calculation graphs.

## Decision
We adopt a **Modular Monolith** architecture for the backend using FastAPI in Python 3.11+. The codebase is partitioned into self-contained domain modules (`auth/`, `deals/`, `documents/`, `financials/`, `valuation/`, `risk/`, `scenarios/`, `post_deal/`, `ai/`, `audit/`) with explicit interface contracts and zero cross-domain circular dependencies.

## Alternatives Considered
- **Microservices Architecture**: Rejected due to premature complexity, operational overhead, and distributed transaction costs.
- **Single-file Monolith**: Rejected due to lack of domain boundary isolation and poor maintainability.

## Consequences
- **Positive**: Blazing fast in-memory financial pipeline execution, unified database transactions, single-deployment simplicity, clear domain boundaries.
- **Negative**: Requires strict code review to prevent leakage between domain packages.
- **Status**: APPROVED & FROZEN
