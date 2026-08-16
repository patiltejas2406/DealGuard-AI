# ADR-002: PostgreSQL 16 + pgvector for Relational and Vector Storage

## Context
M&A due diligence demands strict ACID transactions for financial records, risk overrides, and audit trails alongside semantic vector search over document chunks. Maintaining separate databases for relational state and vector embeddings creates synchronization failure modes, dual-backup complexity, and security leakage vectors.

## Decision
Use **PostgreSQL 16** with the **pgvector** extension as the unified system of record. Document chunk embeddings are stored directly in `document_chunks.embedding` with an HNSW/IVFFlat index.

## Alternatives Considered
- **Pinecone / Qdrant / Milvus + Postgres**: Rejected due to dual-system sync lag, operational split-brain risk, and lack of unified SQL transactions.
- **SQLite**: Rejected for production multi-user concurrency and lack of native pgvector indexing.

## Consequences
- **Positive**: Single backup/restore, unified foreign key constraints, atomic transactions joining document metadata with vector similarities, simplified RBAC filtering.
- **Negative**: High-dimensional vector indexing utilizes Postgres memory buffers; mitigated with appropriate `work_mem` and HNSW indexing parameters.
- **Status**: APPROVED & FROZEN
