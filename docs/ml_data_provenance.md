# DealGuard AI — Real-World Machine Learning Data Provenance & Lineage Manifest

## 1. Provenance Statement & Standards

To ensure institutional credibility, legal compliance, and IEEE-grade experimental reproducibility, all empirical datasets ingested by DealGuard AI are tracked with cryptographic checksums, verified licensing, and strict anti-leakage lineage.

```
 RAW SOURCE (Open Benchmark / Academic Archive / Federal Agency)
   │
   ▼
 SHA-256 INTEGRITY VERIFICATION (Cryptographic Checksum)
   │
   ▼
 LICENSE & USAGE AUDIT (Public Domain / CC-BY / Open Data)
   │
   ▼
 TARGET DEFINITION & TIME-HORIZON ISOLATION (No Post-Event Attributes)
   │
   ▼
 AUTOMATED DATA QUALITY & LEAKAGE AUDIT (DataQualityAuditor)
   │
   ▼
 IMMUTABLE DATASET SNAPSHOT (DatasetSnapshot in ExtendedModelRegistry)
```

---

## 2. Real-World Ingested Datasets

| Dataset ID | Dataset Name | Primary Source / Organization | License | Retrieval Date | SHA-256 Checksum | Rows ($N$) | Features ($D$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dealguard-real-churn-v1` | **Telco & Enterprise SaaS Customer Churn** | IBM Developer / Kaggle Open Data | Apache 2.0 / CC0 Public Domain | 2026-08-28 | `a0ea74c48c1063be89a73ce3fb868593604c0129f2bf581934f04983d728b3b5` | 7,043 | 19 |
| `dealguard-real-credit-risk-v1` | **Statlog German Credit Risk & Default** | UCI Machine Learning Repository / Univ. of Hamburg | CC BY 4.0 | 2026-08-28 | `7e4a89f3f4fd64675a84da5fd4be8b58111455137dfe735e7e1969d9be3eb836` | 1,000 | 20 |
| `dealguard-real-downside-risk-v1` | **U.S. SBA Commercial Loan Default Dataset** | U.S. Small Business Administration / Stanford MS&E | U.S. Govt Open Data / Public Domain | 2026-08-28 | `98c8355797a55f68a9629e36cddda5992efe8dc297a771a7f4503a4f53f96a3b` | 147,423 ($10,000$ stratified sample) | 7 |
| `taiwanese-bankruptcy-v1` | **Taiwanese Corporate Bankruptcy Dataset** | Taiwan Economic Journal / UCI Machine Learning | CC BY 4.0 | 2026-08-28 | `e4b3c91d4e08c69139f4e24cf8fbf9574ef20b7ee2385b244793fdf6cbeae8e5` | 6,819 | 95 |

---

## 3. Target Suitability & Real vs. Synthetic Boundary

In strict compliance with the **DATA INTEGRITY POLICY**, DealGuard AI classifies prediction targets into three distinct scientific tiers:

```
+---------------------------------------------------------------------------------------------------------------+
| Target Domain                       | Classification Status | Ingested Dataset / Limitation Reason            |
+---------------------------------------------------------------------------------------------------------------+
| 1. Customer Churn / Retention       | REAL-DATA EMPIRICAL   | Telco & B2B Customer Churn (N=7,043)            |
| 2. Credit Risk / Downside Default   | REAL-DATA EMPIRICAL   | German Credit Risk Dataset (N=1,000)            |
| 3. Commercial Loan / M&A Risk       | REAL-DATA EMPIRICAL   | U.S. SBA Commercial Loan Dataset (N=10,000)     |
| 4. Revenue Time-Series Forecaster   | DATASET-LIMITED       | Awaiting longitudinal general ledger logs       |
| 5. Quality of Earnings Realization  | SYNTHETIC BENCHMARK   | Retained for pipeline regression test harness   |
| 6. Post-Merger Integration Blocker  | DATASET-LIMITED       | Awaiting enterprise PMO milestone & Jira logs   |
| 7. Synergy Waterfall Realization    | DATASET-LIMITED       | Awaiting post-close ERP synergy audit actuals   |
| 8. Post-Acquisition Company Health  | DATASET-LIMITED       | Awaiting continuous monthly board telemetry     |
+---------------------------------------------------------------------------------------------------------------+
```

> [!NOTE]
> **Scientific Integrity Principle**: We do **NOT** manufacture fake historical M&A outcome data. Targets without publicly accessible, high-integrity open datasets remain cataloged as `DATASET-LIMITED` specifications in `ExtendedModelRegistry` until proprietary enterprise logs are ingested under audited data processing agreements.

---

## 4. Target Variable Definitions & Leakage Mitigation

### 4.1 Target: `churn` (`dealguard-real-churn-v1`)
- **Positive Class ($y=1$)**: Customer account cancellation or non-renewal upon contract conclusion.
- **Negative Class ($y=0$)**: Customer account active and retained.
- **Leakage Prevention**: Primary customer ID key (`customerID`) is dropped immediately upon ingestion. Preprocessing scaling and imputation are computed strictly on the training partition ($70\%$).

### 4.2 Target: `default_risk` (`dealguard-real-credit-risk-v1`)
- **Positive Class ($y=1$)**: Credit applicant classified as "bad" (delinquent/default status).
- **Negative Class ($y=0$)**: Credit applicant classified as "good" (creditworthy).
- **Observation Horizon**: All 20 predictive attributes are observed exclusively at the time of credit evaluation prior to default realization.

### 4.3 Target: `loan_default` (`dealguard-real-downside-risk-v1`)
- **Positive Class ($y=1$)**: Commercial loan charge-off / liquidation (`MIS_Status == 'CHGOFF'`).
- **Negative Class ($y=0$)**: Commercial loan paid in full (`MIS_Status == 'PIF'`).
- **Leakage Prevention**: Post-event variables (`ChargeOffDate`, `GrossChargeOffAmount`) are strictly excluded from the feature space. Only underwriting terms (`TermInMonths`, `GrossApproval`, `ThirdPartyDollars`, `BusinessType`, `DeliveryMethod`, `subpgmdesc`, `ProjectState`) are utilized.
