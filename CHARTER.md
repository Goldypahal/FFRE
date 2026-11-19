# FFIRE-Bench Charter

**Full Title:** Financial Fraud Investigation Reasoning & Evidence Benchmark  
**Short Name:** FFIRE-Bench  
**Status:** Approved Charter  
**Version:** 1.0.0  
**Effective Date:** November 2026

---

## 1. Mission Statement

The mission of **FFIRE-Bench** is to establish an open, rigorous, and vendor-neutral industry standard for measuring whether artificial intelligence systems (and human-AI collaborative workflows) can accurately verify, critique, and audit financial crime investigation narratives against evidentiary case dossiers.

As financial institutions deploy Large Language Models (LLMs) to summarize transaction alerts, draft suspicious activity reports (SARs), and recommend case dispositions, regulatory frameworks—including Federal Reserve SR 11-7 model-risk guidance, OCC bulletins, and the EU Artificial Intelligence Act—demand independent, empirical validation of factual grounding, calibration, and error resilience. FFIRE-Bench provides the foundational evaluation infrastructure to satisfy these regulatory mandates.

---

## 2. Benchmark Tracks & Scope

FFIRE-Bench evaluates AI systems across six structured tracks:

1. **Track 1 (T1) — Claim Verification (Headline)**:
   - *Input*: Evidence bundle (transactions, KYC profile, analyst notes, device logs) + candidate narrative.
   - *Output*: Per-claim classification (`SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`, `NOT_CHECKABLE`) with precise evidence citation IDs.
   - *Primary Metric*: Claim-level Macro-F1 and citation precision/recall/F1.

2. **Track 2 (T2) — Narrative Error Detection**:
   - *Input*: Evidence bundle + candidate investigation narrative.
   - *Output*: Binary regulatory filing safety determination (`safe_to_file: true/false`) and character-level error span annotations tagged with taxonomy codes E1–E12.
   - *Primary Metric*: Critical-error recall at 90% precision and case-level AUROC.

3. **Track 3 (T3) — Calibrated Disposition with Abstention**:
   - *Input*: Heterogeneous alert evidence bundle with controlled information gaps or contradictions.
   - *Output*: Disposition (`ESCALATE`, `CLOSE`, `NEED_MORE_INFO`) accompanied by a calibrated confidence score.
   - *Primary Metric*: Cost-weighted classification accuracy (10:1 false-negative fraud penalty), selective risk-coverage AUC under abstention, and 15-bin Expected Calibration Error (ECE).

4. **Track 4 (T4) — Grounded Narrative Generation**:
   - *Input*: Multi-source evidence bundle.
   - *Output*: End-to-end SAR-compliant narrative.
   - *Primary Metric*: Factual claim precision, regulatory completeness, and hallucination rate.

5. **Track 5 (T5) — Typology Detection (Sanity)**:
   - *Input*: Graph/transaction ledger.
   - *Output*: Underlying laundering/fraud typology.
   - *Primary Metric*: Multi-class Macro-F1 (preserves AMLSim historical baselines).

6. **Track 6 (T6) — Robustness & Adversarial Perturbations**:
   - *Input*: Inputs from T1–T3 subjected to syntactic perturbations, distractor evidence injection, date format shifts, and prompt injections.
   - *Primary Metric*: Performance delta and degradation slope under adversarial noise.

---

## 3. Explicit Non-Goals

To maintain security, ethics, and focus, FFIRE-Bench explicitly excludes:
- **Financial Crime Evasion**: FFIRE-Bench will never generate or publish step-by-step techniques for bypassing AML controls, structuring transactions, or evading transaction monitoring systems. All typologies strictly mirror public FinCEN/FATF typologies.
- **Real Customer PII**: FFIRE-Bench contains zero real-world personally identifiable information (PII). All customer names, account numbers, and device identifiers are synthetically generated and screened against sanctions/PEP lists to prevent coincidental collisions.
- **Vendor-Biased Marketing**: FFIRE-Bench is not a proprietary marketing vehicle for the FFIRE commercial product. The benchmark is governed under open-source licenses, with identical scoring rules and test sets applied to all models.

---

## 4. Vendor Neutrality & Separation of Concerns

1. **Independent Identity**: FFIRE-Bench is branded and governed independently from the commercial FFIRE Verifier engine.
2. **Parity in Evaluation**: The commercial FFIRE engine is treated as an ordinary submitter to the benchmark. FFIRE's predictions are evaluated using the identical public/private test sets, CLI tooling, and scoring pipelines as external frontier models (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) and open-weights baselines.
3. **Transparent Reporting**: If FFIRE fails a metric threshold or underperforms an external baseline on any track or slice, the failure is reported openly on the public leaderboard without curation or suppression.

---

## 5. Licensing & Distribution

- **Benchmark Code & CLI**: Licensed under the **Apache License, Version 2.0** / **MIT License**.
- **Public Datasets (Dev & Public Test Splits)**: Licensed under the **Creative Commons Attribution 4.0 International License (CC-BY-4.0)**.
- **Private Held-Out Test Set**: Retained under secure custodial control by the FFIRE-Bench Governance Committee to prevent training set contamination and benchmark saturation.
