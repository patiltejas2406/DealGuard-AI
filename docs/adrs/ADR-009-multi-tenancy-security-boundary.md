# ADR-009: Server-Side Multi-Tenancy & Deal Security Boundaries

## Context
M&A data rooms contain strictly confidential non-public material information (MNPI). Data leakage across organizations or between deal teams within the same organization can violate federal securities laws, NDAs, and fiduciary duties.

## Decision
Multi-tenancy and authorization are enforced strictly server-side:
1. **Organization Boundary**: All relational queries and API access filters enforce `organization_id`.
2. **Deal Boundary**: Access to deals requires verified membership in `deal_members` with specific assigned roles (`Admin`, `Lead`, `Analyst`, `Legal`, `Auditor`).
3. **Vector Boundary**: Vector similarity searches MUST include hard SQL/metadata filters for `organization_id` and `deal_id` before computing similarity or returning chunks.
4. **Storage Boundary**: Documents in S3/MinIO are organized under `/{org_id}/{deal_id}/{doc_id}` and accessible solely via short-lived, pre-signed URLs generated after verifying the user's deal permissions.

## Consequences
- **Positive**: Strict data isolation, compliance with M&A confidentiality standards, zero cross-tenant vector leakage.
- **Negative**: Requires strict middleware and repository-layer enforcement and automated regression testing.
- **Status**: APPROVED & FROZEN
