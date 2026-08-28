"""Tests for Phase 17 Real-World Data Acquisition, ML Benchmarking & Model Selection."""

import uuid
import pytest
import pandas as pd
import numpy as np

from app.domains.common.context import TenantContext
from app.domains.ml.data_contracts import DataType, TargetType
from app.domains.ml.datasets.manifest import (
    REAL_DATASET_PROVENANCE_REGISTRY,
    get_provenance_record,
    list_all_provenance_records,
)
from app.domains.ml.datasets.real_world_datasets import (
    load_real_commercial_loan_default_dataset,
    load_real_credit_risk_dataset,
    load_real_customer_churn_dataset,
)
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.quality_audit import DataQualityAuditor
from app.domains.ml.real_benchmarking import RealWorldBenchmarkEngine
from app.domains.ml.registry import ExtendedModelRegistry
from app.domains.ml.schemas import ModelStatus, PredictionRequest
from app.domains.ml.service import MLPredictionService


def test_real_dataset_provenance_manifest():
    """Verify that all real-world datasets have valid provenance records, licenses, and SHA256 checksums."""
    records = list_all_provenance_records()
    assert len(records) >= 3

    churn_prov = get_provenance_record("dealguard-real-churn-v1")
    assert churn_prov is not None
    assert churn_prov.is_synthetic is False
    assert len(churn_prov.sha256_checksum) == 64
    assert "IBM" in churn_prov.source_organization or "Kaggle" in churn_prov.source_organization

    credit_prov = get_provenance_record("dealguard-real-credit-risk-v1")
    assert credit_prov is not None
    assert credit_prov.is_synthetic is False
    assert "UCI" in credit_prov.source_organization

    sba_prov = get_provenance_record("dealguard-real-downside-risk-v1")
    assert sba_prov is not None
    assert sba_prov.is_synthetic is False
    assert "SBA" in sba_prov.source_organization


def test_real_world_dataset_loaders():
    """Test loading and cleaning of real-world datasets."""
    # 1. Real Customer Churn
    df_churn, snap_churn = load_real_customer_churn_dataset()
    assert len(df_churn) == 7043
    assert "churn" in df_churn.columns
    assert "customerID" not in df_churn.columns  # Identifier dropped
    assert snap_churn.metadata.is_synthetic is False
    assert snap_churn.target_definition.target_type == TargetType.BINARY_CLASSIFICATION

    # 2. Real German Credit Risk
    df_credit, snap_credit = load_real_credit_risk_dataset()
    assert len(df_credit) == 1000
    assert "default_risk" in df_credit.columns
    assert set(df_credit["default_risk"].unique()) == {0, 1}
    assert snap_credit.metadata.is_synthetic is False

    # 3. Real SBA Loan Default
    df_sba, snap_sba = load_real_commercial_loan_default_dataset(max_samples=1000)
    assert len(df_sba) <= 1000
    assert "loan_default" in df_sba.columns
    assert snap_sba.metadata.is_synthetic is False


def test_automated_data_quality_auditor():
    """Test automated data quality audit and leakage detection on real datasets."""
    df_churn, snap_churn = load_real_customer_churn_dataset()
    report = DataQualityAuditor.audit_dataset(df_churn, "churn", snap_churn.metadata.dataset_id)

    assert report.is_suitable_for_training is True
    assert report.total_rows == 7043
    assert report.missing_value_pct < 0.05
    assert report.class_imbalance_ratio is not None
    assert report.class_imbalance_ratio > 1.0


def test_real_world_multi_model_benchmarking_and_selection():
    """Test full multi-model benchmarking, validation selection, tuning, and SHAP explainability."""
    df_credit, snap_credit = load_real_credit_risk_dataset()

    wrapper, summary = RealWorldBenchmarkEngine.benchmark_and_train_target(
        snapshot=snap_credit,
        df=df_credit,
        target_column="default_risk",
        model_id="dealguard-test-real-credit-v1",
        random_state=42,
        perform_tuning=True,
    )

    assert wrapper is not None
    assert wrapper.metadata.model_id == "dealguard-test-real-credit-v1"
    assert wrapper.metadata.status == ModelStatus.VALIDATED
    assert summary["winning_model"] in ["RandomForest", "XGBoost", "GradientBoosting", "LogisticRegression"]
    assert len(summary["candidate_comparisons"]) >= 5

    # Check candidate comparison fields
    for cand in summary["candidate_comparisons"]:
        assert "val_metrics" in cand
        assert "train_metrics" in cand
        assert "overfitting_gap" in cand
        assert "is_overfitting" in cand

    # Verify SHAP explanation on real instance
    test_feature_dict = df_credit.drop(columns=["default_risk"]).iloc[0].to_dict()
    p_req = PredictionRequest(
        model_id="dealguard-test-real-credit-v1",
        organization_id=uuid.uuid4(),
        deal_id=uuid.uuid4(),
        features=test_feature_dict,
        request_explanation=True,
    )
    res = wrapper.predict(p_req)
    assert res.predicted_value is not None
    assert res.explanation is not None
    assert len(res.explanation.top_features) > 0


def test_extended_model_registry_catalog_completeness():
    """Verify registry contains real-world models, synthetic benchmark models, and specification models."""
    all_models = ExtendedModelRegistry.list_all_models()
    model_ids = {m.model_id for m in all_models}

    # Real-world models
    assert "dealguard-real-churn-v1" in model_ids
    assert "dealguard-real-credit-risk-v1" in model_ids
    assert "dealguard-real-downside-risk-v1" in model_ids

    # Synthetic benchmark models
    assert "dealguard-customer-churn-v1" in model_ids
    assert "dealguard-risk-probability-v1" in model_ids
    assert "dealguard-ebitda-qoe-v1" in model_ids

    # Dataset-limited specification models
    assert "dealguard-revenue-forecast-v1" in model_ids
    assert "dealguard-integration-failure-v1" in model_ids
    assert "dealguard-synergy-realization-v1" in model_ids
    assert "dealguard-post-acquisition-health-v1" in model_ids

    # Verify active trained model instances can be retrieved
    real_churn = ExtendedModelRegistry.get_trained_model("dealguard-real-churn-v1")
    assert real_churn is not None
    assert real_churn.metadata.status == ModelStatus.VALIDATED


@pytest.mark.asyncio
async def test_real_model_inference_via_ml_service(db_session):
    """Test end-to-end ML prediction and persistence for real-world trained model."""
    from app.domains.auth.models import Organization, User
    org = Organization(id=uuid.uuid4(), name="Real ML Org", slug="real-ml-org", tier="ENTERPRISE")
    user = User(id=uuid.uuid4(), email="user@real-ml.com", hashed_password="pw", full_name="ML User", is_active=True)
    db_session.add(org)
    db_session.add(user)
    await db_session.commit()

    context = TenantContext(organization_id=org.id, user_id=user.id, roles=["ADMIN"], permissions={"*"})

    service = MLPredictionService(db_session)
    models = service.list_models()
    assert any(m.model_id == "dealguard-real-churn-v1" for m in models)

    deal_id = uuid.uuid4()
    custom_features = {
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 36,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "Yes",
        "TechSupport": "No",
        "StreamingTV": "Yes",
        "StreamingMovies": "Yes",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 85.50,
        "TotalCharges": 3078.00,
    }

    result = await service.predict(
        context=context,
        deal_id=deal_id,
        model_id="dealguard-real-churn-v1",
        features_override=custom_features,
    )

    assert result.model_id == "dealguard-real-churn-v1"
    assert result.predicted_value is not None
    assert result.explanation is not None
    assert len(result.explanation.top_features) > 0

    # Retrieve persisted record
    persisted = await service.get_prediction_record(context, result.prediction_id)
    assert persisted is not None
    assert persisted.model_id == "dealguard-real-churn-v1"
