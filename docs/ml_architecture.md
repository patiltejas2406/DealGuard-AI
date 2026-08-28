# DealGuard AI — Real Machine Learning & Predictive Intelligence Architecture

## 1. Executive Summary & Foundational Principles

DealGuard AI incorporates an institutional-grade **Machine Learning & Explainable AI (XAI)** subsystem designed for M&A deal diligence and post-acquisition enterprise monitoring.

```
 SYNTHETIC BENCHMARK DATA / PRODUCTION TELEMETRY
   │
   ▼
 DATA VALIDATION & DATA CONTRACTS (DatasetMetadata, is_synthetic=True)
   │
   ▼
 LEAKAGE-PROOF FEATURE ENGINEERING (TabularPreprocessor)
   │
   ▼
 REPRODUCIBLE PARTITION (Train 70% / Val 15% / Test 15%)
   │
   ▼
 STATISTICAL BASELINES (Dummy Mean / Most Frequent)
   │
   ▼
 CANDIDATE MODEL TRAINING (Ridge, Logistic, DecisionTree, RandomForest, GradientBoosting, XGBoost)
   │
   ▼
 VALIDATION SELECTION & TEST EVALUATION (Lift Over Baseline)
   │
   ▼
 MODEL REGISTRY & LIFECYCLE (Versioned Trained Wrappers)
   │
   ▼
 PREDICTION SERVICE & UNCERTAINTY ESTIMATION
   │
   ▼
 REAL SHAP / XAI ATTRBUTION ENGINE (TreeSHAP / LinearSHAP)
   │
   ▼
 SPECIALIST AGENTS & DEAL DECISION SYNTHESIS
```

---

## 2. Cardinal Technical Boundaries & Data Transparency

To preserve technical integrity, academic rigor, and institutional credibility:

### 2.1 The Authoritative Boundary
> [!IMPORTANT]
> **DealGuard deterministic financial engines remain authoritative for all financial arithmetic.**
> Large Language Models (LLMs) and Machine Learning (ML) models are **NEVER** used to calculate historical revenue, normalized EBITDA, debt balances, WACC rates, DCF enterprise values, or contract VaR. Those figures are computed deterministically by audited domain engines.

### 2.2 Synthetic Benchmark Data vs. Real Historical Training Data
> [!NOTE]
> **DATA TRANSPARENCY NOTICE**:
> Initial benchmark datasets generated in `backend/app/domains/ml/datasets/benchmark_datasets.py` are **Synthetic Benchmark Datasets** generated using seeded PRNG parametric distributions.
> - **Purpose**: Used strictly for deterministic machine learning pipeline verification, anti-leakage testing, model selection validation, and end-to-end API/Agent integration testing.
> - **Boundary**: We do **NOT** claim real-world empirical predictive validity on live private equity M&A transactions from synthetic benchmark performance. Real-world predictive validity requires enterprise historical general ledger, CRM, and PMO telemetry datasets.

### 2.3 Conceptual Distinctions

| Concept | Architectural Role | Authority |
| :--- | :--- | :--- |
| **Deterministic Engine** | Exact financial math, 17-pillar risk rules, contract VaR, synergy waterfall | **Authoritative & Exact** |
| **Machine Learning (ML)** | Empirical statistical learning, candidate model selection, probabilistic forecasting | **Probabilistic Estimate** |
| **Large Language Model (LLM)** | Multi-domain reasoning, grounded narrative synthesis, intent routing | **Reasoning & Explanation** |
| **RAG (Retrieval-Augmented Gen)** | Vector search, exact quote retrieval from Data Room documents | **Evidence Grounding** |
| **Specialist Agent** | Autonomous workflow supervisor that queries deterministic tools, ML models, and RAG | **Workflow Orchestrator** |

---

## 3. Measured Benchmark Comparison & Model Selection

All candidate models are evaluated across identical training ($70\%$), validation ($15\%$), and held-out test splits ($15\%$) with anti-leakage preprocessing. The model with the highest validation performance is dynamically selected, stored in the registry, and evaluated on the held-out test split.

### 3.1 Candidate Model Comparison Table

```
+-------------------------------+--------------------------+-------------+-------------+--------------+-----------------+---------------------------+
| Target Name                   | Model Architecture       | Val Metric  | Test Metric | Train Metric | Overfitting Gap | Selection Status          |
+-------------------------------+--------------------------+-------------+-------------+--------------+-----------------+---------------------------+
| dealguard-customer-churn-v1   | Baseline (Most Frequent) | AUC: 0.5000 | AUC: 0.5000 | AUC: 0.5000  | +0.0000         | NO                        |
|                               | Logistic Regression      | AUC: 0.7776 | AUC: 0.7405 | AUC: 0.7960  | +0.0184         | YES (SELECTED WINNER)     |
|                               | Decision Tree            | AUC: 0.5886 | AUC: 0.6416 | AUC: 0.8685  | +0.2799         | NO (Overfitting)          |
|                               | Random Forest            | AUC: 0.6768 | AUC: 0.7413 | AUC: 0.9570  | +0.2802         | NO (Overfitting)          |
|                               | Gradient Boosting        | AUC: 0.5967 | AUC: 0.7187 | AUC: 0.9716  | +0.3749         | NO (Overfitting)          |
|                               | XGBoost                  | AUC: 0.6553 | AUC: 0.7083 | AUC: 0.9740  | +0.3187         | NO (Overfitting)          |
+-------------------------------+--------------------------+-------------+-------------+--------------+-----------------+---------------------------+
| dealguard-risk-probability-v1 | Baseline (Most Frequent) | AUC: 0.5000 | AUC: 0.5000 | AUC: 0.5000  | +0.0000         | NO                        |
|                               | Logistic Regression      | AUC: 0.7415 | AUC: 0.6296 | AUC: 0.7403  | -0.0012         | YES (SELECTED WINNER)     |
|                               | Decision Tree            | AUC: 0.6831 | AUC: 0.5480 | AUC: 0.8213  | +0.1382         | NO                        |
|                               | Random Forest            | AUC: 0.6877 | AUC: 0.7306 | AUC: 0.9925  | +0.3048         | NO                        |
|                               | Gradient Boosting        | AUC: 0.6815 | AUC: 0.6178 | AUC: 0.9914  | +0.3099         | NO                        |
|                               | XGBoost                  | AUC: 0.6938 | AUC: 0.7340 | AUC: 0.9972  | +0.3034         | NO                        |
+-------------------------------+--------------------------+-------------+-------------+--------------+-----------------+---------------------------+
| dealguard-ebitda-qoe-v1       | Baseline (Mean)          | R²: -0.0073 | R²: -0.0117 | R²: 0.0000   | +0.0073         | NO                        |
|                               | Ridge Regression         | R²: 0.9891  | R²: 0.9830  | R²: 0.9853   | -0.0038         | YES (SELECTED WINNER)     |
|                               | Decision Tree            | R²: 0.9743  | R²: 0.9668  | R²: 0.9743   | +0.0000         | NO                        |
|                               | Random Forest            | R²: 0.9888  | R²: 0.9839  | R²: 0.9926   | +0.0038         | NO                        |
|                               | Gradient Boosting        | R²: 0.9889  | R²: 0.9872  | R²: 0.9943   | +0.0054         | NO                        |
|                               | XGBoost                  | R²: 0.9880  | R²: 0.9875  | R²: 0.9965   | +0.0085         | NO                        |
+-------------------------------+--------------------------+-------------+-------------+--------------+-----------------+---------------------------+
```

---

## 4. Leakage-Proof Tabular Preprocessing

`TabularPreprocessor` enforces strict statistical boundaries:
- **Anti-Leakage Guarantee**: Imputation statistics (median/mode) and standard scaling parameters ($\mu, \sigma$) are computed **strictly on the training fold** (`fit`).
- Validation, test, and live inference records are transformed using the saved training parameters (`transform`).
- Feature definitions (`FeatureDefinition`) enforce canonical ordering, allowed categories, and boundary constraints.

---

## 5. Real Explainable AI (XAI) & TreeSHAP / LinearSHAP Engine

DealGuard AI generates exact, mathematically grounded explainability for every inference from the actual winning estimator:
- **`shap.TreeExplainer`**: Computes exact Shapley attribution values ($\phi_i$) for tree models (Decision Tree, Random Forest, Gradient Boosting, XGBoost).
- **`shap.LinearExplainer`**: Computes exact linear attributions for linear and ridge models (`LogisticRegression`, `Ridge`).
- **Directional Categorization**:
  - **Positive Contributors ($\phi_i > 0$)**: Features driving probability higher or expanding predicted value.
  - **Negative Contributors ($\phi_i < 0$)**: Mitigating features lowering probability or compressing predicted value.
- **Synthesized Narrative**: Natural-language explanation generated directly from the top SHAP features without LLM hallucination.

---

## 6. Integration with Specialist Agents & Deal Decision

1. **`RiskIntelligenceAgent`**:
   - Invokes `dealguard-risk-probability-v1` and `dealguard-customer-churn-v1` alongside 17-pillar matrix queries.
   - Injects ML probability into assessment references: `ml_downside_risk_probability`.
2. **`FinanceIntelligenceAgent`**:
   - Invokes `dealguard-ebitda-qoe-v1` to cross-reference reported QoE bridges against empirical realization rates.
3. **`DealDecisionAgent`**:
   - Considers ML probabilities as supplemental evidence.
   - Distinctly highlights:
     - `[DETERMINISTIC FACT]`: Decision Score = 78.4 / 100.
     - `[ML PREDICTION]`: Downside Risk Probability = 22.4% (Confidence: 94.2%).
     - `[GROUNDED CITATION]`: Data Room contract section 4.2.

---

## 7. REST API Reference

| Method | Endpoint | Description | Required Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ml/models` | List all registered model architectures and status | `deals:read` |
| `GET` | `/api/v1/ml/models/{model_id}` | Get model architecture metadata and features | `deals:read` |
| `GET` | `/api/v1/ml/models/{model_id}/metrics` | Get evaluation metrics and statistical baseline comparison | `deals:read` |
| `GET` | `/api/v1/ml/training-runs` | List historical reproducible training runs | `deals:read` |
| `GET` | `/api/v1/ml/predictions/{prediction_id}` | Retrieve persisted inference record with exact SHAP explanations | `deals:read` |
| `POST` | `/api/v1/deals/{deal_id}/ml/predict` | Execute ML prediction on a deal workspace with automatic feature extraction | `analysis:run` |

---

## 8. Database Schema & Migration (Revision `017`)

- **`ml_datasets`**: Immutable training/benchmark datasets with SHA256 checksums, row counts, split metadata, and `is_synthetic` flag.
- **`ml_training_runs`**: Audit trail of training executions, parameter payloads, metrics, and durations.
- **`ml_models`**: Catalog of active models with framework, task type, and evaluation metrics.
- **`ml_predictions`**: Tenant-scoped inference records storing feature snapshots, probability distributions, uncertainty intervals, and SHAP payloads.
