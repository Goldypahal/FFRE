# Third-Party Evaluation Datasets

This directory contains benchmark datasets and provenance manifests for third-party evaluation tracks.

---

## 1. Track A: IBM AMLSim Dataset (`amlsim_typology_benchmark_v1`)
- **Upstream Project**: [IBM/AMLSim](https://github.com/IBM/AMLSim)
- **License**: Apache-2.0
- **Provenance**: Multi-agent financial crime simulation generating synthetic transactions with injected suspicious money laundering typologies and realistic benign control networks.
- **Label Isolation Protocol**:
  - The dataset maintains strict separation between transaction feature fields (`step`, `type`, `amount`, `nameOrig`, `nameDest`) and ground-truth evaluation labels (`isSAR`, `alert_id`, `typology`).
  - When ingested into FFIRE, only feature fields are loaded into the database/evidence store.
  - Evaluation runners score predictions against external gold labels without exposing labels to the reasoning engine or LLM prompt templates.
- **Files**:
  - `amlsim_transactions.csv`: Transaction log with source/dest accounts, amounts, and step timestamps.
  - `amlsim_accounts.csv`: Account entities with initial balances and model types.
  - `amlsim_alerts.json`: Ground-truth typology definitions and alert membership lists.

---

## 2. Track B: Grounded RAG Evaluation Dataset (`ragas_grounded_eval_v1`)
- **Format**: JSONL (`ragas_eval_dataset.jsonl`)
- **Categories**:
  1. `answerable_complete`: Single-source answerable questions with ground-truth evidence IDs.
  2. `answerable_multihop`: Multi-hop synthesis across customer KYC, device, geolocation, and velocity.
  3. `insufficient_evidence`: Missing or degraded data sources testing pipeline abstention/escalation.
  4. `adversarial_unsupported`: Injected adversarial assertions testing claim-mutation verification.
- **Metrics Evaluated**:
  - Precision@k, Recall@k, MRR, nDCG@k (k ∈ {1, 3, 5})
  - Critical-claim mutation rejection rate & false rejection rate
  - Adversarial prompt injection defense
