"""Comprehensive Test Suite for Phase 12: Legal, Contract & Compliance Diligence Intelligence Engine."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Document, DocumentChunk
from app.domains.legal.config import (
    ContractCategory,
    LegalFindingStatus,
    validate_finding_transition,
)
from app.domains.legal.exposure import calculate_contract_value_at_risk
from app.domains.legal.scanner import (
    compute_clause_fingerprint,
    extract_clauses_from_chunks,
    generate_baseline_compliance_matrix,
)


# ==========================================
# 1. Deterministic Extraction & Algorithm Tests
# ==========================================

def test_clause_extraction_and_fingerprint_idempotency():
    """Verify deterministic keyword clause extraction, category tagging, and SHA-256 fingerprinting."""
    deal_id = uuid.uuid4()
    org_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    class MockChunk:
        def __init__(self, content, page=1):
            self.id = uuid.uuid4()
            self.document_id = doc_id
            self.content = content
            self.page_number = page
            self.section_name = "Section 12: General Terms"

    chunks = [
        MockChunk("In the event of a change of control, merger, consolidation, or sale of all or substantially all assets, prior written consent of Customer shall be required."),
        MockChunk("Executive agrees that during the term and for 12 months following separation, Executive shall not engage in competing business in the restricted territory."),
        MockChunk("All software, source code, and deliverables created hereunder shall be deemed a work made for hire, and Vendor irrevocably assigns all right, title and interest to Company."),
    ]

    clauses, findings = extract_clauses_from_chunks(chunks, deal_id, org_id, user_id=None)

    assert len(clauses) == 3
    assert len(findings) == 3

    # Check categories
    categories = [c["category"] for c in clauses]
    assert ContractCategory.CHANGE_OF_CONTROL.value in categories
    assert ContractCategory.NON_COMPETE.value in categories
    assert ContractCategory.IP_OWNERSHIP.value in categories

    # Verify Change of Control consent requirement
    coc_clause = next(c for c in clauses if c["category"] == ContractCategory.CHANGE_OF_CONTROL.value)
    assert coc_clause["requires_consent"] is True
    assert coc_clause["severity"] == "CRITICAL"

    # Verify fingerprint determinism (re-running produces identical fingerprints)
    fp1 = compute_clause_fingerprint(deal_id, doc_id, ContractCategory.CHANGE_OF_CONTROL.value, chunks[0].content)
    fp2 = compute_clause_fingerprint(deal_id, doc_id, ContractCategory.CHANGE_OF_CONTROL.value, chunks[0].content)
    assert fp1 == fp2
    assert coc_clause["fingerprint"] == fp1


def test_deterministic_contract_value_at_risk_calculation():
    """Verify calculation of exposed contract revenue based on change-of-control consent requirements."""
    class MockContract:
        def __init__(self, cid, val):
            self.id = cid
            self.annual_value = val

    class MockClause:
        def __init__(self, cid, cat, req_consent, sev="HIGH"):
            self.contract_id = cid
            self.category = cat
            self.requires_consent = req_consent
            self.severity = sev

    class MockFinding:
        def __init__(self, cid, status, sev="HIGH"):
            self.contract_id = cid
            self.status = status
            self.severity = sev

    c1 = uuid.uuid4()  # $5M contract with Change of Control consent
    c2 = uuid.uuid4()  # $2M contract with standard terms
    c3 = uuid.uuid4()  # $3M contract with Termination Right
    contracts = [MockContract(c1, 5000000.0), MockContract(c2, 2000000.0), MockContract(c3, 3000000.0)]

    clauses = [
        MockClause(c1, "CHANGE_OF_CONTROL", req_consent=True, sev="CRITICAL"),
        MockClause(c3, "TERMINATION_RIGHT", req_consent=False, sev="CRITICAL"),
    ]
    findings = [
        MockFinding(c1, "IDENTIFIED", "CRITICAL"),
    ]

    exposure = calculate_contract_value_at_risk(contracts, clauses, findings)
    assert exposure["total_annual_contract_value"] == 10000000.0
    assert exposure["revenue_at_risk"] == 8000000.0  # c1 ($5M) + c3 ($3M)
    assert exposure["revenue_at_risk_pct"] == 80.0
    assert exposure["contracts_at_risk_count"] == 2
    assert exposure["change_of_control_contracts_count"] == 1
    assert exposure["consents_required_count"] == 1


def test_legal_finding_lifecycle_state_machine():
    """Verify legal finding status state transitions."""
    # Valid transitions
    validate_finding_transition(LegalFindingStatus.IDENTIFIED.value, LegalFindingStatus.REQUIRES_REVIEW.value)
    validate_finding_transition(LegalFindingStatus.REQUIRES_REVIEW.value, LegalFindingStatus.ACTION_PLANNED.value)
    validate_finding_transition(LegalFindingStatus.ACTION_PLANNED.value, LegalFindingStatus.CONSENT_OBTAINED.value)
    validate_finding_transition(LegalFindingStatus.CONSENT_OBTAINED.value, LegalFindingStatus.MITIGATED.value)

    # Invalid transitions
    with pytest.raises(ValueError, match="Illegal legal finding transition"):
        validate_finding_transition(LegalFindingStatus.IDENTIFIED.value, LegalFindingStatus.CONSENT_OBTAINED.value)


def test_compliance_matrix_generation():
    """Verify compliance requirements generated across major frameworks."""
    deal_id = uuid.uuid4()
    org_id = uuid.uuid4()

    comp_items = generate_baseline_compliance_matrix(deal_id, org_id, user_id=None, detected_privacy_evidence=True, detected_ip_evidence=True)
    assert len(comp_items) >= 4

    frameworks = [item["framework"] for item in comp_items]
    assert "GDPR" in frameworks
    assert "SOC2" in frameworks
    assert "EMPLOYMENT_LABOR" in frameworks
    assert "CYBERSECURITY" in frameworks

    gdpr = next(i for i in comp_items if i["framework"] == "GDPR")
    assert gdpr["status"] == "EVIDENCE_PRESENT"


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_legal_env(db_session: AsyncSession):
    """Seed deal workspace with target company, documents, and document chunks."""
    org = Organization(name="Sequoia Capital Flagship", slug="sequoia-legal-demo", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Legal Diligence Lead", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="general.counsel@sequoia.demo",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Roelof Botha",
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
        name="CloudShield Networks",
        industry="Enterprise Security & Infrastructure",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project CloudShield Legal Diligence",
        target_ev=180000000.0,
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

    # Add sample ingested contract document and chunk
    doc = Document(
        organization_id=org.id,
        deal_id=deal.id,
        name="Apex_Customer_Master_Agreement.pdf",
        file_type="PDF",
        mime_type="application/pdf",
        size_bytes=102400,
        storage_path="/data/Apex_Customer_Master_Agreement.pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status="PROCESSED",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        chunk_index=0,
        page_number=14,
        section_title="Section 14.2: Assignment and Change of Control",
        content="Section 14.2: In the event of a change of control, merger, or acquisition of more than 50% of voting shares, Customer must be provided 30 days prior written notice and prior written consent shall be required.",
        token_count=45,
    )
    db_session.add(chunk)
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ANALYST")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "doc": doc,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_legal_api_full_workflow(seed_legal_env, async_client: AsyncClient):
    """Verify complete legal diligence API workflow: scan, contract listing, clause review, change of control console, finding status update, and summary metrics."""
    env = seed_legal_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Trigger Legal Scan
    scan_res = await async_client.post(f"/api/v1/deals/{deal_id}/legal/scan", headers=headers)
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["clauses_extracted"] >= 1
    assert scan_data["findings_generated"] >= 1

    # 2. List Extracted Contracts
    contracts_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/contracts", headers=headers)
    assert contracts_res.status_code == 200
    contracts = contracts_res.json()
    assert len(contracts) >= 1
    assert contracts[0]["has_change_of_control"] is True

    # 3. List Extracted Clauses
    clauses_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/clauses", headers=headers)
    assert clauses_res.status_code == 200
    clauses = clauses_res.json()
    assert len(clauses) >= 1
    assert any(c["category"] == "CHANGE_OF_CONTROL" for c in clauses)

    # 4. Check Change of Control Console
    coc_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/change-of-control", headers=headers)
    assert coc_res.status_code == 200
    coc_data = coc_res.json()
    assert coc_data["total_change_of_control_contracts"] >= 1
    assert coc_data["total_consents_required"] >= 1

    # 5. List Compliance Matrix
    comp_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/compliance", headers=headers)
    assert comp_res.status_code == 200
    comp_items = comp_res.json()
    assert len(comp_items) >= 4

    # 6. List Findings & Update Status
    findings_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/findings", headers=headers)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 1
    finding_id = findings[0]["id"]

    patch_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/legal/findings/{finding_id}/status",
        headers=headers,
        json={"status": "REQUIRES_REVIEW", "notes": "Escalated to deal lead"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "REQUIRES_REVIEW"

    # 7. Executive Legal Summary
    sum_res = await async_client.get(f"/api/v1/deals/{deal_id}/legal/summary", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_contracts_reviewed"] >= 1
    assert summary["change_of_control_contracts_count"] >= 1


@pytest.mark.asyncio
async def test_legal_tenant_isolation(seed_legal_env, async_client: AsyncClient):
    """Verify cross-tenant requests to access legal findings or trigger scans are strictly blocked."""
    env = seed_legal_env
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

    res = await async_client.get(f"/api/v1/deals/{deal_id}/legal", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    scan_res = await async_client.post(f"/api/v1/deals/{deal_id}/legal/scan", headers=foreign_headers)
    assert scan_res.status_code in [401, 403, 404]
