"""Deterministic Synthetic Data Seeder for DealGuard AI."""

import asyncio
import os
import sys
import uuid
from datetime import date, datetime, timezone

# Add backend directory to sys.path so app modules are importable from anywhere
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
root_backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if os.path.isdir(root_backend_dir) and root_backend_dir not in sys.path:
    sys.path.insert(0, root_backend_dir)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, get_engine, get_session_factory
from app.core.security import hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Citation, Document, DocumentChunk, DocumentVersion
from app.domains.financials.models import FinancialMetric, FinancialStatement
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.audit.models import AuditEvent


async def seed_database() -> None:
    """Seed the database with verified realistic synthetic M&A datasets."""
    print("=== DealGuard AI: Initializing Database Seeder ===")

    engine = get_engine()
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory()
    async with session_factory() as session:
        # Idempotency check: if admin demo user already exists, skip seeding
        existing_admin = await session.scalar(select(User).filter_by(email="admin@dealguard.ai"))
        if existing_admin is not None:
            print("✓ Database already contains seed demo accounts (admin@dealguard.ai found). Skipping seed.")
            return

        # 1. Organization
        org = Organization(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="DealGuard Demo Capital",
            slug="dealguard-demo-capital",
            tier="ENTERPRISE",
        )
        session.add(org)
        await session.flush()
        print(f"✓ Seeded Organization: {org.name} ({org.id})")

        # 2. Roles
        roles = {
            "ADMIN": Role(name="ADMIN", description="Platform and Tenant Governance", permissions={"all": True}),
            "LEAD": Role(name="M_AND_A_LEAD", description="M&A Deal Director", permissions={"deals": "manage"}),
            "ANALYST": Role(name="FINANCIAL_ANALYST", description="Financial Modeling Analyst", permissions={"financials": "edit"}),
            "REVIEWER": Role(name="REVIEWER", description="Investment Committee Reviewer", permissions={"review": "write"}),
        }
        for role in roles.values():
            session.add(role)
        await session.flush()

        # 3. Users & Memberships
        users_data = [
            ("admin@dealguard.ai", "Alex Vance", "ADMIN"),
            ("analyst@dealguard.ai", "Sarah Chen", "ANALYST"),
            ("reviewer@dealguard.ai", "Marcus Brody", "REVIEWER"),
        ]
        users = {}
        for email, name, role_key in users_data:
            user = User(
                email=email,
                hashed_password=hash_password("DemoPassword123!"),
                full_name=name,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            users[email] = user

            membership = OrganizationMembership(
                organization_id=org.id,
                user_id=user.id,
                role_id=roles[role_key].id,
            )
            session.add(membership)
        await session.flush()
        print(f"✓ Seeded {len(users)} Users & Memberships")

        # -------------------------------------------------------------
        # DEAL 1: ApexCloud Technologies (B2B SaaS - $65M EV)
        # -------------------------------------------------------------
        target_apex = TargetCompany(
            organization_id=org.id,
            name="ApexCloud Technologies Inc.",
            industry="Enterprise Software / B2B SaaS",
            sector="Cloud Infrastructure",
            headquarters="Austin, TX",
            website="https://apexcloud.demo",
            founding_year=2018,
            employee_count=145,
            description="Multi-tenant cloud cost optimization and infrastructure monitoring platform.",
        )
        session.add(target_apex)
        await session.flush()

        deal_apex = Deal(
            organization_id=org.id,
            target_company_id=target_apex.id,
            title="Project CloudGuard: ApexCloud Acquisition",
            code_name="Project CloudGuard",
            deal_type="MAJORITY_ACQUISITION",
            stage="CONFIRMATORY_DILIGENCE",
            target_ev=65000000.0,
            currency="USD",
            decision_score=78.5,
            created_by_id=users["admin@dealguard.ai"].id,
        )
        session.add(deal_apex)
        await session.flush()

        # Deal Members
        session.add(DealMember(organization_id=org.id, deal_id=deal_apex.id, user_id=users["admin@dealguard.ai"].id, deal_role="LEAD"))
        session.add(DealMember(organization_id=org.id, deal_id=deal_apex.id, user_id=users["analyst@dealguard.ai"].id, deal_role="ANALYST"))

        # Documents & Citations for ApexCloud
        doc_apex_fin = Document(
            organization_id=org.id,
            deal_id=deal_apex.id,
            name="ApexCloud_FY2023_Audited_Financials.pdf",
            file_type="PDF",
            mime_type="application/pdf",
            size_bytes=3420000,
            storage_path=f"/demo/{org.id}/{deal_apex.id}/ApexCloud_FY2023_Audited_Financials.pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="INDEXED",
            doc_category="FINANCIAL",
        )
        session.add(doc_apex_fin)
        await session.flush()

        chunk_apex = DocumentChunk(
            organization_id=org.id,
            deal_id=deal_apex.id,
            document_id=doc_apex_fin.id,
            chunk_index=14,
            page_number=18,
            section_title="Note 8 - Customer Concentration & Revenue Quality",
            content="During the fiscal year ended December 31, 2023, three customers accounted for 18%, 14%, and 10% of total consolidated revenues, respectively.",
            token_count=120,
            embedding_model="gemini-embedding-2",
        )
        session.add(chunk_apex)
        await session.flush()

        citation_apex = Citation(
            organization_id=org.id,
            deal_id=deal_apex.id,
            document_id=doc_apex_fin.id,
            chunk_id=chunk_apex.id,
            page_number=18,
            section="Note 8",
            exact_quote="three customers accounted for 18%, 14%, and 10% of total consolidated revenues",
            confidence_score=0.98,
        )
        session.add(citation_apex)
        await session.flush()

        # Financial Statements & Metrics for ApexCloud
        stmt_apex = FinancialStatement(
            organization_id=org.id,
            deal_id=deal_apex.id,
            statement_type="INCOME_STATEMENT",
            fiscal_year=2023,
            fiscal_period="FY2023",
            source_currency="USD",
            is_audited=True,
            is_normalized=True,
            source_document_id=doc_apex_fin.id,
            line_items={
                "revenue": 45200000.0,
                "cogs": 10400000.0,
                "gross_profit": 34800000.0,
                "operating_expenses": 25700000.0,
                "ebitda": 9100000.0,
                "normalized_ebitda": 9850000.0,
                "net_income": 6200000.0,
            },
        )
        session.add(stmt_apex)
        await session.flush()

        session.add(FinancialMetric(
            organization_id=org.id,
            deal_id=deal_apex.id,
            statement_id=stmt_apex.id,
            citation_id=citation_apex.id,
            metric_name="REVENUE",
            period="FY2023",
            value=45200000.0,
            unit="CURRENCY",
            source_currency="USD",
            is_normalized=False,
        ))
        session.add(FinancialMetric(
            organization_id=org.id,
            deal_id=deal_apex.id,
            statement_id=stmt_apex.id,
            metric_name="EBITDA_MARGIN",
            period="FY2023",
            value=0.201,
            unit="PERCENTAGE",
            source_currency="USD",
            is_normalized=False,
            calculation_formula="ebitda / revenue",
        ))

        # Risk for ApexCloud
        risk_apex = Risk(
            organization_id=org.id,
            deal_id=deal_apex.id,
            category="CUSTOMER_CONCENTRATION",
            title="High Customer Revenue Concentration (Top 3 = 42% ARR)",
            description="Loss of top customer represents an immediate 18% ARR drag ($8.1M ARR).",
            severity=4,
            likelihood=3,
            score=12,
            status="UNDER_REVIEW",
            mitigation_strategy="Structure deal with 15% earnout tied to 24-month customer retention covenants.",
        )
        session.add(risk_apex)
        await session.flush()

        session.add(RiskEvidence(
            organization_id=org.id,
            deal_id=deal_apex.id,
            risk_id=risk_apex.id,
            citation_id=citation_apex.id,
            relevance_explanation="Direct SEC Note 8 disclosure confirms 42% concentration across 3 counterparties.",
        ))

        # -------------------------------------------------------------
        # DEAL 2: TitanPrecision Manufacturing ($140M EV Industrial)
        # -------------------------------------------------------------
        target_titan = TargetCompany(
            organization_id=org.id,
            name="TitanPrecision Components GmbH",
            industry="Industrial Manufacturing / Aerospace",
            sector="Precision Tooling",
            headquarters="Stuttgart, Germany",
            website="https://titanprecision.demo",
            founding_year=1998,
            employee_count=520,
            description="Manufacturer of mission-critical titanium turbine assemblies and aerospace fasteners.",
        )
        session.add(target_titan)
        await session.flush()

        deal_titan = Deal(
            organization_id=org.id,
            target_company_id=target_titan.id,
            title="Project Titan: Precision Tooling M&A",
            code_name="Project Titan",
            deal_type="M_AND_A_BUY_SIDE",
            stage="PRE_DILIGENCE",
            target_ev=140000000.0,
            currency="EUR",
            decision_score=71.2,
            created_by_id=users["admin@dealguard.ai"].id,
        )
        session.add(deal_titan)
        await session.flush()

        # -------------------------------------------------------------
        # DEAL 3: MedVance Health Services ($95M EV Healthcare)
        # -------------------------------------------------------------
        target_med = TargetCompany(
            organization_id=org.id,
            name="MedVance Ambulatory Care LLC",
            industry="Healthcare Services / Clinics",
            sector="Outpatient Specialty",
            headquarters="Denver, CO",
            website="https://medvance.demo",
            founding_year=2014,
            employee_count=310,
            description="Operator of 18 regional outpatient surgical and diagnostic oncology centers.",
        )
        session.add(target_med)
        await session.flush()

        deal_med = Deal(
            organization_id=org.id,
            target_company_id=target_med.id,
            title="Project MedCare: Regional Clinic Rollup",
            code_name="Project MedCare",
            deal_type="GROWTH_EQUITY",
            stage="IC_REVIEW",
            target_ev=95000000.0,
            currency="USD",
            decision_score=83.0,
            created_by_id=users["admin@dealguard.ai"].id,
        )
        session.add(deal_med)
        await session.flush()

        # Audit Event for Seeding
        session.add(AuditEvent(
            organization_id=org.id,
            deal_id=deal_apex.id,
            actor_user_id=users["admin@dealguard.ai"].id,
            action="SYSTEM_SEEDED",
            entity_type="Deal",
            entity_id=deal_apex.id,
            details={"source": "backend/scripts/seed.py", "synthetic_profile": "ApexCloud, TitanPrecision, MedVance"},
        ))

        await session.commit()
        print(f"✓ Seeded 3 Core Synthetic Deals: ApexCloud ($65M), TitanPrecision ($140M), MedVance ($95M)")
        print("=== DealGuard AI: Database Seeding Completed Successfully ===")


if __name__ == "__main__":
    asyncio.run(seed_database())
