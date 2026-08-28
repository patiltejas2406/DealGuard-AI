"""Real-World Dataset Loaders, Cleaners & Schema Adapters."""

import os
import re
from typing import Dict, List, Optional, Tuple
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
from app.domains.ml.datasets.benchmark_datasets import _compute_checksum
from app.domains.ml.datasets.manifest import get_provenance_record


DATASETS_DIR = os.path.join(os.path.dirname(__file__), "real_world")


def load_real_customer_churn_dataset(
    filepath: Optional[str] = None,
) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Load and clean the real-world Telco / Enterprise Customer Churn Dataset (IBM / Kaggle Open Data).
    7,043 observations with 19 predictors. Target: Churn (1 = Churned, 0 = Retained).
    """
    path = filepath or os.path.join(DATASETS_DIR, "telco_customer_churn.csv")
    df_raw = pd.read_csv(path)

    # 1. Clean TotalCharges (handle whitespace/blank strings)
    df = df_raw.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")
    # Impute missing TotalCharges with MonthlyCharges for brand new accounts (tenure == 0)
    df["TotalCharges"] = df["TotalCharges"].fillna(df["MonthlyCharges"])

    # 2. Encode Target 'Churn' ('Yes' -> 1, 'No' -> 0)
    df["churn"] = (df["Churn"].astype(str).str.strip() == "Yes").astype(int)

    # 3. Drop non-predictive Primary Key Identifier
    df = df.drop(columns=["customerID", "Churn"])

    # 4. Feature Definitions
    feature_defs = [
        FeatureDefinition(name="gender", data_type=DataType.CATEGORICAL, description="Customer gender (Male/Female)", domain="OPERATIONAL"),
        FeatureDefinition(name="SeniorCitizen", data_type=DataType.INT, description="Binary flag indicating whether account is senior citizen", domain="OPERATIONAL"),
        FeatureDefinition(name="Partner", data_type=DataType.CATEGORICAL, description="Whether customer has partner", domain="OPERATIONAL"),
        FeatureDefinition(name="Dependents", data_type=DataType.CATEGORICAL, description="Whether customer has dependents", domain="OPERATIONAL"),
        FeatureDefinition(name="tenure", data_type=DataType.INT, description="Number of months customer has stayed with company", domain="FINANCIAL"),
        FeatureDefinition(name="PhoneService", data_type=DataType.CATEGORICAL, description="Whether customer has phone service", domain="OPERATIONAL"),
        FeatureDefinition(name="MultipleLines", data_type=DataType.CATEGORICAL, description="Whether customer has multiple lines", domain="OPERATIONAL"),
        FeatureDefinition(name="InternetService", data_type=DataType.CATEGORICAL, description="Internet service provider type (DSL, Fiber optic, No)", domain="OPERATIONAL"),
        FeatureDefinition(name="OnlineSecurity", data_type=DataType.CATEGORICAL, description="Online security add-on status", domain="OPERATIONAL"),
        FeatureDefinition(name="OnlineBackup", data_type=DataType.CATEGORICAL, description="Online backup add-on status", domain="OPERATIONAL"),
        FeatureDefinition(name="DeviceProtection", data_type=DataType.CATEGORICAL, description="Device protection add-on status", domain="OPERATIONAL"),
        FeatureDefinition(name="TechSupport", data_type=DataType.CATEGORICAL, description="Premium technical support status", domain="OPERATIONAL"),
        FeatureDefinition(name="StreamingTV", data_type=DataType.CATEGORICAL, description="Streaming TV add-on status", domain="OPERATIONAL"),
        FeatureDefinition(name="StreamingMovies", data_type=DataType.CATEGORICAL, description="Streaming movies add-on status", domain="OPERATIONAL"),
        FeatureDefinition(name="Contract", data_type=DataType.CATEGORICAL, description="Contract term (Month-to-month, One year, Two year)", domain="LEGAL"),
        FeatureDefinition(name="PaperlessBilling", data_type=DataType.CATEGORICAL, description="Whether paperless billing is enabled", domain="OPERATIONAL"),
        FeatureDefinition(name="PaymentMethod", data_type=DataType.CATEGORICAL, description="Customer payment method", domain="FINANCIAL"),
        FeatureDefinition(name="MonthlyCharges", data_type=DataType.FLOAT, description="Monthly recurring charge amount in USD", domain="FINANCIAL"),
        FeatureDefinition(name="TotalCharges", data_type=DataType.FLOAT, description="Total cumulative charges billed in USD", domain="FINANCIAL"),
    ]

    target_def = TargetDefinition(
        name="churn",
        target_type=TargetType.BINARY_CLASSIFICATION,
        description="Whether customer terminated contract",
        class_labels=["RETAINED", "CHURNED"],
    )

    prov = get_provenance_record("dealguard-real-churn-v1")
    checksum = _compute_checksum(df)

    metadata = DatasetMetadata(
        dataset_id="dealguard-real-churn-v1",
        version="1.0.0",
        name="Real-World Customer Churn Dataset",
        source="IBM Developer / Kaggle Open Data (Apache 2.0)",
        task_type="CHURN_PREDICTION",
        target_name="churn",
        row_count=len(df),
        feature_count=len(feature_defs),
        split_method=SplitMethod.STRATIFIED,
        data_checksum=checksum,
        is_benchmark=False,
        is_synthetic=False,
        leakage_notes="Customer ID removed. Preprocessing fits solely on train fold.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["churn"]).to_dict(orient="records"),
        targets=df["churn"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot


def load_real_credit_risk_dataset(
    filepath: Optional[str] = None,
) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Load and clean the real-world German Credit Risk Dataset (UCI Machine Learning Repository).
    1,000 corporate/commercial credit instances with 20 financial predictors. Target: default_risk (1 = Bad, 0 = Good).
    """
    path = filepath or os.path.join(DATASETS_DIR, "german_credit_risk.csv")
    df_raw = pd.read_csv(path)
    df = df_raw.copy()

    # Encode target 'class' ('bad' -> 1, 'good' -> 0)
    df["default_risk"] = (df["class"].astype(str).str.lower().str.strip() == "bad").astype(int)
    df = df.drop(columns=["class"])

    feature_defs = [
        FeatureDefinition(name="checking_status", data_type=DataType.CATEGORICAL, description="Status of existing checking account balance", domain="FINANCIAL"),
        FeatureDefinition(name="duration", data_type=DataType.INT, description="Loan duration in months", domain="FINANCIAL"),
        FeatureDefinition(name="credit_history", data_type=DataType.CATEGORICAL, description="Past credit repayment history", domain="FINANCIAL"),
        FeatureDefinition(name="purpose", data_type=DataType.CATEGORICAL, description="Purpose of commercial/personal credit", domain="OPERATIONAL"),
        FeatureDefinition(name="credit_amount", data_type=DataType.FLOAT, description="Credit amount in DM / Currency units", domain="FINANCIAL"),
        FeatureDefinition(name="savings_status", data_type=DataType.CATEGORICAL, description="Savings account / bond balance", domain="FINANCIAL"),
        FeatureDefinition(name="employment", data_type=DataType.CATEGORICAL, description="Present employment / business tenure", domain="OPERATIONAL"),
        FeatureDefinition(name="installment_commitment", data_type=DataType.FLOAT, description="Installment rate in % of disposable income", domain="FINANCIAL"),
        FeatureDefinition(name="personal_status", data_type=DataType.CATEGORICAL, description="Personal / management status", domain="OPERATIONAL"),
        FeatureDefinition(name="other_parties", data_type=DataType.CATEGORICAL, description="Other debtors or commercial guarantors", domain="LEGAL"),
        FeatureDefinition(name="residence_since", data_type=DataType.INT, description="Present residence / headquarters duration", domain="OPERATIONAL"),
        FeatureDefinition(name="property_magnitude", data_type=DataType.CATEGORICAL, description="Real estate / collateral property magnitude", domain="FINANCIAL"),
        FeatureDefinition(name="age", data_type=DataType.INT, description="Age in years", domain="OPERATIONAL"),
        FeatureDefinition(name="other_payment_plans", data_type=DataType.CATEGORICAL, description="Other installment plans (bank, stores, none)", domain="FINANCIAL"),
        FeatureDefinition(name="housing", data_type=DataType.CATEGORICAL, description="Housing / property tenure (rent, own, for free)", domain="OPERATIONAL"),
        FeatureDefinition(name="existing_credits", data_type=DataType.INT, description="Number of existing credits at this bank", domain="FINANCIAL"),
        FeatureDefinition(name="job", data_type=DataType.CATEGORICAL, description="Employment skill / management tier", domain="OPERATIONAL"),
        FeatureDefinition(name="num_dependents", data_type=DataType.INT, description="Number of dependents liable for maintenance", domain="OPERATIONAL"),
        FeatureDefinition(name="own_telephone", data_type=DataType.CATEGORICAL, description="Telephone registration flag", domain="OPERATIONAL"),
        FeatureDefinition(name="foreign_worker", data_type=DataType.CATEGORICAL, description="Foreign worker flag", domain="LEGAL"),
    ]

    target_def = TargetDefinition(
        name="default_risk",
        target_type=TargetType.BINARY_CLASSIFICATION,
        description="Whether credit account defaulted / presented bad credit quality",
        class_labels=["CREDITWORTHY", "DEFAULT_RISK"],
    )

    checksum = _compute_checksum(df)

    metadata = DatasetMetadata(
        dataset_id="dealguard-real-credit-risk-v1",
        version="1.0.0",
        name="German Credit Risk & Downside Default Dataset",
        source="UCI Machine Learning Repository (CC BY 4.0)",
        task_type="RISK_PROBABILITY",
        target_name="default_risk",
        row_count=len(df),
        feature_count=len(feature_defs),
        split_method=SplitMethod.STRATIFIED,
        data_checksum=checksum,
        is_benchmark=False,
        is_synthetic=False,
        leakage_notes="All features observed at time of application before credit default outcome.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["default_risk"]).to_dict(orient="records"),
        targets=df["default_risk"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot


def load_real_commercial_loan_default_dataset(
    filepath: Optional[str] = None,
    max_samples: int = 10000,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, DatasetSnapshot]:
    """
    Load and clean the U.S. Small Business Administration (SBA) Commercial Loan Default Dataset.
    Contains real historical commercial lending outcomes. Target: loan_default (1 = Charged Off, 0 = Paid In Full).
    """
    path = filepath or os.path.join(DATASETS_DIR, "sba_loan_default.csv")
    df_raw = pd.read_csv(path, low_memory=False)

    # 1. Filter completed loans (LoanStatus in ['CHGOFF', 'PIF'])
    df = df_raw[df_raw["LoanStatus"].isin(["CHGOFF", "PIF"])].copy()

    # 2. Helper to clean currency strings
    def clean_currency(s):
        if pd.isna(s):
            return 0.0
        if isinstance(s, (int, float)):
            return float(s)
        cleaned = re.sub(r"[^\d.]", "", str(s))
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    df["GrossApproval"] = df["GrossApproval"].apply(clean_currency)
    df["ThirdPartyDollars"] = df["ThirdPartyDollars"].apply(clean_currency)

    # Clean numeric fields
    df["TermInMonths"] = pd.to_numeric(df["TermInMonths"], errors="coerce").fillna(60)

    # Encode target (CHGOFF = 1, PIF = 0)
    df["loan_default"] = (df["LoanStatus"] == "CHGOFF").astype(int)

    selected_cols = [
        "TermInMonths",
        "GrossApproval",
        "ThirdPartyDollars",
        "BusinessType",
        "DeliveryMethod",
        "subpgmdesc",
        "ProjectState",
        "loan_default",
    ]

    # Keep only available selected columns
    available_cols = [c for c in selected_cols if c in df.columns]
    df = df[available_cols].dropna(subset=["loan_default"])

    # Sample for reproducible high-speed training if dataset exceeds max_samples
    if len(df) > max_samples:
        df = df.groupby("loan_default", group_keys=False).apply(
            lambda x: x.sample(int(max_samples * len(x) / len(df)), random_state=random_state)
        ).reset_index(drop=True)

    feature_cols = [c for c in df.columns if c != "loan_default"]

    feature_defs = []
    for c in feature_cols:
        dtype = DataType.FLOAT if pd.api.types.is_numeric_dtype(df[c]) else DataType.CATEGORICAL
        feature_defs.append(FeatureDefinition(name=c, data_type=dtype, description=f"SBA commercial lending feature {c}", domain="FINANCIAL"))

    target_def = TargetDefinition(
        name="loan_default",
        target_type=TargetType.BINARY_CLASSIFICATION,
        description="Whether commercial loan experienced liquidation/charge-off",
        class_labels=["PAID_IN_FULL", "CHARGED_OFF"],
    )

    checksum = _compute_checksum(df)

    metadata = DatasetMetadata(
        dataset_id="dealguard-real-downside-risk-v1",
        version="1.0.0",
        name="U.S. SBA Commercial Loan Default Dataset",
        source="U.S. Small Business Administration (Public Domain)",
        task_type="RISK_PROBABILITY",
        target_name="loan_default",
        row_count=len(df),
        feature_count=len(feature_defs),
        split_method=SplitMethod.STRATIFIED,
        data_checksum=checksum,
        is_benchmark=False,
        is_synthetic=False,
        leakage_notes="Excludes post-charge-off recovery amounts. Only features known at underwriting time.",
    )

    snapshot = DatasetSnapshot(
        metadata=metadata,
        features=df.drop(columns=["loan_default"]).to_dict(orient="records"),
        targets=df["loan_default"].tolist(),
        feature_definitions=feature_defs,
        target_definition=target_def,
    )

    return df, snapshot
