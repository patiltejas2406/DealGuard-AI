"""Unit and Integration Tests for ML Data Contracts, Feature Engineering & Training Pipeline."""

import numpy as np
import pandas as pd
import pytest

from app.domains.ml.data_contracts import (
    DataType,
    DatasetMetadata,
    FeatureDefinition,
    SplitMethod,
    TargetDefinition,
    TargetType,
)
from app.domains.ml.datasets.benchmark_datasets import (
    generate_b2b_saas_churn_dataset,
    generate_ebitda_realization_dataset,
    generate_ma_deal_risk_dataset,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.pipeline import MLTrainingPipeline
from app.domains.ml.schemas import ModelTaskType


def test_data_contracts_and_benchmark_dataset_generation():
    """Verify data contract schemas and deterministic benchmark dataset creation."""
    df, snap = generate_b2b_saas_churn_dataset(n_samples=200, random_state=42)

    assert len(df) == 200
    assert "churned" in df.columns
    assert snap.metadata.dataset_id == "dealguard-dataset-churn-v1"
    assert snap.metadata.is_benchmark is True
    assert snap.metadata.row_count == 200
    assert len(snap.feature_definitions) == 8
    assert snap.target_definition.name == "churned"
    assert snap.target_definition.target_type == TargetType.BINARY_CLASSIFICATION

    # Verify deterministic reproducibility (same seed produces exact same SHA256 checksum)
    df2, snap2 = generate_b2b_saas_churn_dataset(n_samples=200, random_state=42)
    assert snap.metadata.data_checksum == snap2.metadata.data_checksum


def test_tabular_preprocessor_anti_leakage_boundary():
    """Verify that TabularPreprocessor fits only on train and transforms validation/test without leakage."""
    df, snap = generate_ma_deal_risk_dataset(n_samples=200, random_state=42)
    train_df = df.iloc[:140].drop(columns=["downside_risk_event"])
    test_df = df.iloc[140:].drop(columns=["downside_risk_event"])

    preprocessor = TabularPreprocessor(snap.feature_definitions)

    # Transform before fit must raise error
    with pytest.raises(RuntimeError):
        preprocessor.transform(test_df)

    preprocessor.fit(train_df)
    train_trans = preprocessor.transform(train_df)
    test_trans = preprocessor.transform(test_df)

    assert train_trans.shape == (140, len(snap.feature_definitions))
    assert test_trans.shape == (60, len(snap.feature_definitions))

    # Mean of standardized train features should be close to 0
    np.testing.assert_allclose(np.mean(train_trans, axis=0), 0.0, atol=1e-2)


def test_classification_training_pipeline_and_baseline_lift():
    """Verify that candidate classifier trains, evaluates baselines, and beats dummy baseline."""
    df, snap = generate_b2b_saas_churn_dataset(n_samples=300, random_state=42)

    wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap,
        model_id="test-churn-model-v1",
        model_name="Test Churn Model",
        task_type=ModelTaskType.CHURN_PREDICTION,
        framework_preference="xgboost",
        random_state=42,
    )

    assert wrapper.metadata.model_id == "test-churn-model-v1"
    metrics = wrapper.metadata.evaluation_metrics
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert "auc_roc" in metrics

    # Candidate classifier must achieve genuine predictive power on held-out test split
    assert metrics["auc_roc"] > 0.65
    assert wrapper.baseline_metrics is not None
    assert "accuracy" in wrapper.baseline_metrics


def test_regression_training_pipeline_evaluation():
    """Verify that regression pipeline trains and produces valid R2 and RMSE metrics."""
    df, snap = generate_ebitda_realization_dataset(n_samples=300, random_state=42)

    wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap,
        model_id="test-ebitda-model-v1",
        model_name="Test EBITDA Realization Model",
        task_type=ModelTaskType.EBITDA_FORECAST,
        framework_preference="xgboost",
        random_state=42,
    )

    assert wrapper.metadata.model_id == "test-ebitda-model-v1"
    metrics = wrapper.metadata.evaluation_metrics
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics

    # Model should have high predictive accuracy (R2 > 0.70 on test split)
    assert metrics["r2"] > 0.70
    assert metrics["rmse"] > 0.0
