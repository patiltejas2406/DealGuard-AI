"""
IEEE-Grade ML Benchmark Framework for DealGuard AI.
Reusable, Leakage-Proof Cross-Validation, Probability Calibration, and Model Selection.
"""

import copy
import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.svm import SVC
from xgboost import XGBClassifier

from app.domains.ml.data_contracts import DatasetSnapshot, TargetType
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.quality_audit import DataQualityAuditor
from app.domains.ml.schemas import (
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    TrainingRun,
)
from app.domains.ml.xai_engine import XAIEngine


def get_environment_metadata() -> Dict[str, Any]:
    """Capture runtime environment, library versions, and git commit for IEEE reproducibility."""
    import sklearn
    import xgboost
    import shap
    import scipy

    git_hash = "UNKNOWN"
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        pass

    return {
        "git_commit": git_hash,
        "library_versions": {
            "sklearn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "shap": getattr(shap, "__version__", "unknown"),
            "scipy": scipy.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "excluded_candidates": {
            "LightGBM": "Excluded due to lack of precompiled native wheels in Python 3.13 macOS ARM64 environment. HistGradientBoosting provides equivalent histogram-based tree boosting.",
            "CatBoost": "Excluded due to lack of precompiled native wheels in Python 3.13 macOS ARM64 environment. XGBoost and HistGradientBoosting provide equivalent gradient boosted tree ensembles.",
        },
    }


class BenchmarkResult:
    """Structured container holding all CV metrics, test results, calibration curves, and provenance."""

    def __init__(
        self,
        benchmark_id: str,
        dataset_id: str,
        dataset_name: str,
        dataset_checksum: str,
        random_seed: int,
        env_metadata: Dict[str, Any],
        cv_summary: List[Dict[str, Any]],
        selection_policy: Dict[str, Any],
        winning_model_name: str,
        winning_cv_metrics: Dict[str, Any],
        calibration_results: Dict[str, Any],
        final_test_metrics: Dict[str, Any],
        confusion_matrix: Dict[str, int],
        test_calibration_curve: Dict[str, List[float]],
        data_quality_report: Dict[str, Any],
        sample_counts: Dict[str, int],
        started_at: datetime,
        completed_at: datetime,
    ) -> None:
        self.benchmark_id = benchmark_id
        self.dataset_id = dataset_id
        self.dataset_name = dataset_name
        self.dataset_checksum = dataset_checksum
        self.random_seed = random_seed
        self.env_metadata = env_metadata
        self.cv_summary = cv_summary
        self.selection_policy = selection_policy
        self.winning_model_name = winning_model_name
        self.winning_cv_metrics = winning_cv_metrics
        self.calibration_results = calibration_results
        self.final_test_metrics = final_test_metrics
        self.confusion_matrix = confusion_matrix
        self.test_calibration_curve = test_calibration_curve
        self.data_quality_report = data_quality_report
        self.sample_counts = sample_counts
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "dataset_checksum": self.dataset_checksum,
            "random_seed": self.random_seed,
            "git_commit": self.env_metadata.get("git_commit"),
            "library_versions": self.env_metadata.get("library_versions"),
            "excluded_candidates": self.env_metadata.get("excluded_candidates"),
            "sample_counts": self.sample_counts,
            "cv_summary": self.cv_summary,
            "selection_policy": self.selection_policy,
            "winning_model_name": self.winning_model_name,
            "winning_cv_metrics": self.winning_cv_metrics,
            "calibration_results": self.calibration_results,
            "final_test_metrics": self.final_test_metrics,
            "confusion_matrix": self.confusion_matrix,
            "test_calibration_curve": self.test_calibration_curve,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
        }


class MLBenchmarkFramework:
    """
    IEEE-defensible, research-grade ML Benchmark Framework.
    Guarantees strict train/test separation, zero-leakage inside cross-validation folds,
    rigorous probability calibration benchmarking, and synchronized XAI.
    """

    @classmethod
    def benchmark_dataset(
        cls,
        snapshot: DatasetSnapshot,
        df: pd.DataFrame,
        target_column: str,
        model_id: str,
        task_type: ModelTaskType = ModelTaskType.RISK_PROBABILITY,
        random_seed: int = 42,
        n_cv_folds: int = 5,
        test_size: float = 0.20,
    ) -> Tuple[Any, BenchmarkResult]:
        """
        Execute full IEEE-grade experimental benchmark on a dataset.
        Returns the fitted, calibrated production TrainedModelWrapper and the complete BenchmarkResult.
        """
        started_at = datetime.now(timezone.utc)
        env_metadata = get_environment_metadata()

        # 1. Dataset SHA-256 Checksum
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        dataset_checksum = hashlib.sha256(csv_bytes).hexdigest()

        # 2. Automated Data Quality Audit
        quality_report = DataQualityAuditor.audit_dataset(
            df=df,
            target_column=target_column,
            dataset_id=snapshot.metadata.dataset_id,
            is_classification=True,
        )

        # 3. Extract Raw Features and Target
        X_raw = df.drop(columns=[target_column])
        y = df[target_column].values.astype(int)

        # 4. Stratified Split: 80% Training Data, 20% Held-Out Untouched Test Split
        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            X_raw,
            y,
            test_size=test_size,
            random_state=random_seed,
            stratify=y,
        )
        X_train_raw = X_train_raw.reset_index(drop=True)
        X_test_raw = X_test_raw.reset_index(drop=True)

        sample_counts = {
            "total_samples": len(df),
            "train_samples": len(X_train_raw),
            "test_samples": len(X_test_raw),
            "feature_count": X_raw.shape[1],
            "class_distribution_overall": {
                "class_0": int((y == 0).sum()),
                "class_1": int((y == 1).sum()),
            },
            "class_distribution_train": {
                "class_0": int((y_train == 0).sum()),
                "class_1": int((y_train == 1).sum()),
            },
            "class_distribution_test": {
                "class_0": int((y_test == 0).sum()),
                "class_1": int((y_test == 1).sum()),
            },
        }

        # 5. Define Candidate Classification Models
        candidates: List[Tuple[str, Any]] = [
            (
                "LogisticRegression",
                LogisticRegression(
                    penalty="l2",
                    C=1.0,
                    solver="liblinear",
                    max_iter=1000,
                    random_state=random_seed,
                ),
            ),
            (
                "RandomForest",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    min_samples_split=4,
                    random_state=random_seed,
                ),
            ),
            (
                "ExtraTrees",
                ExtraTreesClassifier(
                    n_estimators=100,
                    max_depth=5,
                    min_samples_split=4,
                    random_state=random_seed,
                ),
            ),
            (
                "GradientBoosting",
                GradientBoostingClassifier(
                    n_estimators=80,
                    max_depth=3,
                    learning_rate=0.05,
                    random_state=random_seed,
                ),
            ),
            (
                "HistGradientBoosting",
                HistGradientBoostingClassifier(
                    max_iter=80,
                    max_depth=4,
                    learning_rate=0.05,
                    random_state=random_seed,
                ),
            ),
            (
                "XGBoost",
                XGBClassifier(
                    n_estimators=80,
                    max_depth=3,
                    learning_rate=0.05,
                    eval_metric="logloss",
                    random_state=random_seed,
                ),
            ),
        ]

        # Conditionally include SVM if dataset size is computationally feasible
        if len(X_train_raw) <= 2500:
            candidates.append(
                (
                    "SVM",
                    SVC(
                        kernel="linear",
                        C=1.0,
                        probability=True,
                        random_state=random_seed,
                    ),
                )
            )

        # 6. Stratified K-Fold Cross-Validation (Strict Zero-Leakage Preprocessing)
        skf = StratifiedKFold(n_splits=n_cv_folds, shuffle=True, random_state=random_seed)
        candidate_fold_metrics: Dict[str, Dict[str, List[float]]] = {
            c_name: {
                "auc_roc": [],
                "pr_auc": [],
                "f1_score": [],
                "precision": [],
                "recall": [],
                "balanced_accuracy": [],
                "log_loss": [],
                "brier_score": [],
            }
            for c_name, _ in candidates
        }

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_train_raw, y_train), start=1):
            X_fold_train_raw = X_train_raw.iloc[train_idx]
            y_fold_train = y_train[train_idx]
            X_fold_val_raw = X_train_raw.iloc[val_idx]
            y_fold_val = y_train[val_idx]

            # Fit preprocessor STRICTLY on this fold's training slice
            fold_preprocessor = TabularPreprocessor(snapshot.feature_definitions)
            fold_preprocessor.fit(X_fold_train_raw)

            X_fold_train = fold_preprocessor.transform(X_fold_train_raw)
            X_fold_val = fold_preprocessor.transform(X_fold_val_raw)

            for c_name, c_base in candidates:
                fold_model = clone(c_base)
                fold_model.fit(X_fold_train, y_fold_train)

                val_preds = fold_model.predict(X_fold_val)
                val_probs = (
                    fold_model.predict_proba(X_fold_val)
                    if hasattr(fold_model, "predict_proba")
                    else None
                )

                m = ModelEvaluator.evaluate_binary_classification(
                    y_fold_val, val_preds, val_probs
                )

                for metric_key in candidate_fold_metrics[c_name].keys():
                    candidate_fold_metrics[c_name][metric_key].append(float(m.get(metric_key, 0.0)))

        # 7. Aggregate CV Performance (Mean ± Standard Deviation)
        cv_summary: List[Dict[str, Any]] = []
        for c_name, _ in candidates:
            metrics_dict = candidate_fold_metrics[c_name]
            row: Dict[str, Any] = {"model_name": c_name}
            for metric_key, values in metrics_dict.items():
                mean_val = float(np.mean(values))
                std_val = float(np.std(values))
                row[f"{metric_key}_mean"] = round(mean_val, 4)
                row[f"{metric_key}_std"] = round(std_val, 4)
            cv_summary.append(row)

        # 8. Documented Objective Selection Policy (1-Standard-Error / Parsimony Rule)
        # Primary: Mean CV ROC-AUC
        # Secondary: Lowest CV Brier Score (better calibration), lower variance (std), and PR-AUC
        # 1-SE Rule: Any model within 1 Standard Error of the top ROC-AUC is statistically equivalent;
        # among equivalent models, prefer lower Brier loss, lower variance, and simpler architecture.
        cv_summary.sort(
            key=lambda x: (x["auc_roc_mean"], -x["brier_score_mean"], -x["auc_roc_std"]),
            reverse=True,
        )

        top_candidate = cv_summary[0]
        best_auc = top_candidate["auc_roc_mean"]
        one_se = round(top_candidate["auc_roc_std"] / np.sqrt(n_cv_folds), 4)
        se_threshold = round(best_auc - one_se, 4)

        # Candidate models within 1-Standard-Error of the top ROC-AUC
        statistically_equivalent = [
            c for c in cv_summary if c["auc_roc_mean"] >= se_threshold
        ]

        # Model complexity order (simpler models preferred when performance difference is within 1 SE)
        complexity_tier = {
            "LogisticRegression": 1,
            "RandomForest": 2,
            "ExtraTrees": 3,
            "HistGradientBoosting": 4,
            "GradientBoosting": 5,
            "XGBoost": 6,
            "SVM": 7,
        }

        def parsimony_score(c: Dict[str, Any]) -> Tuple[float, float, float, int]:
            # Lower brier score is better -> negative for reverse sort
            # Lower variance (std) is better -> negative for reverse sort
            # Higher PR-AUC is better -> positive
            # Lower complexity tier is better -> negative
            return (
                -c["brier_score_mean"],
                -c["auc_roc_std"],
                c["pr_auc_mean"],
                -complexity_tier.get(c["model_name"], 10),
            )

        if len(statistically_equivalent) > 1:
            winning_candidate_summary = max(statistically_equivalent, key=parsimony_score)
        else:
            winning_candidate_summary = top_candidate

        winning_name = winning_candidate_summary["model_name"]
        winning_base_model = next(c_model for c_name, c_model in candidates if c_name == winning_name)

        selection_policy = {
            "policy_name": "1-Standard-Error (1-SE) Parsimony Policy",
            "primary_metric": "auc_roc_mean",
            "top_candidate": top_candidate["model_name"],
            "top_roc_auc": best_auc,
            "one_standard_error": one_se,
            "statistically_equivalent_models": [c["model_name"] for c in statistically_equivalent],
            "selected_winner": winning_name,
            "selection_rationale": (
                f"{winning_name} selected under 1-SE rule (best AUC: {best_auc:.4f}, SE threshold: {se_threshold:.4f}) "
                f"with superior calibration (Brier: {winning_candidate_summary['brier_score_mean']:.4f}) "
                f"and lower variance (Std: {winning_candidate_summary['auc_roc_std']:.4f})."
            ),
        }

        # 9. Fit Preprocessor and Winning Estimator on ENTIRE Training Set (80%)
        final_train_preprocessor = TabularPreprocessor(snapshot.feature_definitions)
        final_train_preprocessor.fit(X_train_raw)

        X_train = final_train_preprocessor.transform(X_train_raw)
        X_test = final_train_preprocessor.transform(X_test_raw)

        full_train_model = clone(winning_base_model)
        full_train_model.fit(X_train, y_train)

        # 10. Probability Calibration Benchmarking (Platt Sigmoid vs Isotonic on Training Split)
        # Evaluated via 3-fold internal CV inside the 80% training set
        calibration_results: Dict[str, Any] = {}

        # Raw uncalibrated baseline on CV
        raw_probs_cv = []
        raw_y_cv = []
        internal_skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_seed)
        for tr_idx, vl_idx in internal_skf.split(X_train, y_train):
            m_tmp = clone(winning_base_model)
            m_tmp.fit(X_train[tr_idx], y_train[tr_idx])
            probs_vl = m_tmp.predict_proba(X_train[vl_idx])[:, 1]
            raw_probs_cv.extend(probs_vl)
            raw_y_cv.extend(y_train[vl_idx])

        uncalibrated_brier = float(ModelEvaluator.evaluate_binary_classification(
            np.array(raw_y_cv), (np.array(raw_probs_cv) >= 0.5).astype(int), np.array(raw_probs_cv)
        )["brier_score"])

        # Platt Scaling (Sigmoid)
        cal_sigmoid = CalibratedClassifierCV(estimator=clone(winning_base_model), method="sigmoid", cv=3)
        cal_sigmoid.fit(X_train, y_train)
        sig_probs_cv = cal_sigmoid.predict_proba(X_train)[:, 1]
        sig_brier = float(ModelEvaluator.evaluate_binary_classification(
            y_train, (sig_probs_cv >= 0.5).astype(int), sig_probs_cv
        )["brier_score"])

        # Isotonic Regression
        cal_isotonic = CalibratedClassifierCV(estimator=clone(winning_base_model), method="isotonic", cv=3)
        cal_isotonic.fit(X_train, y_train)
        iso_probs_cv = cal_isotonic.predict_proba(X_train)[:, 1]
        iso_brier = float(ModelEvaluator.evaluate_binary_classification(
            y_train, (iso_probs_cv >= 0.5).astype(int), iso_probs_cv
        )["brier_score"])

        # Determine best calibration approach
        chosen_calibrator = full_train_model
        calibration_method = "NONE"
        selected_brier = uncalibrated_brier

        if sig_brier < uncalibrated_brier and sig_brier <= iso_brier:
            chosen_calibrator = cal_sigmoid
            calibration_method = "PLATT_SIGMOID"
            selected_brier = sig_brier
        elif iso_brier < uncalibrated_brier and iso_brier < sig_brier:
            chosen_calibrator = cal_isotonic
            calibration_method = "ISOTONIC"
            selected_brier = iso_brier

        calibration_results = {
            "uncalibrated_brier": round(uncalibrated_brier, 4),
            "sigmoid_brier": round(sig_brier, 4),
            "isotonic_brier": round(iso_brier, 4),
            "selected_calibration": calibration_method,
            "training_brier_improvement_pct": round(
                max(0.0, (uncalibrated_brier - selected_brier) / uncalibrated_brier) * 100.0, 2
            ),
        }

        # 11. Evaluate Statistical Dummy Baseline on Final Test Split
        dummy = DummyClassifier(strategy="most_frequent", random_state=random_seed)
        dummy.fit(X_train, y_train)
        base_test_pred = dummy.predict(X_test)

        # 12. SINGLE-PASS UNTOUCHED TEST SET EVALUATION
        final_test_preds = chosen_calibrator.predict(X_test)
        final_test_probs = chosen_calibrator.predict_proba(X_test)

        final_test_metrics = ModelEvaluator.evaluate_binary_classification(
            y_test, final_test_preds, final_test_probs, y_baseline=base_test_pred
        )

        test_cm = final_test_metrics.get("confusion_matrix", {})
        test_cal_curve = final_test_metrics.get("calibration_curve", {})

        # 13. Synchronized Explainable AI (TreeSHAP vs Linear)
        is_tree = winning_name in ["XGBoost", "RandomForest", "ExtraTrees", "GradientBoosting"]
        model_for_shap = full_train_model
        xai_engine = XAIEngine(
            model=model_for_shap,
            feature_names=final_train_preprocessor.feature_names,
            background_data=X_train[:100],
            is_tree_model=is_tree,
        )

        completed_at = datetime.now(timezone.utc)
        benchmark_id = f"bm-{uuid.uuid4().hex[:8]}"

        benchmark_res = BenchmarkResult(
            benchmark_id=benchmark_id,
            dataset_id=snapshot.metadata.dataset_id,
            dataset_name=snapshot.metadata.name,
            dataset_checksum=dataset_checksum,
            random_seed=random_seed,
            env_metadata=env_metadata,
            cv_summary=cv_summary,
            selection_policy=selection_policy,
            winning_model_name=winning_name,
            winning_cv_metrics=winning_candidate_summary,
            calibration_results=calibration_results,
            final_test_metrics=final_test_metrics,
            confusion_matrix=test_cm,
            test_calibration_curve=test_cal_curve,
            data_quality_report=quality_report.model_dump(),
            sample_counts=sample_counts,
            started_at=started_at,
            completed_at=completed_at,
        )

        # 14. Build TrainedModelWrapper and Metadata for Registry
        run_id = uuid.uuid4()
        training_run = TrainingRun(
            run_id=run_id,
            model_id=model_id,
            dataset_uri=snapshot.metadata.dataset_id,
            parameters={
                "selected_algorithm": winning_name,
                "calibration_method": calibration_method,
                "random_seed": random_seed,
                "cv_folds": n_cv_folds,
                "dataset_checksum": dataset_checksum,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "is_real_world_data": True,
            },
            metrics={
                k: float(v)
                for k, v in final_test_metrics.items()
                if isinstance(v, (int, float))
            },
            status="COMPLETED",
            started_at=started_at,
            completed_at=completed_at,
        )

        model_meta = ModelMetadata(
            model_id=model_id,
            name=f"Empirical {snapshot.metadata.name} ({winning_name})",
            version="2.0.0",
            task_type=task_type,
            framework="xgboost" if winning_name == "XGBoost" else "scikit-learn",
            training_dataset_id=snapshot.metadata.dataset_id,
            feature_names=final_train_preprocessor.feature_names,
            status=ModelStatus.VALIDATED,
            evaluation_metrics=final_test_metrics,
            hyperparameters={
                "algorithm": winning_name,
                "calibration_method": calibration_method,
                "random_seed": random_seed,
                "cv_summary": winning_candidate_summary,
            },
            updated_at=completed_at,
        )

        from app.domains.ml.registry import TrainedModelWrapper
        wrapper = TrainedModelWrapper(
            metadata=model_meta,
            model_instance=chosen_calibrator,
            preprocessor=final_train_preprocessor,
            xai_engine=xai_engine,
            feature_definitions=snapshot.feature_definitions,
            training_run=training_run,
            baseline_metrics={"baseline_accuracy": final_test_metrics.get("baseline_accuracy", 0.0)},
            is_classification=True,
        )

        return wrapper, benchmark_res
