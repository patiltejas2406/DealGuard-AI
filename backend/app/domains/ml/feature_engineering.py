"""Feature Engineering & Leakage-Proof Tabular Preprocessing."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from app.domains.ml.data_contracts import DataType, FeatureDefinition


class TabularPreprocessor(BaseEstimator, TransformerMixin):
    """
    Leakage-proof tabular data preprocessor.
    Guarantees that imputation statistics, mean, and variance scalers
    are computed strictly on the training fold and applied to validation,
    testing, and production inference.
    """

    def __init__(self, feature_definitions: List[FeatureDefinition]) -> None:
        self.feature_definitions = feature_definitions
        self.feature_names = [f.name for f in feature_definitions]
        self._imputer: Optional[SimpleImputer] = None
        self._scaler: Optional[StandardScaler] = None
        self._fitted = False

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "TabularPreprocessor":
        """Fit imputation and scaling strictly on training features."""
        # Align features
        X_df = self._ensure_aligned_df(X)

        self._imputer = SimpleImputer(strategy="median")
        X_imputed = self._imputer.fit_transform(X_df)

        self._scaler = StandardScaler()
        self._scaler.fit(X_imputed)

        self._fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted training statistics."""
        if not self._fitted or self._imputer is None or self._scaler is None:
            raise RuntimeError("TabularPreprocessor must be fitted before transforming data.")

        X_df = self._ensure_aligned_df(X)
        X_imputed = self._imputer.transform(X_df)
        return self._scaler.transform(X_imputed)

    def transform_df(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features and return as DataFrame with original column names."""
        transformed = self.transform(X)
        return pd.DataFrame(transformed, columns=self.feature_names, index=X.index)

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
            X_df = pd.DataFrame(X, columns=self.feature_names)

        # Ensure all required features are present
        for feat in self.feature_definitions:
            if feat.name not in X_df.columns:
                if feat.default_value is not None:
                    X_df[feat.name] = feat.default_value
                else:
                    X_df[feat.name] = np.nan

        # Return in exact canonical feature order
        return X_df[self.feature_names]


class DealFeatureExtractor:
    """Extracts standardized ML feature sets from institutional deal domain entities."""

    @staticmethod
    def extract_saas_churn_features(
        metrics: Dict[str, float],
        operational: Dict[str, Any],
        risks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract feature payload for B2B customer churn classification."""
        arr = float(metrics.get("REVENUE", metrics.get("ARR", 1000000.0)))
        nrr = float(metrics.get("NET_REVENUE_RETENTION", 1.05))

        # Risks customer concentration
        concentration = 0.15
        for r in risks:
            if "CONCENTRATION" in r.get("category", ""):
                concentration = max(concentration, float(r.get("score", 12)) / 25.0)

        return {
            "arr_usd": arr,
            "top_customer_concentration_pct": float(operational.get("top_customer_concentration_pct", concentration)),
            "license_utilization_rate": float(operational.get("license_utilization_rate", 0.78)),
            "exec_sponsor_turnover": int(operational.get("exec_sponsor_turnover", 0)),
            "support_tickets_p1_count": int(operational.get("support_tickets_p1_count", 1)),
            "nps_sentiment_score": float(operational.get("nps_sentiment_score", 45.0)),
            "contract_remaining_months": int(operational.get("contract_remaining_months", 12)),
            "net_revenue_retention_pct": nrr,
        }

    @staticmethod
    def extract_ma_risk_features(
        metrics: Dict[str, float],
        qoe_total_add_backs: float,
        risks: List[Dict[str, Any]],
        tech_findings: List[Dict[str, Any]],
        clauses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract feature payload for 17-pillar M&A downside risk probability."""
        rev = float(metrics.get("REVENUE", 50000000.0))
        growth = float(metrics.get("REVENUE_GROWTH", 0.15))
        gross_margin = float(metrics.get("GROSS_MARGIN", 0.70))
        ebitda_margin = float(metrics.get("EBITDA_MARGIN", 0.20))
        leverage = float(metrics.get("DEBT_TO_EBITDA", 3.0))

        qoe_ratio = qoe_total_add_backs / max(rev, 1000000.0)

        # Tech cybersecurity score
        cyber_score = 80.0
        for tf in tech_findings:
            if "SECURITY" in tf.get("category", "") or "INFRASTRUCTURE" in tf.get("category", ""):
                if tf.get("severity") == "CRITICAL":
                    cyber_score -= 25.0
                elif tf.get("severity") == "HIGH":
                    cyber_score -= 15.0
        cyber_score = max(20.0, cyber_score)

        # Legal compliance violations count
        compliance_count = sum(1 for c in clauses if c.get("requires_consent") or c.get("severity") in ["CRITICAL", "HIGH"])

        # Customer concentration
        concentration = 0.20
        for r in risks:
            if "CONCENTRATION" in r.get("category", ""):
                concentration = max(concentration, 0.35)

        return {
            "revenue_growth_rate_pct": growth,
            "gross_margin_pct": gross_margin,
            "ebitda_margin_pct": ebitda_margin,
            "qoe_add_backs_ratio": qoe_ratio,
            "debt_to_ebitda_leverage": leverage,
            "cybersecurity_score": cyber_score,
            "compliance_violations_count": compliance_count,
            "it_systems_overlap_score": float(metrics.get("IT_SYSTEMS_OVERLAP", 0.45)),
            "customer_concentration_top3_pct": concentration,
        }

    @staticmethod
    def extract_ebitda_realization_features(
        reported_ebitda: float,
        qoe_add_backs: float,
        one_time_legal: float,
        headcount_cost: float,
        cloud_hosting: float,
        gross_margin: float,
        cagr_3yr: float,
    ) -> Dict[str, Any]:
        """Extract feature payload for normalized EBITDA realization regression."""
        return {
            "reported_ebitda_usd": reported_ebitda,
            "qoe_add_backs_ratio": qoe_add_backs / max(reported_ebitda, 100000.0),
            "one_time_legal_expenses": one_time_legal,
            "headcount_runrate_cost": headcount_cost,
            "cloud_hosting_spend": cloud_hosting,
            "gross_margin_pct": gross_margin,
            "revenue_cagr_3yr": cagr_3yr,
        }
