# DealGuard AI — Model Selection & Explainable AI (XAI) Architecture

## 1. Model Selection Criteria & Decision Policy

DealGuard AI strictly adheres to an empirical model selection policy that balances **Validation Discriminative Power (ROC-AUC / PR-AUC)**, **Generalization Stability (Overfitting Gap $\le 0.15$)**, and **Model Parsimony**:

```
           ┌───────────────────────────────────────┐
           │      Candidate Model Benchmarking     │
           │  (Dummy, Logistic, DT, RF, GBDT, XGB) │
           └──────────────────┬────────────────────┘
                              │
                              ▼
           ┌───────────────────────────────────────┐
           │        Validation Performance         │
           │   Rank by Val ROC-AUC / F1 / PR-AUC   │
           └──────────────────┬────────────────────┘
                              │
                              ▼
           ┌───────────────────────────────────────┐
           │        Overfitting Gap Audit          │
           │  Is (Train Metric - Val Metric) ≤ 0.15?│
           └──────────┬─────────────────┬──────────┘
                     YES                NO
                      │                  │
                      ▼                  ▼
           ┌─────────────────────┐  ┌─────────────────────┐
           │  Select Top Validated│  │ Penalize Overfitting│
           │      Architecture   │  │   & Fallback to Top │
           │                     │  │  Regularized Model   │
           └──────────┬──────────┘  └─────────────────────┘
                      │
                      ▼
           ┌───────────────────────────────────────┐
           │   Hyperparameter Tuning on Train/Val  │
           │   (GridSearchCV / Cross-Validation)   │
           └──────────────────┬────────────────────┘
                              │
                              ▼
           ┌───────────────────────────────────────┐
           │   Single Final Test Split Evaluation  │
           │   (Untouched 15% Held-Out Split)      │
           └──────────────────┬────────────────────┘
                              │
                              ▼
           ┌───────────────────────────────────────┐
           │   Real SHAP Explainability Engine     │
           │      (TreeSHAP / LinearSHAP)          │
           └───────────────────────────────────────┘
```

---

## 2. Why Different Estimators Won Across Domains

| Target Name | Selected Winning Model | Key Rationale & Empirical Justification |
| :--- | :--- | :--- |
| `dealguard-real-churn-v1` | **XGBoost Classifier** | Demonstrated highest validation AUC ($0.8475$) with minimal overfitting gap ($+0.0305$) and strong non-linear split handling on contract duration and monthly charges. |
| `dealguard-real-credit-risk-v1` | **Random Forest Classifier** | Achieved superior validation generalization ($0.7881$) while complex boosting algorithms (XGBoost / Gradient Boosting) exhibited significant overfitting ($\Delta > 0.16$) due to the smaller sample size ($N=1,000$). |
| `dealguard-real-downside-risk-v1` | **Gradient Boosting Classifier** | Optimal bias-variance balance ($\text{Val AUC} = 0.8109$, $\Delta = -0.0057$) across commercial loan attributes (term length, loan size, and business type) with zero overfitting. |
| `dealguard-customer-churn-v1` (Synth) | **Logistic Regression** | Selected on synthetic benchmark dataset for high parsimony and zero generalization gap. |
| `dealguard-ebitda-qoe-v1` (Synth) | **Ridge Regression** | Outperformed tree ensembles on linear EBITDA bridge arithmetic ($R^2 = 0.9830$). |

---

## 3. Mathematical Explainability & SHAP Attribution

DealGuard AI generates exact Shapley additive explanations ($\phi_i$) for every inference via `XAIEngine`:

$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$

Where:
- $\phi_0$ is the expected baseline model prediction over the training background distribution.
- $\phi_i(x)$ is the exact marginal attribution of feature $i$ to the prediction outcome.

### 3.1 Explainability Engine Dispatch
- **Tree Architectures (Random Forest / Gradient Boosting / XGBoost)**: Computed via `shap.TreeExplainer` utilizing tree path conditional expectations.
- **Linear Architectures (Logistic Regression / Ridge)**: Computed via `shap.LinearExplainer` leveraging the training covariance structure.

### 3.2 Attribution Directionality
- **Positive Contributors ($\phi_i > 0$)**: Factors elevating churn probability or loan default risk.
- **Negative Contributors ($\phi_i < 0$)**: Mitigating credit strengths or customer retention factors compressing downside risk.
