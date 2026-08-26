"""Async Database Repository for Legal, Contract & Compliance Intelligence."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.legal.models import (
    ComplianceRequirement,
    ContractClause,
    ContractRecord,
    LegalFinding,
)


class LegalRepository:
    """Encapsulates all database operations for contracts, clauses, findings, and compliance requirements."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==========================================
    # Contracts
    # ==========================================

    async def list_contracts(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        contract_type: Optional[str] = None,
    ) -> List[ContractRecord]:
        query = select(ContractRecord).where(
            ContractRecord.organization_id == organization_id,
            ContractRecord.deal_id == deal_id,
        )
        if contract_type:
            query = query.where(ContractRecord.contract_type == contract_type)
        query = query.order_by(ContractRecord.annual_value.desc(), ContractRecord.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_contract(
        self, organization_id: uuid.UUID, contract_id: uuid.UUID
    ) -> Optional[ContractRecord]:
        query = select(ContractRecord).where(
            ContractRecord.organization_id == organization_id,
            ContractRecord.id == contract_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_contract(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        company_id: Optional[uuid.UUID],
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID],
    ) -> ContractRecord:
        contract = ContractRecord(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=company_id,
            title=data["title"],
            contract_type=data.get("contract_type", "CUSTOMER_MSA"),
            counterparty=data["counterparty"],
            document_id=data.get("document_id"),
            effective_date=data.get("effective_date"),
            expiration_date=data.get("expiration_date"),
            auto_renewal=data.get("auto_renewal", False),
            annual_value=data.get("annual_value", 0.0),
            currency=data.get("currency", "USD"),
            governing_law=data.get("governing_law"),
            jurisdiction=data.get("jurisdiction"),
            status=data.get("status", "ACTIVE"),
            citation_id=data.get("citation_id"),
            created_by_id=user_id,
        )
        self.session.add(contract)
        await self.session.flush()
        return contract

    async def update_contract(
        self, contract: ContractRecord, data: Dict[str, Any]
    ) -> ContractRecord:
        for k, v in data.items():
            if hasattr(contract, k) and v is not None:
                setattr(contract, k, v)
        await self.session.flush()
        return contract

    # ==========================================
    # Clauses
    # ==========================================

    async def list_clauses(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        category: Optional[str] = None,
        contract_id: Optional[uuid.UUID] = None,
    ) -> List[ContractClause]:
        query = select(ContractClause).where(
            ContractClause.organization_id == organization_id,
            ContractClause.deal_id == deal_id,
        )
        if category:
            query = query.where(ContractClause.category == category)
        if contract_id:
            query = query.where(ContractClause.contract_id == contract_id)
        query = query.order_by(ContractClause.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def upsert_clause_by_fingerprint(
        self, data: Dict[str, Any]
    ) -> ContractClause:
        query = select(ContractClause).where(
            ContractClause.deal_id == data["deal_id"],
            ContractClause.fingerprint == data["fingerprint"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        clause = ContractClause(**data)
        self.session.add(clause)
        await self.session.flush()
        return clause

    # ==========================================
    # Legal Findings
    # ==========================================

    async def list_findings(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        finding_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[LegalFinding]:
        query = select(LegalFinding).where(
            LegalFinding.organization_id == organization_id,
            LegalFinding.deal_id == deal_id,
        )
        if finding_type:
            query = query.where(LegalFinding.finding_type == finding_type)
        if severity:
            query = query.where(LegalFinding.severity == severity)
        query = query.order_by(LegalFinding.created_at.desc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_finding(
        self, organization_id: uuid.UUID, finding_id: uuid.UUID
    ) -> Optional[LegalFinding]:
        query = select(LegalFinding).where(
            LegalFinding.organization_id == organization_id,
            LegalFinding.id == finding_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def upsert_finding_by_fingerprint(
        self, data: Dict[str, Any]
    ) -> LegalFinding:
        query = select(LegalFinding).where(
            LegalFinding.deal_id == data["deal_id"],
            LegalFinding.fingerprint == data["fingerprint"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        finding = LegalFinding(**data)
        self.session.add(finding)
        await self.session.flush()
        return finding

    # ==========================================
    # Compliance Requirements
    # ==========================================

    async def list_compliance(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        framework: Optional[str] = None,
    ) -> List[ComplianceRequirement]:
        query = select(ComplianceRequirement).where(
            ComplianceRequirement.organization_id == organization_id,
            ComplianceRequirement.deal_id == deal_id,
        )
        if framework:
            query = query.where(ComplianceRequirement.framework == framework)
        query = query.order_by(ComplianceRequirement.created_at.asc())
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def upsert_compliance(
        self, data: Dict[str, Any]
    ) -> ComplianceRequirement:
        query = select(ComplianceRequirement).where(
            ComplianceRequirement.deal_id == data["deal_id"],
            ComplianceRequirement.framework == data["framework"],
            ComplianceRequirement.requirement_name == data["requirement_name"],
        )
        res = await self.session.execute(query)
        existing = res.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            await self.session.flush()
            return existing

        req = ComplianceRequirement(**data)
        self.session.add(req)
        await self.session.flush()
        return req
