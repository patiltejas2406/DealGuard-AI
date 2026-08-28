"""Multi-Domain Retrieval Engine for Evidence-Grounded Deal Intelligence."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.copilot.intent import CopilotIntent, CopilotLanguage, IntentRouter
from app.domains.deals.models import Deal, TargetCompany
from app.domains.decision.models import DecisionScore
from app.domains.documents.models import Document, DocumentChunk
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.integration.models import IntegrationMilestone, IntegrationWorkstream
from app.domains.legal.models import ContractClause, ContractRecord, LegalFinding
from app.domains.risk.models import Risk
from app.domains.synergy.models import SynergyOpportunity
from app.domains.technology.models import (
    OperationalMetric,
    TechnologyDependency,
    TechnologyFinding,
)
from app.domains.valuation.models import Valuation, ValuationAssumption


class MultiDomainRetriever:
    """Retrieves verified structured facts and grounded document evidence across all DealGuard phases."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def retrieve_context_for_query(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Aggregate cross-domain deal intelligence and relevant document chunks based on intent routing."""
        intent, language, candidate_domains = IntentRouter.route_query(query, conversation_history)

        retrieved_domains: List[str] = []
        context_sections: List[str] = []
        citations: List[Dict[str, Any]] = []
        domain_data: Dict[str, Any] = {
            "deal": None,
            "decision_score": None,
            "risks": [],
            "financials": [],
            "statements": [],
            "qoe": [],
            "legal": [],
            "technology": [],
            "valuation": [],
            "synergies": [],
            "integration": [],
        }

        # 1. Deal & Target Company Context
        deal_q = (
            select(Deal, TargetCompany)
            .outerjoin(TargetCompany, Deal.target_company_id == TargetCompany.id)
            .where(Deal.id == deal_id, Deal.organization_id == organization_id)
        )
        deal_res = await self.session.execute(deal_q)
        deal_row = deal_res.first()

        deal_obj = deal_row[0] if deal_row else None
        target_obj = deal_row[1] if deal_row else None

        if deal_obj:
            domain_data["deal"] = {
                "id": str(deal_obj.id),
                "title": deal_obj.title,
                "target_ev": deal_obj.target_ev,
                "currency": deal_obj.currency or "USD",
                "stage": deal_obj.stage,
                "deal_type": deal_obj.deal_type,
                "decision_score": deal_obj.decision_score,
                "company_name": target_obj.name if target_obj else "Target Company",
                "industry": target_obj.industry if target_obj else "Unknown",
                "employee_count": target_obj.employee_count if target_obj else None,
                "headquarters": target_obj.headquarters if target_obj else None,
            }
            context_sections.append(
                f"Target Deal: {deal_obj.title} (Target EV: ${deal_obj.target_ev:,.0f} {deal_obj.currency}, Stage: {deal_obj.stage}, Industry: {target_obj.industry if target_obj else 'N/A'})"
            )

        # 2. Decision Score Record
        if "DECISION_SCORE" in candidate_domains or intent == CopilotIntent.INVESTMENT_DECISION:
            score_q = (
                select(DecisionScore)
                .where(
                    DecisionScore.deal_id == deal_id,
                    DecisionScore.organization_id == organization_id,
                )
                .order_by(DecisionScore.created_at.desc())
                .limit(1)
            )
            score_res = await self.session.execute(score_q)
            score_rec = score_res.scalar_one_or_none()
            if score_rec:
                retrieved_domains.append("DECISION_SCORE")
                domain_data["decision_score"] = {
                    "overall_score": score_rec.overall_score,
                    "decision_band": score_rec.decision_band,
                    "positive_drivers": score_rec.positive_drivers or [],
                    "negative_drivers": score_rec.negative_drivers or [],
                    "recommendations": score_rec.recommendations or [],
                    "component_scores": score_rec.component_scores or {},
                }
                context_sections.append(
                    f"Decision Intelligence Score: {score_rec.overall_score:.1f}/100 (Band: {score_rec.decision_band})\n"
                    f"- Positive Drivers: {', '.join(score_rec.positive_drivers or ['N/A'])}\n"
                    f"- Negative Drivers: {', '.join(score_rec.negative_drivers or ['N/A'])}"
                )

        # 3. Risks Domain
        if "RISKS" in candidate_domains:
            risk_q = (
                select(Risk)
                .where(
                    Risk.deal_id == deal_id,
                    Risk.organization_id == organization_id,
                )
                .order_by(Risk.score.desc())
                .limit(6)
            )
            risk_res = await self.session.execute(risk_q)
            risks = list(risk_res.scalars().all())
            if risks:
                retrieved_domains.append("RISKS")
                domain_data["risks"] = [
                    {
                        "category": r.category,
                        "title": r.title,
                        "description": r.description,
                        "severity": r.severity,
                        "likelihood": r.likelihood,
                        "score": r.score,
                        "risk_level": r.risk_level,
                        "mitigation_strategy": r.mitigation_strategy,
                        "recommendation": r.recommendation,
                    }
                    for r in risks
                ]
                r_text = "Top Ingested Deal Risks:\n" + "\n".join(
                    [
                        f"- [{r.category}] {r.title} (Severity: {r.severity}/5, Score: {r.score}/25, Level: {r.risk_level}): {r.description} | Mitigation: {r.mitigation_strategy or 'None'}"
                        for r in risks
                    ]
                )
                context_sections.append(r_text)

        # 4. Financials & QoE Domain
        if "FINANCIALS" in candidate_domains:
            metrics_q = (
                select(FinancialMetric)
                .where(
                    FinancialMetric.deal_id == deal_id,
                    FinancialMetric.organization_id == organization_id,
                )
                .limit(10)
            )
            metrics_res = await self.session.execute(metrics_q)
            f_metrics = list(metrics_res.scalars().all())

            stmts_q = (
                select(FinancialStatement)
                .where(
                    FinancialStatement.deal_id == deal_id,
                    FinancialStatement.organization_id == organization_id,
                )
                .limit(3)
            )
            stmts_res = await self.session.execute(stmts_q)
            stmts = list(stmts_res.scalars().all())

            if f_metrics or stmts:
                retrieved_domains.append("FINANCIALS")
                domain_data["financials"] = [
                    {
                        "metric_name": m.metric_name,
                        "value": m.value,
                        "unit": m.unit,
                        "period": m.period,
                    }
                    for m in f_metrics
                ]
                f_parts = ["Financial Performance & Normalized Metrics:"]
                for m in f_metrics:
                    val_str = f"{m.value * 100:.1f}%" if m.unit == "PERCENTAGE" else f"${m.value:,.2f}"
                    f_parts.append(f"- {m.metric_name}: {val_str} (Period: {m.period})")
                for s in stmts:
                    domain_data["statements"].append({
                        "statement_type": s.statement_type,
                        "fiscal_period": s.fiscal_period,
                        "line_items": s.line_items,
                    })
                    if s.line_items:
                        rev = s.line_items.get("revenue")
                        ebitda = s.line_items.get("ebitda")
                        norm_ebitda = s.line_items.get("normalized_ebitda")
                        f_parts.append(
                            f"- {s.statement_type} ({s.fiscal_period}): Revenue=${rev:,.0f} | EBITDA=${ebitda:,.0f} | Normalized EBITDA=${norm_ebitda:,.0f}"
                            if rev is not None and ebitda is not None
                            else f"- {s.statement_type} ({s.fiscal_period}): Audited statement recorded"
                        )
                context_sections.append("\n".join(f_parts))

        # 5. QoE Domain
        if "QOE" in candidate_domains:
            qoe_q = (
                select(QoEAdjustment)
                .where(
                    QoEAdjustment.deal_id == deal_id,
                    QoEAdjustment.organization_id == organization_id,
                )
                .limit(5)
            )
            qoe_res = await self.session.execute(qoe_q)
            qoe_adjs = list(qoe_res.scalars().all())
            if qoe_adjs:
                retrieved_domains.append("QOE")
                domain_data["qoe"] = [
                    {
                        "category": adj.category,
                        "description": adj.description,
                        "treatment": adj.treatment,
                        "amount": adj.amount,
                        "status": adj.status,
                    }
                    for adj in qoe_adjs
                ]
                qoe_text = "Quality of Earnings (QoE) Adjustments:\n" + "\n".join(
                    [
                        f"- [{adj.category}] {adj.description}: {adj.treatment} ${adj.amount:,.2f} ({adj.status})"
                        for adj in qoe_adjs
                    ]
                )
                context_sections.append(qoe_text)

        # 6. Legal & Contracts Domain
        if "LEGAL_CONTRACTS" in candidate_domains:
            clause_q = (
                select(ContractClause)
                .where(
                    ContractClause.deal_id == deal_id,
                    ContractClause.organization_id == organization_id,
                )
                .limit(6)
            )
            clause_res = await self.session.execute(clause_q)
            clauses = list(clause_res.scalars().all())

            legal_findings_q = (
                select(LegalFinding)
                .where(
                    LegalFinding.deal_id == deal_id,
                    LegalFinding.organization_id == organization_id,
                )
                .limit(5)
            )
            lf_res = await self.session.execute(legal_findings_q)
            legal_findings = list(lf_res.scalars().all())

            if clauses or legal_findings:
                retrieved_domains.append("LEGAL_CONTRACTS")
                domain_data["legal"] = [
                    {
                        "title": cl.clause_title,
                        "category": cl.category,
                        "requires_consent": cl.requires_consent,
                        "text": cl.clause_text,
                    }
                    for cl in clauses
                ]
                l_parts = ["Legal & Contractual Diligence:"]
                for cl in clauses:
                    l_parts.append(
                        f"- [{cl.category}] {cl.clause_title}: \"{cl.clause_text}\" (Requires Consent: {cl.requires_consent})"
                    )
                for lf in legal_findings:
                    l_parts.append(
                        f"- [Finding - {lf.severity}] {lf.title}: {lf.description} (Action: {lf.recommended_action})"
                    )
                context_sections.append("\n".join(l_parts))

        # 7. Technology & Operations Domain
        if "TECHNOLOGY_OPERATIONS" in candidate_domains:
            tech_q = (
                select(TechnologyFinding)
                .where(
                    TechnologyFinding.deal_id == deal_id,
                    TechnologyFinding.organization_id == organization_id,
                )
                .limit(6)
            )
            tech_res = await self.session.execute(tech_q)
            tech_findings = list(tech_res.scalars().all())

            op_q = (
                select(OperationalMetric)
                .where(
                    OperationalMetric.deal_id == deal_id,
                    OperationalMetric.organization_id == organization_id,
                )
                .limit(5)
            )
            op_res = await self.session.execute(op_q)
            op_metrics = list(op_res.scalars().all())

            if tech_findings or op_metrics:
                retrieved_domains.append("TECHNOLOGY_OPERATIONS")
                domain_data["technology"] = [
                    {
                        "category": tf.category,
                        "title": tf.title,
                        "severity": tf.severity,
                        "technical_fact": tf.technical_fact,
                        "recommendation": tf.recommendation,
                    }
                    for tf in tech_findings
                ]
                t_parts = ["Technology & Operational Reliability:"]
                for tf in tech_findings:
                    t_parts.append(
                        f"- [{tf.category}] {tf.title} (Severity: {tf.severity}): {tf.technical_fact} | Remediation: {tf.recommendation}"
                    )
                for op in op_metrics:
                    t_parts.append(
                        f"- Metric {op.metric_name}: {op.metric_value} {op.unit} (SLA Met: {op.is_meeting_sla})"
                    )
                context_sections.append("\n".join(t_parts))

        # 8. Valuation Domain
        if "VALUATION" in candidate_domains:
            val_q = (
                select(Valuation)
                .where(
                    Valuation.deal_id == deal_id,
                    Valuation.organization_id == organization_id,
                )
                .limit(3)
            )
            val_res = await self.session.execute(val_q)
            valuations = list(val_res.scalars().all())
            if valuations:
                retrieved_domains.append("VALUATION")
                v_parts = ["Valuation & Financial Modeling:"]
                for v in valuations:
                    domain_data["valuation"].append({
                        "title": v.title,
                        "selected_method": v.selected_method,
                        "proposed_ev": v.proposed_ev,
                        "currency": v.currency,
                    })
                    v_parts.append(
                        f"- {v.title} ({v.selected_method}): Implied EV ${v.proposed_ev:,.0f} {v.currency} (Status: {v.status})"
                    )
                context_sections.append("\n".join(v_parts))

        # 9. Synergies Domain
        if "SYNERGIES" in candidate_domains:
            syn_q = (
                select(SynergyOpportunity)
                .where(
                    SynergyOpportunity.deal_id == deal_id,
                    SynergyOpportunity.organization_id == organization_id,
                )
                .limit(5)
            )
            syn_res = await self.session.execute(syn_q)
            synergies = list(syn_res.scalars().all())
            if synergies:
                retrieved_domains.append("SYNERGIES")
                domain_data["synergies"] = [
                    {
                        "type": s.synergy_type,
                        "name": s.name,
                        "run_rate": s.annual_run_rate_usd,
                        "npv": s.net_present_value_usd,
                    }
                    for s in synergies
                ]
                s_text = "Synergy Realization & Value Creation:\n" + "\n".join(
                    [
                        f"- [{s.synergy_type}] {s.name}: Annual Run-Rate ${s.annual_run_rate_usd:,.0f} (NPV: ${s.net_present_value_usd:,.0f})"
                        for s in synergies
                    ]
                )
                context_sections.append(s_text)

        # 10. Integration Domain
        if "INTEGRATION" in candidate_domains:
            ms_q = (
                select(IntegrationMilestone)
                .where(
                    IntegrationMilestone.deal_id == deal_id,
                    IntegrationMilestone.organization_id == organization_id,
                )
                .limit(6)
            )
            ms_res = await self.session.execute(ms_q)
            milestones = list(ms_res.scalars().all())
            if milestones:
                retrieved_domains.append("INTEGRATION")
                domain_data["integration"] = [
                    {
                        "day": ms.target_day,
                        "title": ms.title,
                        "status": ms.status,
                        "critical_path": ms.is_critical_path,
                    }
                    for ms in milestones
                ]
                m_text = "100-Day Post-Acquisition Integration Milestones:\n" + "\n".join(
                    [
                        f"- [Day {ms.target_day}] {ms.title} (Status: {ms.status}, Critical Path: {ms.is_critical_path})"
                        for ms in milestones
                    ]
                )
                context_sections.append(m_text)

        # 11. Document Chunks Grounded Search
        if "DOCUMENTS" in candidate_domains or not retrieved_domains:
            chunk_q = (
                select(DocumentChunk)
                .where(
                    DocumentChunk.deal_id == deal_id,
                    DocumentChunk.organization_id == organization_id,
                )
                .limit(4)
            )
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

                    sec = getattr(c, "section_title", None) or "General Due Diligence"
                    citations.append({
                        "document_id": str(c.document_id) if c.document_id else None,
                        "document_name": doc_name,
                        "page_number": c.page_number or 1,
                        "section_title": sec,
                        "quote": (c.content[:180] + "...") if len(c.content or "") > 180 else c.content,
                        "confidence": "HIGH",
                    })

        # Deduplicate retrieved domains while preserving order
        seen_domains = set()
        final_domains = []
        for d in retrieved_domains:
            if d not in seen_domains:
                seen_domains.add(d)
                final_domains.append(d)

        return {
            "intent": intent,
            "language": language,
            "candidate_domains": candidate_domains,
            "retrieved_domains": final_domains,
            "context_text": "\n\n".join(context_sections),
            "citations": citations,
            "domain_data": domain_data,
        }
