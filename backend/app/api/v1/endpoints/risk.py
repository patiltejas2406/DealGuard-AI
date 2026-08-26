"""17-Pillar Deal Risk Intelligence REST API Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import validate_deal_membership
from app.domains.common.context import TenantContext
from app.domains.risk.schemas import (
    RiskCategoryInfoResponse,
    RiskCreateRequest,
    RiskDetectionRequest,
    RiskDetectionResponse,
    RiskEvidenceDetail,
    RiskListResponse,
    RiskMatrixResponse,
    RiskResponse,
    RiskStatusUpdateRequest,
    RiskUpdateRequest,
)
from app.domains.risk.service import RiskService
from app.domains.risk.taxonomy import RiskCategory, RiskLevel, RiskStatus

router = APIRouter(prefix="/deals/{deal_id}/risks", tags=["Risk Intelligence"])


def _format_risk_response(r) -> RiskResponse:
    """Format ORM risk object into typed Pydantic response."""
    evidence_items = []
    if hasattr(r, "evidence_items") and r.evidence_items:
        for ev in r.evidence_items:
            cit_data = None
            if hasattr(ev, "citation") and ev.citation:
                c = ev.citation
                doc_name = None
                if hasattr(c, "document") and c.document:
                    doc_name = c.document.name
                cit_data = {
                    "id": c.id,
                    "document_id": c.document_id,
                    "document_name": doc_name,
                    "page_number": c.page_number,
                    "section": c.section,
                    "exact_quote": c.exact_quote,
                    "char_offset_start": c.char_offset_start,
                    "char_offset_end": c.char_offset_end,
                    "confidence_score": c.confidence_score,
                }
            evidence_items.append(
                RiskEvidenceDetail(
                    id=ev.id,
                    citation_id=ev.citation_id,
                    citation=cit_data,
                    relevance_explanation=ev.relevance_explanation,
                    weight=ev.weight,
                )
            )

    return RiskResponse(
        id=r.id,
        organization_id=r.organization_id,
        deal_id=r.deal_id,
        company_id=r.company_id,
        category=r.category,
        title=r.title,
        description=r.description,
        severity=r.severity,
        likelihood=r.likelihood,
        score=r.score,
        risk_level=r.risk_level,
        status=r.status,
        detection_source=r.detection_source,
        confidence_score=r.confidence_score,
        mitigation_strategy=r.mitigation_strategy,
        recommendation=r.recommendation,
        fingerprint=r.fingerprint,
        evidence_items=evidence_items,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=RiskListResponse)
async def list_deal_risks(
    deal_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter by risk category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MODERATE, HIGH, CRITICAL"),
    status: Optional[str] = Query(None, description="Filter by status: IDENTIFIED, REVIEWED, ACCEPTED, MITIGATED, REJECTED"),
    min_severity: Optional[int] = Query(None, ge=1, le=5),
    min_likelihood: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = Query(None, description="Search term in title or description"),
    sort_by: str = Query("score", description="Sort field: score, severity, likelihood, created_at, category, status"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve filtered, sorted, and paginated risk register for a deal."""
    service = RiskService(db)
    items, total = await service.list_risks(
        context=context,
        deal_id=deal_id,
        category=category,
        risk_level=risk_level,
        status=status,
        min_severity=min_severity,
        min_likelihood=min_likelihood,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
        offset=offset,
        limit=limit,
    )
    formatted = [_format_risk_response(r) for r in items]
    return RiskListResponse(total=total, items=formatted)


@router.get("/matrix", response_model=RiskMatrixResponse)
async def get_risk_matrix(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Compute 5x5 Likelihood x Severity heatmap matrix and summary metrics."""
    service = RiskService(db)
    return await service.get_risk_matrix(context, deal_id)


@router.get("/categories", response_model=List[RiskCategoryInfoResponse])
async def get_risk_categories(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Fetch taxonomy metadata and heuristics for all 17 risk categories."""
    service = RiskService(db)
    categories = service.get_categories_metadata()
    return [
        RiskCategoryInfoResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            signals=c.signals,
            default_mitigation=c.default_mitigation,
            typical_severity_range=c.typical_severity_range,
        )
        for c in categories
    ]


@router.post("", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_deal_risk(
    deal_id: uuid.UUID,
    request: RiskCreateRequest,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Manually record a new risk item in the deal register."""
    service = RiskService(db)
    risk = await service.create_risk(
        context=context,
        deal_id=deal_id,
        category=request.category,
        title=request.title,
        description=request.description,
        severity=request.severity,
        likelihood=request.likelihood,
        status=request.status,
        detection_source=request.detection_source,
        confidence_score=request.confidence_score,
        mitigation_strategy=request.mitigation_strategy,
        recommendation=request.recommendation,
        company_id=request.company_id,
        citation_ids=request.citation_ids,
    )
    await db.commit()
    return _format_risk_response(risk)


@router.post("/detect", response_model=RiskDetectionResponse)
async def detect_deal_risks(
    deal_id: uuid.UUID,
    request: Optional[RiskDetectionRequest] = None,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger automated document risk scanner across all data room chunks.
    Detects signals across 17 categories, binds verifiable citations, and enforces deduplication.
    """
    service = RiskService(db)
    target_cats = request.categories if request else None
    min_conf = request.min_confidence if request else 0.60

    created_risks, scanned_chunks, detected_count, duplicates_skipped = (
        await service.run_automated_risk_scan(
            context=context,
            deal_id=deal_id,
            categories=target_cats,
            min_confidence=min_conf,
        )
    )
    await db.commit()

    formatted = [_format_risk_response(r) for r in created_risks]
    return RiskDetectionResponse(
        deal_id=deal_id,
        scanned_chunks_count=scanned_chunks,
        detected_count=detected_count,
        created_count=len(created_risks),
        duplicates_skipped=duplicates_skipped,
        risks=formatted,
    )


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_single_risk(
    deal_id: uuid.UUID,
    risk_id: uuid.UUID,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information and evidence citations for a specific risk."""
    service = RiskService(db)
    risk = await service.get_risk(context, deal_id, risk_id)
    return _format_risk_response(risk)


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_single_risk(
    deal_id: uuid.UUID,
    risk_id: uuid.UUID,
    request: RiskUpdateRequest,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Update risk title, description, category, severity, likelihood, or mitigation."""
    service = RiskService(db)
    updated = await service.update_risk(
        context=context,
        deal_id=deal_id,
        risk_id=risk_id,
        title=request.title,
        description=request.description,
        category=request.category,
        severity=request.severity,
        likelihood=request.likelihood,
        status=request.status,
        mitigation_strategy=request.mitigation_strategy,
        recommendation=request.recommendation,
    )
    await db.commit()
    return _format_risk_response(updated)


@router.patch("/{risk_id}/status", response_model=RiskResponse)
async def update_risk_status(
    deal_id: uuid.UUID,
    risk_id: uuid.UUID,
    request: RiskStatusUpdateRequest,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Update risk workflow state (REVIEWED, ACCEPTED, MITIGATED, REJECTED) with audit rationale."""
    service = RiskService(db)
    updated = await service.update_risk_status(
        context=context,
        deal_id=deal_id,
        risk_id=risk_id,
        new_status=request.status,
        rationale=request.rationale,
    )
    await db.commit()
    return _format_risk_response(updated)


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_risk(
    deal_id: uuid.UUID,
    risk_id: uuid.UUID,
    context: TenantContext = Depends(validate_deal_membership),
    db: AsyncSession = Depends(get_db),
):
    """Remove a risk item from the deal register."""
    service = RiskService(db)
    await service.delete_risk(context, deal_id, risk_id)
    await db.commit()
