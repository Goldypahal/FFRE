# FFIRE Third-Party Cross-Track Evaluation Synthesis

- **Generated**: `2026-10-24T04:35:00Z`
- **Readiness Posture**: `EVALUATION_MILESTONE_UNRESOLVED_GROUNDING_GAPS`
- **Defensible Interpretation Stance**:
  > *The current challenge results suggest that contextual evidence and reasoning may improve performance on these scenarios. Wide cluster-bootstrap confidence intervals on moderate sample sizes reflect genuine statistical variance, and results are not claimed as proof of general production readiness or general detection capability.*

---

## Executive Scorecard: Synthetic Baseline vs Hardened Challenge & Held-Out Evaluations

### 1. Track 1: IBM AMLSim Synthetic Benchmark (61 Cases, Strongly Separable Bimodal Distribution)
| Evaluation Track / Configuration | Metric | Result | Target SLA | Benchmark Status |
| :--- | :--- | :--- | :--- | :--- |
| **Config A: Rules-Only (Precision)** | Precision (30/30) | **100.0%** | >= 90.0% | PASS (Baseline) |
| **Config A: Rules-Only (Recall)** | Recall (30/30) | **100.0%** | >= 80.0% | PASS (Baseline) |
| **Config A: Rules-Only (F1 Score)** | Macro F1 [95% Cluster CI] | **1.0000** `[1.0000, 1.0000]` | >= 0.8500 | PASS (Baseline) |
| **Config B: Retrieval-Assisted (Precision)** | Precision (30/30) | **100.0%** | >= 90.0% | PASS |
| **Config B: Retrieval-Assisted (Recall)** | Recall (30/30) | **100.0%** | >= 80.0% | PASS |
| **Config B: Retrieval-Assisted (F1 Score)** | Macro F1 [95% Cluster CI] | **1.0000** `[1.0000, 1.0000]` | >= 0.8500 | PASS |
| **Config C: Full Pipeline (Precision)** | Precision (30/30) | **100.0%** | >= 90.0% | PASS |
| **Config C: Full Pipeline (Recall)** | Recall (30/30) | **100.0%** | >= 80.0% | PASS |
| **Config C: Full Pipeline (F1 Score)** | Macro F1 [95% Cluster CI] | **1.0000** `[1.0000, 1.0000]` | >= 0.8500 | PASS |
| **McNemar Exact Binomial p-value** | Baseline vs Full Pipeline | **p = 1.0000** | p < 0.05 | **No statistical difference (p > 0.05)** |

*Audit Assessment*: Strong performance on this synthetic set reflects rule alignment with synthetic bimodal heuristics, not proof of general detection ability. Added pipeline complexity demonstrates zero empirical detection uplift on this separable dataset.

---

### 2. Track 2A: Untouched Final Held-Out Test Battery (24 Cases, Post-Freeze Test Set)
*Created and frozen independently of model prompts and development tuning.*

| Configuration | Precision (95% CI) | Recall (95% CI) | Macro F1 (95% CI) | FPR | TP | FP | TN | FN | Mean Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Config A: Rules-Only Baseline** | 38.5% `[0.10, 0.67]` | 50.0% `[0.17, 0.83]` | **0.4079** `[0.19, 0.61]` | 66.7% | 5 | 8 | 4 | 5 | 4.98ms |
| **Config B: Retrieval-Assisted** | 100.0% `[1.00, 1.00]` | 40.0% `[0.09, 0.75]` | **0.6857** `[0.43, 0.89]` | 0.0% | 4 | 0 | 12 | 6 | 9.72ms |
| **Config C: Full FFIRE Pipeline** | 100.0% `[1.00, 1.00]` | 40.0% `[0.09, 0.75]` | **0.6857** `[0.43, 0.89]` | 0.0% | 4 | 0 | 12 | 6 | 1129.89ms |

#### Paired Head-to-Head Contingency (Config A vs Config C)
| | Config C Correct | Config C Incorrect | Total |
| :--- | :---: | :---: | :---: |
| **Config A Correct** | 10 | 1 | 11 |
| **Config A Incorrect** | 8 | 5 | 13 |
| **Total** | 18 | 6 | 24 |

- **McNemar Chi-Square**: 4.0 (`p = 0.0455`)
- **Discordant Pairs**: 9 divergent decisions.
- **Key Divergence Drivers**: Config C eliminated 8 false positives on legitimate commercial disbursements ($42.8k–$115k equipment, treasury, bonus, lease, dividend wires) by verifying KYC and counterparty relationships while preserving mandatory CTR reporting alerts.

---

### 3. Track 2B: Development Challenge Battery (16 Cases, Diagnostic Hardening Set)
*Used during active benchmark hardening to audit failure modes and rule floor behavior.*

| Configuration | Precision (95% CI) | Recall (95% CI) | Macro F1 (95% CI) | FPR | TP | FP | TN | FN | Mean Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Config A: Rules-Only Baseline** | 14.3% `[0.00, 0.50]` | 16.7% `[0.00, 0.50]` | **0.2534** `[0.06, 0.46]` | 66.7% | 1 | 6 | 3 | 5 | 4.05ms |
| **Config B: Retrieval-Assisted** | 0.0% `[0.00, 0.00]` | 0.0% `[0.00, 0.00]` | **0.2500** `[0.11, 0.36]` | 44.4% | 0 | 4 | 5 | 6 | 4.01ms |
| **Config C: Full FFIRE Pipeline** | 0.0% `[0.00, 0.00]` | 0.0% `[0.00, 0.00]` | **0.3750** `[0.25, 0.46]` | 0.0% | 0 | 0 | 9 | 6 | 1267.54ms |

#### Paired Head-to-Head Contingency (Config A vs Config C)
| | Config C Correct | Config C Incorrect | Total |
| :--- | :---: | :---: | :---: |
| **Config A Correct** | 4 | 1 | 5 |
| **Config A Incorrect** | 6 | 5 | 11 |
| **Total** | 10 | 6 | 16 |

- **McNemar Chi-Square**: 2.2857 (`p = 0.1306`, not statistically significant at alpha = 0.05)
- **Discordant Pairs**: 7 divergent decisions.

---

### 4. Supporting Evaluation Tracks

| Track | Metric | Result | Target SLA | Benchmark Status |
| :--- | :--- | :--- | :--- | :--- |
| **Track B: IR Retrieval (MRR)** | Mean Reciprocal Rank (24 cases) | **0.7083** | >= 0.7000 | PASS |
| **Track B: IR Retrieval (nDCG@3)** | Ranking Quality | **0.7917** | >= 0.7500 | PASS |
| **Track B: IR Retrieval (Abstention)**| Correct Abstention Rate | **95.8%** | >= 90.0% | PASS |
| **Track C: Claim Mutation (Calibration)**| 20-Case Calibration Rejection | **100.0%** | >= 95.0% | PASS |
| **Track C: Claim Mutation (Held-Out)**| 16-Case Held-Out Rejection | **100.0%** | >= 95.0% | PASS |
| **Track C: Claim False Rejection (FRR)**| False Rejection Rate | **0.0%** | <= 5.0% | PASS |
| **Adversarial Security** | Prompt Injection Defense | **100% BLOCKED (4/4)** | 100% Blocked | PASS |

---

## Methodological Audit Findings & Engineering Remediations

### 1. P0: Sample Size Uncertainty & Variance Disclosure
- **Finding**: On moderate sample sizes (16 dev cases, 24 held-out cases), exact 95% cluster-bootstrap confidence intervals are wide (e.g. `[0.43, 0.89]` on held-out Macro F1).
- **Remediation**: Point-estimate uplifts are explicitly framed as diagnostic evidence that contextual evidence and reasoning may improve performance on non-separable scenarios, rather than proof of generalized superiority.

### 2. P0: Challenge-Set Independence & No Label Peeking
- **Finding**: Evaluators must not inspect `ground_truth_label`, `category`, or scenario typologies.
- **Remediation**:
  - The 16 original cases are classified as the **Development Challenge Battery**.
  - A separate, untouched **Held-Out Test Battery (24 cases)** was constructed and frozen.
  - Test suite `test_challenge_independence_and_parity.py` asserts zero supervisory labels in model features, queries, or LangGraph state.

### 3. P0: Strict Evidence Parity Across Configurations
- **Finding**: All configurations must evaluate identical underlying database records and fail closed consistently on missing provenance.
- **Remediation**:
  - Configurations A, B, and C query identical database records.
  - Missing entities or disconnected graphs reliably escalate (`ESCALATED`) across all 3 configurations.

### 4. P1: Rule-Score Floor & Statutory Adjudication Policy
- **Finding**: Mandatory compliance alerts (e.g. CTR recordkeeping for currency transfers >= $10,000 under 31 CFR § 1010.311) were previously conflated with criminal money laundering convictions (`SUSPICIOUS`), causing routine corporate payroll to be falsely convicted.
- **Remediation**:
  - Separated rule classification via `is_typology_rule()` and `is_compliance_mandate_rule()`.
  - Regulatory threshold triggers are recorded in `state["compliance_alerts"]` and audit logs.
  - When commercial counterparties and verified KYC establish legitimate business operations, the laundering verdict is adjudicated as `BENIGN` while the compliance alert is preserved.
  - For illicit typologies (cycles, structuring, scatter-gather), `rule_score >= 0.50` enforces a strict floor `max(base_combined, rule_score)` preventing low vector similarity from suppressing illicit alerts.
