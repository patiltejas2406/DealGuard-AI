"""Feature Engineering & Leakage-Proof Tabular Preprocessing."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from app.domains.ml.data_contracts import DataType, FeatureDefinition


class TabularPreprocessor(BaseEstimator, TransformerMixin):
    """
    Leakage-proof tabular data preprocessor supporting mixed numeric and categorical features.
    Guarantees that imputation statistics, ordinal encoders, mean, and variance scalers
    are computed strictly on the training fold and applied to validation,
    testing, and production inference without leakage.
    """

    def __init__(self, feature_definitions: List[FeatureDefinition]) -> None:
        self.feature_definitions = feature_definitions
        self.raw_feature_names = [f.name for f in feature_definitions]
        self.numeric_cols = [f.name for f in feature_definitions if f.data_type in [DataType.FLOAT, DataType.INT]]
        self.categorical_cols = [f.name for f in feature_definitions if f.data_type in [DataType.CATEGORICAL, DataType.BOOLEAN, DataType.TIMESTAMP]]

        self._num_imputer: Optional[SimpleImputer] = None
        self._cat_imputer: Optional[SimpleImputer] = None
        self._scaler: Optional[StandardScaler] = None
        self._encoder: Optional[OrdinalEncoder] = None
        self._fitted = False
        self.feature_names = self.raw_feature_names

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "TabularPreprocessor":
        """Fit imputation, encoding, and scaling strictly on training features."""
        X_df = self._ensure_aligned_df(X)

        if self.numeric_cols:
            self._num_imputer = SimpleImputer(strategy="median")
            X_num = self._num_imputer.fit_transform(X_df[self.numeric_cols])
            self._scaler = StandardScaler()
            self._scaler.fit(X_num)

        if self.categorical_cols:
            self._cat_imputer = SimpleImputer(strategy="most_frequent")
            X_cat = self._cat_imputer.fit_transform(X_df[self.categorical_cols].astype(str))
            self._encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            self._encoder.fit(X_cat)

        self._fitted = True
        self.feature_names = self.numeric_cols + self.categorical_cols
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted training statistics."""
        if not self._fitted:
            raise RuntimeError("TabularPreprocessor must be fitted before transforming data.")

        X_df = self._ensure_aligned_df(X)
        parts = []

        if self.numeric_cols and self._num_imputer is not None and self._scaler is not None:
            X_num_imp = self._num_imputer.transform(X_df[self.numeric_cols])
            X_num_scaled = self._scaler.transform(X_num_imp)
            parts.append(X_num_scaled)

        if self.categorical_cols and self._cat_imputer is not None and self._encoder is not None:
            X_cat_imp = self._cat_imputer.transform(X_df[self.categorical_cols].astype(str))
            X_cat_enc = self._encoder.transform(X_cat_imp)
            parts.append(X_cat_enc)

        if not parts:
            return np.empty((len(X_df), 0))

        return np.hstack(parts)

    def transform_df(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features and return as DataFrame with original column names."""
        transformed = self.transform(X)
        col_names = self.numeric_cols + self.categorical_cols
        return pd.DataFrame(transformed, columns=col_names, index=X.index)

    def transform_single_dict(self, features: Dict[str, Any]) -> np.ndarray:
        """Transform a single feature payload dictionary for real-time inference."""
        row_df = pd.DataFrame([features])
        return self.transform(row_df)

    def _ensure_aligned_df(self, X: Any) -> pd.DataFrame:
        """Ensure input matches defined feature schemas and column ordering."""
        if isinstance(X, dict):
            X_df = pd.DataFrame([X])
        elif isinstance(X, pd.DataFrame):
            X_df = X.copy()
        elif isinstance(X, list):
            X_df = pd.DataFrame(X)
        else:
            X_df = pd.DataFrame(X, columns=self.raw_feature_names)

        # Ensure all required features are present
        for feat in self.feature_definitions:
            if feat.name not in X_df.columns:
                if feat.default_value is not None:
                    X_df[feat.name] = feat.default_value
                else:
                    X_df[feat.name] = np.nan

        # Return in exact canonical feature order
        return X_df[self.raw_feature_names]


class DealFeatureExtractor:
    """Extracts standardized ML feature sets from institutional deal domain entities."""

    @staticmethod
    def extract_saas_churn_features(
        metrics: Optional[Dict[str, float]] = None,
        operational: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract standardized features for customer churn model."""
        m = metrics or {}
        op = operational or {}
        return {
            "arr_usd": float(m.get("REVENUE", 1000000.0)),
            "top_customer_concentration_pct": float(m.get("CUSTOMER_CONCENTRATION", 0.25)),
            "license_utilization_rate": float(op.get("license_utilization", op.get("license_utilization_rate", 0.85))),
            "exec_sponsor_turnover": int(op.get("exec_sponsor_turnover", 0)),
            "support_tickets_p1_count": int(op.get("p1_tickets", op.get("support_tickets_p1_count", 1))),
            "nps_sentiment_score": float(op.get("nps_score", op.get("nps_sentiment_score", 45.0))),
            "contract_remaining_months": int(op.get("contract_months", op.get("contract_remaining_months", 12))),
            "net_revenue_retention_pct": float(m.get("NRR", 1.10)),
        }

    @staticmethod
    def extract_deal_risk_features(
        financials: Optional[Dict[str, float]] = None,
        risk_counts: Optional[Dict[str, int]] = None,
        tech_scores: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract standardized features for M&A deal downside risk probability model."""
        fin = financials or kwargs.get("metrics") or {}
        rc = risk_counts or {}
        ts = tech_scores or {}
        risks_list = kwargs.get("risks", [])
        return {
            "revenue_growth_rate_pct": float(fin.get("REVENUE_CAGR", fin.get("REVENUE_GROWTH", 0.15))),
            "gross_margin_pct": float(fin.get("GROSS_MARGIN", 0.70)),
            "ebitda_margin_pct": float(fin.get("EBITDA_MARGIN", 0.22)),
            "qoe_add_backs_ratio": float(fin.get("QOE_RATIO", kwargs.get("qoe_total_add_backs", 0.08) / 1000000.0 if kwargs.get("qoe_total_add_backs") else 0.08)),
            "debt_to_ebitda_leverage": float(fin.get("LEVERAGE", 3.0)),
            "cybersecurity_score": float(ts.get("cyber_score", 82.0)),
            "compliance_violations_count": int(rc.get("compliance_violations", len(risks_list))),
            "it_systems_overlap_score": float(ts.get("it_overlap", 0.40)),
            "customer_concentration_top3_pct": float(fin.get("CONCENTRATION_TOP3", 0.30)),
        }

    extract_ma_risk_features = extract_deal_risk_features

    @staticmethod
    def extract_ebitda_realization_features(
        financials: Optional[Dict[str, float]] = None,
        expenses: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract standardized features for EBITDA realization predictor."""
        fin = financials or {}
        exp = expenses or {}
        reported = float(fin.get("REPORTED_EBITDA", kwargs.get("reported_ebitda", 5000000.0)))
        qoe_val = float(fin.get("QOE_ADJUSTMENTS", kwargs.get("qoe_add_backs", 400000.0)))
        qoe_ratio = round(qoe_val / reported, 4) if reported > 0 else 0.0

        return {
            "reported_ebitda_usd": reported,
            "qoe_add_backs_ratio": qoe_ratio,
            "one_time_legal_expenses": float(exp.get("legal_expenses", kwargs.get("one_time_legal", 150000.0))),
            "headcount_runrate_cost": float(exp.get("headcount_cost", kwargs.get("headcount_cost", 1200000.0))),
            "cloud_hosting_spend": float(exp.get("cloud_spend", kwargs.get("cloud_hosting", 350000.0))),
            "gross_margin_pct": float(fin.get("GROSS_MARGIN", kwargs.get("gross_margin", 0.72))),
            "revenue_cagr_3yr": float(fin.get("REVENUE_CAGR", kwargs.get("cagr_3yr", 0.20))),
        }
