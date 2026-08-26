"""Comprehensive Test Suite for Phase 13: Operational, Technology & Product Architecture Diligence."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Document, DocumentChunk
from app.domains.technology.analytics import (
    calculate_cloud_cost_summary,
    calculate_technology_risk_score,
)
from app.domains.technology.config import (
    TechFindingStatus,
    TechnologyCategory,
    validate_tech_transition,
)
from app.domains.technology.scanner import (
    compute_tech_fingerprint,
    extract_technology_findings_from_chunks,
)


# ==========================================
# 1. Deterministic Extraction & Algorithm Tests
# ==========================================

def test_tech_finding_extraction_and_fingerprinting():
    """Verify deterministic technology keyword extraction and SHA-256 fingerprinting."""
    deal_id = uuid.uuid4()
    org_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    class MockChunk:
        def __init__(self, content, page=1):
            self.id = uuid.uuid4()
            self.document_id = doc_id
            self.content = content
            self.page_number = page
            self.section_title = "Architecture & Infrastructure Overview"

    chunks = [
        MockChunk("The primary core system is a legacy monolith with technical debt that restricts weekly release velocity."),
        MockChunk("The production PostgreSQL cluster represents a single point of failure without multi-region standby replication."),
        MockChunk("Current monthly AWS infrastructure spend averages $75,000 across EC2 and RDS instances."),
    ]

    findings, metrics, dependencies = extract_technology_findings_from_chunks(chunks, deal_id, org_id, user_id=None)

    assert len(findings) >= 3
    assert len(metrics) >= 2
    assert len(dependencies) >= 2

    cats = [f["category"] for f in findings]
    assert TechnologyCategory.TECHNOLOGY_DEBT.value in cats
    assert TechnologyCategory.SINGLE_POINT_OF_FAILURE.value in cats
    assert TechnologyCategory.CLOUD_COST.value in cats

    # Check SPOF severity
    spof_f = next(f for f in findings if f["category"] == TechnologyCategory.SINGLE_POINT_OF_FAILURE.value)
    assert spof_f["severity"] == "CRITICAL"

    # Verify fingerprint idempotency
    fp1 = compute_tech_fingerprint(deal_id, doc_id, TechnologyCategory.TECHNOLOGY_DEBT.value, chunks[0].content)
    fp2 = compute_tech_fingerprint(deal_id, doc_id, TechnologyCategory.TECHNOLOGY_DEBT.value, chunks[0].content)
    assert fp1 == fp2


def test_deterministic_technology_risk_and_cloud_cost_scoring():
    """Verify technology risk index and cloud cost run-rate calculations."""
    class MockFinding:
        def __init__(self, sev, lik, status="IDENTIFIED", exp=100000.0):
            self.severity = sev
            self.likelihood = lik
            self.status = status
            self.monetary_exposure = exp

    class MockMetric:
        def __init__(self, cat, name, val, st="ON_TARGET"):
            self.metric_category = cat
            self.metric_name = name
            self.observed_value = val
            self.status = st

    class MockDep:
        def __init__(self, name, spof=False, cost=100000.0):
            self.dependency_name = name
            self.is_single_point_of_failure = spof
            self.annual_cost = cost
            self.dependency_type = "CLOUD_PROVIDER"

    findings = [
        MockFinding("CRITICAL", "HIGH"),
        MockFinding("HIGH", "MEDIUM"),
    ]
    metrics = [
        MockMetric("UPTIME_SLA", "Core Uptime", 99.85, "DEVIATION"),
        MockMetric("CLOUD_SPEND", "Monthly AWS", 50000.0, "ON_TARGET"),
    ]
    dependencies = [
        MockDep("AWS us-east-1", spof=True, cost=600000.0),
    ]

    risk_info = calculate_technology_risk_score(findings, metrics, dependencies)
    assert risk_info["technology_risk_score"] > 40.0
    assert risk_info["risk_band"] in ["HIGH", "CRITICAL"]
    assert risk_info["spof_count"] == 1

    cloud_info = calculate_cloud_cost_summary(metrics, dependencies)
    assert cloud_info["annual_cloud_spend"] == 600000.0
    assert cloud_info["monthly_run_rate"] == 50000.0


def test_technology_finding_state_machine():
    """Verify technology finding lifecycle state transitions."""
    # Valid
    validate_tech_transition(TechFindingStatus.IDENTIFIED.value, TechFindingStatus.REQUIRES_REVIEW.value)
    validate_tech_transition(TechFindingStatus.REQUIRES_REVIEW.value, TechFindingStatus.REMEDIATION_PLANNED.value)
    validate_tech_transition(TechFindingStatus.REMEDIATION_PLANNED.value, TechFindingStatus.MITIGATED.value)

    # Invalid
    with pytest.raises(ValueError, match="Illegal technology finding transition"):
        validate_tech_transition(TechFindingStatus.IDENTIFIED.value, TechFindingStatus.MITIGATED.value)


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_tech_env(db_session: AsyncSession):
    """Seed deal workspace with target company, documents, and architecture chunks."""
    org = Organization(name="Andreessen Horowitz Growth", slug="a16z-tech-demo", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Tech Diligence Lead", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="cto.advisor@a16z.demo",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Marc Andreessen",
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
        name="DataScale Enterprise",
        industry="Cloud Data Infrastructure",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project DataScale Tech Diligence",
        target_ev=250000000.0,
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

    # Add sample architecture document and chunk
    doc = Document(
        organization_id=org.id,
        deal_id=deal.id,
        name="DataScale_Architecture_and_SLA_Report.pdf",
        file_type="PDF",
        mime_type="application/pdf",
        size_bytes=204800,
        storage_path="/data/DataScale_Architecture_and_SLA_Report.pdf",
        sha256_hash="f4c0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b999",
        status="PROCESSED",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        organization_id=org.id,
        deal_id=deal.id,
        document_id=doc.id,
        chunk_index=0,
        page_number=8,
        section_title="Section 4: Infrastructure & Technical Debt",
        content="Section 4.1: The primary transactional pipeline is a legacy monolith that exhibits technical debt and lacks automated rollback capabilities.",
        token_count=50,
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
async def test_technology_api_full_workflow(seed_tech_env, async_client: AsyncClient):
    """Verify complete technology diligence API workflow: scan, findings, infrastructure, dependencies, and summary."""
    env = seed_tech_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Trigger Technology Scan
    scan_res = await async_client.post(f"/api/v1/deals/{deal_id}/technology/scan", headers=headers)
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["findings_extracted"] >= 1
    assert scan_data["metrics_recorded"] >= 2
    assert scan_data["dependencies_identified"] >= 2

    # 2. List Findings
    findings_res = await async_client.get(f"/api/v1/deals/{deal_id}/technology/findings", headers=headers)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 1
    finding_id = findings[0]["id"]

    # 3. Update Finding Status
    patch_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/technology/findings/{finding_id}/status",
        headers=headers,
        json={"status": "REQUIRES_REVIEW", "notes": "Assigned to Lead Architect"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "REQUIRES_REVIEW"

    # 4. List Dependencies
    deps_res = await async_client.get(f"/api/v1/deals/{deal_id}/technology/dependencies", headers=headers)
    assert deps_res.status_code == 200
    deps = deps_res.json()
    assert len(deps) >= 2
    assert any(d["is_single_point_of_failure"] for d in deps)

    # 5. List Reliability & Infrastructure Metrics
    rel_res = await async_client.get(f"/api/v1/deals/{deal_id}/technology/reliability", headers=headers)
    assert rel_res.status_code == 200
    assert len(rel_res.json()) >= 1

    infra_res = await async_client.get(f"/api/v1/deals/{deal_id}/technology/infrastructure", headers=headers)
    assert infra_res.status_code == 200
    assert len(infra_res.json()) >= 1

    # 6. Executive Technology Summary
    sum_res = await async_client.get(f"/api/v1/deals/{deal_id}/technology/summary", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["technology_risk_score"] > 0.0
    assert summary["annual_cloud_spend"] > 0.0


@pytest.mark.asyncio
async def test_technology_tenant_isolation(seed_tech_env, async_client: AsyncClient):
    """Verify cross-tenant requests to access technology findings are strictly rejected."""
    env = seed_tech_env
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

    res = await async_client.get(f"/api/v1/deals/{deal_id}/technology", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    scan_res = await async_client.post(f"/api/v1/deals/{deal_id}/technology/scan", headers=foreign_headers)
    assert scan_res.status_code in [401, 403, 404]
