"""Machine Learning Training Pipeline, Candidate Models & Model Selection."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

from app.domains.ml.data_contracts import (
    DatasetMetadata,
    DatasetSnapshot,
    FeatureDefinition,
    SplitMethod,
    TargetType,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.schemas import (
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    PredictionRequest,
    PredictionResult,
    TrainingRun,
)
from app.domains.ml.xai_engine import XAIEngine


class TrainedModelWrapper:
    """Production wrapper encapsulating fitted preprocessor, ML estimator, and SHAP explainer."""

    def __init__(
        self,
        metadata: ModelMetadata,
        model_instance: Any,
        preprocessor: TabularPreprocessor,
        xai_engine: XAIEngine,
        feature_definitions: List[FeatureDefinition],
        training_run: TrainingRun,
        baseline_metrics: Dict[str, float],
        is_classification: bool = True,
    ) -> None:
        self.metadata = metadata
        self.model = model_instance
        self.preprocessor = preprocessor
        self.xai_engine = xai_engine
        self.feature_definitions = feature_definitions
        self.training_run = training_run
        self.baseline_metrics = baseline_metrics
        self.is_classification = is_classification

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Execute inference, calculate confidence & uncertainty, and compute real SHAP attributions."""
        feature_dict = request.features

        # Transform features through fitted preprocessor
        X_trans = self.preprocessor.transform_single_dict(feature_dict)

        prediction_id = uuid.uuid4()
        prob_dist: Optional[Dict[str, float]] = None
        conf_interval: Optional[Tuple[float, float]] = None
        confidence = 0.90

        if self.is_classification:
            # Classification inference
            pred_class = int(self.model.predict(X_trans)[0])
            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(X_trans)[0]
                prob_pos = float(probs[1]) if len(probs) > 1 else float(probs[0])
                prob_neg = float(probs[0]) if len(probs) > 1 else 1.0 - prob_pos
                prob_dist = {"CLASS_0": round(prob_neg, 4), "CLASS_1": round(prob_pos, 4)}

                # Confidence based on probability certainty
                dist_from_boundary = abs(prob_pos - 0.5) * 2.0  # 0.0 at 0.5, 1.0 at 0.0 or 1.0
                confidence = max(0.60, min(0.98, 0.60 + 0.38 * dist_from_boundary))
            predicted_val = pred_class
        else:
            # Regression inference
            pred_numeric = float(self.model.predict(X_trans)[0])
            predicted_val = round(pred_numeric, 2)

            # Estimate standard uncertainty interval
            rmse = self.metadata.evaluation_metrics.get("rmse", abs(pred_numeric) * 0.08)
            conf_interval = (round(pred_numeric - 1.96 * rmse, 2), round(pred_numeric + 1.96 * rmse, 2))
            confidence = 0.92

        # Generate Real SHAP Explanation if requested
        explanation = None
        if request.request_explanation:
            explanation = self.xai_engine.explain_instance(
                X_instance=X_trans,
                feature_dict=feature_dict,
                model_id=self.metadata.model_id,
                prediction_id=prediction_id,
                target_name=self.metadata.name,
                is_classification=self.is_classification,
            )

        return PredictionResult(
            prediction_id=prediction_id,
            model_id=self.metadata.model_id,
            model_version=self.metadata.version,
            task_type=self.metadata.task_type,
            predicted_value=predicted_val,
            probability_distribution=prob_dist,
            confidence_interval=conf_interval,
            prediction_confidence=round(confidence, 4),
            explanation=explanation,
            created_at=datetime.now(timezone.utc),
        )


class MLTrainingPipeline:
    """
    Automated training, model selection, baseline comparison,
    and validation pipeline.
    """

    @classmethod
    def train_and_select(
        cls,
        snapshot: DatasetSnapshot,
        model_id: str,
        model_name: str,
        task_type: ModelTaskType,
        framework_preference: str = "xgboost",
        random_state: int = 42,
    ) -> TrainedModelWrapper:
        """
        Execute reproducible training pipeline:
        1. Preprocess data (fit preprocessor strictly on train split)
        2. Evaluate dummy baseline model
        3. Train candidate models (Linear/Logistic, Random Forest, XGBoost)
        4. Validate and select best candidate
        5. Evaluate on held-out test split
        6. Initialize SHAP explainer on training background
        """
        start_time = datetime.now(timezone.utc)
        run_id = uuid.uuid4()

        # Build DataFrame
        df_features = pd.DataFrame(snapshot.features)
        y = np.array(snapshot.targets)
        is_classification = snapshot.target_definition.target_type in [
            TargetType.BINARY_CLASSIFICATION,
            TargetType.MULTICLASS_CLASSIFICATION,
        ]

        # 1. Stratified / Random Train (70%), Val (15%), Test (15%) Split
        stratify = y if is_classification else None
        X_train_df, X_temp_df, y_train, y_temp = train_test_split(
            df_features, y, test_size=0.30, random_state=random_state, stratify=stratify
        )

        stratify_temp = y_temp if is_classification else None
        X_val_df, X_test_df, y_val, y_test = train_test_split(
            X_temp_df, y_temp, test_size=0.50, random_state=random_state, stratify=stratify_temp
        )

        # 2. Fit Preprocessor Strictly on Training Fold (Anti-Leakage)
        preprocessor = TabularPreprocessor(snapshot.feature_definitions)
        preprocessor.fit(X_train_df)

        X_train = preprocessor.transform(X_train_df)
        X_val = preprocessor.transform(X_val_df)
        X_test = preprocessor.transform(X_test_df)

        # 3. Fit Statistical Baseline Model
        if is_classification:
            baseline_model = DummyClassifier(strategy="most_frequent")
            baseline_model.fit(X_train, y_train)
            base_pred_val = baseline_model.predict(X_val)
            base_pred_test = baseline_model.predict(X_test)
            baseline_metrics = ModelEvaluator.evaluate_binary_classification(y_test, base_pred_test)
        else:
            baseline_model = DummyRegressor(strategy="mean")
            baseline_model.fit(X_train, y_train)
            base_pred_val = baseline_model.predict(X_val)
            base_pred_test = baseline_model.predict(X_test)
            baseline_metrics = ModelEvaluator.evaluate_regression(y_test, base_pred_test)

        # 4. Train Candidate Models
        candidate_results = []

        if is_classification:
            candidates = [
                ("LogisticRegression", LogisticRegression(penalty="l2", C=1.0, max_iter=500, random_state=random_state)),
                ("RandomForest", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state)),
                ("XGBoost", XGBClassifier(n_estimators=80, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=random_state)),
            ]
            for c_name, c_model in candidates:
                c_model.fit(X_train, y_train)
                val_preds = c_model.predict(X_val)
                val_probs = c_model.predict_proba(X_val) if hasattr(c_model, "predict_proba") else None
                val_metrics = ModelEvaluator.evaluate_binary_classification(y_val, val_preds, val_probs)
                score = val_metrics.get("auc_roc", val_metrics.get("f1_score", 0.0))
                candidate_results.append((score, c_name, c_model, val_metrics))
        else:
            candidates = [
                ("Ridge", Ridge(alpha=1.0, random_state=random_state)),
                ("RandomForest", RandomForestRegressor(n_estimators=100, max_depth=5, random_state=random_state)),
                ("XGBoost", XGBRegressor(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=random_state)),
            ]
            for c_name, c_model in candidates:
                c_model.fit(X_train, y_train)
                val_preds = c_model.predict(X_val)
                val_metrics = ModelEvaluator.evaluate_regression(y_val, val_preds)
                # Maximize R2 (or minimize RMSE)
                score = val_metrics.get("r2", 0.0)
                candidate_results.append((score, c_name, c_model, val_metrics))

        # 5. Select Winning Candidate
        candidate_results.sort(key=lambda x: x[0], reverse=True)
        best_score, best_name, best_model, best_val_metrics = candidate_results[0]

        # 6. Evaluate Winning Model on Final Test Split
        test_preds = best_model.predict(X_test)
        if is_classification:
            test_probs = best_model.predict_proba(X_test) if hasattr(best_model, "predict_proba") else None
            final_metrics = ModelEvaluator.evaluate_binary_classification(
                y_test, test_preds, test_probs, y_baseline=base_pred_test
            )
        else:
            final_metrics = ModelEvaluator.evaluate_regression(
                y_test, test_preds, y_baseline=base_pred_test
            )

        # 7. Initialize Real SHAP Explainer on Training Fold Background
        is_tree = best_name in ["XGBoost", "RandomForest"]
        xai_engine = XAIEngine(
            model=best_model,
            feature_names=preprocessor.feature_names,
            background_data=X_train[:100],  # 100 background samples
            is_tree_model=is_tree,
        )

        completed_time = datetime.now(timezone.utc)

        # 8. Construct Training Audit Record
        training_run = TrainingRun(
            run_id=run_id,
            model_id=model_id,
            dataset_uri=snapshot.metadata.dataset_id,
            parameters={"best_model": best_name, "random_state": random_state, "n_samples": len(y)},
            metrics={k: float(v) for k, v in final_metrics.items() if isinstance(v, (int, float))},
            status="COMPLETED",
            started_at=start_time,
            completed_at=completed_time,
        )

        metadata = ModelMetadata(
            model_id=model_id,
            name=model_name,
            version="1.0.0",
            task_type=task_type,
            framework="xgboost" if best_name == "XGBoost" else "scikit-learn",
            training_dataset_id=snapshot.metadata.dataset_id,
            feature_names=preprocessor.feature_names,
            hyperparameters={"algorithm": best_name, "random_state": random_state},
            evaluation_metrics={k: float(v) for k, v in final_metrics.items() if isinstance(v, (int, float))},
            status=ModelStatus.VALIDATED,
            created_at=completed_time,
            updated_at=completed_time,
        )

        return TrainedModelWrapper(
            metadata=metadata,
            model_instance=best_model,
            preprocessor=preprocessor,
            xai_engine=xai_engine,
            feature_definitions=snapshot.feature_definitions,
            training_run=training_run,
            baseline_metrics={k: float(v) for k, v in baseline_metrics.items() if isinstance(v, (int, float))},
            is_classification=is_classification,
        )
