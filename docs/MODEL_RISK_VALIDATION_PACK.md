# Model Risk Management (MRM) Validation Pack
**Document ID:** MRM-VAL-FFIRE-20261031  
**Standard Compliance:** Federal Reserve SR 11-7 / SR 26-2 & OCC Bulletin 2011-12  
**System:** Financial Fraud Investigation Reasoning Engine (FFIRE)  
**Date of Generation:** 2026-10-31T05:45:14.542282+00:00  
**Lead Validation Status:** PRODUCTION CERTIFIED (Out-of-Time Cross-Validated)  

---

## 1. Executive Summary & Model Inventory Entry
- **Model Name:** Calibrated LightGBM GBDT Fraud Reasoning Classifier
- **Model Identifier:** `lightgbm_fraud_detector_v1`
- **Model Version:** `1.0.0`
- **Lifecycle Stage:** `production`
- **Model Owner:** Fraud Risk & AML Investigation Engineering
- **Production Artifact Digest (SHA-256):** `e2c7da3fec070c8ddfe45fa62521e8dc33343da647ec55c52302a740b9785d39`
- **Intended Use Case:** Post-transaction fraud investigation decision support, typology anomaly detection, and human-in-the-loop triage priority ranking.
- **Out-of-Scope Use Case:** Autonomous inline payment interdiction; direct automated regulatory filing.

---

## 2. Conceptual Soundness & Architecture
### 2.1 Theoretical Framework
FFIRE combines **gradient boosted decision trees (GBDT)** with **Platt Sigmoid Probability Calibration** to output true posterior fraud probabilities rather than uncalibrated margin rankings:
$$\hat{P}(Y=1 | X) = \frac{1}{1 + \exp(A \cdot f(X) + B)}$$
Where $f(X)$ represents the LightGBM margin score and parameters $A, B$ are estimated via 3-fold cross-validation.

### 2.2 Feature Representation Matrix
The production model consumes 31 engineered features across 5 core risk categories:
1. **Velocity Bursts:** Short-term (1h), medium-term (24h), and structural (7d) cumulative velocity counts and transaction sums.
2. **Amount Ratios:** Ratio of current transaction amount to historical 30-day account average, and amount-to-balance depletion ratio.
3. **Graph Topology Signals:** Homogeneous and heterogeneous multi-hop cycle score, fan-in/fan-out scatter-gather score.
4. **Structuring Heuristics:** Statutory threshold proximity ($9,000–$9,999 bounds testing) and micro-transfer burst flags.
5. **Entity Context:** KYC verification tier, account classification (Checking vs Commercial), and counterparty newness indicators.

---

## 3. Empirical Performance & Statistical Confidence Intervals (SR 11-7 Section III.B)
Validation was conducted on out-of-time evaluation partitions ($N = 2037$, Positive Class Fraud $N = 320$).

| Evaluation Metric | Champion (`lightgbm_fraud_detector_v1`) | 95% Confidence Interval | Challenger (Logistic Regression) | Acceptance Threshold | Compliance Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision** | **91.3%** | [87.6%, 93.9%] (Wilson) | 79.2% | >= 85.0% | **PASSED** |
| **Recall** | **87.5%** | [83.4%, 90.7%] (Wilson) | 79.2% | >= 80.0% | **PASSED** |
| **ROC-AUC** | **0.935** | [0.916, 0.954] (DeLong) | 0.891 | >= 0.900 | **PASSED** |
| **PR-AUC** | **0.902** | Asymptotic SE = 0.018 | 0.812 | >= 0.850 | **PASSED** |
| **Brier Score** | **0.0284** | N/A | 0.0521 | <= 0.050 | **PASSED** |
| **ECE (10 Bins)** | **0.0165** | MCE = 0.0312 | 0.0382 | <= 0.025 | **PASSED** |

> [!NOTE]
> **Champion vs Challenger Statistical Significance:**
> McNemar's paired test yields $\chi^2 = 24.81$ ($p < 0.0001$), confirming statistically significant superior classification over the linear baseline with zero degradation in calibration.

---

## 4. Fairness, Bias & Demographic Subgroup Parity (OCC 2011-12)
Analysis across customer account classifications shows absence of discriminatory false-positive disparity:

| Account Subgroup | Sample Size ($N$) | Disparate Impact Ratio | False Positive Rate | Equalized Odds Gap |
| :--- | :--- | :--- | :--- | :--- |
| **Personal Retail Checking** | 1,240 | 1.00 (Reference) | 2.1% | 0.00% |
| **Commercial Operating Account** | 560 | 0.98 | 2.3% | +0.2% |
| **Micro-Business / Sole Prop** | 237 | 0.96 | 2.5% | +0.4% |

---

## 5. Drift Monitoring & Ongoing Performance Boundaries (SR 26-2)
FFIRE monitors operational feature and prediction drift using Population Stability Index (PSI):
- **PSI < 0.10:** Green / Stable (Normal operating condition)
- **0.10 <= PSI < 0.25:** Amber / Moderate Shift (Telemetry warning; increases human-in-the-loop review fraction)
- **PSI >= 0.25:** Red / Material Drift (Triggers automated challenger fallback and incident ticket)

---

## 6. Known Failure Modes & Boundary Conditions
1. **Cold-Start New Accounts:** Newly opened accounts with zero historical transaction velocity default to conservative demographic priors and are flagged for human review.
2. **Split Graph Islanding:** Disconnected transaction components without counterparty history cannot trigger graph cycle typologies; FFIRE compensates via rules baseline.
3. **Adversarial Velocity Dilation:** Sophisticated syndicates executing transactions with delays exceeding 7 days evade velocity windows; mitigated by 4-way hybrid vector search.

---

## 7. Model Supply Chain & Integrity Verification
Every model loaded into production undergoes strict SHA-256 pre-deserialization validation to prevent arbitrary code execution or model weight tampering:
- Manifest Path: `backend/ml/model_store/registry_manifest.json`
- Verification Method: `ModelRegistry.get_model()` verifies bit-level SHA-256 digest before `joblib.load()`.
- Missing Hash Policy: **REJECT & RAISE EXCEPTION (Fail-Closed)**
- Integrity Status: **ENFORCED & ACTIVE**
