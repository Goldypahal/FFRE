# Model Risk Management (MRM) Validation Pack
**Document ID:** MRM-VAL-FFIRE-20261101
**Reference Frameworks:** Federal Reserve SR 11-7 & OCC Bulletin 2011-12 (structure only; this document is not an independent validation)
**System:** Financial Fraud Investigation Reasoning Engine (FFIRE)
**Date of Generation:** 2026-11-01T13:40:16.305628+00:00
**Validation Status:** INTERNAL SYNTHETIC-DATA BENCHMARK CANDIDATE - NOT EMPIRICALLY QUALIFIED
**Evidence Source:** persisted training report (backend/ml/training_report.json)

> [!WARNING]
> **Why this status:**
> - 98.6% of the holdout was produced by the in-repo synthetic generator (`generate_synthetic_aml_stream`); the remainder is AMLSim-style simulated data.
> - No real-world transaction data is present in the evaluation partition.
> - Perfect separation (zero errors, ROC-AUC = 1.0) reflects how the synthetic generator draws fraud and benign samples from distinct feature distributions; it is not evidence of real-world discrimination performance.
> - Champion and challenger made identical classifications on every holdout case, so the paired McNemar test is uninformative and provides no evidence that the champion is superior.
> - No independent external validation on real-world data is recorded; empirical qualification cannot be claimed until one is performed.

---

## 1. Model Inventory Entry
- **Model Name:** Calibrated LightGBM GBDT Fraud Classifier
- **Model Identifier:** `lightgbm_fraud_detector_v1`
- **Model Version:** `1.0.0`
- **Lifecycle Stage (registry):** `production`
- **Production Artifact Digest (SHA-256):** `e2c7da3fec070c8ddfe45fa62521e8dc33343da647ec55c52302a740b9785d39`
- **Intended Use:** Post-transaction fraud investigation decision support and human-in-the-loop triage ranking.
- **Out-of-Scope Use:** Autonomous inline payment interdiction; automated regulatory filing.

---

## 2. Data Provenance
- **Full dataset:** provenance unavailable
- **Holdout partition:** N = 509 (amlsim_style_challenge_cases: 2, amlsim_style_held_out_cases: 5, generated_synthetic_stream: 502); generated-synthetic share = 98.6%; real-world data present = False

All current data sources are simulated: the in-repo generator draws fraud and benign samples from deliberately
different feature distributions (KYC status, risk tier, velocity, graph signals), and the remaining cases are
AMLSim-style simulated scenarios. Metrics below therefore measure how well the model recovers the generator's
rules, not real-world fraud detection performance.

---

## 3. Conceptual Soundness
FFIRE combines gradient boosted decision trees with Platt sigmoid calibration
(`CalibratedClassifierCV(method="sigmoid", cv=3)`):
$$\hat{P}(Y=1 | X) = \frac{1}{1 + \exp(A \cdot f(X) + B)}$$
The production model consumes 31 engineered features (velocity, amount ratios,
graph topology, structuring heuristics, and entity context).

---

## 4. Holdout Performance (internal, synthetic-data benchmark)
Every value below is computed from per-observation prediction arrays ($N = 509$, positives = 24,
negatives = 485). No stored or default metric values are used.

### Champion Confusion Matrix
- **TP:** 24 | **FP:** 0 | **TN:** 485 | **FN:** 0

| Metric | Champion (`lightgbm_fraud_detector_v1`) | 95% CI | Challenger (Logistic Regression) | Threshold | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision** | **100.0%** | [0.862, 1.000] Wilson, n=24 | 100.0% | >= 85.0% | MEETS THRESHOLD |
| **Recall** | **100.0%** | [0.862, 1.000] Wilson, n=24 | 100.0% | >= 80.0% | MEETS THRESHOLD |
| **ROC-AUC** | **1.000** | [1.000, 1.000] Hanley-McNeil (degenerate: zero width at a boundary estimate) | 1.000 | >= 0.9 | MEETS THRESHOLD |
| **PR-AUC** | **1.000** | [1.000, 1.000] Wald (degenerate: zero width at a boundary estimate) | 1.000 | >= 0.85 | MEETS THRESHOLD |
| **Brier Score** | **0.0001** | N/A | 0.0000 | <= 0.05 | MEETS THRESHOLD |
| **ECE (10 bins)** | **0.0038** | MCE = 0.0386 | 0.0003 | <= 0.025 | MEETS THRESHOLD |

Meeting these thresholds on this holdout is a necessary internal check, not a qualification.

### Champion vs. Challenger (paired McNemar, Edwards continuity correction)
- Champion correct / challenger wrong ($b$): **0**
- Challenger correct / champion wrong ($c$): **0**
- $\chi^2 = 0.0$, $p = 1.0000$
- **Interpretation:** Uninformative: the two models made identical classifications on every case. This is not evidence that the champion outperforms the challenger.

---

## 5. Sensitivity Analysis & Stress Testing
**Not performed.** No stress-test results are recorded in the training report. Earlier versions of this document listed stress-test figures that were not produced by any executed test; they have been removed.

---

## 6. Monitoring & Governance Controls
1. **Population Stability Index (PSI):**
   - PSI between training scores ($N=1528$) and holdout scores ($N=509$): **`0.004`** - stable (< 0.10).
   - Scope: both partitions come from one random split of the same dataset, so this checks split consistency only. It is not evidence of stability against production traffic, which requires monitoring live score distributions.
2. **Artifact Integrity:** the registry recomputes each artifact's SHA-256 and compares it with the manifest before
   loading it with joblib. This detects tampering with the artifact file; it does not make untrusted pickles safe.
3. **Audit Trail:** model scores and top feature attributions are written to the SHA-256 chained audit log.

---

## 7. Required Before Empirical Qualification
1. Independent validation on real (or contractually representative) labelled transaction data.
2. Out-of-time evaluation rather than a single random split.
3. Executed stress tests with recorded results.
4. A challenger evaluation in which the models actually disagree, so that superiority can be tested.

---
*Generated by `scripts/generate_model_validation_kit.py`. Status and every metric are derived from recorded evidence.*
