"""Automated Data Quality Audit, Leakage Detection & Suitability Evaluator."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.domains.ml.data_contracts import DatasetSuitabilityReport


class DataQualityAuditor:
    """
    Automated statistical data quality and leakage auditor for real-world datasets.
    Evaluates missingness, duplicate frequency, extreme imbalance, constant features,
    and potential target contamination.
    """

    @classmethod
    def audit_dataset(
        cls,
        df: pd.DataFrame,
        target_column: str,
        dataset_id: str,
        is_classification: bool = True,
        max_allowed_missing_pct: float = 0.35,
    ) -> DatasetSuitabilityReport:
        """
        Execute comprehensive automated data quality and integrity audit.
        """
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols if total_rows > 0 else 1

        missing_count = int(df.isna().sum().sum())
        missing_pct = round(missing_count / total_cells, 4)

        duplicate_count = int(df.duplicated().sum())

        leakage_risks: List[str] = []
        recommendations: List[str] = []
        is_suitable = True

        # 1. Check Missingness Severity
        if missing_pct > max_allowed_missing_pct:
            is_suitable = False
            leakage_risks.append(f"High overall missingness: {missing_pct:.1%} of data matrix is missing.")
            recommendations.append("Apply targeted domain imputation or drop columns exceeding 50% missing values.")
        elif missing_count > 0:
            recommendations.append(f"Dataset contains {missing_count} missing values ({missing_pct:.2%}). Imputation required during preprocessing.")

        # 2. Check for Constant Columns (Zero Variance)
        feature_cols = [c for c in df.columns if c != target_column]
        constant_cols = [c for c in feature_cols if df[c].nunique(dropna=False) <= 1]
        if constant_cols:
            leakage_risks.append(f"Constant/Zero-variance columns detected: {constant_cols}")
            recommendations.append(f"Drop constant columns before fitting: {constant_cols}")

        # 3. Check for ID / High Cardinality Leakage
        for c in feature_cols:
            if df[c].dtype == object or isinstance(df[c].dtype, pd.CategoricalDtype):
                unique_ratio = df[c].nunique() / total_rows
                if unique_ratio > 0.90 and total_rows > 50:
                    leakage_risks.append(f"Potential Identifier / High-cardinality leak in column '{c}' ({unique_ratio:.1%} unique).")
                    recommendations.append(f"Exclude primary key / identifier '{c}' from model feature space.")

        # 4. Check Class Balance for Classification
        class_imbalance_ratio: Optional[float] = None
        if is_classification and target_column in df.columns:
            val_counts = df[target_column].value_counts(normalize=True)
            if len(val_counts) >= 2:
                minority_pct = float(val_counts.min())
                majority_pct = float(val_counts.max())
                class_imbalance_ratio = round(majority_pct / minority_pct, 2)

                if minority_pct < 0.03:
                    leakage_risks.append(f"Severe class imbalance: minority class is {minority_pct:.2%}.")
                    recommendations.append("Use StratifiedKFold and PR-AUC / balanced class weights for evaluation.")
                elif class_imbalance_ratio > 3.0:
                    recommendations.append(f"Moderate class imbalance ({class_imbalance_ratio}:1). Evaluate with ROC-AUC and F1 rather than raw Accuracy.")

        # 5. Check Feature-Target Correlation Contamination (Leakage Proxy)
        if target_column in df.columns:
            for c in feature_cols:
                if pd.api.types.is_numeric_dtype(df[c]) and pd.api.types.is_numeric_dtype(df[target_column]):
                    corr = df[[c, target_column]].corr().iloc[0, 1]
                    if abs(corr) > 0.99:
                        is_suitable = False
                        leakage_risks.append(f"Severe Target Leakage: feature '{c}' has {corr:.4f} Pearson correlation with target.")
                        recommendations.append(f"Immediately remove contaminated feature '{c}'.")

        return DatasetSuitabilityReport(
            dataset_id=dataset_id,
            is_suitable_for_training=is_suitable,
            total_rows=total_rows,
            missing_value_pct=missing_pct,
            duplicate_rows_count=duplicate_count,
            class_imbalance_ratio=class_imbalance_ratio,
            leakage_risks=leakage_risks,
            recommendations=recommendations,
        )
