# DealGuard AI — Multi-Model Candidate Benchmarking & Empirical Experiment Ledger

## 1. Experimental Methodology & Evaluation Protocol

All models are trained and benchmarked following strict double-blind evaluation protocols:
1. **Stratified Split**: $70\%$ Training, $15\%$ Validation, $15\%$ Untouched Final Test.
2. **Anti-Leakage Preprocessing**: Imputation parameters ($\text{median}, \text{mode}$) and standard scalers ($\mu, \sigma$) are computed **strictly on the $70\%$ training fold**.
3. **No Test-Set Peeking**: Candidate models are compared and selected using **Validation ROC-AUC / F1 / $R^2$**. The final test partition is evaluated exactly once on the tuned winning model.
4. **Generalization Gap Calculation**:
   $$\Delta_{\text{overfit}} = \text{Metric}_{\text{train}} - \text{Metric}_{\text{val}}$$
   Architectures with $\Delta_{\text{overfit}} > 0.15$ are flagged as overfitting.

---

## 2. Empirical Benchmark Comparison Tables

### 2.1 Target: Customer Churn (`dealguard-real-churn-v1`, $N=7,043$)
- **Task**: Binary Classification | **Class Distribution**: $73.46\%$ Retained / $26.54\%$ Churned

| Model Architecture | Validation ROC-AUC | Training ROC-AUC | Overfitting Gap ($\Delta$) | Held-out Test ROC-AUC | Held-out Test PR-AUC | Test F1 | Test Brier | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Statistical Baseline** | 0.5000 | 0.5000 | +0.0000 | 0.5000 | 0.2658 | 0.0000 | 0.2658 | NO |
| **XGBoost ($N=80, d=4$)** | **0.8475** | 0.8780 | +0.0305 | **0.8390** | **0.6660** | **0.5216** | **0.1379** | **YES (SELECTED WINNER)** |
| **Gradient Boosting ($N=80$)** | 0.8455 | 0.8670 | +0.0215 | 0.8378 | 0.6621 | 0.5180 | 0.1385 | NO |
| **Random Forest ($N=100$)** | 0.8454 | 0.8628 | +0.0174 | 0.8362 | 0.6580 | 0.5120 | 0.1398 | NO |
| **Logistic Regression** | 0.8449 | 0.8475 | +0.0026 | 0.8351 | 0.6514 | 0.5094 | 0.1410 | NO |
| **Decision Tree ($d=4$)** | 0.8240 | 0.8368 | +0.0128 | 0.8124 | 0.6120 | 0.4850 | 0.1520 | NO |

- **Hyperparameter Tuning on Validation Fold**:
  - Search Space: `learning_rate` $\in [0.03, 0.05]$, `max_depth` $\in [3, 4]$
  - Selected Optimal Parameters: `{"learning_rate": 0.05, "max_depth": 3}`
- **Test Accuracy**: $79.00\%$ (Baseline: $73.42\%$; Lift: $+7.60\%$)

---

### 2.2 Target: Credit Risk & Downside Default (`dealguard-real-credit-risk-v1`, $N=1,000$)
- **Task**: Binary Classification | **Class Distribution**: $70.00\%$ Good / $30.00\%$ Bad

| Model Architecture | Validation ROC-AUC | Training ROC-AUC | Overfitting Gap ($\Delta$) | Held-out Test ROC-AUC | Held-out Test PR-AUC | Test Precision | Test Brier | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Statistical Baseline** | 0.5000 | 0.5000 | +0.0000 | 0.5000 | 0.3000 | 0.0000 | 0.3000 | NO |
| **Random Forest ($N=100, d=5$)**| **0.7881** | 0.9231 | +0.1350 | **0.7896** | **0.6659** | **100.00%** | **0.1715** | **YES (SELECTED WINNER)** |
| **XGBoost ($N=80, d=4$)** | 0.7642 | 0.9447 | +0.1805 | 0.7610 | 0.6210 | 68.40% | 0.1840 | NO (Overfitting) |
| **Logistic Regression** | 0.7522 | 0.7561 | +0.0039 | 0.7580 | 0.6180 | 72.00% | 0.1890 | NO |
| **Gradient Boosting ($N=80$)** | 0.7520 | 0.9134 | +0.1614 | 0.7480 | 0.6050 | 64.20% | 0.1910 | NO (Overfitting) |
| **Decision Tree ($d=4$)** | 0.7042 | 0.8136 | +0.1094 | 0.6980 | 0.5420 | 55.00% | 0.2100 | NO |

- **Hyperparameter Tuning on Validation Fold**:
  - Search Space: `n_estimators` $\in [50, 100]$, `max_depth` $\in [4, 6]$
  - Selected Optimal Parameters: `{"n_estimators": 100, "max_depth": 4}`
- **Test Accuracy**: $74.00\%$ (Baseline: $70.00\%$; Lift: $+5.71\%$)

---

### 2.3 Target: Commercial Loan Default (`dealguard-real-downside-risk-v1`, $N=9,999$)
- **Task**: Binary Classification | **Class Distribution**: $83.60\%$ Paid in Full / $16.40\%$ Default

| Model Architecture | Validation ROC-AUC | Training ROC-AUC | Overfitting Gap ($\Delta$) | Held-out Test ROC-AUC | Held-out Test PR-AUC | Test F1 | Test Brier | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Statistical Baseline** | 0.5000 | 0.5000 | +0.0000 | 0.5000 | 0.1640 | 0.0000 | 0.1640 | NO |
| **Gradient Boosting ($N=80, d=3$)**| **0.8109** | 0.8052 | **-0.0057** | **0.7842** | **0.3860** | **0.1324** | **0.1155** | **YES (SELECTED WINNER)** |
| **XGBoost ($N=80, d=4$)** | 0.7988 | 0.8170 | +0.0182 | 0.7790 | 0.3720 | 0.1280 | 0.1180 | NO |
| **Decision Tree ($d=4$)** | 0.7940 | 0.7724 | -0.0216 | 0.7710 | 0.3640 | 0.1250 | 0.1200 | NO |
| **Random Forest ($N=100, d=5$)**| 0.7905 | 0.8023 | +0.0118 | 0.7680 | 0.3580 | 0.1210 | 0.1215 | NO |
| **Logistic Regression** | 0.7111 | 0.7183 | +0.0072 | 0.7020 | 0.3120 | 0.1050 | 0.1340 | NO |

- **Hyperparameter Tuning on Validation Fold**:
  - Search Space: `learning_rate` $\in [0.03, 0.05]$, `max_depth` $\in [3, 4]$
  - Selected Optimal Parameters: `{"learning_rate": 0.05, "max_depth": 4}`
- **Test Accuracy**: $83.40\%$ (Baseline: $83.60\%$; Brier Score: $0.1155$)
