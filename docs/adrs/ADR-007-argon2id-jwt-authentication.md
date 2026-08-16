# ADR-007: Argon2id Password Hashing and JWT Session Management

## Context
DealGuard AI handles confidential M&A transaction documents, valuation models, and strategy data. Storing passwords insecurely or using weak authentication schemes presents unacceptable vulnerability.

## Decision
Use **Argon2id** (the memory-hard winner of the Password Hashing Competition) for all application-managed credential hashing. Session authentication uses short-lived JWT access tokens (15 minutes) with rotating refresh tokens stored in secure, HttpOnly, SameSite cookies. Token revocation and session invalidation are enforced server-side.

## Alternatives Considered
- **Plain SHA-256 / MD5 / standard bcrypt**: Rejected in favor of modern Argon2id with resistance to GPU/ASIC attacks.
- **Pure long-lived API tokens**: Rejected for web user sessions to mitigate token theft exposure.

## Consequences
- **Positive**: High cryptographic security, resistance to offline brute-force attacks, robust session invalidation.
- **Negative**: Argon2id requires memory/CPU overhead per hash verification (tuned for ~100ms per verification).
- **Status**: APPROVED & FROZEN
