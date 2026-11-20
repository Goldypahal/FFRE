# FFIRE-Bench Governance Model

**Version:** 1.0.0  
**Effective Date:** November 2026  
**Charter Reference:** `CHARTER.md`

---

## 1. Governance Principles

The FFIRE-Bench benchmark operates under four foundational principles:
1. **Scientific Rigor**: All leaderboard scores must be fully reproducible from version-controlled seeds, with 95% cluster-bootstrap confidence intervals and statistical significance markers.
2. **Absolute Neutrality**: No participant, sponsor, or affiliated entity (including the commercial FFIRE product) receives preferential scoring, private set access, or leaderboard curation.
3. **Data Integrity & Anti-Contamination**: Private test sets are shielded with canary GUID strings and strict custodial security to prevent training-data leakage.
4. **Community Transparency**: Annotation guidelines, schema definitions, baseline model cards, and errata are published openly.

---

## 2. Advisory Board Structure

The Benchmark is overseen by an independent **Advisory Board** composed of 3–5 rotating professionals across three distinct domains:

1. **AML / Financial Crime Investigation Specialist (CAMS-Certified)**:
   - Validates scenario realism, typology accuracy, and regulatory consistency under FATF/FinCEN standards.
   - Audits annotation quality guidelines and presides over edge-case claim adjudication.
2. **Model Risk Management & Validation Professional (SR 11-7 Specialist)**:
   - Evaluates statistical calibration metrics, cost-weighted penalty matrices, and conceptual soundness of evaluation outputs.
   - Ensures validation packs satisfy institutional model governance requirements.
3. **Independent Academic / Machine Learning Evaluator**:
   - Oversees benchmark methodology, contamination defenses, bootstrap statistical testing, and difficulty calibration rules (§2.8).

---

## 3. Dataset Splits & Release Lifecycle

FFIRE-Bench maintains three distinct data splits:

| Split | Description | Availability | Canary String |
|---|---|---|:---:|
| **Dev Split** | Full evidence bundles, gold claims, narrative spans, and ground-truth error labels for model development and prompt engineering. | Public (GitHub / Hugging Face) | ✅ |
| **Public Test Split** | Publicly accessible test evidence and narratives with held-out gold labels for standardized offline reproduction. | Public (HF Dataset) | ✅ |
| **Private Test Split** | Strictly confidential held-out set evaluated exclusively via the automated scoring service. Never published, indexed, or shared. | Private Custody | ✅ |

### Versioning & Annual Rotation
- Benchmark releases adhere to Semantic Versioning (`vMAJOR.MINOR.PATCH`).
- **Minor releases** (e.g., `v0.1` -> `v0.2`) introduce expanded case volume or new tracks while preserving scoring comparability.
- **Annual Rotation**: Every 12 months, 30% of the private test set is rotated into the public test set, and a new batch of double-reviewed private cases is introduced to permanently defeat overfitting.

---

## 4. Submission & Scoring Policy

1. **Submission Rate Limits**: To prevent hill-climbing on the private test set, external teams (including the internal FFIRE engineering team) are limited to a maximum of **three (3) submissions per calendar month**.
2. **Execution Sandbox**: Submissions consist of model predictions generated against blind test inputs formatted per `benchmarks/schemas/case.schema.json`.
3. **Audit Trails & Signed Attestations**:
   - Every submitted prediction bundle is cryptographically hashed (SHA-256).
   - Evaluation reports are digitally signed using the benchmark committee's Ed25519 key, providing verifiable proof of official scoring.
4. **Tie Breaking & Significance**:
   - Systems whose 95% bootstrap confidence intervals overlap without statistically significant separation (p > 0.05 via paired bootstrap test) share an identical leaderboard tier with a designated `[TIE]` marker.

---

## 5. Errata & Appeals Process

1. **Bug Reports & Data Errata**: Any community member may submit an issue regarding ambiguous evidence, debatable claim groundings, or annotation discrepancies.
2. **Adjudication**: The Advisory Board reviews contested cases bi-weekly. If an annotation error is confirmed, a patch release (e.g., `v0.1.1`) is issued with an explicit entry in `CHANGELOG.md`, and all affected leaderboard entries are automatically re-scored.
