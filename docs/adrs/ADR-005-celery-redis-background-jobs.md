# ADR-005: Celery + Redis for Background Processing

## Context
Document parsing, OCR, table extraction, chunk embedding generation, and report rendering are computationally heavy and I/O-intensive operations that must not block synchronous HTTP request cycles.

## Decision
We select **Celery + Redis** as the unified task queue and background execution engine. Background jobs will enforce idempotency, persistent state tracking (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `RETRYING`, `CANCELLED`), retry backoff policies, and task progress events.

## Alternatives Considered
- **ARQ / RQ**: Rejected in favor of Celery's richer ecosystem, broad broker support, and institutional tooling.
- **Synchronous background threads (`BackgroundTasks` in FastAPI)**: Rejected for heavy jobs because they share memory and lifecycle with the web process.

## Consequences
- **Positive**: Resilient asynchronous execution, isolated worker memory pools, explicit task state visibility.
- **Negative**: Requires running Redis and Celery worker processes.
- **Status**: APPROVED & FROZEN
