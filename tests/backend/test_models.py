"""Tests for Database Domain Models, Constraints and Relationships."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, TargetCompany
from app.domains.financials.models import FinancialMetric, FinancialStatement


@pytest.mark.asyncio
async def test_organization_and_user_creation(db_session: AsyncSession):
    """Verify Organization and User persistence with UUID and relationships."""
    org = Organization(name="Blackstone M&A", slug="blackstone-ma", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="M_AND_A_LEAD", description="Deal Lead")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="lead@blackstone.demo",
        hashed_password="hashed-password-123",
        full_name="Jonathan Gray",
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(membership)
    await db_session.commit()

    # Verify query with relationships
    stmt = select(Organization).where(Organization.id == org.id)
    result = await db_session.execute(stmt)
    retrieved_org = result.scalar_one()
    assert retrieved_org.name == "Blackstone M&A"
    assert retrieved_org.slug == "blackstone-ma"
    assert retrieved_org.created_at is not None


@pytest.mark.asyncio
async def test_duplicate_organization_slug_fails(db_session: AsyncSession):
    """Verify unique constraint on organization slug."""
    org1 = Organization(name="Apollo Global", slug="apollo")
    db_session.add(org1)
    await db_session.commit()

    org2 = Organization(name="Apollo Duplicate", slug="apollo")
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_financial_statement_and_metric_relationships(db_session: AsyncSession):
    """Verify 3-statement line items JSON and metric foreign keys."""
    org = Organization(name="KKR Tech", slug="kkr-tech")
    db_session.add(org)
    await db_session.flush()

    target = TargetCompany(organization_id=org.id, name="Databricks", industry="Software")
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project Data: Databricks",
        target_ev=43000000000.0,
        currency="USD",
    )
    db_session.add(deal)
    await db_session.flush()

    stmt = FinancialStatement(
        organization_id=org.id,
        deal_id=deal.id,
        statement_type="INCOME_STATEMENT",
        fiscal_year=2023,
        fiscal_period="FY2023",
        line_items={"revenue": 1600000000.0, "cogs": 320000000.0},
    )
    db_session.add(stmt)
    await db_session.flush()

    metric = FinancialMetric(
        organization_id=org.id,
        deal_id=deal.id,
        statement_id=stmt.id,
        metric_name="REVENUE",
        period="FY2023",
        value=1600000000.0,
        unit="CURRENCY",
        source_currency="USD",
    )
    db_session.add(metric)
    await db_session.commit()

    # Check retrieval
    res = await db_session.execute(select(FinancialMetric).where(FinancialMetric.id == metric.id))
    retrieved = res.scalar_one()
    assert retrieved.value == 1600000000.0
    assert retrieved.statement_id == stmt.id
