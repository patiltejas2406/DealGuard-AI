"""Comprehensive Test Suite for Phase 7: 17-Pillar Deal Risk Intelligence Engine."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.risk.scoring import (
    RiskScoringError,
    calculate_risk_evaluation,
    compute_risk_matrix,
    compute_risk_score,
    determine_risk_level,
)
from app.domains.risk.taxonomy import (
    CATEGORY_METADATA,
    RiskCategory,
    RiskLevel,
    RiskStatus,
)


# ==========================================
# 1. Deterministic Scoring & Taxonomy Tests
# ==========================================

def test_all_17_categories_defined():
    """Verify all 17 M&A risk pillars are defined with comprehensive metadata."""
    assert len(RiskCategory) == 17
    assert len(CATEGORY_METADATA) == 17

    expected_categories = [
        "CUSTOMER_CONCENTRATION",
        "KEY_PERSON",
        "LEGAL_LITIGATION",
        "REGULATORY",
        "CYBERSECURITY",
        "TECHNOLOGY_DEBT",
        "ESG",
        "RESTATEMENT",
        "SUPPLY_CHAIN",
        "IP_INFRINGEMENT",
        "TAX",
        "MACRO_FX",
        "LABOR_WORKFORCE",
        "CHANGE_OF_CONTROL",
        "DEBT_COVENANTS",
        "REVENUE_QUALITY",
        "INTEGRATION_COMPLEXITY",
    ]

    for cat_name in expected_categories:
        cat_enum = RiskCategory(cat_name)
        assert cat_enum in CATEGORY_METADATA
        meta = CATEGORY_METADATA[cat_enum]
        assert len(meta.signals) > 0
        assert len(meta.default_mitigation) > 10


def test_deterministic_scoring_exact_matrices():
    """Verify exact 1x1 to 5x5 deterministic scoring and level mappings."""
    # 1x1 = 1 -> LOW
    score, level = calculate_risk_evaluation(1, 1)
    assert score == 1
    assert level == RiskLevel.LOW

    # 2x2 = 4 -> LOW (boundary)
    score, level = calculate_risk_evaluation(2, 2)
    assert score == 4
    assert level == RiskLevel.LOW

    # 1x5 = 5 -> MODERATE
    score, level = calculate_risk_evaluation(1, 5)
    assert score == 5
    assert level == RiskLevel.MODERATE

    # 3x3 = 9 -> MODERATE (boundary)
    score, level = calculate_risk_evaluation(3, 3)
    assert score == 9
    assert level == RiskLevel.MODERATE

    # 2x5 = 10 -> HIGH (boundary)
    score, level = calculate_risk_evaluation(2, 5)
    assert score == 10
    assert level == RiskLevel.HIGH

    # 3x4 = 12 -> HIGH
    score, level = calculate_risk_evaluation(3, 4)
    assert score == 12
    assert level == RiskLevel.HIGH

    # 3x5 = 15 -> CRITICAL (boundary)
    score, level = calculate_risk_evaluation(3, 5)
    assert score == 15
    assert level == RiskLevel.CRITICAL

    # 4x4 = 16 -> CRITICAL
    score, level = calculate_risk_evaluation(4, 4)
    assert score == 16
    assert level == RiskLevel.CRITICAL

    # 5x5 = 25 -> CRITICAL
    score, level = calculate_risk_evaluation(5, 5)
    assert score == 25
    assert level == RiskLevel.CRITICAL


def test_scoring_boundary_and_invalid_inputs():
    """Verify out-of-bound or invalid scoring parameters raise RiskScoringError."""
    with pytest.raises(RiskScoringError):
        compute_risk_score(0, 3)

    with pytest.raises(RiskScoringError):
        compute_risk_score(6, 3)

    with pytest.raises(RiskScoringError):
        compute_risk_score(3, -1)

    with pytest.raises(RiskScoringError):
        compute_risk_score(3, 7)

    with pytest.raises(RiskScoringError):
        determine_risk_level(0)

    with pytest.raises(RiskScoringError):
        determine_risk_level(26)


def test_compute_risk_matrix_aggregation():
    """Verify 5x5 heatmap aggregation and summary calculations."""
    class DummyRisk:
        def __init__(self, id_val, cat, s, l):
            self.id = id_val
            self.title = f"Risk {id_val}"
            self.category = cat
            self.severity = s
            self.likelihood = l
            self.score = s * l
            self.risk_level = determine_risk_level(self.score).value
            self.status = "IDENTIFIED"

    risks = [
        DummyRisk("r1", "CUSTOMER_CONCENTRATION", 5, 5),  # 25, CRITICAL
        DummyRisk("r2", "KEY_PERSON", 3, 3),              # 9, MODERATE
        DummyRisk("r3", "CYBERSECURITY", 2, 2),           # 4, LOW
        DummyRisk("r4", "LEGAL_LITIGATION", 4, 3),        # 12, HIGH
    ]

    matrix = compute_risk_matrix(risks)
    assert matrix["total_risks"] == 4
    assert matrix["level_counts"]["CRITICAL"] == 1
    assert matrix["level_counts"]["HIGH"] == 1
    assert matrix["level_counts"]["MODERATE"] == 1
    assert matrix["level_counts"]["LOW"] == 1
    assert len(matrix["matrix_grid"][5][5]) == 1
    assert len(matrix["matrix_grid"][3][3]) == 1


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_risk_env(db_session: AsyncSession):
    """Seed authenticated organization, deal workspace, and lead analyst."""
    org = Organization(name="Blackstone Strategic", slug="blackstone-strategic", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Deal Analyst", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="risk.lead@blackstone.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Alexander Hamilton",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(membership)
    await db_session.flush()

    target = TargetCompany(
        organization_id=org.id,
        name="Apex Enterprise SaaS",
        industry="Enterprise Software",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project Apex Risk Diligence",
        target_ev=65000000.0,
        currency="USD",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    db_session.add(DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD",
    ))

    # Create dummy document and chunks for scanner tests
    doc = Document(
        organization_id=org.id,
        deal_id=deal.id,
        name="Apex_Diligence_Disclosures.pdf",
        file_type="PDF",
        mime_type="application/pdf",
        size_bytes=2048,
        storage_path="/docs/apex.pdf",
        sha256_hash="abc123hash456789",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk1 = DocumentChunk(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        chunk_index=0,
        page_number=4,
        section_title="Note 7: Key Customers & Revenue Dependency",
        content="The company has significant customer concentration with its top customer accounting for 38% of total annual recurring revenue in fiscal year 2023.",
    )
    chunk2 = DocumentChunk(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        chunk_index=1,
        page_number=12,
        section_title="Note 14: Legal Proceedings",
        content="There is an active lawsuit and patent infringement claim filed by CompetitorCorp regarding proprietary machine learning indexing algorithms.",
    )
    db_session.add_all([chunk1, chunk2])
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ANALYST")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "doc": doc,
        "chunk1": chunk1,
        "chunk2": chunk2,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_risk_api_crud_workflow(seed_risk_env, async_client: AsyncClient):
    """Verify complete CRUD lifecycle, deterministic scoring, and status updates via REST API."""
    env = seed_risk_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. List risks (initially empty)
    res = await async_client.get(f"/api/v1/deals/{deal_id}/risks", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0

    # 2. Create manual risk (Customer Concentration: Severity 4, Likelihood 3 -> Score 12, HIGH)
    create_payload = {
        "category": "CUSTOMER_CONCENTRATION",
        "title": "Top Customer Accounts for 38% ARR",
        "description": "High revenue cliff risk if anchor client cancels subscription.",
        "severity": 4,
        "likelihood": 3,
        "status": "IDENTIFIED",
        "detection_source": "MANUAL_ENTRY",
        "mitigation_strategy": "Structure 20% purchase price escrow tied to contract renewal.",
        "recommendation": "Require anchor client renewal before definitive agreement closing.",
    }
    create_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/risks", json=create_payload, headers=headers
    )
    assert create_res.status_code == 201
    risk_data = create_res.json()
    assert risk_data["category"] == "CUSTOMER_CONCENTRATION"
    assert risk_data["severity"] == 4
    assert risk_data["likelihood"] == 3
    assert risk_data["score"] == 12
    assert risk_data["risk_level"] == "HIGH"
    risk_id = risk_data["id"]

    # 3. Retrieve single risk
    get_res = await async_client.get(f"/api/v1/deals/{deal_id}/risks/{risk_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == risk_id

    # 4. Update risk severity/likelihood (Severity 5, Likelihood 4 -> Score 20, CRITICAL)
    update_payload = {
        "severity": 5,
        "likelihood": 4,
        "title": "Severe Customer Concentration: 38% ARR with Single Account",
    }
    put_res = await async_client.put(
        f"/api/v1/deals/{deal_id}/risks/{risk_id}", json=update_payload, headers=headers
    )
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["severity"] == 5
    assert updated_data["likelihood"] == 4
    assert updated_data["score"] == 20
    assert updated_data["risk_level"] == "CRITICAL"

    # 5. Patch status (Transition to REVIEWED)
    status_payload = {
        "status": "REVIEWED",
        "rationale": "Diligence team confirmed customer renewal status with anchor client.",
    }
    patch_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/risks/{risk_id}/status", json=status_payload, headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "REVIEWED"

    # 6. Fetch 5x5 Matrix
    matrix_res = await async_client.get(f"/api/v1/deals/{deal_id}/risks/matrix", headers=headers)
    assert matrix_res.status_code == 200
    matrix_json = matrix_res.json()
    assert matrix_json["total_risks"] == 1
    assert matrix_json["level_counts"]["CRITICAL"] == 1

    # 7. Fetch Taxonomy Categories
    cat_res = await async_client.get(f"/api/v1/deals/{deal_id}/risks/categories", headers=headers)
    assert cat_res.status_code == 200
    assert len(cat_res.json()) == 17

    # 8. Delete risk
    del_res = await async_client.delete(f"/api/v1/deals/{deal_id}/risks/{risk_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_again = await async_client.get(f"/api/v1/deals/{deal_id}/risks/{risk_id}", headers=headers)
    assert get_again.status_code == 404


@pytest.mark.asyncio
async def test_automated_document_risk_scanner(seed_risk_env, async_client: AsyncClient):
    """Verify automated document risk scanner detects signals and links verifiable citations."""
    env = seed_risk_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # Trigger Automated Detection Scan
    detect_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/risks/detect",
        json={"min_confidence": 0.50},
        headers=headers,
    )
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    assert detect_data["scanned_chunks_count"] == 2
    assert detect_data["detected_count"] >= 2
    assert detect_data["created_count"] >= 2

    # Verify risks contain citations with exact quotes
    risks = detect_data["risks"]
    has_customer_conc = any(r["category"] == "CUSTOMER_CONCENTRATION" for r in risks)
    has_ip_litigation = any(r["category"] in ["LEGAL_LITIGATION", "IP_INFRINGEMENT"] for r in risks)
    assert has_customer_conc is True
    assert has_ip_litigation is True

    # Check evidence citations attached
    sample_risk = next(r for r in risks if r["category"] == "CUSTOMER_CONCENTRATION")
    assert len(sample_risk["evidence_items"]) > 0
    cit = sample_risk["evidence_items"][0]["citation"]
    assert cit is not None
    assert "top customer" in cit["exact_quote"].lower()
    assert cit["page_number"] == 4

    # Test Duplicate Scan Idempotency (Running scan again skips duplicates)
    rescan_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/risks/detect",
        json={"min_confidence": 0.50},
        headers=headers,
    )
    assert rescan_res.status_code == 200
    rescan_data = rescan_res.json()
    assert rescan_data["created_count"] == 0
    assert rescan_data["duplicates_skipped"] >= 2


@pytest.mark.asyncio
async def test_risk_tenant_isolation(seed_risk_env, async_client: AsyncClient):
    """Verify strict tenant isolation prevents unauthorized cross-tenant risk access."""
    env = seed_risk_env
    deal_id = env["deal"].id

    foreign_org_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()

    foreign_token = create_access_token(
        subject=str(foreign_user_id), org_id=str(foreign_org_id), role="ANALYST"
    )
    foreign_headers = {
        "Authorization": f"Bearer {foreign_token}",
        "X-Organization-ID": str(foreign_org_id),
    }

    # Attempt to read risks from foreign organization
    res = await async_client.get(f"/api/v1/deals/{deal_id}/risks", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]
