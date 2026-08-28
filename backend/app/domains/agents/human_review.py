"""Human-in-the-Loop (HITL) Governance & Escalation Contracts."""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class HumanReviewTrigger(str, Enum):
    """Conditions triggering mandatory human review escalation."""
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MATERIAL_RISK_DETECTED = "MATERIAL_RISK_DETECTED"
    VALUATION_DISCREPANCY = "VALUATION_DISCREPANCY"
    LEGAL_CONSENT_BLOCKER = "LEGAL_CONSENT_BLOCKER"
    TECH_SPOF_CRITICAL = "TECH_SPOF_CRITICAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    MANDATORY_GOVERNANCE_GATE = "MANDATORY_GOVERNANCE_GATE"
    HIGH_MONETARY_EXPOSURE = "HIGH_MONETARY_EXPOSURE"


class EscalationSeverity(str, Enum):
    """Severity of a human review escalation."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EscalationStatus(str, Enum):
    """Status of human review escalation."""
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISMISSED = "DISMISSED"


class HumanReviewEscalation(BaseModel):
    """Actionable human review request emitted by agent systems."""
    escalation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    deal_id: uuid.UUID
    agent_id: str
    trigger: HumanReviewTrigger
    severity: EscalationSeverity = EscalationSeverity.HIGH
    title: str
    reason: str
    unresolved_questions: List[str] = Field(default_factory=list)
    recommended_human_action: str
    status: EscalationStatus = EscalationStatus.PENDING
    reviewed_by_id: Optional[uuid.UUID] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class HumanReviewEvaluator:
    """Evaluates agent assessments against institutional governance thresholds."""

    @classmethod
    def evaluate_escalation_needed(
        cls,
        confidence_score: float,
        critical_issues_count: int,
        unresolved_issues: List[str],
        has_insufficient_evidence: bool,
    ) -> tuple[bool, List[str], str]:
        """
        Determines if human review is required and generates rationale.
        """
        reasons: List[str] = []

        if has_insufficient_evidence:
            reasons.append("Data room records contain insufficient evidence for definitive automated assessment.")

        if confidence_score < 0.70:
            reasons.append(f"Assessment confidence ({confidence_score:.2f}) is below automated threshold (0.70).")

        if critical_issues_count > 0:
            reasons.append(f"Identified {critical_issues_count} critical severity findings requiring senior analyst sign-off.")

        if len(unresolved_issues) >= 2:
            reasons.append(f"{len(unresolved_issues)} unresolved material diligence questions remain open.")

        is_required = len(reasons) > 0
        recommended_action = (
            "Escalate to Deal Diligence Committee for manual verification and confirmation."
            if is_required
            else "Proceed with standard analytical review."
        )

        return is_required, reasons, recommended_action
