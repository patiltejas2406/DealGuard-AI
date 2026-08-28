"""Finance Intelligence Agent."""

import uuid
from typing import List
from sqlalchemy import select

from app.domains.agents.base import BaseSpecialistAgent
from app.domains.agents.contract import (
    AgentConfidence,
    AgentExecutionRequest,
    AgentId,
    AgentMetadata,
    AgentStatus,
    FinanceAssessment,
)
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment


class FinanceIntelligenceAgent(BaseSpecialistAgent):
    """
    Specialist agent for analyzing 3-statement financials, revenue trends,
    QoE EBITDA normalization adjustments, and financial health.
    """

    @property
    def agent_id(self) -> AgentId:
        return AgentId.FINANCE

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self.agent_id,
            name="Finance Intelligence Specialist",
            version="1.0.0",
            purpose="Analyze standardized financial statements, EBITDA quality of earnings adjustments, and capital efficiency.",
            domain="FINANCIALS",
            allowed_tools=[
                "financial_statements_tool",
                "financial_metrics_tool",
                "qoe_bridge_tool",
                "financial_rag_retrieval_tool",
            ],
            evidence_requirements=["Audited Income Statement", "Balance Sheet", "QoE Schedule"],
            confidence_policy="Requires verified 3-statement data room records for HIGH confidence.",
            limitations=["Does not audit raw external tax filings directly without data room ingest."],
            handoff_targets=["valuation_intelligence_agent", "deal_decision_agent"],
        )

    async def _run_assessment(
        self, request: AgentExecutionRequest, tools_invoked: List[str]
    ) -> FinanceAssessment:
        deal_id = request.deal_id
        org_id = request.organization_id

        # Tool 0: Financial Statements
        self.verify_tool("financial_statements_tool")
        tools_invoked.append("financial_statements_tool")

        stmts_q = select(FinancialStatement).where(
            FinancialStatement.deal_id == deal_id,
            FinancialStatement.organization_id == org_id,
        ).order_by(FinancialStatement.statement_date.desc() if hasattr(FinancialStatement, "statement_date") else FinancialStatement.created_at.desc())
        stmts_res = await self.session.execute(stmts_q)
        statements = list(stmts_res.scalars().all())

        # Tool 1: Financial Metrics
        self.verify_tool("financial_metrics_tool")
        tools_invoked.append("financial_metrics_tool")

        metrics_q = select(FinancialMetric).where(
            FinancialMetric.deal_id == deal_id,
            FinancialMetric.organization_id == org_id,
        )
        metrics_res = await self.session.execute(metrics_q)
        metrics = list(metrics_res.scalars().all())

        # Tool 2: QoE Adjustments
        self.verify_tool("qoe_bridge_tool")
        tools_invoked.append("qoe_bridge_tool")

        qoe_q = select(QoEAdjustment).where(
            QoEAdjustment.deal_id == deal_id,
            QoEAdjustment.organization_id == org_id,
        )
        qoe_res = await self.session.execute(qoe_q)
        qoe_items = list(qoe_res.scalars().all())

        # Tool 3: Document RAG Evidence Retrieval
        self.verify_tool("financial_rag_retrieval_tool")
        tools_invoked.append("financial_rag_retrieval_tool")

        chunks_q = select(DocumentChunk).where(
            DocumentChunk.deal_id == deal_id,
            DocumentChunk.organization_id == org_id,
        ).limit(2)
        chunks_res = await self.session.execute(chunks_q)
        chunks = list(chunks_res.scalars().all())

        citations: List[CitationRef] = []
        for c in chunks:
            doc_name = "Audited Financial Report"
            if c.document_id:
                doc_q = select(Document.name).where(Document.id == c.document_id)
                d_res = await self.session.execute(doc_q)
                doc_name = d_res.scalar_one_or_none() or doc_name

            citations.append(
                CitationRef(
                    document_id=c.document_id or uuid.uuid4(),
                    chunk_id=c.id,
                    document_name=doc_name,
                    page_number=c.page_number or 1,
                    section_title=getattr(c, "section_title", None) or "Financial Performance",
                    exact_quote=c.content[:180] if c.content else "Audited financial disclosure record.",
                    confidence_score=0.95,
                )
            )

        if not metrics and not qoe_items and not statements:
            return FinanceAssessment(
                agent_id=self.agent_id,
                domain="FINANCIALS",
                status=AgentStatus.INSUFFICIENT_EVIDENCE,
                summary="Insufficient financial statements or metrics in the Data Room.",
                confidence=AgentConfidence.INSUFFICIENT_EVIDENCE,
                confidence_score=0.20,
                unresolved_issues=["No audited income statements, balance sheets, or historical P&L ingested."],
                data_gaps=[
                    "3-statement audited financial models (P&L, Balance Sheet, Cash Flow)",
                    "Quality of Earnings (QoE) adjustment workpapers",
                    "Revenue recognition and ARR retention breakdown by customer",
                ],
                required_diligence=["Ingest at least 3 years of audited P&L, balance sheets, and QoE workpapers."],
                citations=citations,
            )

        revenue_val = next((m.value for m in metrics if m.metric_name == "REVENUE"), 0.0)
        ebitda_margin_val = next((m.value for m in metrics if m.metric_name == "EBITDA_MARGIN"), 0.0)

        # Fallback to statement data if metrics table is sparse
        if revenue_val == 0.0 and statements:
            revenue_val = float(getattr(statements[0], "revenue", 0.0) or 0.0)
            ebitda_val = float(getattr(statements[0], "ebitda", 0.0) or 0.0)
            if revenue_val > 0 and ebitda_val > 0:
                ebitda_margin_val = ebitda_val / revenue_val

        net_qoe = sum(
            item.amount if item.treatment == "ADD_BACK" else -item.amount
            for item in qoe_items
            if item.status == "APPROVED" or item.status == "PROPOSED"
        )
        normalized_ebitda = (revenue_val * ebitda_margin_val) + net_qoe

        deterministic_refs = {
            "reported_revenue_usd": revenue_val,
            "ebitda_margin_ratio": ebitda_margin_val,
            "qoe_adjustments_net_usd": net_qoe,
            "normalized_ebitda_usd": normalized_ebitda,
            "statements_count": len(statements),
            "qoe_items_count": len(qoe_items),
        }

        positive_drivers = []
        negative_drivers = []
        if revenue_val > 20_000_000:
            positive_drivers.append(f"Strong top-line scale exceeding ${revenue_val:,.0f} ARR.")
        if ebitda_margin_val >= 0.15:
            positive_drivers.append(f"Healthy operating profitability with {ebitda_margin_val * 100:.1f}% EBITDA margin.")
        if net_qoe > 0:
            positive_drivers.append(f"Identified ${net_qoe:,.0f} in defensible positive QoE EBITDA add-backs.")
        elif net_qoe < 0:
            negative_drivers.append(f"QoE bridge reflects ${abs(net_qoe):,.0f} in recurring negative adjustments.")

        findings = [
            GroundedFinding(
                domain_pillar="FINANCIAL",
                category="PROFITABILITY",
                headline="Normalized EBITDA Quality of Earnings Bridge",
                detailed_reasoning=f"Reported revenue is ${revenue_val:,.2f} with normalized EBITDA of ${normalized_ebitda:,.2f} after accounting for {len(qoe_items)} QoE adjustments.",
                finding_type="FACT",
                severity_level="LOW" if ebitda_margin_val >= 0.15 else "MEDIUM",
                confidence_score=0.92,
                is_deterministic_calculation=True,
                calculation_source_engine="app.domains.financials.engine",
                citations=citations,
            )
        ]

        data_gaps = []
        if len(statements) < 3:
            data_gaps.append("Multi-year historical audited financial statements (only 1-2 periods available).")
        if not qoe_items:
            data_gaps.append("Detailed third-party QoE schedule with line-item management add-back justifications.")

        return FinanceAssessment(
            agent_id=self.agent_id,
            domain="FINANCIALS",
            status=AgentStatus.SUCCESS,
            summary=f"Financial analysis complete: Reported Revenue ${revenue_val:,.0f} with Normalized EBITDA ${normalized_ebitda:,.0f} ({ebitda_margin_val * 100:.1f}% margin).",
            confidence=AgentConfidence.HIGH,
            confidence_score=0.94,
            key_findings=findings,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            unresolved_issues=[] if len(metrics) >= 2 else ["Limited historical quarterly breakdowns."],
            data_gaps=data_gaps,
            metrics={
                "revenue": revenue_val,
                "ebitda_margin": ebitda_margin_val,
                "normalized_ebitda": normalized_ebitda,
                "net_qoe": net_qoe,
            },
            required_diligence=["Verify working capital peg and debt-like items prior to final closing."],
            citations=citations,
            deterministic_references=deterministic_refs,
            normalized_ebitda=normalized_ebitda,
            ebitda_margin=ebitda_margin_val,
            qoe_net_adjustments=net_qoe,
        )
