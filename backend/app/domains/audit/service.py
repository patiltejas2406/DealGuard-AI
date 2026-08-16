"""Audit Trail and Human Review Service."""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.audit.models import AuditEvent, HumanReview


class AuditService:
    """Operations for Recording Monotonic Audit Trails and Human Overrides."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_event(
        self,
        organization_id: uuid.UUID,
        action: str,
        entity_type: str,
        deal_id: Optional[uuid.UUID] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        entity_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            deal_id=deal_id,
            actor_user_id=actor_user_id,
            action=action.upper(),
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            details=details or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def record_human_review(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        target_entity_type: str,
        target_entity_id: uuid.UUID,
        review_action: str,
        rationale: str,
        original_value: Optional[dict] = None,
        reviewed_value: Optional[dict] = None,
    ) -> HumanReview:
        review = HumanReview(
            organization_id=organization_id,
            deal_id=deal_id,
            reviewer_user_id=reviewer_user_id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            review_action=review_action.upper(),
            rationale=rationale,
            original_value=original_value,
            reviewed_value=reviewed_value,
        )
        self.session.add(review)
        await self.session.flush()
        return review
