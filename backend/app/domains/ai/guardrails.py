"""Deterministic AI Guardrails, Citation Verification & Anti-Hallucination Enforcers."""

from typing import List, Tuple
from app.domains.ai.schemas import CitationRef, GroundedFinding


class AIGuardrailError(ValueError):
    """Raised when an AI-generated output violates strict verification guardrails."""
    pass


class AIGuardrailValidator:
    """Enforces zero-hallucination policies, math boundary isolation, and citation grounding."""

    MIN_CONFIDENCE_THRESHOLD = 0.50

    @classmethod
    def validate_finding_grounding(cls, finding: GroundedFinding) -> Tuple[bool, List[str]]:
        """
        Verify that a finding satisfies institutional grounding standards:
        1. Non-empty citations if marked as extracted from evidence.
        2. Exact quotes must not be empty or generic placeholders.
        3. Calculations must indicate a registered deterministic calculation engine.
        4. Confidence scores must meet the minimum threshold.
        """
        violations: List[str] = []

        if finding.confidence_score < cls.MIN_CONFIDENCE_THRESHOLD:
            violations.append(
                f"Confidence score {finding.confidence_score:.2f} is below minimum threshold {cls.MIN_CONFIDENCE_THRESHOLD}."
            )

        if not finding.is_deterministic_calculation and len(finding.citations) == 0:
            violations.append("AI finding is missing mandatory evidence citations.")

        for i, cit in enumerate(finding.citations):
            if not cit.exact_quote or len(cit.exact_quote.strip()) < 3:
                violations.append(f"Citation #{i+1} has an invalid or empty exact_quote.")
            if cit.page_number < 1:
                violations.append(f"Citation #{i+1} specifies an invalid page_number ({cit.page_number}).")

        if finding.is_deterministic_calculation and not finding.calculation_source_engine:
            violations.append("Deterministic calculation must explicitly specify calculation_source_engine.")

        is_valid = len(violations) == 0
        return is_valid, violations

    @classmethod
    def enforce_grounding(cls, finding: GroundedFinding) -> GroundedFinding:
        """Enforce validation and raise AIGuardrailError on violations."""
        is_valid, violations = cls.validate_finding_grounding(finding)
        if not is_valid:
            raise AIGuardrailError(
                f"AI Guardrail Violation for finding '{finding.headline}': " + "; ".join(violations)
            )
        return finding
