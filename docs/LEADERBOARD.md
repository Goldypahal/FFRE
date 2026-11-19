# FFIRE-Bench Public Leaderboard
**Benchmark:** Financial Fraud Investigation Reasoning & Evidence Benchmark  
**Version:** v0.1.0 (dev preview) | **Maintained by:** the FFIRE team. No external advisory board yet (see `GOVERNANCE.md`)

> [!WARNING]
> **Not a meaningful ranking yet.** The v0.1 dev set is 20 template-generated cases (8 templates) with 25 claims, generated and labelled automatically and **not reviewed by humans**. Use these numbers to test the pipeline, not to compare systems.

> [!NOTE]
> All scores report point estimates alongside 95% cluster-bootstrap confidence intervals. Pass/Fail verdicts are strictly evaluated against thresholds in `configs/targets.yaml`.

## 1. Headline Leaderboard

| Rank | System Name | Track | Primary Metric (95% CI) | Citation F1 | Safe-to-File Acc | Cost-Weighted Acc | Benchmark Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Baseline-Majority** | `T1` | **0.3750** [0.3030, 0.4255] | 0.7200 | 50.0% | 1.1% | **FAIL** |
| 2 | **Baseline-Random** | `T1` | **0.1375** [0.0667, 0.2118] | 0.7200 | 50.0% | 28.6% | **FAIL** |
| 3 | **Baseline-HeuristicRules** | `T1` | **0.1000** [0.0000, 0.1975] | 0.6486 | 55.0% | 83.5% | **FAIL** |

## 2. Difficulty Calibration Gate (§2.8 Audit)

| Calibration Rule | Requirement | Observed Value | Status |
|---|---|:---:|:---:|
| Ceiling Guard | Top System ≤ 80.0% | 37.5% | ✅ PASS |
| Floor Guard | Trivial Baseline ≤ 40.0% | 37.5% | ✅ PASS |
| Trivial Leader Check | Top system is not a trivial baseline | Baseline-Majority | ❌ INVALID: trivial baseline ranks first |
| Human Expert Ceiling | Expert Ceiling ≥ 90.0% | Not measured | ⚠️ NOT MEASURED |

## 3. Typology & Slice Breakdown

| Typology | Structuring | Rapid Movement | Funnel Accounts | Account Takeover | Mule Network | Trade-Based ML | Elder Exploitation | Sanctions Screening |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline-Majority** | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| **Baseline-Random** | 50.0% | 33.33% | 66.67% | 33.33% | 66.67% | 100.0% | 0.0% | 50.0% |
| **Baseline-HeuristicRules** | 0.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% | 0.0% |
