# Datasheet for the FFIRE-Bench Dataset

Following the recommended dataset documentation framework established by Gebru et al. (*Datasheets for Datasets*, CACM 2021).

**Dataset Name:** FFIRE-Bench (Financial Fraud Investigation Reasoning & Evidence Benchmark)  
**Version:** v0.1.0  
**Release Date:** November 2026  
**Curators:** FFIRE-Bench Consortium  
**License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

---

## 1. Motivation

### For what purpose was the dataset created?
Financial institutions and regulated fintechs are increasingly deploying Large Language Models (LLMs) to synthesize complex transaction alerts, draft Suspicious Activity Report (SAR) narratives, and recommend alert closures. Under Federal Reserve SR 11-7 model-risk guidance, OCC bulletins, and the EU Artificial Intelligence Act (Annex III, High-Risk AI Systems), institutions must rigorously validate that AI systems do not hallucinate facts, misattribute transactions, overlook exculpatory contradictions, or fail to abstain under ambiguous evidence. Existing benchmarks focus either on simple graph classification (AMLSim) or open-domain factoid QA (FEVER). FFIRE-Bench was created to provide the first standardized, vendor-neutral evidentiary verification benchmark specifically measuring whether AI systems can audit and verify financial crime investigations.

### Who created the dataset?
Created by the FFIRE-Bench Consortium in collaboration with certified anti-money laundering (CAMS) domain experts, model-risk validation practitioners, and NLP researchers.

---

## 2. Composition

### What do the instances that comprise the dataset represent?
Each instance represents a complete, self-contained financial crime investigation case file comprising:
1. **Evidentiary Bundle**: Heterogeneous structured and unstructured records (transaction ledgers, KYC profiles, branch manager escalation notes, device telemetry logs, and sanctions screening hits).
2. **Candidate Investigation Narrative**: An investigator or LLM-drafted report detailing the findings, typology interpretation, and recommended disposition.
3. **Atomic Ground-Truth Claims**: Character-level segmented assertions annotated as `SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`, or `NOT_CHECKABLE`, cross-referenced to specific evidence IDs.
4. **Regulatory Error Annotations**: Fine-grained taxonomy codes (E1–E12), severity tiers (`critical`, `major`, `minor`), and binary regulatory filing compliance (`safe_to_file`).
5. **Calibrated Case Disposition**: Expected disposition (`ALLOW`, `CLOSE`, `FLAG`, `ESCALATE`, `NEED_MORE_INFO`) and expected abstention requirements.

### Are there recommended splits?
- **Dev Split**: Publicly available with full evidentiary records, candidate narratives, and gold annotations for prompt development and error analysis.
- **Public Test Split**: Publicly available inputs with hosted gold labels for standard offline replication.
- **Private Test Split**: Held-out confidential evaluation corpus accessible exclusively via the rate-limited scoring service (3 submissions/month/team) to prevent leaderboard contamination.

---

## 3. Collection & Synthesis Process

### How was the data generated or acquired?
Data is produced via a hybrid generative-and-expert-curated pipeline:
1. **Deterministic Scenario Simulation**: Parametric transaction graphs modeling 8 distinct financial crime typologies (Structuring, Rapid Movement, Funnel Accounts, Account Takeover, Mule Networks, Trade-Based ML, Elder Exploitation, Sanctions-Adjacent Screening).
2. **Multi-Family Narrative Generation**: Candidate narratives generated across multiple LLM families (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro), expert investigator templates, and human compliance analysts.
3. **Controlled & Natural Mutation Injection**: Controlled insertion of taxonomy errors E1–E12 with exact character span tracking, complemented by natural errors harvested from unprompted frontier model runs.
4. **Double Expert Review**: Double annotation by trained financial analysts, adjudicated by a CAMS-certified AML specialist.

### Does the dataset contain data that might be considered confidential or private (PII)?
**No.** All customer names, account numbers, IP addresses, and business entities are synthetically generated. Names were cross-referenced against public sanctions (OFAC SDN) and PEP databases to guarantee zero accidental collisions with real living individuals.

---

## 4. Preprocessing, Cleaning & Labeling

### What quality controls were applied?
- **Schema Validation**: Automated Pydantic v2 schema validation in CI for every case record.
- **Arithmetic Verification**: Automated checks ensuring transaction ledger amounts and totals mathematically match claim texts where claims are marked `SUPPORTED`.
- **Span Integrity Testing**: Automated verification that character span indices `[start, end]` slice the exact claim substring from the narrative text without offset drift.
- **Inter-Annotator Agreement**: Cohen's $\kappa \ge 0.70$ on claim labels and $\kappa \ge 0.80$ on case-level `safe_to_file` decisions.

---

## 5. Uses & Limitations

### What tasks is the dataset intended for?
- **Track 1 (T1)**: Fine-grained factual claim verification and citation extraction.
- **Track 2 (T2)**: Investigation narrative regulatory error detection and filing safety triage.
- **Track 3 (T3)**: Calibrated disposition determination with selective abstention under missing/contradictory evidence.
- **Track 4 (T4)**: Grounded SAR narrative generation.
- **Track 6 (T6)**: Robustness evaluation under adversarial prompt injection and distractor noise.

### Are there tasks for which the dataset should NOT be used?
- **Evasion / Laundering Instruction**: FFIRE-Bench must not be used to train illicit money laundering agents or circumvent banking fraud controls.
- **Autonomous Direct Filing**: Benchmark results should not be used as justification to eliminate human compliance officer oversight on regulatory filings.

---

## 6. Distribution & Maintenance

- **Code & Tooling**: Distributed under the **Apache-2.0 / MIT License** at `github.com/Goldypahal/FFRE`.
- **Dataset (Public Splits)**: Distributed under **CC-BY-4.0** on Hugging Face Datasets (`ffire-bench/v0.1`).
- **Canary Identification**: Public and private splits embed canary identifiers (`FFIRE-BENCH-CANARY-v0.1-4f9e8a7c`) to prevent training web scrapers from ingesting benchmark data.
- **Maintenance & Errata**: Governed by the FFIRE-Bench Consortium (`GOVERNANCE.md`). Errata and disputed annotations are logged and patched in `CHANGELOG.md`.
