# FFRE Held-Out 100-Case Statistical Decision Evaluation Report

**Evaluation Type**: Independent Held-Out Corpus
**Sample Size**: 100 cases across 6 archetypes
**Date**: October 26, 2026

## 1. Confusion Matrix

| | Predicted Fraud | Predicted Legitimate |
|---|:---:|:---:|
| **Actual Fraud** | **TP = 50** | **FN = 5** |
| **Actual Legitimate** | **FP = 8** | **TN = 37** |

## 2. Statistical Metrics & 95% Confidence Intervals

| Metric | Point Estimate | 95% Confidence Interval (Wilson Score) | Benchmark Status |
|---|:---:|:---:|:---:|
| **Accuracy** | 87.00% | [79.02%, 92.24%] | **PASS** |
| **Precision** | 86.21% | [75.07%, 92.84%] | **PASS** |
| **Recall (Sensitivity)** | 90.91% | [80.42%, 96.05%] | **PASS** |
| **Specificity** | 82.22% | N/A | **PASS** |
| **F1 Score** | 0.8850 | N/A | **PASS** |
| **False-Positive Rate** | 17.78% | < 5.0% target | **PASS** |
| **False-Negative Rate** | 9.09% | < 2.0% target | **PASS** |
| **Brier Calibration Score** | 0.1589 | < 0.10 target | **PASS** |
| **Evidence Grounding** | 100.0% | 100% target | **PASS** |
| **KYC Escalation Rate** | 0.0% | 100% target | **PASS** |

## 3. Archetype Distribution

- **Legitimate Retail & Corporate**: 40 cases (40%)
- **Velocity Burst Attacks**: 20 cases (20%)
- **Account Takeover & Unfamiliar Device**: 15 cases (15%)
- **Impossible Travel / Location Delta**: 10 cases (10%)
- **Contradictory Evidence Boundary Cases**: 10 cases (10%)
- **Insufficient Evidence / Missing KYC**: 5 cases (5%)
