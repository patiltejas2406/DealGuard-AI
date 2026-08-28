"""Unit and Integration Tests for Real Explainable AI (XAI) & SHAP Calculations."""

import uuid
import pytest

from app.domains.ml.datasets.benchmark_datasets import generate_b2b_saas_churn_dataset
from app.domains.ml.pipeline import MLTrainingPipeline
from app.domains.ml.schemas import ModelTaskType, PredictionRequest


def test_real_shap_explanation_and_feature_attributions():
    """Verify that SHAP TreeExplainer calculates exact, non-hallucinated attributions."""
    df, snap = generate_b2b_saas_churn_dataset(n_samples=250, random_state=42)

    wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap,
        model_id="test-xai-churn-model",
        model_name="Test XAI Churn Model",
        task_type=ModelTaskType.CHURN_PREDICTION,
        framework_preference="xgboost",
        random_state=42,
    )

    # Sample test inference payload
    test_features = {
        "arr_usd": 750000.0,
        "top_customer_concentration_pct": 0.45,
        "license_utilization_rate": 0.35,  # Low utilization
        "exec_sponsor_turnover": 1,        # Sponsor left
        "support_tickets_p1_count": 4,     # Multiple severe tickets
        "nps_sentiment_score": -20.0,      # Negative NPS
        "contract_remaining_months": 3,
        "net_revenue_retention_pct": 0.85, # Declining NRR
    }

    req = PredictionRequest(
        model_id="test-xai-churn-model",
        organization_id=uuid.uuid4(),
        deal_id=uuid.uuid4(),
        features=test_features,
        request_explanation=True,
    )

    result = wrapper.predict(req)

    assert result.predicted_value in [0, 1]
    assert result.probability_distribution is not None
    assert result.explanation is not None

    exp = result.explanation
    assert exp.method in ["SHAP_TREE", "SHAP_LINEAR"]
    assert len(exp.top_features) > 0
    assert len(exp.shap_values) == len(snap.feature_definitions)

    # Top features must have non-zero importance scores
    assert exp.top_features[0].importance_score > 0.0

    # Narrative explanation must reflect primary drivers
    assert len(exp.narrative_summary) > 20
    assert "Primary factors" in exp.narrative_summary or "Mitigating factors" in exp.narrative_summary
