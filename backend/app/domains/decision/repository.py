"""Decision Intelligence Database Repository for querying deal inputs and persisting score calculations."""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.deals.models import Deal
from app.domains.decision.models import DecisionScore
from app.domains.documents.models import Citation, Document
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.risk.models import Risk
from app.domains.valuation.models import Valuation, ValuationOutput


class DecisionRepository:
    """Async database repository for decision score aggregation and persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_complete_deal_diligence_context(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Fetch all cross-domain intelligence data for a deal workspace."""
        # 1. Fetch Deal
        deal_query = select(Deal).where(
            Deal.organization_id == organization_id,
            Deal.id == deal_id,
        )
        deal_res = await self.session.execute(deal_query)
        deal = deal_res.scalar_one_or_none()
        if not deal:
            return None

        # 2. Fetch Financial Statements & Metrics & QoE Adjustments
        stmt_query = (
            select(FinancialStatement)
            .where(
                FinancialStatement.organization_id == organization_id,
                FinancialStatement.deal_id == deal_id,
            )
            .order_by(FinancialStatement.fiscal_year.desc())
        )
        stmts_res = await self.session.execute(stmt_query)
        statements = list(stmts_res.scalars().all())

        metric_query = select(FinancialMetric).where(
            FinancialMetric.organization_id == organization_id,
            FinancialMetric.deal_id == deal_id,
        )
        metric_res = await self.session.execute(metric_query)
        metrics = list(metric_res.scalars().all())

        qoe_query = select(QoEAdjustment).where(
            QoEAdjustment.organization_id == organization_id,
            QoEAdjustment.deal_id == deal_id,
        )
        qoe_res = await self.session.execute(qoe_query)
        qoe_adjustments = list(qoe_res.scalars().all())

        # 3. Fetch Valuation Project & Outputs
        val_query = (
            select(Valuation)
            .options(selectinload(Valuation.outputs))
            .where(
                Valuation.organization_id == organization_id,
                Valuation.deal_id == deal_id,
            )
            .order_by(Valuation.created_at.desc())
        )
        val_res = await self.session.execute(val_query)
        valuation = val_res.scalars().first()

        outputs: List[ValuationOutput] = []
        if valuation and valuation.outputs:
            outputs = list(valuation.outputs)
        else:
            # Check for direct outputs query
            out_query = select(ValuationOutput).where(
                ValuationOutput.organization_id == organization_id,
                ValuationOutput.deal_id == deal_id,
            )
            out_res = await self.session.execute(out_query)
            outputs = list(out_res.scalars().all())

        # 4. Fetch Risks (Phase 7)
        risk_query = (
            select(Risk)
            .options(selectinload(Risk.evidence_items))
            .where(
                Risk.organization_id == organization_id,
                Risk.deal_id == deal_id,
            )
        )
        risk_res = await self.session.execute(risk_query)
        risks = list(risk_res.scalars().all())

        # 5. Fetch Documents & Citations
        doc_query = select(Document).where(
            Document.organization_id == organization_id,
            Document.deal_id == deal_id,
        )
        doc_res = await self.session.execute(doc_query)
        documents = list(doc_res.scalars().all())

        cit_query = select(Citation).where(
            Citation.organization_id == organization_id,
            Citation.deal_id == deal_id,
        )
        cit_res = await self.session.execute(cit_query)
        citations = list(cit_res.scalars().all())

        return {
            "deal": deal,
            "statements": statements,
            "metrics": metrics,
            "qoe_adjustments": qoe_adjustments,
            "valuation": valuation,
            "valuation_outputs": outputs,
            "risks": risks,
            "documents": documents,
            "citations": citations,
        }

    async def get_latest_decision_score(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[DecisionScore]:
        """Fetch the most recent persisted DecisionScore record for a deal."""
        query = (
            select(DecisionScore)
            .where(
                DecisionScore.organization_id == organization_id,
                DecisionScore.deal_id == deal_id,
            )
            .order_by(DecisionScore.created_at.desc())
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def get_decision_score_history(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, limit: int = 50
    ) -> List[DecisionScore]:
        """Fetch chronological calculation history for a deal."""
        query = (
            select(DecisionScore)
            .where(
                DecisionScore.organization_id == organization_id,
                DecisionScore.deal_id == deal_id,
            )
            .order_by(DecisionScore.created_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def save_decision_score(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        company_id: Optional[uuid.UUID],
        score_data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> DecisionScore:
        """Persist a newly calculated DecisionScore record and synchronize deal.decision_score."""
        record = DecisionScore(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=company_id,
            score_type="DEAL",
            overall_score=score_data["overall_score"],
            decision_band=score_data["decision_band"],
            confidence_score=score_data["confidence_score"],
            scoring_version=score_data["scoring_version"],
            weights_used=score_data["weights_used"],
            component_scores=score_data["components"],
            positive_drivers=score_data.get("positive_drivers", []),
            negative_drivers=score_data.get("negative_drivers", []),
            missing_information=score_data.get("missing_information", []),
            recommendations=score_data.get("recommendations", []),
            calculated_by_id=user_id,
        )
        self.session.add(record)

        # Update Deal.decision_score
        deal_query = select(Deal).where(
            Deal.organization_id == organization_id,
            Deal.id == deal_id,
        )
        deal_res = await self.session.execute(deal_query)
        deal = deal_res.scalar_one_or_none()
        if deal:
            deal.decision_score = score_data["overall_score"]

        await self.session.flush()
        return record
