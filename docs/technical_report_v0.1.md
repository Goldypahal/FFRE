# FFIRE-Bench: A Benchmark for Verifying AI-Written Financial Crime Investigations

**Technical Report v0.1.0**  
**Authors:** FFIRE team  
**Date:** November 2026  
**Repository:** `github.com/Goldypahal/FFRE`

> **Draft, not for publication.** v0.1 is a 20-case, template-generated dev set with no human annotation. Results in §6 test the pipeline only. Earlier drafts reported a human expert ceiling (94.2%) that was never measured, plus "LLM" and "FFIRE Verifier" baselines that did not call an LLM or FFIRE. Those claims have been removed (see `CHANGELOG.md`).

---

## Abstract

As global banking institutions deploy Large Language Models (LLMs) to draft alert dispositions and Suspicious Activity Report (SAR) narratives, model risk guidance (e.g., Federal Reserve SR 11-7) and the EU Artificial Intelligence Act demand rigorous, independent verification of these systems. While existing financial NLP benchmarks focus on corporate accounting QA (e.g., FinQA, FinanceBench) and existing AML benchmarks evaluate graph classification (e.g., AMLSim), no benchmark systematically evaluates whether an AI system can detect when an investigation narrative is supported, unsupported, contradicted, or incomplete relative to evidentiary records.

In this report, we introduce **FFIRE-Bench** (Financial Fraud Investigation Reasoning & Evidence Benchmark), an open, vendor-neutral evaluation framework for verifying AI-written financial crime investigations. FFIRE-Bench introduces:
1. A **12-class regulatory error taxonomy (E1–E12)** spanning numerical contradictions, temporal inversions, fabricated entities, ignored exculpatory evidence, and compliance tipping-off violations.
2. A multi-modal synthetic case generator modeling **8 financial crime typologies** (template-based in v0.1).
3. **Statistical evaluation rigor**, including cluster-aware bootstrap 95% confidence intervals, 15-bin Expected Calibration Error (ECE), and an asymmetric **10:1 cost-weighted scoring model** that penalizes missed money laundering 10× higher than false alarms.
4. A pipeline check with three offline baselines on a 20-case dev set. The "always SUPPORTED" baseline currently ranks first (Macro-F1 0.375), which shows the dev set is not yet able to separate systems. Real LLM and FFIRE runs, human annotation and a measured human ceiling are future work.

---

## 1. Introduction & Motivation

Anti-Money Laundering (AML) and Counter-Terrorist Financing (CTF) compliance operations represent one of the highest-stakes domains in financial services. US financial institutions file millions of SARs with FinCEN each year. To alleviate severe backlogs and alert fatigue, tier-1 institutions have rapidly piloted generative AI copilots to synthesize investigator dossiers and draft regulatory narratives.

However, deploying generative models in regulatory workflows introduces existential compliance risks:
- **Factual Hallucinations**: Fabricating transaction amounts, intermediary banks, or counterparty accounts violates federal reporting rules.
- **Confirmation Bias & Ignored Exculpatory Facts**: Citing incriminating velocity while omitting customer travel notifications leads to wrongful account freezes and debanking.
- **Fail-Open Overconfidence**: Concluding that a high-risk entity is legitimate when critical Beneficial Ownership (UBO) documentation is missing exposes banks to multi-million-dollar enforcement penalties.

Existing regulatory frameworks—specifically **Federal Reserve SR 11-7 / OCC Bulletin 2011-12** on model risk management and **Annex III of the EU AI Act** governing high-risk AI in credit and critical services—stipulate that models must undergo independent outcomes analysis, conceptual soundness validation, and adversarial benchmarking. FFIRE-Bench was designed to provide the required independent benchmark infrastructure.

---

## 2. Benchmark Architecture & Tracks

FFIRE-Bench formulates the investigative verification workflow into structured tracks:

```
+-----------------------------------------------------------------------------------+
|                            FFIRE-BENCH CORE TRACKS                                |
+-----------------------------------------------------------------------------------+
| Track 1 (T1) | Claim Verification (Headline): Classify claims as SUPPORTED,       |
|              | CONTRADICTED, UNSUPPORTED, NOT_CHECKABLE + cite evidence IDs.      |
+--------------+--------------------------------------------------------------------+
| Track 2 (T2) | Narrative Error Detection: Predict binary safe_to_file and         |
|              | annotate character-level error spans tagged with E1-E12 codes.     |
+--------------+--------------------------------------------------------------------+
| Track 3 (T3) | Calibrated Disposition & Abstention: Predict case disposition      |
|              | (ALLOW/CLOSE/FLAG/ESCALATE/NEED_MORE_INFO) with cost weighting.    |
+--------------+--------------------------------------------------------------------+
| Track 6 (T6) | Adversarial Robustness: Measure degradation under prompt injection,|
|              | evidence permutation, and distractor noise.                        |
+-----------------------------------------------------------------------------------+
```

---

## 3. The 12-Class Error Taxonomy (E1–E12)

FFIRE-Bench uses a granular error taxonomy intended to reflect failure modes seen in investigation QA reviews. It has not yet been reviewed by external AML practitioners:

| Code | Category | Description | Regulatory Impact | Severity Tier |
|:---:|---|---|---|:---:|
| **E1** | Wrong Amount | Discrepancy between narrative and transaction ledger | Distorts reporting thresholds | `critical` |
| **E2** | Wrong Temporal Order | Narrative inverts chronological sequence of funds | Alters source/destination logic | `critical` |
| **E3** | Fabricated Entity | Narrative hallucinates entity, bank, or jurisdiction | Inaccurate legal filings | `critical` |
| **E4** | Wrong Attribution | Assigns Subject A's actions to Subject B | Wrongful debanking | `critical` |
| **E5** | Unsupported Inference | Accusatory leap without evidentiary basis | Substandard SAR filing | `major` |
| **E6** | Contradiction Ignored | Ignores verified exculpatory travel or KYC record | False-positive escalation | `critical` |
| **E7** | Missing Required Element | Omits Who, What, When, Where, Why, How | Non-compliant SAR structure | `major` |
| **E8** | Wrong Typology | Confuses distinct typologies (e.g., structuring vs TBML) | Misdirected investigation | `major` |
| **E9** | Overconfident Conclusion | Closes case when KYC documents are missing | Failure to abstain / fail-open | `critical` |
| **E10**| Aggregation Error | Arithmetic summation or count error across entries | Defective audit trail | `major` |
| **E11**| Stale Evidence | Cites events outside 90-day authorized review window | Procedural violation | `minor` |
| **E12**| Tipping-Off Leak | Narrative indicates subject was informed of SAR filing | Criminal compliance felony | `critical` |

---

## 4. Multi-Modal Scenario Generation (8 Typologies)

The synthetic scenario generator (`ffire_gen`) produces complete, realistic dossiers across 8 typologies:
1. **Structuring**: Sub-$10,000 cash deposits across multiple branches to evade Currency Transaction Reporting (CTR).
2. **Rapid Movement / Pass-Through**: Substantial international wire inflows followed by near-immediate outflows to third jurisdictions.
3. **Funnel Accounts**: Geographically dispersed deposits into a single account followed by immediate consolidated wire transfer.
4. **Account Takeover (ATO)**: Unfamiliar device fingerprint, foreign IP address via Tor, MFA reset, and immediate balance drain.
5. **Mule Networks**: Multiple low-velocity peer-to-peer micro-transfers aggregated into a centralized beneficiary and converted to crypto vouchers.
6. **Trade-Based Money Laundering (TBML)**: Extreme invoice over-valuation (>14× fair market benchmark) on commercial freight manifests.
7. **Elder Financial Exploitation**: Long-standing senior customer accompanied by an aggressive contractor demanding immediate high-value cashier's checks.
8. **Sanctions-Adjacent Screening**: Fuzzy name match against OFAC Specially Designated Nationals (SDN) lists combined with unverified Beneficial Ownership (UBO) records.

---

## 5. Statistical Rigor & Difficulty Calibration

### 5.1 Asymmetric Cost-Weighted Scoring
Traditional accuracy weights all classification errors equally. In financial crime operations, false negatives (erroneously allowing or dismissing actual money laundering) trigger catastrophic regulatory penalties and facilitate criminal financing, whereas false positives merely incur additional analyst review time. FFIRE-Bench implements an asymmetric cost matrix:
$$\text{Cost}(\hat{y}, y) = \begin{cases} 10.0 & \text{if } y = \text{Fraud and } \hat{y} \ne \text{Fraud} \\ 1.0 & \text{if } y \ne \text{Fraud and } \hat{y} = \text{Fraud} \\ 0.0 & \text{if } \hat{y} = y \end{cases}$$

### 5.2 Difficulty Calibration Rules (§2.8 Audit)
To prevent the rapid benchmark saturation observed in prior datasets (where simple heuristic baselines achieved F1 = 1.000), FFIRE-Bench enforces strict calibration gates:
- **Floor Guard**: Trivial majority baseline must achieve $\le 40.0\%$ Macro-F1.
- **Ceiling Guard**: Best tested baseline system must achieve $\le 80.0\%$ Macro-F1.
- **Human Feasibility**: Human expert ceiling must achieve $\ge 90.0\%$ Macro-F1.

---

## 6. Baseline Experiments (pipeline check only)

Three offline baselines were run on the 20-case dev set (25 claims; only `SUPPORTED` and `CONTRADICTED` occur):
1. **Majority baseline:** labels every claim `SUPPORTED` and every case `safe_to_file: true`.
2. **Random baseline:** uniform random labels and dispositions (seed 42).
3. **Heuristic rules baseline:** string and number containment checks.

Two further runners exist but have **not been run yet**, because they need a real model or a running backend:
- **LLM zero-shot** (`ffire_bench/runners/prompt_runner.py`), via any OpenAI-compatible API or the Anthropic API.
- **FFIRE Verifier** (`ffire_bench/runners/ffire_adapter.py`), via `POST /api/v1/verifier/evaluate`.

### 6.1 Results

| System | Track | Macro-F1 (95% CI) | Citation F1 | Safe-to-File Acc | Cost-Weighted Acc |
|---|:---:|:---:|:---:|:---:|:---:|
| Baseline-Majority | `T1` | 0.3750 [0.3030, 0.4255] | 0.7200 | 50.0% | 1.1% |
| Baseline-Random | `T1` | 0.1375 [0.0667, 0.2118] | 0.7200 | 50.0% | 28.6% |
| Baseline-HeuristicRules | `T1` | 0.1000 [0.0000, 0.1975] | 0.6486 | 55.0% | 83.5% |

Macro-F1 is averaged over the labels that occur in gold or predictions. Earlier drafts averaged over all four labels, which capped every score at 0.5 on this set.

### 6.2 What these numbers mean
- **The trivial baseline ranks first.** That signals the dev set can't separate systems yet, not that the benchmark is hard.
- **Heuristic matching fails by construction.** Evidence is structured JSON and claims are prose, so containment checks rarely match.
- **Human ceiling: not measured.** No human annotation has been done.
- **Next steps:** hand-written, varied cases; all four labels present; independent human labels with agreement statistics; real LLM and FFIRE runs.

---

## 7. Credibility Reset & Integrity Audit

In earlier iterations of the FFRE repository, the held-out evaluation report (`scripts/evaluate_held_out_100_cases.py`) hard-coded static `**PASS**` strings across all metric rows regardless of value, obscuring critical metric failures (e.g., False-Positive Rate 17.78% vs <5% target; KYC escalation 0.0% vs 100% target).

As part of the Phase 0 Credibility Reset:
1. All static verdict strings were purged and replaced with dynamic threshold evaluation against `configs/targets.yaml`.
2. Regression tests in `tests/test_report_status_logic.py` guarantee that metric failures evaluate strictly to `FAIL`.
3. The held-out 100-case report was regenerated to honestly reflect its true status: **FAIL (6/10 Targets Met, 4 Violations)**.
4. Repository hygiene was completed: scratch files were archived, Kubernetes secrets audited (`docs/SECRETS_AUDIT.md`), and the product README was unbundled from benchmark evaluation claims.

---

## 8. Reproducibility

Any researcher or auditor can reproduce the complete evaluation suite and leaderboard in less than 2 minutes using standard commands:

```bash
# 1. Install ffire-bench package
pip install -e .

# 2. Run test suite
pytest tests/ -v

# 3. Execute one-command reproduction script
python scripts/reproduce_v0.1.py
```

---

## 9. Conclusion

FFIRE-Bench establishes the first rigorous, vendor-neutral evaluation foundation for verifying AI-written financial crime investigations. By introducing a fine-grained 12-class error taxonomy, calibrated abstention metrics, and asymmetric cost weighting, FFIRE-Bench aligns AI evaluation directly with banking supervision requirements under SR 11-7 and the EU AI Act.
