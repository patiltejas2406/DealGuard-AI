"""Comprehensive script to audit and extract actual measured benchmark metrics for Phase 16 ML models."""

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
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from xgboost import XGBClassifier, XGBRegressor

from app.domains.ml.data_contracts import TargetType
from app.domains.ml.datasets.benchmark_datasets import (
    generate_b2b_saas_churn_dataset,
    generate_ebitda_realization_dataset,
    generate_ma_deal_risk_dataset,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import TabularPreprocessor
from app.domains.ml.registry import ExtendedModelRegistry


def audit_target(name, dataset_generator, n_samples=500, random_state=42, is_classification=True):
    print(f"\n=========================================================================================")
    print(f"AUDITING TARGET: {name}")
    print(f"=========================================================================================")

    df, snapshot = dataset_generator(n_samples=n_samples, random_state=random_state)
    df_features = pd.DataFrame(snapshot.features)
    y = np.array(snapshot.targets)

    stratify = y if is_classification else None
    X_train_df, X_temp_df, y_train, y_temp = train_test_split(
        df_features, y, test_size=0.30, random_state=random_state, stratify=stratify
    )

    stratify_temp = y_temp if is_classification else None
    X_val_df, X_test_df, y_val, y_test = train_test_split(
        X_temp_df, y_temp, test_size=0.50, random_state=random_state, stratify=stratify_temp
    )

    preprocessor = TabularPreprocessor(snapshot.feature_definitions)
    preprocessor.fit(X_train_df)

    X_train = preprocessor.transform(X_train_df)
    X_val = preprocessor.transform(X_val_df)
    X_test = preprocessor.transform(X_test_df)

    if is_classification:
        candidates = [
            ("Baseline (Most Frequent)", DummyClassifier(strategy="most_frequent")),
            ("Logistic Regression", LogisticRegression(penalty="l2", C=1.0, solver="liblinear", random_state=random_state)),
            ("Decision Tree", DecisionTreeClassifier(max_depth=4, random_state=random_state)),
            ("Random Forest", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state)),
            ("Gradient Boosting", GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=random_state)),
            ("XGBoost", XGBClassifier(n_estimators=80, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=random_state)),
        ]
    else:
        candidates = [
            ("Baseline (Mean)", DummyRegressor(strategy="mean")),
            ("Ridge Regression", Ridge(alpha=1.0, random_state=random_state)),
            ("Decision Tree", DecisionTreeRegressor(max_depth=4, random_state=random_state)),
            ("Random Forest", RandomForestRegressor(n_estimators=100, max_depth=5, random_state=random_state)),
            ("Gradient Boosting", GradientBoostingRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=random_state)),
            ("XGBoost", XGBRegressor(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=random_state)),
        ]

    results = []

    # Fit baseline for relative lift
    base_model = candidates[0][1]
    base_model.fit(X_train, y_train)
    base_test_pred = base_model.predict(X_test)

    for c_name, model in candidates:
        model.fit(X_train, y_train)

        # Train metrics
        tr_pred = model.predict(X_train)
        tr_prob = model.predict_proba(X_train) if is_classification and hasattr(model, "predict_proba") else None

        # Val metrics
        val_pred = model.predict(X_val)
        val_prob = model.predict_proba(X_val) if is_classification and hasattr(model, "predict_proba") else None

        # Test metrics
        te_pred = model.predict(X_test)
        te_prob = model.predict_proba(X_test) if is_classification and hasattr(model, "predict_proba") else None

        if is_classification:
            tr_m = ModelEvaluator.evaluate_binary_classification(y_train, tr_pred, tr_prob)
            val_m = ModelEvaluator.evaluate_binary_classification(y_val, val_pred, val_prob)
            te_m = ModelEvaluator.evaluate_binary_classification(y_test, te_pred, te_prob, y_baseline=base_test_pred)

            val_key = val_m.get("auc_roc", val_m["f1_score"])
            train_key = tr_m.get("auc_roc", tr_m["f1_score"])
            test_key = te_m.get("auc_roc", te_m["f1_score"])
            overfitting_gap = round(train_key - val_key, 4)
        else:
            tr_m = ModelEvaluator.evaluate_regression(y_train, tr_pred)
            val_m = ModelEvaluator.evaluate_regression(y_val, val_pred)
            te_m = ModelEvaluator.evaluate_regression(y_test, te_pred, y_baseline=base_test_pred)

            val_key = val_m["r2"]
            train_key = tr_m["r2"]
            test_key = te_m["r2"]
            overfitting_gap = round(train_key - val_key, 4)

        results.append({
            "target": name,
            "model": c_name,
            "train_metrics": tr_m,
            "val_metrics": val_m,
            "test_metrics": te_m,
            "val_key": val_key,
            "train_key": train_key,
            "test_key": test_key,
            "overfitting_gap": overfitting_gap,
        })

    # Sort candidates by validation score (excluding baseline)
    candidate_ranking = sorted(results[1:], key=lambda x: x["val_key"], reverse=True)
    selected_name = candidate_ranking[0]["model"]

    for r in results:
        r["selected"] = "YES (SELECTED)" if r["model"] == selected_name else "NO"
        gap_str = f"{r['overfitting_gap']:+.4f}"
        print(f"| {r['target']:<28} | {r['model']:<25} | Val: {r['val_key']:.4f} | Test: {r['test_key']:.4f} | Train: {r['train_key']:.4f} | Gap: {gap_str} | Selected: {r['selected']} |")
        if is_classification:
            print(f"   [Validation] Acc: {r['val_metrics']['accuracy']:.4f}, Prec: {r['val_metrics']['precision']:.4f}, Rec: {r['val_metrics']['recall']:.4f}, F1: {r['val_metrics']['f1_score']:.4f}, ROC-AUC: {r['val_metrics'].get('auc_roc', 0.0):.4f}, Brier: {r['val_metrics'].get('brier_score', 0.0):.4f}")
            print(f"   [Held-out Test] Acc: {r['test_metrics']['accuracy']:.4f}, Prec: {r['test_metrics']['precision']:.4f}, Rec: {r['test_metrics']['recall']:.4f}, F1: {r['test_metrics']['f1_score']:.4f}, ROC-AUC: {r['test_metrics'].get('auc_roc', 0.0):.4f}, Brier: {r['test_metrics'].get('brier_score', 0.0):.4f}")
            print(f"   [Train] Acc: {r['train_metrics']['accuracy']:.4f}, Prec: {r['train_metrics']['precision']:.4f}, Rec: {r['train_metrics']['recall']:.4f}, F1: {r['train_metrics']['f1_score']:.4f}, ROC-AUC: {r['train_metrics'].get('auc_roc', 0.0):.4f}, Brier: {r['train_metrics'].get('brier_score', 0.0):.4f}")
        else:
            print(f"   [Validation] MAE: ${r['val_metrics']['mae']:,.2f}, RMSE: ${r['val_metrics']['rmse']:,.2f}, R2: {r['val_metrics']['r2']:.4f}, MAPE: {r['val_metrics']['mape']:.2f}%")
            print(f"   [Held-out Test] MAE: ${r['test_metrics']['mae']:,.2f}, RMSE: ${r['test_metrics']['rmse']:,.2f}, R2: {r['test_metrics']['r2']:.4f}, MAPE: {r['test_metrics']['mape']:.2f}%")
            print(f"   [Train] MAE: ${r['train_metrics']['mae']:,.2f}, RMSE: ${r['train_metrics']['rmse']:,.2f}, R2: {r['train_metrics']['r2']:.4f}, MAPE: {r['train_metrics']['mape']:.2f}%")

    return results


if __name__ == "__main__":
    r1 = audit_target("dealguard-customer-churn-v1", generate_b2b_saas_churn_dataset, n_samples=600, random_state=42, is_classification=True)
    r2 = audit_target("dealguard-risk-probability-v1", generate_ma_deal_risk_dataset, n_samples=500, random_state=42, is_classification=True)
    r3 = audit_target("dealguard-ebitda-qoe-v1", generate_ebitda_realization_dataset, n_samples=500, random_state=42, is_classification=False)
