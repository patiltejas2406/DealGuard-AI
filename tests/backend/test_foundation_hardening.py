"""Tests for Foundation Hardening, Company Lifecycle, AI Guardrails, and Decision Lineage."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.ai.guardrails import AIGuardrailError, AIGuardrailValidator
from app.domains.ai.schemas import CitationRef, GroundedFinding, GroundedRecommendation
from app.domains.common.lineage import ClosedLoopDecisionTrace, PredictionMetadata
from app.domains.auth.models import Organization
from app.domains.deals.models import Deal, TargetCompany
from app.domains.documents.models import Citation, Document


@pytest.mark.asyncio
async def test_target_company_lifecycle_defaults(db_session: AsyncSession):
    """Verify TargetCompany model supports long-term lifecycle evolution without breaking defaults."""
    org = Organization(name="Acme Holdings", slug="acme-holdings")
    db_session.add(org)
    await db_session.flush()

    company = TargetCompany(
        organization_id=org.id,
        name="Acme Health Tech",
        industry="Healthcare",
    )
    db_session.add(company)
    await db_session.flush()

    assert company.company_type == "TARGET_ACQUISITION"
    assert company.lifecycle_stage == "DILIGENCE"

    # Verify transitions to post-acquisition & portfolio company monitoring
    company.lifecycle_stage = "ACQUIRED"
    company.company_type = "PORTFOLIO_COMPANY"
    await db_session.flush()

    res = await db_session.execute(select(TargetCompany).where(TargetCompany.id == company.id))
    retrieved = res.scalar_one()
    assert retrieved.lifecycle_stage == "ACQUIRED"
    assert retrieved.company_type == "PORTFOLIO_COMPANY"


@pytest.mark.asyncio
async def test_citation_source_entity_type_default(db_session: AsyncSession):
    """Verify Citation model supports cross-domain evidence grounding."""
    org = Organization(name="Veritas PE", slug="veritas-pe")
    db_session.add(org)
    await db_session.flush()

    target = TargetCompany(organization_id=org.id, name="Target Corp", industry="SaaS")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(organization_id=org.id, target_company_id=target.id, title="Project Veritas")
    db_session.add(deal)
    await db_session.flush()

    doc = Document(
        organization_id=org.id,
        deal_id=deal.id,
        name="annual_report.pdf",
        file_type="PDF",
        mime_type="application/pdf",
        size_bytes=1024,
        storage_path="/docs/test.pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(doc)
    await db_session.flush()

    citation = Citation(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        page_number=3,
        exact_quote="Top customer churn rate declined to 2.1%.",
    )
    db_session.add(citation)
    await db_session.flush()

    assert citation.source_entity_type == "DOCUMENT"
    citation.source_entity_type = "CONTRACT_CLAUSE"
    await db_session.flush()

    res = await db_session.execute(select(Citation).where(Citation.id == citation.id))
    retrieved = res.scalar_one()
    assert retrieved.source_entity_type == "CONTRACT_CLAUSE"


def test_ai_guardrails_grounding_valid():
    """Verify AI Guardrail accepts strictly grounded findings with valid citations."""
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()
    finding = GroundedFinding(
        domain_pillar="RISK",
        category="CUSTOMER_CONCENTRATION",
        headline="Top 3 Customers Account for 42% of ARR",
        detailed_reasoning="SEC Note 8 disclosure confirms high revenue dependency on three key accounts.",
        confidence_score=0.95,
        is_deterministic_calculation=False,
        citations=[
            CitationRef(
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=18,
                exact_quote="three customers accounted for 18%, 14%, and 10% of total consolidated revenues",
                confidence_score=0.98,
            )
        ],
    )
    is_valid, violations = AIGuardrailValidator.validate_finding_grounding(finding)
    assert is_valid is True
    assert len(violations) == 0

    validated = AIGuardrailValidator.enforce_grounding(finding)
    assert validated.headline == finding.headline


def test_ai_guardrails_catches_ungrounded_and_low_confidence():
    """Verify AI Guardrail rejects ungrounded hallucinations or low confidence scores."""
    # 1. Missing citations on non-deterministic extraction
    finding_no_citations = GroundedFinding(
        domain_pillar="RISK",
        category="TECH_DEBT",
        headline="Legacy Monolith Risk",
        detailed_reasoning="Assumed legacy technology stack.",
        confidence_score=0.85,
        is_deterministic_calculation=False,
        citations=[],
    )
    is_valid, violations = AIGuardrailValidator.validate_finding_grounding(finding_no_citations)
    assert is_valid is False
    assert any("missing mandatory evidence citations" in v for v in violations)

    with pytest.raises(AIGuardrailError):
        AIGuardrailValidator.enforce_grounding(finding_no_citations)

    # 2. Confidence below threshold
    finding_low_conf = GroundedFinding(
        domain_pillar="FINANCIAL",
        category="REVENUE",
        headline="Possible Unrecorded Liabilities",
        detailed_reasoning="Uncertain text snippet.",
        confidence_score=0.40,  # Below 0.50 threshold
        citations=[
            CitationRef(
                document_id=uuid.uuid4(),
                page_number=1,
                exact_quote="Some ambiguous text",
            )
        ],
    )
    is_valid, violations = AIGuardrailValidator.validate_finding_grounding(finding_low_conf)
    assert is_valid is False
    assert any("below minimum threshold" in v for v in violations)


def test_closed_loop_decision_lineage():
    """Verify ClosedLoopDecisionTrace and PredictionMetadata record complete observe-to-outcome lifecycle."""
    org_id = uuid.uuid4()
    deal_id = uuid.uuid4()
    citation_id = uuid.uuid4()

    trace = ClosedLoopDecisionTrace(
        organization_id=org_id,
        deal_id=deal_id,
        evidence_citation_ids=[citation_id],
        prediction=PredictionMetadata(
            model_name="dealguard-decision-score",
            model_version="1.0.0",
            prediction_type="INDEX_SCORE",
            confidence_score=0.92,
        ),
        predicted_value=78.5,
        recommended_action="Proceed to Confirmatory Diligence with 15% earnout escrow.",
        recommendation_rationale="High customer concentration partially mitigated by strong EBITDA margins.",
        human_approval_status="APPROVED",
        action_executed=True,
    )

    assert trace.prediction.model_name == "dealguard-decision-score"
    assert trace.predicted_value == 78.5
    assert trace.human_approval_status == "APPROVED"
    assert trace.action_executed is True
