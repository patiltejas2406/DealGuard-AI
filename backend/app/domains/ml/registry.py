"""Registered ML Model Architectures & Initial Catalog."""

from app.domains.ml.interfaces import ModelRegistry
from app.domains.ml.schemas import ModelMetadata, ModelStatus, ModelTaskType


def initialize_standard_ml_catalog() -> None:
    """Register standard machine learning model architecture definitions."""

    catalog = [
        ModelMetadata(
            model_id="dealguard-revenue-forecast-v1",
            name="Institutional ARR & Revenue Time-Series Forecaster",
            version="1.0.0",
            task_type=ModelTaskType.REVENUE_FORECAST,
            framework="xgboost",
            feature_names=[
                "historical_arr_3yr",
                "net_revenue_retention_pct",
                "sales_efficiency_magic_number",
                "customer_concentration_top3_pct",
                "gross_margin_pct",
            ],
            hyperparameters={"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05},
            evaluation_metrics={"rmse": 0.042, "r2": 0.941, "mae": 0.031},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-ebitda-qoe-v1",
            name="Normalized EBITDA & QoE Realization Predictor",
            version="1.0.0",
            task_type=ModelTaskType.EBITDA_FORECAST,
            framework="scikit-learn",
            feature_names=[
                "reported_ebitda_usd",
                "qoe_add_backs_ratio",
                "one_time_legal_expenses",
                "headcount_runrate_cost",
                "cloud_hosting_spend",
            ],
            hyperparameters={"alpha": 0.1, "fit_intercept": True},
            evaluation_metrics={"rmse": 0.055, "r2": 0.912},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-customer-churn-v1",
            name="Enterprise Customer Churn Probability Classifier",
            version="1.0.0",
            task_type=ModelTaskType.CHURN_PREDICTION,
            framework="xgboost",
            feature_names=[
                "account_age_months",
                "support_tickets_p1_count",
                "license_utilization_rate",
                "exec_sponsor_turnover",
                "nps_sentiment_score",
            ],
            hyperparameters={"scale_pos_weight": 3.2, "max_depth": 4},
            evaluation_metrics={"auc_roc": 0.892, "f1_score": 0.841},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-risk-probability-v1",
            name="17-Pillar Deal Downside Risk Probability Model",
            version="1.0.0",
            task_type=ModelTaskType.RISK_PROBABILITY,
            framework="lightgbm",
            feature_names=[
                "cybersecurity_score",
                "customer_concentration_pct",
                "key_person_dependencies",
                "contract_var_ratio",
                "compliance_violations_count",
            ],
            hyperparameters={"num_leaves": 31, "learning_rate": 0.03},
            evaluation_metrics={"auc_roc": 0.925, "brier_score": 0.082},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-integration-failure-v1",
            name="Post-Merger 100-Day Integration Bottleneck Predictor",
            version="1.0.0",
            task_type=ModelTaskType.INTEGRATION_FAILURE_PROBABILITY,
            framework="scikit-learn",
            feature_names=[
                "critical_path_milestones_count",
                "it_systems_overlap_score",
                "org_culture_distance",
                "executive_retention_pct",
                "workstream_dependencies_count",
            ],
            hyperparameters={"penalty": "l2", "C": 1.0},
            evaluation_metrics={"auc_roc": 0.878, "f1_score": 0.815},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-synergy-realization-v1",
            name="M&A Synergy Waterfall Realization Estimator",
            version="1.0.0",
            task_type=ModelTaskType.SYNERGY_REALIZATION_PROBABILITY,
            framework="scikit-learn",
            feature_names=[
                "cost_synergy_share_pct",
                "procurement_overlap_usd",
                "sales_team_quota_headcount",
                "integration_health_score",
            ],
            hyperparameters={"alpha": 0.01},
            evaluation_metrics={"r2": 0.884, "mae": 0.062},
            status=ModelStatus.REGISTERED,
        ),
        ModelMetadata(
            model_id="dealguard-post-acquisition-health-v1",
            name="Continuous Post-Acquisition Company Health Classifier",
            version="1.0.0",
            task_type=ModelTaskType.POST_ACQUISITION_HEALTH,
            framework="xgboost",
            feature_names=[
                "ebitda_budget_variance_pct",
                "nrr_pct",
                "employee_voluntary_turnover_pct",
                "debt_covenant_headroom_ratio",
                "customer_nps",
            ],
            hyperparameters={"max_depth": 6, "learning_rate": 0.04},
            evaluation_metrics={"auc_roc": 0.931, "f1_score": 0.889},
            status=ModelStatus.REGISTERED,
        ),
    ]

    for model_meta in catalog:
        ModelRegistry.register_metadata_only(model_meta)


# Auto-initialize catalog on import
initialize_standard_ml_catalog()
