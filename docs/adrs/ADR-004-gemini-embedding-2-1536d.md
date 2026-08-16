# ADR-004: Gemini Embedding 2 @ 1536 Dimensions with Provider Abstraction

## Context
Semantic retrieval requires high-quality vector embeddings across dense financial filings and complex contract clauses. Mixing embedding models or dimensions in a single vector table corrupts cosine distance metrics.

## Decision
We standardize on **Gemini Embedding 2** configured at **1536 dimensions** (`vector(1536)`) for the initial pgvector schema. All embedding operations are encapsulated behind a clean provider interface (`EmbeddingProvider` ABC) storing metadata: `provider`, `model`, `dimensionality`, and `embedding_version`. Future model changes will be treated as explicit versioned schema migrations.

## Alternatives Considered
- **Multiple simultaneous unversioned embedding providers**: Rejected to prevent vector space corruption.
- **Legacy embedding-001**: Rejected as deprecated.

## Consequences
- **Positive**: Consistent semantic representation, high embedding quality, clean migration boundary.
- **Negative**: Re-indexing required if the primary embedding model is migrated in the future.
- **Status**: APPROVED & FROZEN
