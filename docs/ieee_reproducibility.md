# DealGuard AI — IEEE Experimental Reproducibility & Research Artifact

## 1. Abstract & System Specification

This document provides complete instructions and mathematical specifications for independently reproducing the empirical Machine Learning and Explainable AI (XAI) experiments conducted in **DealGuard AI**.

- **System Version**: `DealGuard AI Phase 17 (IEEE-Grade ML Subsystem)`
- **Execution Platform**: Python 3.13 / Scikit-Learn 1.6 / XGBoost 2.1 / SHAP 0.46
- **Global Random Seed**: `42` (ensuring deterministic train/val/test splits and estimator initialization)
- **Evaluation Partitioning Protocol**: $70\%$ Training / $15\%$ Validation / $15\%$ Held-out Test

---

## 2. Experimental Reproduction Protocol

To reproduce all empirical candidate benchmarks, model selections, and SHAP attributions from the CLI:

```bash
# 1. Activate environment and set PYTHONPATH
export PYTHONPATH=backend

# 2. Execute automated IEEE benchmark reproduction script
python -c "
from app.domains.ml.datasets.real_world_datasets import (
    load_real_customer_churn_dataset,
    load_real_credit_risk_dataset,
    load_real_commercial_loan_default_dataset,
)
from app.domains.ml.real_benchmarking import RealWorldBenchmarkEngine

benchmarks = [
    ('dealguard-real-churn-v1', load_real_customer_churn_dataset, 'churn'),
    ('dealguard-real-credit-risk-v1', load_real_credit_risk_dataset, 'default_risk'),
    ('dealguard-real-downside-risk-v1', load_real_commercial_loan_default_dataset, 'loan_default'),
]

for model_id, loader, target_col in benchmarks:
    df, snap = loader()
    wrapper, summary = RealWorldBenchmarkEngine.benchmark_and_train_target(
        snapshot=snap, df=df, target_column=target_col, model_id=model_id, random_state=42, perform_tuning=True
    )
    print(f'Model: {model_id} | Winner: {summary[\"winning_model\"]} | Test ROC-AUC: {summary[\"final_test_metrics\"].get(\"auc_roc\")}')
"
```

---

## 3. Master Experimental Results Table

| Target Identifier | Dataset Domain | $N$ Samples | Baseline Test AUC | Selected Algorithm | Tuned Hyperparameters | Val ROC-AUC | Test ROC-AUC | Test PR-AUC | Test Brier Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dealguard-real-churn-v1` | Enterprise / Telco Churn | 7,043 | 0.5000 | **XGBoost Classifier** | `lr=0.05, max_depth=3` | **0.8475** | **0.8390** | 0.6660 | 0.1379 |
| `dealguard-real-credit-risk-v1` | Commercial Credit Risk | 1,000 | 0.5000 | **Random Forest** | `n_est=100, max_depth=4` | **0.7881** | **0.7896** | 0.6659 | 0.1715 |
| `dealguard-real-downside-risk-v1` | U.S. SBA Commercial Loans | 9,999 | 0.5000 | **Gradient Boosting** | `lr=0.05, max_depth=4` | **0.8109** | **0.7842** | 0.3860 | 0.1155 |

---

## 4. Threats to Validity & Scientific Limitations

### 4.1 Selection & Survivorship Bias
- In private equity M&A transactions, target company financials often suffer from survivorship bias (companies undergoing distress prior to acquisition may not generate complete audited data room disclosures).
- Public credit and loan benchmarks (e.g. SBA loans and German Credit) provide realistic proxy distributions but do not account for proprietary PE deal structuring or bespoke debt covenants.

### 4.2 Class Imbalance
- Default events in commercial lending and corporate bankruptcy are inherently rare ($<18\%$). While Stratified splits and PR-AUC/Brier Score evaluation were employed to prevent metric distortion, extreme tail risk remains challenging for standard tabular estimators without continuous operational monitoring.

### 4.3 Dataset-Limited Targets
- In strict adherence to scientific integrity, targets lacking publicly verifiable open datasets (ARR time-series forecasting, PMO integration bottlenecks, and synergy realization) are marked as `DATASET-LIMITED` rather than populated with manufactured ground truth.
