"""IEEE-Grade Multi-Model Candidate Benchmarking, Validation Selection & Tuning Engine."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from xgboost import XGBClassifier, XGBRegressor

from app.domains.ml.data_contracts import (
    DatasetSnapshot,
    TargetType,
)
from app.domains.ml.schemas import (
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    TrainingRun,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.quality_audit import DataQualityAuditor
from app.domains.ml.registry import TrainedModelWrapper
from app.domains.ml.xai_engine import XAIEngine


class RealWorldBenchmarkEngine:
    """
    Scientific multi-model benchmarking engine for real-world empirical datasets.
    Enforces strict train/val/test splits, anti-leakage preprocessing, validation-based selection,
    hyperparameter search, final test evaluation, and real SHAP attribution initialization.
    """

    @classmethod
    def benchmark_and_train_target(
        cls,
        snapshot: DatasetSnapshot,
        df: pd.DataFrame,
        target_column: str,
        model_id: str,
        random_state: int = 42,
        perform_tuning: bool = True,
    ) -> Tuple[TrainedModelWrapper, Dict[str, Any]]:
        """
        Execute full IEEE-grade experimental benchmark on a real dataset.
        """
        start_time = datetime.now(timezone.utc)
        is_classification = snapshot.target_definition.target_type in [
            TargetType.BINARY_CLASSIFICATION,
            TargetType.MULTICLASS_CLASSIFICATION,
        ]

        # 1. Automated Data Quality Audit
        quality_report = DataQualityAuditor.audit_dataset(
            df=df,
            target_column=target_column,
            dataset_id=snapshot.metadata.dataset_id,
            is_classification=is_classification,
        )

        # 2. Extract Features & Target
        X_raw = df.drop(columns=[target_column])
        y = df[target_column].values

        # 3. Partition: 70% Train, 15% Validation, 15% Held-Out Test
        stratify = y if is_classification else None
        X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
            X_raw, y, test_size=0.30, random_state=random_state, stratify=stratify
        )

        stratify_temp = y_temp if is_classification else None
        X_val_raw, X_test_raw, y_val, y_test = train_test_split(
            X_temp_raw, y_temp, test_size=0.50, random_state=random_state, stratify=stratify_temp
        )

        # 4. Fit Preprocessor STRICTLY on Training Fold (Anti-Leakage Boundary)
        preprocessor = TabularPreprocessor(snapshot.feature_definitions)
        preprocessor.fit(X_train_raw)

        X_train = preprocessor.transform(X_train_raw)
        X_val = preprocessor.transform(X_val_raw)
        X_test = preprocessor.transform(X_test_raw)

        # 5. Evaluate Statistical Baseline on Final Test Split
        if is_classification:
            baseline_model = DummyClassifier(strategy="most_frequent", random_state=random_state)
            baseline_model.fit(X_train, y_train)
            base_pred_test = baseline_model.predict(X_test)
            base_probs_test = baseline_model.predict_proba(X_test)
            baseline_metrics = ModelEvaluator.evaluate_binary_classification(
                y_test, base_pred_test, base_probs_test
            )
        else:
            baseline_model = DummyRegressor(strategy="mean")
            baseline_model.fit(X_train, y_train)
            base_pred_test = baseline_model.predict(X_test)
            baseline_metrics = ModelEvaluator.evaluate_regression(y_test, base_pred_test)

        # 6. Candidate Model Benchmarking (Train -> Val)
        candidate_rows: List[Dict[str, Any]] = []

        if is_classification:
            candidates = [
                ("LogisticRegression", LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=random_state)),
                ("DecisionTree", DecisionTreeClassifier(max_depth=4, random_state=random_state)),
                ("RandomForest", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state)),
                ("GradientBoosting", GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=random_state)),
                ("XGBoost", XGBClassifier(n_estimators=80, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=random_state)),
            ]

            for c_name, c_model in candidates:
                c_model.fit(X_train, y_train)

                # Training metrics
                tr_preds = c_model.predict(X_train)
                tr_probs = c_model.predict_proba(X_train) if hasattr(c_model, "predict_proba") else None
                tr_metrics = ModelEvaluator.evaluate_binary_classification(y_train, tr_preds, tr_probs)

                # Validation metrics
                val_preds = c_model.predict(X_val)
                val_probs = c_model.predict_proba(X_val) if hasattr(c_model, "predict_proba") else None
                val_metrics = ModelEvaluator.evaluate_binary_classification(y_val, val_preds, val_probs)

                val_score = val_metrics.get("auc_roc", val_metrics.get("f1_score", 0.0))
                train_score = tr_metrics.get("auc_roc", tr_metrics.get("f1_score", 0.0))
                overfitting_gap = round(train_score - val_score, 4)

                candidate_rows.append({
                    "model_name": c_name,
                    "model_instance": c_model,
                    "val_score": val_score,
                    "val_metrics": val_metrics,
                    "train_metrics": tr_metrics,
                    "overfitting_gap": overfitting_gap,
                    "is_overfitting": overfitting_gap > 0.15,
                })
        else:
            candidates = [
                ("Ridge", Ridge(alpha=1.0, random_state=random_state)),
                ("DecisionTree", DecisionTreeRegressor(max_depth=4, random_state=random_state)),
                ("RandomForest", RandomForestRegressor(n_estimators=100, max_depth=5, random_state=random_state)),
                ("GradientBoosting", GradientBoostingRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=random_state)),
                ("XGBoost", XGBRegressor(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=random_state)),
            ]

            for c_name, c_model in candidates:
                c_model.fit(X_train, y_train)

                tr_preds = c_model.predict(X_train)
                tr_metrics = ModelEvaluator.evaluate_regression(y_train, tr_preds)

                val_preds = c_model.predict(X_val)
                val_metrics = ModelEvaluator.evaluate_regression(y_val, val_preds)

                val_score = val_metrics.get("r2", 0.0)
                train_score = tr_metrics.get("r2", 0.0)
                overfitting_gap = round(train_score - val_score, 4)

                candidate_rows.append({
                    "model_name": c_name,
                    "model_instance": c_model,
                    "val_score": val_score,
                    "val_metrics": val_metrics,
                    "train_metrics": tr_metrics,
                    "overfitting_gap": overfitting_gap,
                    "is_overfitting": overfitting_gap > 0.15,
                })

        # 7. Validation-based Model Selection
        candidate_rows.sort(key=lambda x: x["val_score"], reverse=True)
        winner_info = candidate_rows[0]
        winning_name = winner_info["model_name"]
        winning_model = winner_info["model_instance"]

        # 8. Hyperparameter Tuning on Training Fold (Step 9)
        tuned_model = winning_model
        best_params: Dict[str, Any] = {}

        if perform_tuning and is_classification:
            param_grid: Dict[str, List[Any]] = {}
            if winning_name == "LogisticRegression":
                param_grid = {"C": [0.05, 0.1, 1.0, 5.0]}
            elif winning_name == "RandomForest":
                param_grid = {"n_estimators": [50, 100], "max_depth": [4, 6]}
            elif winning_name in ["GradientBoosting", "XGBoost"]:
                param_grid = {"learning_rate": [0.03, 0.05], "max_depth": [3, 4]}

            if param_grid:
                grid = GridSearchCV(winning_model, param_grid, cv=3, scoring="roc_auc", n_jobs=-1)
                grid.fit(X_train, y_train)
                tuned_model = grid.best_estimator_
                best_params = grid.best_params_

        # 9. Final Test Evaluation (Untouched Test Split)
        test_preds = tuned_model.predict(X_test)
        if is_classification:
            test_probs = tuned_model.predict_proba(X_test) if hasattr(tuned_model, "predict_proba") else None
            final_test_metrics = ModelEvaluator.evaluate_binary_classification(
                y_test, test_preds, test_probs, y_baseline=base_pred_test
            )
        else:
            final_test_metrics = ModelEvaluator.evaluate_regression(
                y_test, test_preds, y_baseline=base_pred_test
            )

        # 10. Real SHAP Explainer Initialization (Step 10)
        is_tree = winning_name in ["XGBoost", "RandomForest", "GradientBoosting", "DecisionTree"]
        xai_engine = XAIEngine(
            model=tuned_model,
            feature_names=preprocessor.feature_names,
            background_data=X_train[:100],
            is_tree_model=is_tree,
        )

        completed_time = datetime.now(timezone.utc)

        # 11. Construct Comprehensive Training Run Audit Record
        run_id = uuid.uuid4()
        training_run = TrainingRun(
            run_id=run_id,
            model_id=model_id,
            dataset_uri=snapshot.metadata.dataset_id,
            parameters={
                "selected_algorithm": winning_name,
                "tuned_parameters": best_params,
                "random_state": random_state,
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
                "is_real_world_data": True,
            },
            metrics={k: float(v) for k, v in final_test_metrics.items() if isinstance(v, (int, float))},
            status="COMPLETED",
            started_at=start_time,
            completed_at=completed_time,
        )

        # 12. Create Versioned Model Architecture
        framework_str = "xgboost" if winning_name == "XGBoost" else "scikit-learn"
        if "churn" in model_id.lower():
            task_type_enum = ModelTaskType.CHURN_PREDICTION
        else:
            task_type_enum = ModelTaskType.RISK_PROBABILITY

        model_meta = ModelMetadata(
            model_id=model_id,
            name=f"Real-Data {snapshot.metadata.name} ({winning_name})",
            version="1.0.0",
            task_type=task_type_enum,
            framework=framework_str,
            training_dataset_id=snapshot.metadata.dataset_id,
            feature_names=preprocessor.feature_names,
            status=ModelStatus.VALIDATED,
            evaluation_metrics=final_test_metrics,
            hyperparameters={"algorithm": winning_name, **best_params},
            updated_at=completed_time,
        )

        wrapper = TrainedModelWrapper(
            metadata=model_meta,
            model_instance=tuned_model,
            preprocessor=preprocessor,
            xai_engine=xai_engine,
            feature_definitions=snapshot.feature_definitions,
            training_run=training_run,
            baseline_metrics=baseline_metrics,
            is_classification=is_classification,
        )

        benchmark_summary = {
            "model_id": model_id,
            "dataset_id": snapshot.metadata.dataset_id,
            "dataset_name": snapshot.metadata.name,
            "row_count": len(df),
            "quality_audit": quality_report.model_dump(),
            "baseline_metrics": baseline_metrics,
            "candidate_comparisons": [
                {
                    "model": r["model_name"],
                    "val_metrics": r["val_metrics"],
                    "train_metrics": r["train_metrics"],
                    "overfitting_gap": r["overfitting_gap"],
                    "is_overfitting": r["is_overfitting"],
                }
                for r in candidate_rows
            ],
            "winning_model": winning_name,
            "tuned_parameters": best_params,
            "final_test_metrics": final_test_metrics,
        }

        return wrapper, benchmark_summary
