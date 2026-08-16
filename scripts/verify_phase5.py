"""Real-World Comprehensive Verification Script for Phase 5 Financial Engine."""

import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ForbiddenException
from app.core.security import hash_password
import app.domains.models  # Register all SQLAlchemy models in registry
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.common.context import TenantContext
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.financials.engine.metrics import MetricCalculationEngine
from app.domains.financials.engine.qoe import QoEEngine
from app.domains.financials.engine.statements import StatementCalculationEngine
from app.domains.financials.extractor import FinancialNormalizer
from app.domains.financials.service import FinancialService


async def verify_phase5_real_world():
    print("=== STARTING REAL-WORLD PHASE 5 VERIFICATION ===")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:

        # 1. Setup Test Tenant & Deal
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        target_id = uuid.uuid4()
        deal_id = uuid.uuid4()

        org = Organization(id=org_id, name="KKR Private Equity", slug="kkr-pe", tier="ENTERPRISE")
        role = Role(name="M_AND_A_LEAD", description="Lead", permissions={"all": True})
        user = User(id=user_id, email="lead@kkr.demo", hashed_password=hash_password("Pass123!"), full_name="Henry Kravis")
        target = TargetCompany(id=target_id, organization_id=org_id, name="FinTech Core Group", industry="Financial Technology")
        deal = Deal(id=deal_id, organization_id=org_id, target_company_id=target_id, title="Project FinTech Core Acquisition")
        member = DealMember(organization_id=org_id, deal_id=deal_id, user_id=user_id, deal_role="LEAD")


        session.add(org)
        session.add(role)
        session.add(user)
        session.add(target)
        await session.flush()

        session.add(OrganizationMembership(organization_id=org_id, user_id=user_id, role_id=role.id))
        session.add(deal)
        session.add(member)

        # Add Source Document & Citation for Provenance
        doc = Document(
            organization_id=org_id,
            deal_id=deal_id,
            name="FinTech_Core_FY2023_Audited.pdf",
            file_type="PDF",
            mime_type="application/pdf",
            size_bytes=2400000,
            storage_path=f"data/vault/{org_id}/{deal_id}/audit_qoe.pdf",
            sha256_hash="112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00",
            status="INDEXED",
        )
        session.add(doc)
        await session.flush()

        chunk = DocumentChunk(
            organization_id=org_id,
            deal_id=deal_id,
            document_id=doc.id,
            chunk_index=5,
            page_number=12,
            section_title="Note 4: Non-Recurring Legal Disputes",
            content="The company incurred $850,000 in one-time legal fees related to a settled patent dispute.",
            embedding_model="gemini-embedding-2",
        )
        session.add(chunk)
        await session.flush()

        citation = Citation(
            organization_id=org_id,
            deal_id=deal_id,
            document_id=doc.id,
            chunk_id=chunk.id,
            page_number=12,
            section="Note 4",
            exact_quote="incurred $850,000 in one-time legal fees",
            confidence_score=0.99,
        )
        session.add(citation)
        await session.commit()

        context = TenantContext(organization_id=org_id, user_id=user_id, roles=["M_AND_A_LEAD"], permissions={"financials:read", "financials:write"})
        service = FinancialService(session)

        # -------------------------------------------------------------
        # 2. Test Financial Normalization & Table Extraction
        # -------------------------------------------------------------
        raw_table = [
            ["Gross Sales", "$ 60,000,000.00"],
            ["Cost of Goods Sold", "$ 18,000,000.00"],
            ["Total OpEx", "$ 24,000,000.00"],
            ["D&A", "$ 4,000,000.00"],
            ["Interest Expense", "$ 2,000,000.00"],
            ["Income Tax", "$ 3,200,000.00"],
        ]
        extracted_is = FinancialNormalizer.extract_statement_from_table(raw_table, statement_type="INCOME_STATEMENT")
        assert extracted_is["revenue"] == 60000000.0
        assert extracted_is["cogs"] == 18000000.0
        assert extracted_is["gross_profit"] == 42000000.0  # 60M - 18M
        assert extracted_is["ebit"] == 18000000.0          # 42M - 24M
        assert extracted_is["ebitda"] == 22000000.0        # 18M + 4M
        assert extracted_is["net_income"] == 12800000.0    # 18M - 2M - 3.2M
        print("✓ Extraction & Line-Item Normalization Passed")

        # -------------------------------------------------------------
        # 3. Test Statement Upsert & Automated Metrics Synchronization
        # -------------------------------------------------------------
        # FY2022
        await service.upsert_statement(
            context, deal_id, "INCOME_STATEMENT", 2022, "FY2022",
            {"revenue": 40000000.0, "cogs": 14000000.0, "operating_expenses": 16000000.0, "ebitda": 10000000.0, "net_income": 7000000.0}
        )
        # FY2023
        await service.upsert_statement(
            context, deal_id, "INCOME_STATEMENT", 2023, "FY2023",
            extracted_is, is_audited=True, source_document_id=doc.id
        )

        metrics = await service.list_metrics(context, deal_id)
        metric_dict = {m.metric_name: m.value for m in metrics if m.period == "FY2023"}
        assert metric_dict["REVENUE"] == 60000000.0
        assert metric_dict["GROSS_MARGIN"] == 70.0        # 42M / 60M = 70.0%
        assert metric_dict["EBITDA_MARGIN"] == 36.67      # 22M / 60M = 36.67%
        assert metric_dict["NET_MARGIN"] == 21.33         # 12.8M / 60M = 21.33%
        print("✓ Statement Derivations & Margin Metrics Synchronization Passed")

        # -------------------------------------------------------------
        # 4. Multi-Year CAGR Analysis ($40M to $60M over 1 year = 50.0%)
        # -------------------------------------------------------------
        cagr = await service.compute_cagr_analysis(context, deal_id)
        assert cagr["revenue_cagr"] == 50.0
        assert cagr["ebitda_cagr"] == 120.0  # $10M to $22M = 120.0%
        print("✓ Multi-Year CAGR Analysis Passed")

        # -------------------------------------------------------------
        # 5. Balance Sheet Balancing & Discrepancy Detection
        # -------------------------------------------------------------
        # Balanced BS
        await service.upsert_statement(
            context, deal_id, "BALANCE_SHEET", 2023, "FY2023",
            {
                "cash": 12000000.0,
                "accounts_receivable": 8000000.0,
                "inventory": 5000000.0,
                "ppe": 25000000.0,
                "accounts_payable": 6000000.0,
                "long_term_debt": 14000000.0,
                "equity": 30000000.0,
            }
        )
        val_report = await service.validate_deal_financials(context, deal_id)
        assert val_report["status"] == "HEALTHY"
        print("✓ Balanced Balance Sheet Validation Passed")

        # Unbalanced BS Check (Intentionally unbalanced: Assets $50M vs Liab+Eq $40M)
        unbalanced_bs = StatementCalculationEngine.calculate_balance_sheet({
            "total_assets": 50000000.0,
            "total_liabilities": 20000000.0,
            "equity": 20000000.0,  # Sum = 40M != 50M
        })
        assert unbalanced_bs["is_balanced"] is False
        assert unbalanced_bs["balance_discrepancy"] == 10000000.0
        print("✓ Unbalanced Balance Sheet Discrepancy Flagging Passed")

        # -------------------------------------------------------------
        # 6. Quality of Earnings (QoE) Full Lifecycle & Filtering
        # -------------------------------------------------------------
        # 1. Proposed Add-back ($850k Legal Dispute with Citation)
        adj1 = await service.create_qoe_adjustment(
            context, deal_id, "LEGAL_NON_RECURRING", "Patent settlement legal fees",
            850000.0, period="FY2023", treatment="ADD_BACK", status="PROPOSED", citation_id=citation.id
        )
        # 2. Approved Add-back ($350k Founder travel)
        adj2 = await service.create_qoe_adjustment(
            context, deal_id, "OWNER_PERSONAL", "Founder personal travel add-back",
            350000.0, period="FY2023", treatment="ADD_BACK", status="APPROVED"
        )
        # 3. Approved Deduction ($200k Domain sale gain)
        adj3 = await service.create_qoe_adjustment(
            context, deal_id, "ONE_TIME_INCOME", "Gain on legacy domain sale",
            200000.0, period="FY2023", treatment="DEDUCTION", status="APPROVED"
        )
        # 4. Rejected Add-back ($500k Unsubstantiated synergy)
        adj4 = await service.create_qoe_adjustment(
            context, deal_id, "PRO_FORMA", "Unverified vendor synergy",
            500000.0, period="FY2023", treatment="ADD_BACK", status="REJECTED"
        )

        # Test QoE Bridge:
        # Reported EBITDA = $22.0M
        # Only APPROVED: +$350k - $200k = +$150k -> $22.15M
        qoe_bridge = await service.get_qoe_bridge(context, deal_id, "FY2023")
        assert qoe_bridge["bridge"]["reported_ebitda"] == 22000000.0

        # When we approve the $850k legal dispute
        await service.update_qoe_adjustment(context, deal_id, adj1.id, status="APPROVED")
        bridge_after_approval = await service.get_qoe_bridge(context, deal_id, "FY2023")

        # All adjustments summary
        adj_list = bridge_after_approval["adjustments"]
        approved_adjs = [a for a in adj_list if a["status"] == "APPROVED"]
        assert len(approved_adjs) == 3

        # Exact formula: $22M + $850k + $350k - $200k = $23.0M
        bridge_calc = QoEEngine.calculate_adjusted_ebitda(22000000.0, adj_list, only_approved=True)
        assert bridge_calc["total_add_backs"] == 1200000.0  # 850k + 350k
        assert bridge_calc["total_deductions"] == 200000.0
        assert bridge_calc["net_adjustment"] == 1000000.0
        assert bridge_calc["adjusted_ebitda"] == 23000000.0
        assert bridge_calc["applied_adjustments_count"] == 3
        print("✓ Quality of Earnings (QoE) Normalization Bridge & Status Exclusion Passed")

        # -------------------------------------------------------------
        # 7. SaaS Metrics & Ratios
        # -------------------------------------------------------------
        # Rule of 40: 50% Revenue Growth + 36.67% EBITDA Margin = 86.67%
        r40 = MetricCalculationEngine.calculate_rule_of_40(50.0, 36.67)
        assert r40["value"] == 86.67
        assert r40["passes_benchmark"] is True

        # CAC Payback: CAC $14,000, Annual ARPU $25,000, Gross Margin 70.0%
        # Gross profit per user = $25,000 * 0.70 = $17,500
        # Payback = (14000 / 17500) * 12 = 9.6 months
        cac_pb = MetricCalculationEngine.calculate_cac_payback(14000.0, 25000.0, 70.0)
        assert cac_pb["value"] == 9.6

        # Net Dollar Retention: $12M starting -> $14.16M ending = 118.0%
        ndr = MetricCalculationEngine.calculate_ndr(12000000.0, 14160000.0)
        assert ndr["value"] == 118.0
        assert ndr["is_best_in_class"] is True
        print("✓ SaaS Metrics (Rule of 40, CAC Payback, NDR) Passed")

        # -------------------------------------------------------------
        # 8. Tenant & Deal Isolation Protection
        # -------------------------------------------------------------
        other_deal_id = uuid.uuid4()
        scoped_context = TenantContext(organization_id=org_id, user_id=user_id, deal_id=other_deal_id)
        try:
            scoped_context.validate_deal_access(deal_id)
            assert False, "Unauthorized deal access was not rejected!"
        except ForbiddenException:
            print("✓ Deal-Scoped Access Enforcement Passed")

        # Database-level tenant isolation check
        other_org_id = uuid.uuid4()
        cross_org_stmts = await service.repo.list_statements_for_deal(other_org_id, deal_id)
        assert len(cross_org_stmts) == 0, "Cross-tenant query returned foreign tenant statements!"
        print("✓ Database-Level Cross-Tenant Isolation Passed")

    print("=== ALL REAL-WORLD PHASE 5 CHECKS PASSED SUCCESSFULLY ===")



if __name__ == "__main__":
    asyncio.run(verify_phase5_real_world())
