# DealGuard AI — System Architecture Specification (Frozen Baseline)

> **Document Status**: FROZEN (Architecture Baseline Approved)  
> **Version**: 1.0.0  
> **Classification**: Production Specification  

---

## 1. Core Architectural Overview

DealGuard AI is built as a **Modular Monolith** designed for high transactional consistency, zero-hallucination deterministic financial computation, strictly grounded AI intelligence, and multi-tenant security.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               Next.js 14+ Frontend Shell                                │
│                     (TypeScript, Tailwind CSS, Radix UI, Recharts)                      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ REST APIs / Server-Sent Events
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application Core (Modular Monolith)                                            │
│                                                                                        │
│  [Auth & RBAC]      [Deal Management]      [Document Ingestion & Parsing]              │
│  [Financial Engine] [Valuation Engine]     [17-Category Deal Risk Engine]              │
│  [What-If Simulator][Post-Deal Matrix]     [LangGraph Agent Orchestration]             │
│  [Audit Ledger]     [Citation Manager]     [System Observability & Tracing]            │
└────────────────┬──────────────────────────┬───────────────────────────┬────────────────┘
                 │                          │                           │
                 ▼                          ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────────────┐ ┌────────────────────────┐
│ PostgreSQL 16 + pgvector      │ │ S3 / MinIO Object Storage │ │ Redis 7 + Celery Queue │
│ (Relational Core, Chunks,     │ │ (Original PDFs, XLSX,     │ │ (Asynchronous parsing, │
│  Vector Embeddings @ 1536d)   │ │  DOCX & Version Vault)    │ │  embeddings & reports) │
└───────────────────────────────┘ └───────────────────────────┘ └────────────────────────┘
```

---

## 2. AI Trust Boundary & The Deterministic Guardrail

```
[Untrusted Diligence Document (PDF/XLSX)]
                   │
                   ▼
       [Structure-Aware Parser]
                   │
                   ▼
  [LLM Extraction & Normalization]
  (Extracts raw cell facts into typed Pydantic models)
                   │
                   ▼
    [Input Validation Layer]
                   │
                   ▼
[DETERMINISTIC DOMAIN ENGINES (Pure Python)]
├── Financial Statement Aggregation
├── EBITDA Normalization & Quality of Earnings
├── DCF, WACC, and Multiple Valuations
├── 17-Category Risk Scoring Model
└── What-If Parameter Sensitivity Graph
                   │
                   ▼
         [Verified Results]
                   │
                   ▼
[AI Synthesis & Strategic Reasoning (LangGraph)]
(Explains findings, synthesizes memos, generates 100-day tasks)
                   │
                   ▼
[Evidence Citation Binder (doc_id, page, offset, text)]
```

---

## 3. Architecture Decision Records (ADRs) Summary

| ADR ID | Title | Status | Primary Rationale |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Modular Monolith Backend Architecture | APPROVED | Avoids microservice network overhead while maintaining strict domain package boundaries. |
| **ADR-002** | PostgreSQL 16 + pgvector Storage | APPROVED | Co-locates relational ACID domain data with vector embeddings, preventing dual-DB sync lag. |
| **ADR-003** | Pure-Python Deterministic Financial Engine | APPROVED | Zero-tolerance for LLM arithmetic in valuations, EBITDA bridges, and leverage metrics. |
| **ADR-004** | Gemini Embedding 2 @ 1536-Dimension Vector Storage | APPROVED | High semantic density with provider abstraction interface for future versioned migrations. |
| **ADR-005** | Celery + Redis for Background Processing | APPROVED | Battle-tested task queue supporting idempotency, retries, job states, and task monitoring. |
| **ADR-006** | LangGraph AI Workflow Orchestration | APPROVED | Deterministic state machine pipelines for multi-step intelligence with strict citation binding. |
| **ADR-007** | Argon2id Password Hashing & JWT Auth | APPROVED | Memory-hard cryptographic hashing with short-lived access tokens and rotated refresh tokens. |
| **ADR-008** | First-Class Evidence & Citation System | APPROVED | Full traceability: Document $\rightarrow$ Version $\rightarrow$ Chunk $\rightarrow$ Cell $\rightarrow$ Finding $\rightarrow$ Recommendation. |
| **ADR-009** | Server-Side Multi-Tenancy & Deal Boundaries | APPROVED | Zero trust client-side: all DB and vector queries enforce `organization_id` & `deal_id`. |
