"""Extended Model Registry — Active Trained Instances & Catalog Lifecycle."""

from typing import Any, Dict, List, Optional
from app.domains.ml.data_contracts import DatasetSnapshot
from app.domains.ml.datasets.benchmark_datasets import (
    generate_b2b_saas_churn_dataset,
    generate_ebitda_realization_dataset,
    generate_ma_deal_risk_dataset,
)
from app.domains.ml.pipeline import MLTrainingPipeline, TrainedModelWrapper
from app.domains.ml.schemas import (
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    TrainingRun,
)


class ExtendedModelRegistry:
    """
    Production registry managing trained model instances, training runs,
    and specification-only catalog entries.
    """

    _trained_models: Dict[str, TrainedModelWrapper] = {}
    _metadata_catalog: Dict[str, ModelMetadata] = {}
    _training_runs: Dict[str, TrainingRun] = {}
    _dataset_snapshots: Dict[str, DatasetSnapshot] = {}

    @classmethod
    def register_trained_model(cls, wrapper: TrainedModelWrapper) -> None:
        """Register an active trained model wrapper instance."""
        meta = wrapper.metadata
        cls._trained_models[meta.model_id] = wrapper
        cls._metadata_catalog[meta.model_id] = meta
        cls._training_runs[str(wrapper.training_run.run_id)] = wrapper.training_run

    @classmethod
    def register_specification_only(cls, metadata: ModelMetadata) -> None:
        """Register a model specification that requires customer dataset ingestion."""
        cls._metadata_catalog[metadata.model_id] = metadata

    @classmethod
    def register_dataset_snapshot(cls, snapshot: DatasetSnapshot) -> None:
        """Store an immutable dataset snapshot."""
        cls._dataset_snapshots[snapshot.metadata.dataset_id] = snapshot

    @classmethod
    def get_trained_model(cls, model_id: str) -> Optional[TrainedModelWrapper]:
        """Retrieve an active trained model wrapper."""
        return cls._trained_models.get(model_id)

    @classmethod
    def get_metadata(cls, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve model metadata by ID."""
        return cls._metadata_catalog.get(model_id)

    @classmethod
    def list_all_models(cls) -> List[ModelMetadata]:
        """List metadata for all models in catalog."""
        return list(cls._metadata_catalog.values())

    @classmethod
    def list_training_runs(cls) -> List[TrainingRun]:
        """List all training runs."""
        return list(cls._training_runs.values())

    @classmethod
    def get_dataset_snapshot(cls, dataset_id: str) -> Optional[DatasetSnapshot]:
        """Retrieve dataset snapshot by ID."""
        return cls._dataset_snapshots.get(dataset_id)


def initialize_and_train_production_models() -> None:
    """
    Train and register empirical production models for benchmark-supported targets,
    and register clean specification metadata for dataset-required targets.
    """
    # 1. Train Enterprise SaaS Churn Model (REAL TRAINED MODEL)
    df_churn, snap_churn = generate_b2b_saas_churn_dataset(n_samples=600, random_state=42)
    ExtendedModelRegistry.register_dataset_snapshot(snap_churn)

    churn_wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap_churn,
        model_id="dealguard-customer-churn-v1",
        model_name="Enterprise Customer Churn Probability Classifier",
        task_type=ModelTaskType.CHURN_PREDICTION,
        framework_preference="xgboost",
        random_state=42,
    )
    ExtendedModelRegistry.register_trained_model(churn_wrapper)

    # 2. Train 17-Pillar Deal Downside Risk Probability Model (REAL TRAINED MODEL)
    df_risk, snap_risk = generate_ma_deal_risk_dataset(n_samples=500, random_state=42)
    ExtendedModelRegistry.register_dataset_snapshot(snap_risk)

    risk_wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap_risk,
        model_id="dealguard-risk-probability-v1",
        model_name="17-Pillar Deal Downside Risk Probability Model",
        task_type=ModelTaskType.RISK_PROBABILITY,
        framework_preference="xgboost",
        random_state=42,
    )
    ExtendedModelRegistry.register_trained_model(risk_wrapper)

    # 3. Train Post-Deal EBITDA Realization Predictor (REAL TRAINED MODEL)
    df_ebitda, snap_ebitda = generate_ebitda_realization_dataset(n_samples=500, random_state=42)
    ExtendedModelRegistry.register_dataset_snapshot(snap_ebitda)

    ebitda_wrapper = MLTrainingPipeline.train_and_select(
        snapshot=snap_ebitda,
        model_id="dealguard-ebitda-qoe-v1",
        model_name="Normalized EBITDA & QoE Realization Predictor",
        task_type=ModelTaskType.EBITDA_FORECAST,
        framework_preference="xgboost",
        random_state=42,
    )
    ExtendedModelRegistry.register_trained_model(ebitda_wrapper)

    # 4. Specification-Only Models (Clearly flagged as REGISTERED / DATASET_REQUIRED without fake training)
    spec_models = [
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
            hyperparameters={"status": "AWAITING_TIME_SERIES_ACCOUNTING_DATASET"},
            evaluation_metrics={},
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
            hyperparameters={"status": "AWAITING_PMO_MILESTONE_LOGS"},
            evaluation_metrics={},
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
            hyperparameters={"status": "AWAITING_ERP_REALIZATION_LOGS"},
            evaluation_metrics={},
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
            hyperparameters={"status": "AWAITING_BOARD_TELEMETRY_LOGS"},
            evaluation_metrics={},
            status=ModelStatus.REGISTERED,
        ),
    ]

    for sm in spec_models:
        ExtendedModelRegistry.register_specification_only(sm)


# Initialize and train on module load
initialize_and_production_models = initialize_and_train_production_models
initialize_and_train_production_models()

# Export alias for compatibility
ModelRegistry = ExtendedModelRegistry
