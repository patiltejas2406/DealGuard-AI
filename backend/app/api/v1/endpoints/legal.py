"""REST API Endpoints for Legal, Contract & Compliance Diligence Intelligence Engine."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.legal.schemas import (
    ChangeOfControlConsoleResponse,
    ComplianceRequirementResponse,
    ContractClauseResponse,
    ContractRecordCreateRequest,
    ContractRecordResponse,
    LegalFindingResponse,
    LegalFindingStatusUpdateRequest,
    LegalScanResponse,
    LegalSummaryResponse,
)
from app.domains.legal.service import LegalService

router = APIRouter(prefix="/deals/{deal_id}/legal", tags=["legal"])


@router.get(
    "",
    summary="Get Executive Legal Diligence Summary",
    status_code=status.HTTP_200_OK,
    response_model=LegalSummaryResponse,
)
async def get_legal_overview(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> LegalSummaryResponse:
    """Retrieve executive legal diligence summary, contract exposure, and compliance posture."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.get_legal_summary(context, deal_id)


@router.post(
    "/scan",
    summary="Scan Ingested Documents for Legal Clauses",
    status_code=status.HTTP_200_OK,
    response_model=LegalScanResponse,
)
async def scan_legal_documents(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> LegalScanResponse:
    """Trigger deterministic RAG-grounded legal clause and compliance evidence extraction."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = LegalService(db)
    return await service.scan_deal_documents(context, deal_id)


# ==========================================
# Contracts
# ==========================================

@router.get(
    "/contracts",
    summary="List Contract Records",
    status_code=status.HTTP_200_OK,
    response_model=List[ContractRecordResponse],
)
async def list_contracts(
    deal_id: uuid.UUID,
    contract_type: Optional[str] = Query(None, description="Filter by contract type (e.g. CUSTOMER_MSA)"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ContractRecordResponse]:
    """List contracts with counterparty metadata, annual values, and change-of-control flags."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.list_contracts(context, deal_id, contract_type)


@router.post(
    "/contracts",
    summary="Create Contract Record",
    status_code=status.HTTP_201_CREATED,
    response_model=ContractRecordResponse,
)
async def create_contract(
    deal_id: uuid.UUID,
    payload: ContractRecordCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ContractRecordResponse:
    """Manually register or import a contract agreement."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = LegalService(db)
    return await service.create_contract(context, deal_id, payload)


# ==========================================
# Clauses & Intelligence
# ==========================================

@router.get(
    "/clauses",
    summary="List Extracted Contract Clauses",
    status_code=status.HTTP_200_OK,
    response_model=List[ContractClauseResponse],
)
async def list_clauses(
    deal_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter by 32-category taxonomy"),
    contract_id: Optional[uuid.UUID] = Query(None, description="Filter by parent contract"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ContractClauseResponse]:
    """List verifiable clause extracts with grounded page/chunk citations."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.list_clauses(context, deal_id, category, contract_id)


# ==========================================
# Findings & Business Impacts
# ==========================================

@router.get(
    "/findings",
    summary="List Legal & Regulatory Findings",
    status_code=status.HTTP_200_OK,
    response_model=List[LegalFindingResponse],
)
async def list_findings(
    deal_id: uuid.UUID,
    finding_type: Optional[str] = Query(None, description="Filter by finding type"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, etc.)"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[LegalFindingResponse]:
    """List actionable legal findings with business impacts and recommendations."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.list_findings(context, deal_id, finding_type, severity)


@router.patch(
    "/findings/{finding_id}/status",
    summary="Update Legal Finding Status",
    status_code=status.HTTP_200_OK,
    response_model=LegalFindingResponse,
)
async def update_finding_status(
    deal_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: LegalFindingStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> LegalFindingResponse:
    """Transition finding status (e.g. IDENTIFIED -> ACTION_PLANNED -> CONSENT_OBTAINED -> MITIGATED)."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = LegalService(db)
    return await service.update_finding_status(context, deal_id, finding_id, payload)


# ==========================================
# Change of Control Console
# ==========================================

@router.get(
    "/change-of-control",
    summary="Get Change of Control Console",
    status_code=status.HTTP_200_OK,
    response_model=ChangeOfControlConsoleResponse,
)
async def get_change_of_control(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ChangeOfControlConsoleResponse:
    """Retrieve dedicated Change-of-Control console with exposed revenue and required consents."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.get_change_of_control_console(context, deal_id)


# ==========================================
# Compliance Matrix
# ==========================================

@router.get(
    "/compliance",
    summary="Get Compliance Evidence Matrix",
    status_code=status.HTTP_200_OK,
    response_model=List[ComplianceRequirementResponse],
)
async def list_compliance(
    deal_id: uuid.UUID,
    framework: Optional[str] = Query(None, description="Filter by framework (GDPR, SOC2, etc.)"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ComplianceRequirementResponse]:
    """Retrieve compliance framework matrix items with evidence status and remediation actions."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.list_compliance(context, deal_id, framework)


@router.get(
    "/summary",
    summary="Get Detailed Legal Summary Metrics",
    status_code=status.HTTP_200_OK,
    response_model=LegalSummaryResponse,
)
async def get_summary(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> LegalSummaryResponse:
    """Retrieve complete executive legal scorecard with Revenue-at-Risk calculations."""
    context.require_permission(PERM_DEALS_READ)
    service = LegalService(db)
    return await service.get_legal_summary(context, deal_id)
