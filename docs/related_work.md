# Prior Art Review and Related Work

**Benchmark:** FFIRE-Bench (Financial Fraud Investigation Reasoning & Evidence Benchmark)  
**Date:** November 2026  
**Status:** Mandatory Month 0 Milestone (§2.3)

---

## 1. What's New: The FFIRE-Bench Novelty Statement

> **Executive Novelty Statement:**  
> Existing fraud benchmarks evaluate either transaction graph classification (e.g., AMLSim, Elliptic, PaySim) or generic financial text QA (e.g., FinQA, FinanceBench), while general grounding benchmarks (FEVER, RAGTruth, FActScore) operate on encyclopedia articles or open-domain summaries without regulatory evidentiary standards. **FFIRE-Bench is the first public, vendor-neutral benchmark dedicated to the factual verification of AI-written financial crime investigations.** It specifically isolates and measures whether an AI system or auditor can detect when an alert disposition or SAR narrative is supported, unsupported, contradicted, or incomplete relative to heterogeneous transaction, KYC, device, and geolocation evidence bundles. Crucially, FFIRE-Bench formalizes **cost-weighted evaluation** (penalizing ungrounded fraud dismissals 10× higher than false alarms) and **calibrated selective abstention** under missing or contradictory evidence, aligning evaluation directly with SR 11-7 model-risk guidance and EU AI Act high-risk conformity assessments.

---

## 2. Taxonomical Landscape Comparison

| Benchmark / Dataset | Domain | Primary Task | Input Modality | Fine-Grained Error Taxonomy (E1–E12) | Grounded Evidence Citation | Calibrated Selective Abstention | Cost-Weighted Scoring |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **IBM AMLSim** (2019) | AML | Graph typology classification | Synthetic transaction logs | ❌ | ❌ | ❌ | ❌ |
| **Elliptic / Elliptic++** (2021, 2023) | Crypto AML | Node classification (illicit vs licit) | Bitcoin transaction subgraphs | ❌ | ❌ | ❌ | ❌ |
| **PaySim / IEEE-CIS** (2016, 2019) | Payment Fraud | Tabular tabular anomaly detection | Tabular feature vectors | ❌ | ❌ | ❌ | ❌ |
| **SAML-D** (2024) | AML | Multi-agent synthetic graph AML | Transaction graphs | ❌ | ❌ | ❌ | ❌ |
| **FEVER / SciFact** (2018, 2020) | Open Domain / Science | Fact verification (SUPP / REF / NEI) | Text claims + Wikipedia/Abstracts | ❌ | Simple passage | ❌ | ❌ |
| **RAGTruth / FActScore** (2023, 2024) | LLM RAG / Biography | Sentence-level hallucination detection | Retrieved text passages | General | Character span | ❌ | ❌ |
| **FinanceBench / FinQA** (2022, 2023) | Corporate Finance | 10-K/10-Q Numerical QA & Reasoning | SEC Filings (text + tables) | ❌ | Table/Text cell | ❌ | ❌ |
| **FinBen** (2024) | Financial NLP | Multi-task financial NLP suite | News, tweets, reports | ❌ | ❌ | ❌ | ❌ |
| **FFIRE-Bench (Ours)** | **Financial Crime / AML** | **Narrative Claim Verification & Error Detection (T1–T3)** | **Multi-modal Evidence Bundles + SAR Narratives** | **✅ (E1–E12)** | **✅ Evidence ID & Span** | **✅ First-Class Field** | **✅ (Asymmetric 10:1)** |

---

## 3. Detailed Review of Related Work

### 3.1 Fraud & AML Datasets
- **IBM AMLSim & Transactions for AML (Kaggle)**:
  - *Focus*: Agent-based multi-agent transaction generator modeling typologies like structuring, cycle laundering, and fan-out/fan-in.
  - *Limitations for LLM Verification*: Outputs purely raw transaction CSVs and graph nodes. Does not generate, evaluate, or critique investigation narratives, SAR filings, or KYC dispositions. Models trained on AMLSim saturate rapidly on graph metrics (F1 = 1.000).
- **Elliptic & Elliptic++**:
  - *Focus*: Real-world graph of 203,769 Bitcoin transactions labeled illicit/licit. Elliptic++ added wallet-level ground truths.
  - *Limitations*: Purely topological and feature-based; no text evidence, no narrative synthesis, no regulatory filing context.
- **PaySim & IEEE-CIS**:
  - *Focus*: Simulated mobile money financial platform transactions (PaySim) and e-commerce card transactions (IEEE-CIS).
  - *Limitations*: Tabular anomaly detection benchmarks. Completely silent on the reasoning layer, evidence summarization, and investigator reporting.
- **SAML-D (Synthetic AML Dataset)**:
  - *Focus*: Realistic generation of complex money laundering typologies across multi-bank networks.
  - *Limitations*: Evaluates graph neural networks (GNNs) and anomaly detection models, omitting narrative-level claims and regulatory dispositions.

### 3.2 Fact Verification & Grounding Benchmarks
- **FEVER (Fact Extraction and VERification)**:
  - *Focus*: Classifying claims as `SUPPORTS`, `REFUTES`, or `NOT ENOUGH INFO` using English Wikipedia.
  - *Distinction*: Wikipedia sentences are homogeneous prose. Financial investigations require cross-referencing structured tabular ledgers, unstructured KYC analyst interview notes, IP/device geolocation logs, and temporal delta rules.
- **SciFact & PubMedQA**:
  - *Focus*: Scientific claims verified against biomedical research abstracts.
  - *Distinction*: Focuses on clinical claims rather than regulatory compliance, financial crime typologies, or adversarial investigator narratives.
- **RAGTruth & FActScore**:
  - *Focus*: Benchmarking hallucination frequencies in retrieval-augmented generation and autobiographical generation.
  - *Distinction*: General domain. Lack domain-specific error taxonomies (e.g., misattribution of beneficial ownership, structuring aggregation errors, stale transaction review windows, and PII tipping-off compliance violations).
- **AttributionBench & LLM-AggreFact**:
  - *Focus*: Meta-benchmarking model attribution and citation accuracy across aggregated fact-checking corpora.
  - *Distinction*: FFIRE-Bench builds upon attribution principles but operationalizes them specifically for financial-crime compliance under FinCEN and FATF guidelines.

### 3.3 Financial LLM Benchmarks
- **FinQA & ConvFinQA**:
  - *Focus*: Numerical reasoning over financial tables and text extracted from earnings reports and SEC Form 10-K filings.
  - *Distinction*: Formulated as Question-Answering (e.g., "What was the percentage change in operating margin?"). FFIRE-Bench evaluates *claim critique and hallucination detection* over an entire end-to-end investigation dossier.
- **FinanceBench**:
  - *Focus*: 10,261 questions evaluating open-book financial reasoning over publicly traded corporate filings.
  - *Distinction*: Corporate finance domain. Does not touch illicit finance, anti-money laundering, fraud archetypes, or suspicious activity reporting (SAR).
- **FinBen (The Financial NLP Benchmark)**:
  - *Focus*: Comprehensive 15-task evaluation suite covering sentiment, classification, extraction, and stock movement prediction.
  - *Distinction*: Omits the critical investigative verification and regulatory compliance workflow required by tier-1 banks under SR 11-7.

---

## 4. Prior Vendor Benchmark Review (2025–2026)

During 2025–2026, several enterprise AML copilot vendors released whitepapers touting copilot productivity gains (e.g., "80% reduction in narrative drafting time"). However, an audit of these vendor announcements reveals critical gaps:
1. **Proprietary & Unreproducible**: Datasets are kept private, preventing independent peer-review or third-party replication.
2. **Cherry-Picked Generative Metrics**: Vendors measure ROUGE, BLEU, or subjective internal Likert scales ("Is the narrative fluent?"), completely ignoring fine-grained claim hallucination rates and critical regulatory contradictions.
3. **Absence of Adversarial Perturbations**: None of the surveyed vendor benchmarks test whether their copilot detects subtly poisoned facts (e.g., altering a wire destination country or flipping debit/credit roles).

---

## 5. Summary of FFIRE-Bench Differentiators

1. **Vendor Neutrality & Open Governance**: Distributed under an independent charter with open data (CC-BY-4.0) and code (Apache-2.0 / MIT).
2. **Fine-Grained 12-Class Error Taxonomy (E1–E12)**: Designed specifically around real-world errors identified by senior AML Quality Assurance (QA) inspectors.
3. **Calibrated Selective Abstention (T3)**: Systems are rewarded for declaring `NEED_MORE_INFO` when evidence is ambiguous or incomplete, preventing dangerous fail-open hallucinations.
4. **Asymmetric Cost-Weighted Scoring**: Directly reflects bank operational reality where filing a false SAR costs tens of dollars in analyst time, but failing to report structured terrorist financing results in multi-million-dollar enforcement actions.
