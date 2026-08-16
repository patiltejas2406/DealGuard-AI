# ADR-008: First-Class Evidence & Citation System

## Context
In investment banking and M&A due diligence, every assertion must be defensible under audit. AI claims without direct line-of-sight to the source document are legally and financially inadmissible.

## Decision
Evidence and citations are first-class domain models in DealGuard AI. Every extracted fact, identified risk, contract clause, and strategic recommendation links directly to an immutable citation containing:
- `document_id` & `document_version_id`
- `page_number` & `section`
- `table_reference` / `cell_reference` (if structured)
- `exact_text_quote` & character span
- `extraction_method` (parser vs regex vs AI)
- `confidence_score`

The UI visually distinguishes: **FACT**, **INFERENCE**, **ASSUMPTION**, **MODEL OUTPUT**, and **RECOMMENDATION**. Unsupported claims trigger an explicit "Insufficient Evidence" state.

## Consequences
- **Positive**: Complete forensic traceability, auditability, zero tolerance for fabricated findings.
- **Negative**: Adds storage and query overhead to link every finding to its source chunk.
- **Status**: APPROVED & FROZEN
