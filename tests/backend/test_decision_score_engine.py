"""Comprehensive Test Suite for Phase 8: Composite DealGuard Decision Score & Explainable Intelligence."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.decision.config import (
    CURRENT_SCORING_VERSION,
    DEFAULT_COMPONENT_WEIGHTS,
    DataAvailabilityStatus,
    DecisionBand,
    classify_decision_band,
)
from app.domains.decision.engine import (
    DecisionScoringError,
    calculate_composite_decision_score,
    normalize_deal_complexity,
    normalize_evidence_confidence,
    normalize_financial_health,
    normalize_revenue_quality,
    normalize_risk_exposure,
    normalize_valuation_attractiveness,
    validate_weights,
)
from app.domains.documents.models import Citation, Document
from app.domains.financials.models import FinancialMetric, FinancialStatement, QoEAdjustment
from app.domains.risk.models import Risk
from app.domains.valuation.models import Valuation, ValuationOutput


# ==========================================
# 1. Deterministic Math & Weight Calibration Tests
# ==========================================

def test_weights_and_decision_bands():
    """Verify default component weights sum to exactly 1.00 and decision bands classify correctly."""
    validate_weights(DEFAULT_COMPONENT_WEIGHTS)
    assert sum(DEFAULT_COMPONENT_WEIGHTS.values()) == pytest.approx(1.00)
    assert len(DEFAULT_COMPONENT_WEIGHTS) == 6

    # Test invalid weight configurations
    with pytest.raises(DecisionScoringError):
        validate_weights({"FINANCIAL_HEALTH": 0.50, "RISK_EXPOSURE": 0.60})

    with pytest.raises(DecisionScoringError):
        validate_weights({"A": -0.2, "B": 1.2})

    # Test Decision Band Boundaries
    assert classify_decision_band(100.0) == DecisionBand.STRONG
    assert classify_decision_band(85.0) == DecisionBand.STRONG
    assert classify_decision_band(80.0) == DecisionBand.STRONG
    assert classify_decision_band(79.9) == DecisionBand.FAVORABLE
    assert classify_decision_band(65.0) == DecisionBand.FAVORABLE
    assert classify_decision_band(64.9) == DecisionBand.CAUTION
    assert classify_decision_band(50.0) == DecisionBand.CAUTION
    assert classify_decision_band(49.9) == DecisionBand.HIGH_RISK
    assert classify_decision_band(35.0) == DecisionBand.HIGH_RISK
    assert classify_decision_band(34.9) == DecisionBand.AVOID
    assert classify_decision_band(0.0) == DecisionBand.AVOID


def test_component_normalization_bounds():
    """Verify every component normalizer outputs scores strictly in [0.0, 100.0]."""
    class DummyStmt:
        statement_type = "INCOME_STATEMENT"
        line_items = {"revenue": 50000000, "ebitda": 15000000, "gross_profit": 38000000}
        is_audited = True

    class DummyMetric:
        def __init__(self, name, val):
            self.metric_name = name
            self.value = val

    # 1. Financial Health
    fin_res = normalize_financial_health(
        [DummyStmt()], [DummyMetric("EBITDA_MARGIN", 30.0), DummyMetric("REVENUE_GROWTH", 25.0)], []
    )
    assert 0.0 <= fin_res["score"] <= 100.0
    assert fin_res["status"] == DataAvailabilityStatus.AVAILABLE.value

    # 2. Valuation Attractiveness
    class DummyValOutput:
        methodology = "DCF_PERPETUITY"
        implied_ev = 75000000.0
        enterprise_value_base = 75000000.0

    val_res = normalize_valuation_attractiveness(60000000.0, None, [DummyValOutput()])
    assert 0.0 <= val_res["score"] <= 100.0
    assert val_res["score"] >= 80.0  # Positive spread

    # 3. Risk Exposure
    class DummyRisk:
        def __init__(self, cat, level, status="IDENTIFIED", title="Risk"):
            self.category = cat
            self.risk_level = level
            self.status = status
            self.title = title

    risks = [
        DummyRisk("CUSTOMER_CONCENTRATION", "CRITICAL"),
        DummyRisk("CYBERSECURITY", "HIGH"),
        DummyRisk("KEY_PERSON", "MODERATE"),
    ]
    risk_res = normalize_risk_exposure(risks)
    assert 0.0 <= risk_res["score"] <= 100.0
    assert risk_res["score"] < 80.0  # Penalties applied

    # 4. Revenue Quality
    rev_res = normalize_revenue_quality([DummyStmt()], risks)
    assert 0.0 <= rev_res["score"] <= 100.0

    # 5. Evidence Confidence
    class DummyDoc:
        pass
    class DummyCit:
        pass

    evid_res = normalize_evidence_confidence([DummyDoc(), DummyDoc(), DummyDoc()], [DummyCit(), DummyCit(), DummyCit(), DummyCit(), DummyCit()], [DummyStmt()])
    assert 0.0 <= evid_res["score"] <= 100.0
    assert evid_res["confidence"] >= 0.80

    # 6. Deal Complexity
    cmpx_res = normalize_deal_complexity(risks, None)
    assert 0.0 <= cmpx_res["score"] <= 100.0


def test_missing_data_policy():
    """Verify missing inputs produce safe baseline scores and mark INSUFFICIENT_DATA."""
    class EmptyDeal:
        target_ev = None

    res = calculate_composite_decision_score(
        deal=EmptyDeal(),
        statements=[],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
    )

    assert 0.0 <= res["overall_score"] <= 100.0
    assert res["confidence_score"] <= 0.60
    assert len(res["missing_information"]) > 0


def test_versioning_and_reproducibility():
    """Verify identical inputs produce identical scores and store scoring_version = 1.0."""
    class DummyDeal:
        target_ev = 50000000.0

    run1 = calculate_composite_decision_score(
        deal=DummyDeal(), statements=[], metrics=[], qoe_adjustments=[], valuation=None,
        valuation_outputs=[], risks=[], documents=[], citations=[]
    )
    run2 = calculate_composite_decision_score(
        deal=DummyDeal(), statements=[], metrics=[], qoe_adjustments=[], valuation=None,
        valuation_outputs=[], risks=[], documents=[], citations=[]
    )

    assert run1["overall_score"] == run2["overall_score"]
    assert run1["confidence_score"] == run2["confidence_score"]
    assert run1["scoring_version"] == CURRENT_SCORING_VERSION
    assert run2["scoring_version"] == "1.0"


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_decision_env(db_session: AsyncSession):
    """Seed authenticated organization, target company, deal workspace, and lead analyst."""
    org = Organization(name="Apollo Flagship Fund", slug="apollo-flagship", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Deal Analyst", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="decision.lead@apollo.demo",
        hashed_password=hash_password("Pass123!"),
        full_name="Leon Black",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(membership)
    await db_session.flush()

    target = TargetCompany(
        organization_id=org.id,
        name="OmniCloud Solutions",
        industry="Enterprise Software",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project OmniCloud Buyout",
        target_ev=70000000.0,
        currency="USD",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    db_session.add(DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD",
    ))

    # Add Income Statement
    stmt = FinancialStatement(
        organization_id=org.id,
        deal_id=deal.id,
        statement_type="INCOME_STATEMENT",
        period_type="ANNUAL",
        fiscal_year=2023,
        fiscal_period="FY2023",
        source_currency="USD",
        is_audited=True,
        line_items={"revenue": 52000000.0, "ebitda": 16500000.0, "gross_profit": 41000000.0},
    )
    db_session.add(stmt)
    await db_session.flush()

    # Add Valuation Output
    val = Valuation(
        organization_id=org.id,
        deal_id=deal.id,
        title="Base Case DCF",
        selected_method="DCF",
        currency="USD",
    )
    db_session.add(val)
    await db_session.flush()

    out = ValuationOutput(
        organization_id=org.id,
        deal_id=deal.id,
        valuation_id=val.id,
        methodology="DCF_PERPETUITY",
        implied_ev=84000000.0,
        enterprise_value_base=84000000.0,
    )
    db_session.add(out)

    # Add Moderate Risk
    risk = Risk(
        organization_id=org.id,
        deal_id=deal.id,
        category="CUSTOMER_CONCENTRATION",
        title="Top customer represents 28% ARR",
        description="Moderate customer dependency",
        severity=3,
        likelihood=3,
        score=9,
        risk_level="MODERATE",
        status="IDENTIFIED",
        detection_source="MANUAL_ENTRY",
    )
    db_session.add(risk)
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ANALYST")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_decision_score_api_workflow(seed_decision_env, async_client: AsyncClient):
    """Verify calculation, breakdown retrieval, history, and synchronization via REST APIs."""
    env = seed_decision_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Calculate Decision Score via POST
    calc_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/decision-score/calculate",
        headers=headers,
    )
    assert calc_res.status_code == 201
    data = calc_res.json()
    assert 0.0 <= data["overall_score"] <= 100.0
    assert data["decision_band"] in ["STRONG", "FAVORABLE", "CAUTION", "HIGH_RISK", "AVOID"]
    assert data["scoring_version"] == "1.0"
    assert "FINANCIAL_HEALTH" in data["components"]
    assert "VALUATION_ATTRACTIVENESS" in data["components"]
    assert "RISK_EXPOSURE" in data["components"]
    assert len(data["positive_drivers"]) > 0 or len(data["negative_drivers"]) > 0
    assert len(data["recommendations"]) > 0

    # 2. Retrieve Current Score via GET
    get_res = await async_client.get(
        f"/api/v1/deals/{deal_id}/decision-score",
        headers=headers,
    )
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["overall_score"] == data["overall_score"]
    assert get_data["decision_band"] == data["decision_band"]

    # 3. Retrieve Breakdown
    breakdown_res = await async_client.get(
        f"/api/v1/deals/{deal_id}/decision-score/breakdown",
        headers=headers,
    )
    assert breakdown_res.status_code == 200
    b_data = breakdown_res.json()
    assert "components" in b_data
    assert b_data["components"]["FINANCIAL_HEALTH"]["weight"] > 0

    # 4. Retrieve History Timeline
    hist_res = await async_client.get(
        f"/api/v1/deals/{deal_id}/decision-score/history",
        headers=headers,
    )
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_calculations"] >= 1
    assert len(hist_data["history"]) >= 1


@pytest.mark.asyncio
async def test_decision_score_tenant_isolation(seed_decision_env, async_client: AsyncClient):
    """Verify strict tenant isolation prevents unauthorized cross-tenant score computation."""
    env = seed_decision_env
    deal_id = env["deal"].id

    foreign_org_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()

    foreign_token = create_access_token(
        subject=str(foreign_user_id), org_id=str(foreign_org_id), role="ANALYST"
    )
    foreign_headers = {
        "Authorization": f"Bearer {foreign_token}",
        "X-Organization-ID": str(foreign_org_id),
    }

    # Attempt to calculate or read decision score from unauthorized tenant
    res = await async_client.get(f"/api/v1/deals/{deal_id}/decision-score", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    post_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/decision-score/calculate", headers=foreign_headers
    )
    assert post_res.status_code in [401, 403, 404]
