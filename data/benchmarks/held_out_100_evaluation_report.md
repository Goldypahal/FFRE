# FFRE Held-Out 100-Case Statistical Decision Evaluation Report

**Evaluation Type**: Independent Held-Out Corpus
**Sample Size**: 100 cases across 6 archetypes
**Date**: November 2026 (Updated with dynamic threshold evaluation)

### Overall Benchmark Status: **FAIL** (6/10 Targets Met)

> [!WARNING]
> **Credibility Notice**: Earlier iterations hard-coded "PASS" across all rows. Dynamic evaluation against `configs/targets.yaml` confirms 4 target violations requiring optimization.

## 1. Confusion Matrix

| | Predicted Fraud | Predicted Legitimate |
|---|:---:|:---:|
| **Actual Fraud** | **TP = 50** | **FN = 5** |
| **Actual Legitimate** | **FP = 8** | **TN = 37** |

## 2. Statistical Metrics & 95% Confidence Intervals

| Metric | Point Estimate | 95% Confidence Interval (Wilson Score) | Configured Target | Benchmark Status |
|---|:---:|:---:|:---:|:---:|
| **Accuracy** | 87.00% | [79.02%, 92.24%] | >= 85.0% target | **PASS** |
| **Precision** | 86.21% | [75.07%, 92.84%] | >= 85.0% target | **PASS** |
| **Recall (Sensitivity)** | 90.91% | [80.42%, 96.05%] | >= 90.0% target | **PASS** |
| **Specificity** | 82.22% | N/A | >= 80.0% target | **PASS** |
| **F1 Score** | 0.8850 | N/A | >= 0.85 target | **PASS** |
| **False-Positive Rate** | 17.78% | N/A | < 5.0% target | **FAIL** |
| **False-Negative Rate** | 9.09% | N/A | < 2.0% target | **FAIL** |
| **Brier Calibration Score** | 0.1589 | N/A | < 0.10 target | **FAIL** |
| **Evidence Grounding** | 100.0% | N/A | 100% target | **PASS** |
| **KYC Escalation Rate** | 0.0% | N/A | 100% target | **FAIL** |

## 3. Archetype Distribution

- **Legitimate Retail & Corporate**: 40 cases (40%)
- **Velocity Burst Attacks**: 20 cases (20%)
- **Account Takeover & Unfamiliar Device**: 15 cases (15%)
- **Impossible Travel / Location Delta**: 10 cases (10%)
- **Contradictory Evidence Boundary Cases**: 10 cases (10%)
- **Insufficient Evidence / Missing KYC**: 5 cases (5%)
