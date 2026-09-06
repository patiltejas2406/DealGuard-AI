"""
Tests for IEEE-Grade ML Benchmark Framework, Zero-Leakage Cross-Validation,
Probability Calibration, and Four-Pillar Uncertainty Architecture.
"""

import uuid
import pytest
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

from app.domains.decision.engine import calculate_composite_decision_score
from app.domains.ml.benchmark_framework import MLBenchmarkFramework, get_environment_metadata
from app.domains.ml.data_contracts import (
    DataType,
    DatasetMetadata,
    DatasetSnapshot,
    FeatureDefinition,
    SplitMethod,
    TargetDefinition,
    TargetType,
)
from app.domains.ml.datasets.real_world_datasets import (
    load_real_commercial_loan_default_dataset,
    load_real_credit_risk_dataset,
    load_real_customer_churn_dataset,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.registry import ExtendedModelRegistry
from app.domains.ml.schemas import ModelTaskType


def test_environment_metadata_ieee_reproducibility():
    """Verify runtime metadata captures git commit, library versions, and candidate exclusions."""
    meta = get_environment_metadata()
    assert "git_commit" in meta
    assert len(meta["git_commit"]) > 0
    assert "library_versions" in meta
    assert "sklearn" in meta["library_versions"]
    assert "xgboost" in meta["library_versions"]
    assert "shap" in meta["library_versions"]
    assert "excluded_candidates" in meta
    assert "LightGBM" in meta["excluded_candidates"]
    assert "CatBoost" in meta["excluded_candidates"]


def test_zero_leakage_tabular_preprocessor():
    """Verify that TabularPreprocessor parameters are fitted solely on training slices."""
    feature_defs = [
        FeatureDefinition(name="num1", data_type=DataType.FLOAT, description="num1", domain="FINANCIAL"),
        FeatureDefinition(name="cat1", data_type=DataType.CATEGORICAL, description="cat1", domain="OPERATIONAL"),
    ]
    df_train = pd.DataFrame({"num1": [10.0, 20.0, 30.0], "cat1": ["A", "B", "A"]})
    df_test = pd.DataFrame({"num1": [100.0, 200.0], "cat1": ["C", "B"]})  # 'C' is unseen

    preprocessor = TabularPreprocessor(feature_defs)
    preprocessor.fit(df_train)

    # Scaler mean must match df_train (20.0), NOT contaminated by df_test
    assert preprocessor._scaler.mean_[0] == pytest.approx(20.0)

    # Transform test: unseen category 'C' must map to -1 without raising error
    X_test_trans = preprocessor.transform(df_test)
    assert X_test_trans.shape == (2, 2)
    assert X_test_trans[0, 1] == -1.0  # OrdinalEncoder unknown_value=-1


def test_ieee_model_evaluator_eight_metrics():
    """Verify ModelEvaluator produces all 8 required IEEE evaluation metrics."""
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 0, 0, 1, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.4, 0.3, 0.9, 0.1, 0.6, 0.7, 0.85])

    metrics = ModelEvaluator.evaluate_binary_classification(y_true, y_pred, y_prob)

    assert "auc_roc" in metrics
    assert "pr_auc" in metrics
    assert "f1_score" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "balanced_accuracy" in metrics
    assert "log_loss" in metrics
    assert "brier_score" in metrics
    assert "confusion_matrix" in metrics
    assert "calibration_curve" in metrics

    assert 0.0 <= metrics["auc_roc"] <= 1.0
    assert 0.0 <= metrics["brier_score"] <= 1.0
    assert metrics["confusion_matrix"]["tn"] >= 0


def test_stratified_cv_benchmarking_and_calibration():
    """Verify Stratified 5-Fold CV computes mean ± std across all candidates and calibrates probability."""
    df_credit, snap_credit = load_real_credit_risk_dataset()

    wrapper, bench_res = MLBenchmarkFramework.benchmark_dataset(
        snapshot=snap_credit,
        df=df_credit,
        target_column="default_risk",
        model_id="test-ieee-credit-v1",
        random_seed=42,
        n_cv_folds=3,  # Fast 3-fold execution for unit test
        test_size=0.20,
    )

    assert bench_res is not None
    assert bench_res.random_seed == 42
    assert len(bench_res.dataset_checksum) == 64
    assert len(bench_res.cv_summary) >= 6

    # Verify fold-wise mean ± std metrics are present
    for cand in bench_res.cv_summary:
        assert "auc_roc_mean" in cand
        assert "auc_roc_std" in cand
        assert "brier_score_mean" in cand
        assert "f1_score_mean" in cand
        assert "balanced_accuracy_mean" in cand
        assert "log_loss_mean" in cand

    # Verify calibration results recorded
    assert "selected_calibration" in bench_res.calibration_results
    assert bench_res.calibration_results["selected_calibration"] in ["PLATT_SIGMOID", "ISOTONIC", "NONE"]

    # Verify final test split metrics are populated and distinct from CV
    test_m = bench_res.final_test_metrics
    assert "auc_roc" in test_m
    assert "brier_score" in test_m
    assert "confusion_matrix" in test_m
    assert test_m["confusion_matrix"]["tn"] > 0


def test_explainability_synchronization_with_winner():
    """Verify XAIEngine is initialized with appropriate explainer matching winning model."""
    df_credit, snap_credit = load_real_credit_risk_dataset()
    wrapper, bench_res = MLBenchmarkFramework.benchmark_dataset(
        snapshot=snap_credit,
        df=df_credit,
        target_column="default_risk",
        model_id="test-xai-sync",
        random_seed=42,
        n_cv_folds=3,
    )

    is_tree = bench_res.winning_model_name in ["RandomForest", "XGBoost", "ExtraTrees", "GradientBoosting"]
    assert wrapper.xai_engine.is_tree_model == is_tree


def test_four_pillar_uncertainty_architecture_and_insufficient_evidence():
    """Verify decision engine outputs 4-pillar uncertainty and flags INSUFFICIENT_EVIDENCE on sparse data."""
    class SparseDeal:
        target_ev = None

    # Test 1: Sparse deal with zero documents, citations, or statements
    sparse_res = calculate_composite_decision_score(
        deal=SparseDeal(),
        statements=[],
        metrics=[],
        qoe_adjustments=[],
        valuation=None,
        valuation_outputs=[],
        risks=[],
        documents=[],
        citations=[],
    )

    assert "uncertainty_profile" in sparse_res
    profile = sparse_res["uncertainty_profile"]
    assert profile["is_insufficient_evidence"] is True
    assert profile["decision_confidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert profile["evidence_coverage"] < 0.50
    assert "INSUFFICIENT EVIDENCE" in sparse_res["recommendations"][0]

    # Test 2: Verify all 4 dimensions are documented
    dims = profile["uncertainty_dimensions"]
    assert "A_model_performance" in dims
    assert "B_prediction_probability" in dims
    assert "C_evidence_coverage" in dims
    assert "D_decision_confidence" in dims
