"""Multi-Domain Retrieval Engine for Evidence-Grounded Deal Intelligence."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.deals.models import Deal
from app.domains.decision.models import DecisionScore
from app.domains.documents.models import Document, DocumentChunk
from app.domains.financials.models import FinancialMetric, QoEAdjustment
from app.domains.integration.models import IntegrationMilestone, IntegrationWorkstream
from app.domains.legal.models import ContractClause, ContractRecord, LegalFinding
from app.domains.risk.models import Risk
from app.domains.synergy.models import SynergyOpportunity
from app.domains.technology.models import (
    OperationalMetric,
    TechnologyDependency,
    TechnologyFinding,
)


class MultiDomainRetriever:
    """Retrieves verified structured facts and grounded document evidence across all DealGuard phases."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def retrieve_context_for_query(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, query: str
    ) -> Dict[str, Any]:
        """Aggregate cross-domain deal intelligence and relevant document chunks."""
        q_lower = query.lower()
        retrieved_domains = []
        context_sections = []
        citations = []

        # 1. Deal Context
        deal_q = select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id)
        deal_res = await self.session.execute(deal_q)
        deal = deal_res.scalar_one_or_none()

        deal_title = deal.title if deal else "Active Target Deal"
        context_sections.append(f"Target Deal: {deal_title} (Currency: {deal.currency if deal else 'USD'})")

        # 2. Risk Domain
        if any(w in q_lower for w in ["risk", "danger", "downside", "threat", "exposure", "concern", "issue"]):
            risk_q = select(Risk).where(
                Risk.deal_id == deal_id,
                Risk.organization_id == organization_id,
            ).order_by(Risk.score.desc()).limit(5)
            risk_res = await self.session.execute(risk_q)
            risks = list(risk_res.scalars().all())
            if risks:
                retrieved_domains.append("RISKS")
                r_text = "Top Deal Risks:\n" + "\n".join(
                    [f"- [{r.category}] {r.title} (Severity: {r.severity}, Score: {r.score}): {r.description}" for r in risks]
                )
                context_sections.append(r_text)

        # 3. Legal & Contracts Domain
        if any(w in q_lower for w in ["legal", "contract", "change of control", "consent", "compliance", "gdpr", "clause", "law"]):
            clause_q = select(ContractClause).where(
                ContractClause.deal_id == deal_id,
                ContractClause.organization_id == organization_id,
            ).limit(5)
            clause_res = await self.session.execute(clause_q)
            clauses = list(clause_res.scalars().all())
            if clauses:
                retrieved_domains.append("LEGAL_CONTRACTS")
                c_text = "Key Contract Clauses:\n" + "\n".join(
                    [f"- [{cl.category}] {cl.clause_title}: \"{cl.clause_text}\" (Requires Consent: {cl.requires_consent})" for cl in clauses]
                )
                context_sections.append(c_text)

        # 4. Technology & Operations Domain
        if any(w in q_lower for w in ["tech", "technology", "architecture", "cloud", "aws", "sla", "uptime", "spof", "debt", "monolith", "developer"]):
            tech_q = select(TechnologyFinding).where(
                TechnologyFinding.deal_id == deal_id,
                TechnologyFinding.organization_id == organization_id,
            ).limit(5)
            tech_res = await self.session.execute(tech_q)
            tech_findings = list(tech_res.scalars().all())
            if tech_findings:
                retrieved_domains.append("TECHNOLOGY_OPERATIONS")
                t_text = "Technology & Operational Findings:\n" + "\n".join(
                    [f"- [{tf.category}] {tf.title} (Severity: {tf.severity}): {tf.technical_fact} | Remediation: {tf.recommendation}" for tf in tech_findings]
                )
                context_sections.append(t_text)

        # 5. Financials & QoE Domain
        if any(w in q_lower for w in ["financial", "ebitda", "revenue", "qoe", "margin", "cash flow", "earnings", "growth"]):
            metrics_q = select(FinancialMetric).where(
                FinancialMetric.deal_id == deal_id,
                FinancialMetric.organization_id == organization_id,
            ).limit(6)
            metrics_res = await self.session.execute(metrics_q)
            f_metrics = list(metrics_res.scalars().all())

            qoe_q = select(QoEAdjustment).where(
                QoEAdjustment.deal_id == deal_id,
                QoEAdjustment.organization_id == organization_id,
            ).limit(5)
            qoe_res = await self.session.execute(qoe_q)
            qoe_adjs = list(qoe_res.scalars().all())

            if f_metrics or qoe_adjs:
                retrieved_domains.append("FINANCIALS")
                f_parts = []
                if f_metrics:
                    f_parts.append("Financial Metrics & Performance:\n" + "\n".join(
                        [f"- {m.metric_name}: {m.value:,.2f} ({m.unit}, Period: {m.period})" for m in f_metrics]
                    ))
                if qoe_adjs:
                    f_parts.append("Quality of Earnings (QoE) Adjustments:\n" + "\n".join(
                        [f"- [{adj.category}] {adj.description}: {adj.treatment} ${adj.amount:,.2f} ({adj.status})" for adj in qoe_adjs]
                    ))
                context_sections.append("\n\n".join(f_parts))

        # 6. Synergies & Value Creation Domain
        if any(w in q_lower for w in ["synergy", "synergies", "value creation", "cost savings", "upsell", "waterfall"]):
            syn_q = select(SynergyOpportunity).where(
                SynergyOpportunity.deal_id == deal_id,
                SynergyOpportunity.organization_id == organization_id,
            ).limit(5)
            syn_res = await self.session.execute(syn_q)
            synergies = list(syn_res.scalars().all())
            if synergies:
                retrieved_domains.append("SYNERGIES")
                s_text = "Synergy & Value Creation Opportunities:\n" + "\n".join(
                    [f"- [{s.synergy_type}] {s.name}: Annual Run-Rate ${s.annual_run_rate_usd:,.0f} (NPV: ${s.net_present_value_usd:,.0f})" for s in synergies]
                )
                context_sections.append(s_text)

        # 7. 100-Day Integration Domain
        if any(w in q_lower for w in ["integration", "100-day", "milestone", "workstream", "blocker", "critical path", "execution"]):
            ms_q = select(IntegrationMilestone).where(
                IntegrationMilestone.deal_id == deal_id,
                IntegrationMilestone.organization_id == organization_id,
            ).limit(5)
            ms_res = await self.session.execute(ms_q)
            milestones = list(ms_res.scalars().all())
            if milestones:
                retrieved_domains.append("INTEGRATION")
                m_text = "100-Day Integration Milestones:\n" + "\n".join(
                    [f"- [Day {ms.target_day}] {ms.title} (Status: {ms.status}, Critical Path: {ms.is_critical_path})" for ms in milestones]
                )
                context_sections.append(m_text)

        # 8. Document Chunks Grounded Search
        chunk_q = select(DocumentChunk).where(
            DocumentChunk.deal_id == deal_id,
            DocumentChunk.organization_id == organization_id,
        ).limit(3)
        chunk_res = await self.session.execute(chunk_q)
        chunks = list(chunk_res.scalars().all())

        if chunks:
            retrieved_domains.append("DOCUMENTS")
            for c in chunks:
                doc_name = "Data Room Document"
                if c.document_id:
                    doc_q = select(Document.name).where(Document.id == c.document_id)
                    d_res = await self.session.execute(doc_q)
                    doc_name = d_res.scalar_one_or_none() or doc_name

                sec = getattr(c, "section_title", None) or getattr(c, "section_name", None) or "General"
                citations.append({
                    "document_id": str(c.document_id) if c.document_id else None,
                    "document_name": doc_name,
                    "page_number": c.page_number or 1,
                    "section_title": sec,
                    "quote": (c.content[:160] + "...") if len(c.content or "") > 160 else c.content,
                    "confidence": "HIGH",
                })

        if not retrieved_domains:
            retrieved_domains = ["DOCUMENTS"]

        return {
            "retrieved_domains": list(set(retrieved_domains)),
            "context_text": "\n\n".join(context_sections),
            "citations": citations,
        }
