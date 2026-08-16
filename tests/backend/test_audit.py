"""Tests for Audit Trail and Human-in-the-Loop Review Ledger."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.audit.models import AuditEvent, HumanReview
from app.domains.audit.service import AuditService
from app.domains.auth.models import Organization, User


@pytest.mark.asyncio
async def test_audit_event_logging(db_session: AsyncSession):
    """Verify monotonic audit event creation."""
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deal_id = uuid.uuid4()

    db_session.add(Organization(id=org_id, name="Audit Org", slug="audit-org"))
    db_session.add(User(id=user_id, email="auditor@firm.demo", hashed_password="pw", full_name="Auditor One"))
    await db_session.commit()

    service = AuditService(db_session)
    event = await service.log_event(
        organization_id=org_id,
        deal_id=deal_id,
        actor_user_id=user_id,
        action="VALUATION_ADJUSTED",
        entity_type="Valuation",
        details={"wacc_old": 0.095, "wacc_new": 0.105, "reason": "Fed Rate Hike Adjustment"},
    )
    await db_session.commit()
    event_id = event.id

    result = await db_session.execute(select(AuditEvent).where(AuditEvent.id == event_id))
    retrieved = result.scalar_one()
    assert retrieved.action == "VALUATION_ADJUSTED"
    assert retrieved.details["wacc_new"] == 0.105
    assert retrieved.actor_user_id == user_id


@pytest.mark.asyncio
async def test_human_review_override(db_session: AsyncSession):
    """Verify recording of human override with mandatory rationale."""
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    deal_id = uuid.uuid4()
    risk_id = uuid.uuid4()

    db_session.add(Organization(id=org_id, name="Review Org", slug="review-org"))
    db_session.add(User(id=user_id, email="partner@firm.demo", hashed_password="pw", full_name="Managing Partner"))
    await db_session.commit()

    service = AuditService(db_session)
    review = await service.record_human_review(
        organization_id=org_id,
        deal_id=deal_id,
        reviewer_user_id=user_id,
        target_entity_type="Risk",
        target_entity_id=risk_id,
        review_action="OVERRIDDEN",
        rationale="Customer concentration risk mitigated by 3-year enterprise contract renewal signed yesterday.",
        original_value={"severity": 4, "likelihood": 4},
        reviewed_value={"severity": 2, "likelihood": 2},
    )
    await db_session.commit()
    review_id = review.id

    res = await db_session.execute(select(HumanReview).where(HumanReview.id == review_id))
    retrieved_review = res.scalar_one()
    assert retrieved_review.review_action == "OVERRIDDEN"
    assert "Customer concentration risk mitigated" in retrieved_review.rationale
