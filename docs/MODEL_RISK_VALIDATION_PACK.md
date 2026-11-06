# Model Risk Management (MRM) Validation Pack
**Document ID:** MRM-VAL-FFIRE-20261106
**Reference Frameworks:** Federal Reserve SR 11-7 & OCC Bulletin 2011-12 (structure only; this document is not an independent validation)
**System:** Financial Fraud Investigation Reasoning Engine (FFIRE)
**Date of Generation:** 2026-11-06T16:14:30.105504+00:00
**Validation Status:** INTERNAL SYNTHETIC-DATA BENCHMARK CANDIDATE - NOT EMPIRICALLY QUALIFIED
**Evidence Source:** persisted training report (backend/ml/training_report.json)

> [!WARNING]
> **Why this status:**
> - 99.6% of the holdout was produced by the in-repo synthetic generator (`generate_synthetic_aml_stream`); the remainder is AMLSim-style simulated data.
> - No real-world transaction data is present in the evaluation partition.
> - No independent external validation on real-world data is recorded; empirical qualification cannot be claimed until one is performed.

---

## 1. Model Inventory Entry
- **Model Name:** Calibrated LightGBM GBDT Fraud Classifier
- **Model Identifier:** `lightgbm_fraud_detector_v1`
- **Model Version:** `1.0.0`
- **Lifecycle Stage (registry):** `production`
- **Production Artifact Digest (SHA-256):** `785efa44d0b852e163b2762c6ae1fe490be1bc3737ab97a569a702fdca23bb66`
- **Intended Use:** Post-transaction fraud investigation decision support and human-in-the-loop triage ranking.
- **Out-of-Scope Use:** Autonomous inline payment interdiction; automated regulatory filing.

---

## 2. Data Provenance
- **Full dataset:** N = 2015 (amlsim_style_challenge_cases: 15, generated_synthetic_stream: 2000); generated-synthetic share = 99.3%; real-world data present = False
- **Holdout partition:** N = 503 (amlsim_style_challenge_cases: 2, generated_synthetic_stream: 501); generated-synthetic share = 99.6%; real-world data present = False

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
Every value below is computed from per-observation prediction arrays ($N = 503$, positives = 21,
negatives = 482). No stored or default metric values are used.

### Champion Confusion Matrix
- **TP:** 19 | **FP:** 0 | **TN:** 482 | **FN:** 2

| Metric | Champion (`lightgbm_fraud_detector_v1`) | 95% CI | Challenger (Logistic Regression) | Threshold | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Precision** | **100.0%** | [0.832, 1.000] Wilson, n=19 | 100.0% | >= 85.0% | MEETS THRESHOLD |
| **Recall** | **90.5%** | [0.711, 0.974] Wilson, n=21 | 100.0% | >= 80.0% | MEETS THRESHOLD |
| **ROC-AUC** | **1.000** | [1.000, 1.000] Hanley-McNeil (degenerate: zero width at a boundary estimate) | 1.000 | >= 0.9 | MEETS THRESHOLD |
| **PR-AUC** | **1.000** | [1.000, 1.000] Wald (degenerate: zero width at a boundary estimate) | 1.000 | >= 0.85 | MEETS THRESHOLD |
| **Brier Score** | **0.0023** | N/A | 0.0002 | <= 0.05 | MEETS THRESHOLD |
| **ECE (10 bins)** | **0.0079** | MCE = 0.7749 | 0.0031 | <= 0.025 | MEETS THRESHOLD |

Meeting these thresholds on this holdout is a necessary internal check, not a qualification.

### Held-out Scenario Battery (excluded from training)
Source: `benchmarks/third_party/datasets/amlsim_held_out_test.json`, $N = 22$ (positives = 10, negatives = 12); cases also present in training: **0**.

| Model | TP | FP | TN | FN | Precision | Recall | F1 | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Champion | 5 | 0 | 12 | 5 | 100.0% | 50.0% | 0.667 | 0.946 |
| Challenger | 9 | 4 | 8 | 1 | 69.2% | 90.0% | 0.783 | 0.942 |

These hand-built AMLSim-style scenarios carry no observed KYC, risk-tier, balance or graph-detector values, so those features are set to label-independent neutral values. Earlier versions derived them from the scenario label, which made scenario scores meaningless. With $N$ this small, the result is indicative only.

### Champion vs. Challenger (paired McNemar, Edwards continuity correction)
- Champion correct / challenger wrong ($b$): **0**
- Challenger correct / champion wrong ($c$): **2**
- $\chi^2 = 0.5$, $p = 0.4795$
- **Interpretation:** No statistically significant difference at alpha = 0.05.

---

## 5. Sensitivity Analysis & Stress Testing
**Not performed.** No stress-test results are recorded in the training report. Earlier versions of this document listed stress-test figures that were not produced by any executed test; they have been removed.

---

## 6. Monitoring & Governance Controls
1. **Population Stability Index (PSI):**
   - PSI between training scores ($N=1512$) and holdout scores ($N=503$): **`0.0226`** - stable (< 0.10).
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
