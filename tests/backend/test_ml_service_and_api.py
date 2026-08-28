"""Integration & Tenant Isolation Tests for ML Prediction Service & REST APIs."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.financials.models import FinancialMetric, FinancialStatement
from app.domains.risk.models import Risk


@pytest_asyncio.fixture
async def ml_test_setup(db_session: AsyncSession):
    """Set up two organizations, users, and deals for ML tenant isolation testing."""
    # Org A (Analyst user)
    org_a = Organization(
        id=uuid.uuid4(),
        name="Alpha Capital ML",
        slug="alpha-capital-ml",
        tier="ENTERPRISE",
    )
    role_q = select(Role).where(Role.name == "ADMIN")
    role_res = await db_session.execute(role_q)
    role_admin = role_res.scalar_one_or_none()
    if not role_admin:
        role_admin = Role(
            id=uuid.uuid4(),
            name="ADMIN",
            description="Admin with full permissions",
            permissions={"all": True},
        )
        db_session.add(role_admin)
        await db_session.flush()

    user_a = User(
        id=uuid.uuid4(),
        email="analyst@alpha-ml.com",
        hashed_password="hash",
        full_name="Analyst A",
        is_active=True,
    )
    mem_a = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        user_id=user_a.id,
        role_id=role_admin.id,
    )

    comp_a = TargetCompany(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="Alpha Target SaaS Inc.",
        lifecycle_stage="DILIGENCE",
        industry="Enterprise SaaS",
    )

    deal_a = Deal(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        target_company_id=comp_a.id,
        title="Alpha Target SaaS Acquisition",
        code_name="ALPHA-SAAS",
        status="ACTIVE",
        created_by_id=user_a.id,
    )
    deal_mem_a = DealMember(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        deal_id=deal_a.id,
        user_id=user_a.id,
        deal_role="LEAD",
    )

    # Seed Financial Metrics & Risk for Deal A
    m1 = FinancialMetric(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        deal_id=deal_a.id,
        metric_name="REVENUE",
        unit="CURRENCY",
        value=15000000.0,
        period="FY2025",
    )
    m2 = FinancialMetric(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        deal_id=deal_a.id,
        metric_name="EBITDA",
        unit="CURRENCY",
        value=3500000.0,
        period="FY2025",
    )
    r1 = Risk(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        deal_id=deal_a.id,
        category="CUSTOMER_CONCENTRATION",
        title="Top 2 Customer Reliance",
        description="Top 2 customers account for 38% of ARR.",
        severity=4,
        likelihood=4,
        score=16.0,
        risk_level="HIGH",
    )

    # Org B (Isolated Org)
    org_b = Organization(
        id=uuid.uuid4(),
        name="Beta Capital ML",
        slug="beta-capital-ml",
        tier="ENTERPRISE",
    )
    user_b = User(
        id=uuid.uuid4(),
        email="analyst@beta-ml.com",
        hashed_password="hash",
        full_name="Analyst B",
        is_active=True,
    )
    mem_b = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        user_id=user_b.id,
        role_id=role_admin.id,
    )
    comp_b = TargetCompany(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        name="Beta Target Healthcare Inc.",
        lifecycle_stage="DILIGENCE",
        industry="Healthcare",
    )
    deal_b = Deal(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        target_company_id=comp_b.id,
        title="Beta Target Healthcare",
        code_name="BETA-HEALTH",
        status="ACTIVE",
        created_by_id=user_b.id,
    )

    db_session.add_all([org_a, user_a, mem_a, comp_a, deal_a, deal_mem_a, m1, m2, r1, org_b, user_b, mem_b, comp_b, deal_b])
    await db_session.commit()

    token_a = create_access_token(subject=str(user_a.id), org_id=str(org_a.id), role="ADMIN")
    token_b = create_access_token(subject=str(user_b.id), org_id=str(org_b.id), role="ADMIN")

    return {
        "org_a": org_a,
        "user_a": user_a,
        "deal_a": deal_a,
        "token_a": token_a,
        "org_b": org_b,
        "user_b": user_b,
        "deal_b": deal_b,
        "token_b": token_b,
    }


@pytest.mark.asyncio
async def test_ml_models_list_and_metrics_api(async_client: AsyncClient, ml_test_setup: dict):
    """Verify listing ML models and retrieving evaluation metrics."""
    headers = {"Authorization": f"Bearer {ml_test_setup['token_a']}"}

    # 1. List models
    res = await async_client.get("/api/v1/ml/models", headers=headers)
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 7

    # 2. Get specific trained model
    res_m = await async_client.get("/api/v1/ml/models/dealguard-customer-churn-v1", headers=headers)
    assert res_m.status_code == 200
    m_data = res_m.json()
    assert m_data["model_id"] == "dealguard-customer-churn-v1"
    assert m_data["status"] == "VALIDATED"
    assert len(m_data["evaluation_metrics"]) > 0

    # 3. Get metrics with baseline comparison
    res_met = await async_client.get("/api/v1/ml/models/dealguard-customer-churn-v1/metrics", headers=headers)
    assert res_met.status_code == 200
    met_data = res_met.json()
    assert met_data["model_id"] == "dealguard-customer-churn-v1"
    assert "accuracy" in met_data["evaluation_metrics"]
    assert met_data["baseline_metrics"] is not None


@pytest.mark.asyncio
async def test_deal_ml_prediction_and_shap_persistence(async_client: AsyncClient, ml_test_setup: dict):
    """Verify executing real ML prediction on deal and retrieving persisted record with SHAP."""
    headers = {"Authorization": f"Bearer {ml_test_setup['token_a']}"}
    deal_id = str(ml_test_setup["deal_a"].id)

    # 1. Execute prediction for trained churn model
    pred_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/ml/predict",
        headers=headers,
        json={"model_id": "dealguard-customer-churn-v1"},
    )
    assert pred_res.status_code == 200
    p_data = pred_res.json()
    assert p_data["model_id"] == "dealguard-customer-churn-v1"
    assert p_data["predicted_value"] in [0, 1]
    assert p_data["prediction_confidence"] > 0.50
    assert p_data["explanation"] is not None
    assert len(p_data["explanation"]["top_features"]) > 0

    pred_id = p_data["prediction_id"]

    # 2. Retrieve persisted prediction record
    rec_res = await async_client.get(f"/api/v1/ml/predictions/{pred_id}", headers=headers)
    assert rec_res.status_code == 200
    r_data = rec_res.json()
    assert r_data["id"] == pred_id
    assert r_data["model_id"] == "dealguard-customer-churn-v1"
    assert r_data["explanation"] is not None


@pytest.mark.asyncio
async def test_ml_tenant_isolation(async_client: AsyncClient, ml_test_setup: dict):
    """Verify that User from Org B cannot execute ML prediction on Org A's deal."""
    headers_b = {"Authorization": f"Bearer {ml_test_setup['token_b']}"}
    deal_a_id = str(ml_test_setup["deal_a"].id)

    res = await async_client.post(
        f"/api/v1/deals/{deal_a_id}/ml/predict",
        headers=headers_b,
        json={"model_id": "dealguard-customer-churn-v1"},
    )
    assert res.status_code in [403, 404]
