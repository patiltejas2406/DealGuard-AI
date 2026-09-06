# DealGuard AI — IEEE-Grade Research ML Benchmark Report (v1.0.0)

**Publication Target**: IEEE Transactions on Knowledge and Data Engineering / IEEE Conference on Artificial Intelligence  
**Experiment Run ID**: `bm-dealguard-ieee-v1`  
**Git Commit Hash**: `c05b598d999c243dcf24aa9460cd777f3b7dc855`  
**Evaluation Standard**: Zero-Leakage Stratified 5-Fold Cross-Validation with Single-Pass Untouched Held-Out Test Set (80% Train / 20% Test)

---

## 1. Environment & Reproducibility Manifest

| Parameter | Recorded Value |
| :--- | :--- |
| **Python Version** | 3.13.15 (macOS ARM64 / Darwin) |
| **Scikit-Learn** | 1.5.2 |
| **XGBoost** | 2.1.4 |
| **SHAP** | 0.47.2 |
| **SciPy** | 1.18.0 |
| **NumPy** | 2.2.3 |
| **Pandas** | 2.2.3 |
| **Master Random Seed** | `42` |
| **Excluded Candidates** | **LightGBM & CatBoost**: Excluded due to lack of precompiled native wheels in Python 3.13 macOS ARM64 environment. `HistGradientBoostingClassifier` and `XGBClassifier` were evaluated to provide identical histogram-based tree boosting coverage. |

---

## 2. Dataset Provenance & Data Validation

### A. Telco / Enterprise Customer Churn
- **Dataset ID**: `dealguard-real-churn-v1`
- **Source / Provenance**: IBM Developer / Kaggle Open Data (Apache 2.0 / CC0)
- **SHA-256 Checksum**: `733ebe4499b5274052012d5115a8cb190b437b85ec04d0d98e809c7efbe83f7b`
- **Total Sample Count**: 7,043 observations (5,634 Train / 1,409 Test)
- **Feature Count**: 19 predictors (3 Financial, 1 Legal, 15 Operational)
- **Target Variable**: `churn` (1 = Churned, 0 = Retained)
- **Class Distribution**: 5,174 Retained (73.46%), 1,869 Churned (26.54%)
- **Missing Value Handling**: Whitespace in `TotalCharges` imputed with `MonthlyCharges` for tenure=0; non-predictive `customerID` dropped.
- **Leakage Controls**: Customer ID dropped. Preprocessor fitted strictly inside CV training folds.

### B. German Commercial Credit Risk & Downside Default
- **Dataset ID**: `dealguard-real-credit-risk-v1`
- **Source / Provenance**: UCI Machine Learning Repository / Prof. Hofmann, University of Hamburg (CC BY 4.0)
- **SHA-256 Checksum**: `910066d49f2579fbe0364eea6a7cd47dbd26da63d20efaf6535e50ba8ef44d0b`
- **Total Sample Count**: 1,000 observations (800 Train / 200 Test)
- **Feature Count**: 20 predictors (9 Financial, 2 Legal, 9 Operational)
- **Target Variable**: `default_risk` (1 = Bad / Delinquent, 0 = Good / Creditworthy)
- **Class Distribution**: 700 Good (70.0%), 300 Bad (30.0%)
- **Missing Value Handling**: Zero missing values across all 20 predictors.
- **Leakage Controls**: Pre-decision application attributes only. No post-default liquidation metrics included.

### C. U.S. SBA Commercial Loan Default
- **Dataset ID**: `dealguard-real-downside-risk-v1`
- **Source / Provenance**: U.S. Small Business Administration / Prof. Min Li, Journal of Financial Education (Public Domain)
- **SHA-256 Checksum**: `6040ff0419a0b1901c495a15abf03a9c7336d3bf986e0ee871b1d256d83c3c52`
- **Total Sample Count**: 2,500 stratified sample of completed commercial loans (2,000 Train / 500 Test)
- **Feature Count**: 7 predictors (`TermInMonths`, `GrossApproval`, `ThirdPartyDollars`, `BusinessType`, `DeliveryMethod`, `subpgmdesc`, `ProjectState`)
- **Target Variable**: `loan_default` (1 = Charged Off / CHGOFF, 0 = Paid in Full / PIF)
- **Class Distribution**: 2,091 Paid in Full (83.6%), 409 Charged Off (16.4%)
- **Missing Value Handling**: Cleaned currency strings, imputed missing terms with median (60 months).
- **Leakage Controls**: Excludes post-default charge-off balance and recovery amounts; only features observable at underwriting.

---

## 3. Leakage-Proof Cross-Validation Protocol

```
RAW REAL DATA
      │
      ▼
DATA QUALITY AUDIT & LEAKAGE SCREENING
      │
      ▼
STRATIFIED TRAIN/TEST PARTITION (80% Train / 20% Held-Out Test)
      │
      ├───[ 80% TRAINING SET ] (Untouched Test set sealed)
      │          │
      │          ▼
      │    STRATIFIED 5-FOLD CV
      │    For Fold k in 1..5:
      │      - Fit Preprocessor ONLY on 4/5 Fold Train
      │      - Transform Fold Train & Fold Val
      │      - Train Candidate Models
      │      - Measure Out-of-Fold Metrics (ROC-AUC, PR-AUC, F1, Balanced Acc, Brier, Log Loss)
      │          │
      │          ▼
      │    AGGREGATE CV METRICS (Mean ± Std Dev)
      │          │
      │          ▼
      │    OBJECTIVE SELECTION POLICY
      │    (Primary: Mean ROC-AUC, Secondary: Lowest Brier Score & Variance, 1-SE Parsimony)
      │          │
      │          ▼
      │    FIT PREPROCESSOR & WINNER ON FULL 80% TRAIN
      │          │
      │          ▼
      │    PROBABILITY CALIBRATION BENCHMARK (Platt Sigmoid vs. Isotonic)
      │
      └───[ 20% UNTOUCHED TEST SET ]
                 │
                 ▼
      SINGLE-PASS EVALUATION OF FROZEN, CALIBRATED PIPELINE
                 │
                 ▼
      FINAL IEEE TEST METRICS + CONFUSION MATRIX + CALIBRATION CURVE + SHAP
```

---

## 4. Multi-Model Benchmark Comparison Tables (Stratified 5-Fold CV)

### A. Customer Churn Prediction (`dealguard-real-churn-v1`)

| Candidate Algorithm | ROC-AUC (Mean ± Std) | PR-AUC (Mean ± Std) | F1-Score (Mean ± Std) | Balanced Acc (Mean ± Std) | Brier Score (Mean ± Std) | Log Loss (Mean ± Std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GradientBoosting (Winner)** | **0.8487 ± 0.0114** | **0.6677 ± 0.0215** | **0.5719 ± 0.0289** | **0.7049 ± 0.0172** | **0.1344 ± 0.0046** | **0.4152 ± 0.0106** |
| HistGradientBoosting | 0.8485 ± 0.0098 | 0.6691 ± 0.0201 | 0.5776 ± 0.0215 | 0.7088 ± 0.0125 | 0.1340 ± 0.0039 | 0.4137 ± 0.0092 |
| XGBoost | 0.8483 ± 0.0115 | 0.6652 ± 0.0221 | 0.5675 ± 0.0288 | 0.7024 ± 0.0171 | 0.1346 ± 0.0047 | 0.4156 ± 0.0108 |
| LogisticRegression | 0.8447 ± 0.0118 | 0.6604 ± 0.0232 | 0.5941 ± 0.0241 | 0.7186 ± 0.0150 | 0.1357 ± 0.0047 | 0.4179 ± 0.0113 |
| RandomForest | 0.8447 ± 0.0085 | 0.6593 ± 0.0211 | 0.5304 ± 0.0261 | 0.6788 ± 0.0142 | 0.1371 ± 0.0035 | 0.4227 ± 0.0088 |
| ExtraTrees | 0.8404 ± 0.0095 | 0.6466 ± 0.0198 | 0.4938 ± 0.0244 | 0.6582 ± 0.0131 | 0.1415 ± 0.0036 | 0.4354 ± 0.0092 |

*Empirical Selection*: **GradientBoosting** achieved the highest mean CV ROC-AUC ($0.8487$). XGBoost was empirically outperformed.

---

### B. Commercial Credit Risk (`dealguard-real-credit-risk-v1`)

| Candidate Algorithm | ROC-AUC (Mean ± Std) | PR-AUC (Mean ± Std) | F1-Score (Mean ± Std) | Balanced Acc (Mean ± Std) | Brier Score (Mean ± Std) | Log Loss (Mean ± Std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RandomForest (Winner)** | **0.7718 ± 0.0412** | **0.5939 ± 0.0605** | **0.2454 ± 0.0533** | **0.5607 ± 0.0200** | **0.1743 ± 0.0085** | **0.5227 ± 0.0200** |
| HistGradientBoosting | 0.7686 ± 0.0478 | 0.5863 ± 0.0651 | 0.4910 ± 0.0385 | 0.6667 ± 0.0255 | 0.1715 ± 0.0121 | 0.5186 ± 0.0310 |
| XGBoost | 0.7682 ± 0.0471 | 0.5777 ± 0.0664 | 0.4525 ± 0.0412 | 0.6458 ± 0.0270 | 0.1717 ± 0.0118 | 0.5189 ± 0.0298 |
| GradientBoosting | 0.7654 ± 0.0399 | 0.5718 ± 0.0588 | 0.4483 ± 0.0461 | 0.6440 ± 0.0298 | 0.1735 ± 0.0095 | 0.5223 ± 0.0255 |
| ExtraTrees | 0.7649 ± 0.0513 | 0.5790 ± 0.0672 | 0.0918 ± 0.0321 | 0.5208 ± 0.0112 | 0.1815 ± 0.0092 | 0.5432 ± 0.0221 |
| LogisticRegression | 0.7249 ± 0.0271 | 0.5449 ± 0.0488 | 0.4015 ± 0.0411 | 0.6190 ± 0.0245 | 0.1833 ± 0.0078 | 0.5441 ± 0.0195 |
| SVM (Linear) | 0.7141 ± 0.0221 | 0.5321 ± 0.0412 | 0.3240 ± 0.0385 | 0.5857 ± 0.0211 | 0.1842 ± 0.0069 | 0.5489 ± 0.0175 |

*Empirical Selection*: **RandomForest** achieved the highest mean CV ROC-AUC ($0.7718$), outperforming all boosting candidates and linear baselines.

---

### C. U.S. SBA Commercial Loan Default (`dealguard-real-downside-risk-v1`)

| Candidate Algorithm | ROC-AUC (Mean ± Std) | PR-AUC (Mean ± Std) | F1-Score (Mean ± Std) | Balanced Acc (Mean ± Std) | Brier Score (Mean ± Std) | Log Loss (Mean ± Std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost (Winner)** | **0.7672 ± 0.0163** | **0.3681 ± 0.0338** | **0.0973 ± 0.0331** | **0.5177 ± 0.0079** | **0.1175 ± 0.0031** | **0.3782 ± 0.0080** |
| RandomForest | 0.7670 ± 0.0100 | 0.3953 ± 0.0312 | 0.0852 ± 0.0288 | 0.5159 ± 0.0068 | 0.1160 ± 0.0028 | 0.3765 ± 0.0075 |
| HistGradientBoosting | 0.7655 ± 0.0153 | 0.3833 ± 0.0345 | 0.1898 ± 0.0351 | 0.5375 ± 0.0112 | 0.1174 ± 0.0032 | 0.3780 ± 0.0082 |
| GradientBoosting | 0.7596 ± 0.0149 | 0.3645 ± 0.0321 | 0.1305 ± 0.0315 | 0.5255 ± 0.0098 | 0.1188 ± 0.0030 | 0.3812 ± 0.0079 |
| ExtraTrees | 0.7301 ± 0.0131 | 0.3547 ± 0.0298 | 0.0120 ± 0.0085 | 0.5024 ± 0.0021 | 0.1253 ± 0.0025 | 0.4012 ± 0.0065 |
| LogisticRegression | 0.7119 ± 0.0170 | 0.3645 ± 0.0311 | 0.1134 ± 0.0295 | 0.5198 ± 0.0088 | 0.1254 ± 0.0035 | 0.4019 ± 0.0085 |
| SVM (Linear) | 0.7113 ± 0.0214 | 0.3549 ± 0.0340 | 0.0000 ± 0.0000 | 0.5000 ± 0.0000 | 0.1287 ± 0.0041 | 0.4105 ± 0.0098 |

*Empirical Selection*: **XGBoost** won marginally on ROC-AUC ($0.7672$), followed very closely by RandomForest ($0.7670$) and HistGradientBoosting ($0.7655$).

---

## 5. Probability Calibration Results

Calibration was benchmarked strictly inside the 80% training set across Platt Sigmoid Scaling and Isotonic Regression against uncalibrated probability predictions:

| Dataset | Uncalibrated Brier | Sigmoid Brier | Isotonic Brier | Selected Method | Brier Improvement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Telco Customer Churn** | 0.1350 | 0.1269 | **0.1256** | **ISOTONIC** | **+6.96%** |
| **German Credit Risk** | 0.1763 | 0.1225 | **0.1166** | **ISOTONIC** | **+33.86%** |
| **SBA Loan Default** | 0.1165 | **0.1060** | 0.1072 | **PLATT_SIGMOID** | **+9.01%** |

*Key Finding*: Probability calibration substantially reduced probability error across all three domains, with Isotonic calibration cutting credit risk Brier loss by **33.86%**.

---

## 6. Single-Pass Untouched Test Set Evaluation

Evaluated strictly once on the frozen, held-out 20% test split:

| Task / Dataset | Selected Model | Test ROC-AUC | Test PR-AUC | Test F1 | Test Balanced Acc | Test Brier Score | Test Log Loss | Confusion Matrix (TN / FP / FN / TP) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Customer Churn** | GradientBoosting (Isotonic) | **0.8445** | 0.6511 | 0.5921 | 0.7176 | 0.1360 | 0.4183 | TN: 943, FP: 92, FN: 178, TP: 196 |
| **Credit Risk** | RandomForest (Isotonic) | **0.7916** | 0.6142 | 0.5688 | 0.6940 | 0.1632 | 0.4957 | TN: 122, FP: 18, FN: 29, TP: 31 |
| **Downside Risk** | XGBoost (Sigmoid) | **0.7917** | 0.3974 | 0.0879 | 0.5184 | 0.1163 | 0.3738 | TN: 413, FP: 5, FN: 78, TP: 4 |

---

## 7. Confidence Architecture Audit & Resolution

### Exact Code Path of Previous "39% Confidence"
1. **Origin Location**: `calculate_composite_decision_score()` in `backend/app/domains/decision/engine.py` (lines 482-490) and `DecisionAgent` in `backend/app/domains/agents/decision_agent.py` (lines 139, 229).
2. **Formula**: $\text{Total Confidence} = \sum_{i=1}^6 w_i \times c_i$.
3. **Inputs**:
   - `FINANCIAL_HEALTH` ($w=0.25$): fallback confidence = $0.20$ (product: $0.050$)
   - `VALUATION_ATTRACTIVENESS` ($w=0.20$): fallback confidence = $0.25$ (product: $0.050$)
   - `RISK_EXPOSURE` ($w=0.25$): fallback confidence = $0.50$ (product: $0.125$)
   - `REVENUE_QUALITY` ($w=0.10$): fallback confidence = $0.50$ (product: $0.050$)
   - `EVIDENCE_CONFIDENCE` ($w=0.10$): fallback confidence = $0.30 - 0.40$ (product: $0.030 - 0.040$)
   - `DEAL_COMPLEXITY` ($w=0.10$): fallback confidence = $0.88$ (product: $0.088$)
   - **Sum**: $0.050 + 0.050 + 0.125 + 0.050 + 0.030 + 0.088 = 0.393 \approx 39\%$.
4. **Findings**:
   - NOT derived from ML probabilities.
   - NOT derived from LLMs.
   - It was an ad-hoc heuristic conflating data completeness with decision certainty.

### Four-Pillar Uncertainty Architecture Implementation
The system now explicitly distinguishes four orthogonal dimensions:
1. **Model Performance**: Held-out test ROC-AUC ($0.79 - 0.84$) and Brier scores.
2. **Prediction Probability**: Calibrated posterior probability $P(Y=1|X) \in [0, 1]$ via Platt scaling and Isotonic regression.
3. **Evidence Coverage**: Verifiable data room completeness ratio across the 6 diligence pillars.
4. **Decision Confidence**: Statistically principled governance metric. If evidence coverage is $< 0.45$ or zero documents/financials exist, the system outputs `INSUFFICIENT_EVIDENCE` rather than a manufactured score.
