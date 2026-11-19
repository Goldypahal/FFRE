# FFIRE-Bench Public Leaderboard
**Benchmark:** Financial Fraud Investigation Reasoning & Evidence Benchmark  
**Version:** v0.1.0 | **Governed by:** FFIRE-Bench Consortium (`GOVERNANCE.md`)
> [!NOTE]
> All scores report point estimates alongside 95% cluster-bootstrap confidence intervals (1,000 resamples). Pass/Fail verdicts are strictly evaluated against thresholds in `configs/targets.yaml`.

## 1. Headline Leaderboard

| Rank | System Name | Track | Primary Metric (95% CI) | Citation F1 | Safe-to-File Acc | Cost-Weighted Acc | Benchmark Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Baseline-Majority** | `T1` | **0.1875** [0.1515, 0.2128] | 0.7200 | 50.0% | 1.1% | **FAIL** |
| 2 | **Baseline-Random** | `T1` | **0.1375** [0.0667, 0.2114] | 0.7200 | 50.0% | 28.6% | **FAIL** |
| 3 | **Baseline-HeuristicRules** | `T1` | **0.0750** [0.0000, 0.1481] | 0.6486 | 55.0% | 83.5% | **FAIL** |
| 4 | **llm-zero-shot** | `T1` | **0.0536** [0.0000, 0.1071] | 0.7200 | 30.0% | 56.0% | **FAIL** |
| 5 | **FFIRE-Verifier-v1.0** | `T1` | **0.0000** [0.0000, 0.0000] | 0.5405 | 50.0% | 100.0% | **FAIL** |

## 2. Difficulty Calibration Gate (§2.8 Audit)

| Calibration Rule | Requirement | Observed Value | Status |
|---|---|:---:|:---:|
| Ceiling Guard | Top System ≤ 80.0% | 18.8% | ✅ PASS |
| Floor Guard | Trivial Baseline ≤ 40.0% | 18.8% | ✅ PASS |
| Human Expert Ceiling | Expert Ceiling ≥ 90.0% | 94.2% | ✅ PASS |

## 3. Typology & Slice Breakdown

| Typology | Structuring | Rapid Movement | Funnel Accounts | Account Takeover | Mule Network | Trade-Based ML | Elder Exploitation | Sanctions Screening |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline-Majority** | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| **Baseline-Random** | 50.0% | 33.33% | 66.67% | 33.33% | 66.67% | 100.0% | 0.0% | 50.0% |
| **Baseline-HeuristicRules** | 0.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% | 0.0% |
| **llm-zero-shot** | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **FFIRE-Verifier-v1.0** | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% |
