"""REST API Integration Tests for Document Ingestion, Chunks, Search & Jobs."""

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany


@pytest.fixture
async def seeded_deal_workspace(db_session: AsyncSession):
    """Seed authenticated organization, deal workspace, and assigned user."""
    org = Organization(name="Silver Lake", slug="silver-lake", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ADMIN", description="Admin", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="director@silverlake.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Egon Durban",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role_id=role.id))

    target = TargetCompany(organization_id=org.id, name="FinTech Core LLC", industry="Fintech")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project FinTech Core",
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
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ADMIN")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


import pytest_asyncio

@pytest_asyncio.fixture
async def deal_context(db_session: AsyncSession):
    """Async fixture for deal workspace context."""
    org = Organization(name="Silver Lake", slug="silver-lake", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ADMIN", description="Admin", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="director@silverlake.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Egon Durban",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(OrganizationMembership(organization_id=org.id, user_id=user.id, role_id=role.id))

    target = TargetCompany(organization_id=org.id, name="FinTech Core LLC", industry="Fintech")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project FinTech Core",
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
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ADMIN")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_upload_document_and_query_chunks_api(deal_context, async_client: AsyncClient):
    """Verify document upload, ingestion pipeline execution, and chunk retrieval."""
    deal_id = deal_context["deal"].id
    headers = deal_context["headers"]

    # 1. Upload Document via Multipart Form
    file_bytes = (
        "# Quality of Earnings Assessment\n\n"
        "Adjusted EBITDA for FY2023 is normalized at $12.8M after adding back $1.5M in one-time legal fees.\n\n"
        "# Working Capital Target\n\n"
        "Net working capital peg is set at $4.2M based on the 12-month trailing average."
    ).encode("utf-8")

    files = {"file": ("QoE_Report.txt", file_bytes, "text/plain")}
    data = {"category": "FINANCIAL"}

    response = await async_client.post(
        f"/api/v1/deals/{deal_id}/documents/upload",
        files=files,
        data=data,
        headers=headers,
    )
    assert response.status_code == 202
    res_data = response.json()

    assert res_data["document"]["name"] == "QoE_Report.txt"
    assert res_data["document"]["status"] == "INDEXED"
    doc_id = res_data["document"]["id"]
    job_id = res_data["job"]["id"]

    # 2. Query Ingestion Job Status
    job_res = await async_client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    assert job_res.json()["status"] == "COMPLETED"
    assert job_res.json()["progress_pct"] == 100

    # 3. Get Document Details
    doc_res = await async_client.get(f"/api/v1/deals/{deal_id}/documents/{doc_id}", headers=headers)
    assert doc_res.status_code == 200
    assert doc_res.json()["name"] == "QoE_Report.txt"

    # 4. List Document Chunks
    chunks_res = await async_client.get(f"/api/v1/deals/{deal_id}/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 2
    assert chunks[0]["embedding_model"] is not None

    # 5. Semantic Vector Search
    search_payload = {
        "query": "What is the adjusted EBITDA normalization?",
        "top_k": 3,
        "min_similarity": 0.1,
    }
    search_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/documents/search",
        json=search_payload,
        headers=headers,
    )
    assert search_res.status_code == 200
    search_items = search_res.json()
    assert len(search_items) >= 1
    assert any("EBITDA" in item["content"] or "working capital" in item["content"].lower() for item in search_items)

