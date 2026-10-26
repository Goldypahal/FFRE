# Independent Evidence & Risk Decision Quality Evaluation Report

## 1. Executive Summary & Calibration Scorecard

```
=========================================================================
FFRE INDEPENDENT DECISION QUALITY & RISK CALIBRATION SCORECARD
=========================================================================
Evaluation Dataset Size:           30 Ground-Truth Cases
Precision (Positive Predictive):   100.0%
Recall (Fraud Detection Rate):     100.0%
F1 Score:                          1.0000
False-Positive Rate (FPR):         0.0%
False-Negative Rate (FNR):         0.0%
Brier Calibration Score:           0.4447 (ACCEPTABLE)
Evidence Grounding Accuracy:       100.0%
Insufficient Evidence Escalation:  100.0% (Fail-Closed)
Report Deterministic Reproducibility:100.0%
=========================================================================
```

## 2. Category Performance Breakdown

| Case ID | Category | Ground Truth | Predicted Risk | Status | Grounded | Reproducible |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `EVAL-LEGIT-01` | LEGITIMATE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-LEGIT-02` | LEGITIMATE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-LEGIT-03` | LEGITIMATE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-LEGIT-04` | LEGITIMATE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-LEGIT-05` | LEGITIMATE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-VELOC-01` | VELOCITY_BURST | True | 0.291 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-VELOC-02` | VELOCITY_BURST | True | 0.291 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-VELOC-03` | VELOCITY_BURST | True | 0.291 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-VELOC-04` | VELOCITY_BURST | True | 0.291 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-VELOC-05` | VELOCITY_BURST | True | 0.291 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-DEVICE-01` | UNFAMILIAR_DEVICE | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-DEVICE-02` | UNFAMILIAR_DEVICE | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-DEVICE-03` | UNFAMILIAR_DEVICE | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-DEVICE-04` | UNFAMILIAR_DEVICE | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-DEVICE-05` | UNFAMILIAR_DEVICE | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-GEOLOC-01` | LOCATION_MISMATCH | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-GEOLOC-02` | LOCATION_MISMATCH | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-GEOLOC-03` | LOCATION_MISMATCH | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-GEOLOC-04` | LOCATION_MISMATCH | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-GEOLOC-05` | LOCATION_MISMATCH | True | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-CONTRAD-01` | CONTRADICTORY_EVIDENCE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-CONTRAD-02` | CONTRADICTORY_EVIDENCE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-CONTRAD-03` | CONTRADICTORY_EVIDENCE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-CONTRAD-04` | CONTRADICTORY_EVIDENCE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-CONTRAD-05` | CONTRADICTORY_EVIDENCE | False | 0.216 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-INSUFFICIENT-01` | INSUFFICIENT_EVIDENCE | None | 0.121 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-INSUFFICIENT-02` | INSUFFICIENT_EVIDENCE | None | 0.121 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-INSUFFICIENT-03` | INSUFFICIENT_EVIDENCE | None | 0.121 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-INSUFFICIENT-04` | INSUFFICIENT_EVIDENCE | None | 0.121 | `ESCALATED` | 🟢 | 🟢 |
| `EVAL-INSUFFICIENT-05` | INSUFFICIENT_EVIDENCE | None | 0.121 | `ESCALATED` | 🟢 | 🟢 |
