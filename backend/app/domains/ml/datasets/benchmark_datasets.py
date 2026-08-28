"""Synthetic Benchmark Datasets for Model Pipeline Validation & Reproducible Training."""

import hashlib
import json
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from app.domains.ml.data_contracts import (
    DataType,
    DatasetMetadata,
    DatasetSnapshot,
    FeatureDefinition,
    SplitMethod,
    TargetDefinition,
    TargetType,
)


def _compute_checksum(df: pd.DataFrame) -> str:
    """Compute deterministic SHA256 checksum of a pandas DataFrame."""
    buf = df.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(buf).hexdigest()


def generate_b2b_saas_churn_dataset(n_samples: int = 600, random_state: int = 42) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Generate a Synthetic Benchmark Dataset for enterprise B2B SaaS customer churn.
    Used exclusively for deterministic ML pipeline validation, anti-leakage verification,
    and end-to-end integration testing. (Not real historical customer data).
    """
    rng = np.random.default_rng(random_state)

    # Feature distributions
    arr = rng.lognormal(mean=13.0, sigma=0.8, size=n_samples)  # ~$100k - $2M ARR
    concentration = rng.uniform(0.05, 0.65, size=n_samples)
    utilization = rng.beta(a=5, b=2, size=n_samples)  # Skewed toward higher utilization
    exec_turnover = rng.choice([0, 1], size=n_samples, p=[0.75, 0.25])
    p1_tickets = rng.poisson(lam=1.8, size=n_samples)
    nps_score = np.clip(rng.normal(loc=42.0, scale=28.0, size=n_samples), -100.0, 100.0)
    contract_months = rng.choice([3, 6, 12, 24, 36], size=n_samples, p=[0.1, 0.15, 0.5, 0.15, 0.1])
    nrr = np.clip(rng.normal(loc=1.06, scale=0.14, size=n_samples), 0.60, 1.60)

    # Non-linear probability of churn
    # Low utilization, exec turnover, high P1 tickets, low NPS, and low NRR increase churn logit
    z = (
        -1.8
        + 1.8 * (1.0 - utilization)
        + 1.4 * exec_turnover
        + 0.35 * p1_tickets
        - 0.02 * nps_score
        - 2.2 * (nrr - 1.0)
        + 0.8 * concentration
        - 0.03 * contract_months
    )
    prob_churn = 1.0 / (1.0 + np.exp(-z))
    churned = (rng.uniform(0.0, 1.0, size=n_samples) < prob_churn).astype(int)

    df = pd.DataFrame({
        "arr_usd": np.round(arr, 2),
        "top_customer_concentration_pct": np.round(concentration, 4),
        "license_utilization_rate": np.round(utilization, 4),
        "exec_sponsor_turnover": exec_turnover,
        "support_tickets_p1_count": p1_tickets,
        "nps_sentiment_score": np.round(nps_score, 1),
        "contract_remaining_months": contract_months,
        "net_revenue_retention_pct": np.round(nrr, 4),
        "churned": churned,
    })

    checksum = _compute_checksum(df)

    feature_defs = [
        FeatureDefinition(name="arr_usd", data_type=DataType.FLOAT, description="Annual recurring revenue in USD", domain="FINANCIAL"),
        FeatureDefinition(name="top_customer_concentration_pct", data_type=DataType.FLOAT, description="Top customer share of account revenue", domain="RISK"),
        FeatureDefinition(name="license_utilization_rate", data_type=DataType.FLOAT, description="Active user seat utilization (0.0 to 1.0)", domain="OPERATIONAL"),
        FeatureDefinition(name="exec_sponsor_turnover", data_type=DataType.INT, description="Binary flag indicating executive buyer departure", domain="OPERATIONAL"),
        FeatureDefinition(name="support_tickets_p1_count", data_type=DataType.INT, description="Number of critical Severity-1 tickets opened in 90 days", domain="OPERATIONAL"),
        FeatureDefinition(name="nps_sentiment_score", data_type=DataType.FLOAT, description="Net Promoter Score (-100 to +100)", domain="OPERATIONAL"),
        FeatureDefinition(name="contract_remaining_months", data_type=DataType.INT, description="Months until contract renewal", domain="LEGAL"),
        FeatureDefinition(name="net_revenue_retention_pct", data_type=DataType.FLOAT, description="Historical Net Revenue Retention ratio", domain="FINANCIAL"),
    ]

    target_def = TargetDefinition(
        name="churned",
        target_type=TargetType.BINARY_CLASSIFICATION,
        description="Whether account terminated contract at expiration",
        class_labels=["RETAINED", "CHURNED"],
    )

    metadata = DatasetMetadata(
        dataset_id="dealguard-dataset-churn-v1",
        version="1.0.0",
        name="Synthetic Benchmark — Enterprise B2B SaaS Churn Dataset",
        source="Synthetic Benchmark Data (Parametric Simulation for Pipeline Validation)",
        task_type="CHURN_PREDICTION",
        target_name="churned",
        row_count=n_samples,
        feature_count=len(feature_defs),
        split_method=SplitMethod.STRATIFIED,
        data_checksum=checksum,
        is_benchmark=True,
        is_synthetic=True,
        leakage_notes="Synthetic benchmark dataset generated with fixed PRNG seed for deterministic validation. Not real customer data.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["churned"]).to_dict(orient="records"),
        targets=df["churned"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot


def generate_ma_deal_risk_dataset(n_samples: int = 500, random_state: int = 42) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Generate a Synthetic Benchmark Dataset for M&A 17-pillar downside risk probability.
    Used exclusively for deterministic ML pipeline validation, anti-leakage verification,
    and end-to-end integration testing. (Not real historical customer data).
    """
    rng = np.random.default_rng(random_state)

    rev_growth = rng.normal(loc=0.18, scale=0.15, size=n_samples)
    gross_margin = np.clip(rng.normal(loc=0.68, scale=0.12, size=n_samples), 0.20, 0.95)
    ebitda_margin = np.clip(rng.normal(loc=0.19, scale=0.10, size=n_samples), -0.20, 0.50)
    qoe_ratio = np.clip(rng.exponential(scale=0.12, size=n_samples), 0.0, 0.60)
    leverage = np.clip(rng.normal(loc=3.2, scale=1.4, size=n_samples), 0.5, 9.0)
    cyber_score = np.clip(rng.normal(loc=76.0, scale=14.0, size=n_samples), 20.0, 100.0)
    compliance_violations = rng.poisson(lam=1.2, size=n_samples)
    it_systems_overlap = np.clip(rng.beta(a=3, b=3, size=n_samples), 0.0, 1.0)
    customer_concentration = np.clip(rng.beta(a=2, b=5, size=n_samples), 0.05, 0.75)

    # Risk score function
    z = (
        -2.2
        - 2.5 * rev_growth
        - 1.8 * gross_margin
        - 2.0 * ebitda_margin
        + 2.8 * qoe_ratio
        + 0.35 * (leverage - 3.0)
        - 0.03 * (cyber_score - 70.0)
        + 0.45 * compliance_violations
        + 1.2 * it_systems_overlap
        + 2.2 * customer_concentration
    )
    prob_risk = 1.0 / (1.0 + np.exp(-z))
    risk_event = (rng.uniform(0.0, 1.0, size=n_samples) < prob_risk).astype(int)

    df = pd.DataFrame({
        "revenue_growth_rate_pct": np.round(rev_growth, 4),
        "gross_margin_pct": np.round(gross_margin, 4),
        "ebitda_margin_pct": np.round(ebitda_margin, 4),
        "qoe_add_backs_ratio": np.round(qoe_ratio, 4),
        "debt_to_ebitda_leverage": np.round(leverage, 2),
        "cybersecurity_score": np.round(cyber_score, 1),
        "compliance_violations_count": compliance_violations,
        "it_systems_overlap_score": np.round(it_systems_overlap, 4),
        "customer_concentration_top3_pct": np.round(customer_concentration, 4),
        "downside_risk_event": risk_event,
    })

    checksum = _compute_checksum(df)

    feature_defs = [
        FeatureDefinition(name="revenue_growth_rate_pct", data_type=DataType.FLOAT, description="YoY top-line revenue expansion", domain="FINANCIAL"),
        FeatureDefinition(name="gross_margin_pct", data_type=DataType.FLOAT, description="Gross profit margin %", domain="FINANCIAL"),
        FeatureDefinition(name="ebitda_margin_pct", data_type=DataType.FLOAT, description="Reported EBITDA margin %", domain="FINANCIAL"),
        FeatureDefinition(name="qoe_add_backs_ratio", data_type=DataType.FLOAT, description="Total QoE add-backs divided by reported revenue", domain="FINANCIAL"),
        FeatureDefinition(name="debt_to_ebitda_leverage", data_type=DataType.FLOAT, description="Total Debt divided by normalized EBITDA", domain="FINANCIAL"),
        FeatureDefinition(name="cybersecurity_score", data_type=DataType.FLOAT, description="SOC 2 & infrastructure security posture score (0-100)", domain="TECHNOLOGY"),
        FeatureDefinition(name="compliance_violations_count", data_type=DataType.INT, description="Open legal/regulatory non-compliance issues", domain="LEGAL"),
        FeatureDefinition(name="it_systems_overlap_score", data_type=DataType.FLOAT, description="IT systems redundancy score (0.0 to 1.0)", domain="TECHNOLOGY"),
        FeatureDefinition(name="customer_concentration_top3_pct", data_type=DataType.FLOAT, description="Top 3 customers share of total revenue", domain="RISK"),
    ]

    target_def = TargetDefinition(
        name="downside_risk_event",
        target_type=TargetType.BINARY_CLASSIFICATION,
        description="Whether target experienced post-acquisition value impairment (>20% EBITDA drop)",
        class_labels=["NO_IMPAIRMENT", "DOWNSIDE_IMPAIRMENT"],
    )

    metadata = DatasetMetadata(
        dataset_id="dealguard-dataset-risk-v1",
        version="1.0.0",
        name="Synthetic Benchmark — M&A Deal Downside Risk Benchmark Dataset",
        source="Synthetic Benchmark Data (Parametric Simulation for Pipeline Validation)",
        task_type="RISK_PROBABILITY",
        target_name="downside_risk_event",
        row_count=n_samples,
        feature_count=len(feature_defs),
        split_method=SplitMethod.STRATIFIED,
        data_checksum=checksum,
        is_benchmark=True,
        is_synthetic=True,
        leakage_notes="Synthetic benchmark dataset generated with fixed PRNG seed for deterministic validation. Not real customer data.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["downside_risk_event"]).to_dict(orient="records"),
        targets=df["downside_risk_event"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot


def generate_ebitda_realization_dataset(n_samples: int = 500, random_state: int = 42) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Generate a Synthetic Benchmark Dataset for EBITDA realization regression.
    Used exclusively for deterministic ML pipeline validation, anti-leakage verification,
    and end-to-end integration testing. (Not real historical customer data).
    """
    rng = np.random.default_rng(random_state)

    reported_ebitda = rng.uniform(2000000.0, 35000000.0, size=n_samples)
    qoe_add_backs = rng.uniform(0.0, 0.35, size=n_samples) * reported_ebitda
    one_time_legal = rng.exponential(scale=250000.0, size=n_samples)
    headcount_runrate = rng.uniform(0.20, 0.65, size=n_samples) * reported_ebitda
    cloud_hosting = rng.uniform(0.04, 0.15, size=n_samples) * reported_ebitda
    gross_margin = np.clip(rng.normal(loc=0.72, scale=0.10, size=n_samples), 0.30, 0.95)
    cagr_3yr = np.clip(rng.normal(loc=0.22, scale=0.12, size=n_samples), -0.10, 0.70)

    # Target: Realized EBITDA post-close = Reported EBITDA + ~85% of approved QoE add-backs - headcount leakage + noise
    realized_ebitda = (
        reported_ebitda
        + 0.82 * qoe_add_backs
        + 0.90 * one_time_legal
        - 0.08 * headcount_runrate
        - 0.05 * cloud_hosting
        + 0.15 * gross_margin * reported_ebitda
        + rng.normal(loc=0.0, scale=0.05 * reported_ebitda, size=n_samples)
    )

    df = pd.DataFrame({
        "reported_ebitda_usd": np.round(reported_ebitda, 2),
        "qoe_add_backs_ratio": np.round(qoe_add_backs / reported_ebitda, 4),
        "one_time_legal_expenses": np.round(one_time_legal, 2),
        "headcount_runrate_cost": np.round(headcount_runrate, 2),
        "cloud_hosting_spend": np.round(cloud_hosting, 2),
        "gross_margin_pct": np.round(gross_margin, 4),
        "revenue_cagr_3yr": np.round(cagr_3yr, 4),
        "realized_ebitda_post_close_usd": np.round(realized_ebitda, 2),
    })

    checksum = _compute_checksum(df)

    feature_defs = [
        FeatureDefinition(name="reported_ebitda_usd", data_type=DataType.FLOAT, description="Base reported EBITDA before diligence", domain="FINANCIAL"),
        FeatureDefinition(name="qoe_add_backs_ratio", data_type=DataType.FLOAT, description="QoE add-backs as a fraction of reported EBITDA", domain="FINANCIAL"),
        FeatureDefinition(name="one_time_legal_expenses", data_type=DataType.FLOAT, description="Non-recurring legal and diligence costs", domain="LEGAL"),
        FeatureDefinition(name="headcount_runrate_cost", data_type=DataType.FLOAT, description="Annualized headcount compensation spend", domain="OPERATIONAL"),
        FeatureDefinition(name="cloud_hosting_spend", data_type=DataType.FLOAT, description="Annualized AWS/GCP cloud hosting expenditure", domain="TECHNOLOGY"),
        FeatureDefinition(name="gross_margin_pct", data_type=DataType.FLOAT, description="Gross profit margin %", domain="FINANCIAL"),
        FeatureDefinition(name="revenue_cagr_3yr", data_type=DataType.FLOAT, description="3-year revenue compound annual growth rate", domain="FINANCIAL"),
    ]

    target_def = TargetDefinition(
        name="realized_ebitda_post_close_usd",
        target_type=TargetType.REGRESSION,
        description="Actual audited normalized EBITDA realized in Year 1 post-close",
        unit="USD",
    )

    metadata = DatasetMetadata(
        dataset_id="dealguard-dataset-ebitda-v1",
        version="1.0.0",
        name="Synthetic Benchmark — Post-Deal EBITDA Realization Benchmark Dataset",
        source="Synthetic Benchmark Data (Parametric Simulation for Pipeline Validation)",
        task_type="EBITDA_FORECAST",
        target_name="realized_ebitda_post_close_usd",
        row_count=n_samples,
        feature_count=len(feature_defs),
        split_method=SplitMethod.RANDOM,
        data_checksum=checksum,
        is_benchmark=True,
        is_synthetic=True,
        leakage_notes="Synthetic benchmark dataset generated with fixed PRNG seed for deterministic validation. Not real customer data.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["realized_ebitda_post_close_usd"]).to_dict(orient="records"),
        targets=df["realized_ebitda_post_close_usd"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot
