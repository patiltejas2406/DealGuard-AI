"""Multi-Tenancy Security & Boundary Isolation Tests."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.auth.models import Organization
from app.domains.common.context import TenantContext
from app.domains.deals.service import DealService
from app.domains.documents.service import DocumentService


@pytest.mark.asyncio
async def test_cross_tenant_deal_isolation(db_session: AsyncSession):
    """Verify Organization B cannot access or list Organization A's deals."""
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    ctx_a = TenantContext(organization_id=org_a_id, user_id=user_a_id)
    ctx_b = TenantContext(organization_id=org_b_id, user_id=user_b_id)

    # 1. Seed Org A and Org B
    db_session.add(Organization(id=org_a_id, name="Tenant Alpha", slug="tenant-alpha"))
    db_session.add(Organization(id=org_b_id, name="Tenant Beta", slug="tenant-beta"))
    await db_session.commit()

    # Organization A creates a confidential deal
    service_a = DealService(db_session)
    deal_a = await service_a.create_deal_with_target(
        context=ctx_a,
        company_name="Secret Target Corp",
        company_industry="Defense & Aerospace",
        deal_title="Project Blackbird",
        target_ev=500000000.0,
    )
    deal_a_id = deal_a.id

    # 2. Organization B lists deals -> Should be EMPTY
    service_b = DealService(db_session)
    deals_b = await service_b.list_deals(ctx_b)
    assert len(deals_b) == 0

    # 3. Organization B attempts direct get on Organization A's deal -> Must raise NotFoundException
    with pytest.raises(NotFoundException):
        await service_b.get_deal(ctx_b, deal_a_id)


@pytest.mark.asyncio
async def test_cross_tenant_document_isolation(db_session: AsyncSession):
    """Verify Organization B cannot view documents uploaded by Organization A."""
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    ctx_a = TenantContext(organization_id=org_a_id, user_id=user_a_id)
    ctx_b = TenantContext(organization_id=org_b_id, user_id=user_b_id)

    db_session.add(Organization(id=org_a_id, name="Fund A", slug="fund-a"))
    db_session.add(Organization(id=org_b_id, name="Fund B", slug="fund-b"))
    await db_session.commit()

    # Org A creates deal and registers document
    deal_service = DealService(db_session)
    deal = await deal_service.create_deal_with_target(
        context=ctx_a,
        company_name="Target Tech",
        company_industry="Software",
        deal_title="Project Tech",
    )
    doc_service = DocumentService(db_session)
    doc = await doc_service.register_document(
        context=ctx_a,
        deal_id=deal.id,
        name="Confidential_CapTable.xlsx",
        file_type="XLSX",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=102400,
        storage_path="/secure/vault/captable.xlsx",
        sha256_hash="abcd1234efgh5678",
    )
    doc_id = doc.id
    deal_id = deal.id

    # Org B attempts to access Org A's document -> Must fail with NotFoundException
    doc_service_b = DocumentService(db_session)
    with pytest.raises(NotFoundException):
        await doc_service_b.get_document(ctx_b, deal_id, doc_id)
