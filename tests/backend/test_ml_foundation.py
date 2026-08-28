"""Test Suite for Phase 15A: Machine Learning Foundation & XAI Contracts."""

import pytest
import uuid
from httpx import AsyncClient
from app.domains.ml.interfaces import ModelRegistry
from app.domains.ml.schemas import (
    FeatureImportance,
    FeatureSet,
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    PredictionRequest,
    PredictionResult,
    SHAPValue,
    XAIExplanation,
)


def test_ml_model_metadata_and_task_schemas():
    """Verify ML ModelMetadata schemas enforce evaluation metric requirements and framework boundaries."""
    meta = ModelMetadata(
        model_id="test-churn-model-v1",
        name="Enterprise SaaS Churn Predictor",
        version="1.0.0",
        task_type=ModelTaskType.CHURN_PREDICTION,
        framework="xgboost",
        feature_names=["nrr", "support_tickets", "exec_turnover"],
        evaluation_metrics={"auc_roc": 0.891, "f1_score": 0.835},
        status=ModelStatus.VALIDATED,
    )
    assert meta.model_id == "test-churn-model-v1"
    assert meta.task_type == ModelTaskType.CHURN_PREDICTION
    assert meta.evaluation_metrics["auc_roc"] == 0.891


def test_xai_explanation_and_shap_contracts():
    """Verify XAI explanation contracts structure feature importance and SHAP attributions."""
    fi1 = FeatureImportance(feature_name="customer_concentration_pct", importance_score=0.42, rank=1, direction="NEGATIVE")
    fi2 = FeatureImportance(feature_name="ebitda_margin", importance_score=0.35, rank=2, direction="POSITIVE")

    shap1 = SHAPValue(feature_name="customer_concentration_pct", base_value=0.15, shap_value=-0.12, actual_value=0.42)
    shap2 = SHAPValue(feature_name="ebitda_margin", base_value=0.18, shap_value=0.08, actual_value=0.25)

    xai = XAIExplanation(
        prediction_id=uuid.uuid4(),
        model_id="dealguard-risk-probability-v1",
        method="SHAP_TREE",
        top_features=[fi1, fi2],
        shap_values=[shap1, shap2],
        feature_snapshot={"customer_concentration_pct": 0.42, "ebitda_margin": 0.25},
        narrative_summary="High customer concentration (42%) is the primary driver increasing downside risk probability.",
    )
    assert len(xai.top_features) == 2
    assert xai.top_features[0].feature_name == "customer_concentration_pct"
    assert xai.shap_values[0].shap_value == -0.12


def test_model_registry_catalog_initialization():
    """Verify built-in model architectures are registered in ModelRegistry catalog."""
    catalog = ModelRegistry.list_all_models()
    assert len(catalog) >= 7

    model_ids = [m.model_id for m in catalog]
    assert "dealguard-revenue-forecast-v1" in model_ids
    assert "dealguard-ebitda-qoe-v1" in model_ids
    assert "dealguard-customer-churn-v1" in model_ids
    assert "dealguard-risk-probability-v1" in model_ids
    assert "dealguard-integration-failure-v1" in model_ids
    assert "dealguard-synergy-realization-v1" in model_ids
    assert "dealguard-post-acquisition-health-v1" in model_ids

    # Look up specific model
    rev_meta = ModelRegistry.get_metadata("dealguard-revenue-forecast-v1")
    assert rev_meta is not None
    assert rev_meta.task_type == ModelTaskType.REVENUE_FORECAST
    assert "historical_arr_3yr" in rev_meta.feature_names


import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from sqlalchemy import select


@pytest_asyncio.fixture
async def seed_ml_env(db_session: AsyncSession):
    """Seed test fixtures for ML API authentication."""
    org = Organization(name="Acutus ML Org", slug=f"acutus-ml-{uuid.uuid4().hex[:6]}")
    db_session.add(org)
    await db_session.flush()

    role_q = select(Role).where(Role.name == "ADMIN")
    role_res = await db_session.execute(role_q)
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(name="ADMIN", description="Admin", permissions={"all": True})
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"ml-partner-{uuid.uuid4().hex[:6]}@acutus.com",
        hashed_password=hash_password("PartnerPassword123!"),
        full_name="ML Specialist",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    mem = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
        is_active=True,
    )
    db_session.add(mem)
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ADMIN")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}
    return {"headers": headers}


@pytest.mark.asyncio
async def test_ml_models_api_endpoints(seed_ml_env, async_client: AsyncClient):
    """Verify REST API endpoints for listing and querying ML model metadata."""
    env = seed_ml_env
    headers = env["headers"]

    # 1. List all ML Models
    list_res = await async_client.get("/api/v1/ml/models", headers=headers)
    assert list_res.status_code == 200
    models = list_res.json()
    assert len(models) >= 7

    # 2. Get specific ML Model Details
    detail_res = await async_client.get(
        "/api/v1/ml/models/dealguard-risk-probability-v1", headers=headers
    )
    assert detail_res.status_code == 200
    meta = detail_res.json()
    assert meta["model_id"] == "dealguard-risk-probability-v1"
    assert meta["task_type"] == "RISK_PROBABILITY"
    assert len(meta["feature_names"]) >= 3
