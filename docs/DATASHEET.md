# Datasheet for the FFIRE-Bench Dataset

Structured after *Datasheets for Datasets* (Gebru et al., CACM 2021).

**Dataset name:** FFIRE-Bench (Financial Fraud Investigation Reasoning & Evidence Benchmark)
**Version:** v0.1.0 (dev preview)
**Release date:** November 2026 (not yet published to Hugging Face)
**Maintainers:** the FFIRE team (`github.com/Goldypahal/FFRE`)
**License:** CC-BY-4.0 for data; code under the repository license

> **Status: dev preview.** v0.1 is a 20-case dev set that is generated and labelled automatically from 8 templates. No human has reviewed or annotated it. It's suitable for testing the pipeline, not for comparing systems. The process described in `docs/annotation_guidelines.md` and `GOVERNANCE.md` is the plan for later releases, not something that has already happened.

---

## 1. Motivation

### Why was the dataset created?
Banks and fintechs are starting to use LLMs to draft alert dispositions and SAR narratives. Model-risk guidance (for example US SR 11-7) and the EU AI Act push institutions to validate those systems independently. FFIRE-Bench aims to measure whether a system can tell when an investigation narrative is supported, contradicted, unsupported or incomplete relative to the case evidence. Overlap with existing benchmarks is discussed in `docs/related_work.md`.

### Who created it?
The FFIRE team. No external AML practitioners, model-risk validators or annotators have contributed to v0.1 yet. Recruiting them is on the roadmap.

---

## 2. Composition (v0.1 dev set as shipped)

| Item | Value |
|---|---|
| File | `data/gold_standard_20_cases.json` |
| Cases | 20 |
| Typologies | 8 (structuring, rapid movement, funnel accounts, account takeover, mule network, trade-based ML, elder exploitation, sanctions-adjacent) |
| Distinct narrative templates | 8 (cases of the same typology share wording and differ in names and numbers) |
| Claims | 25 (1–2 per case) |
| Claim labels present | `SUPPORTED` (15), `CONTRADICTED` (10). `UNSUPPORTED` and `NOT_CHECKABLE` don't occur yet. |
| `safe_to_file` | 10 true / 10 false (errors injected into every other case) |
| Split | `dev` only. No public-test or private-test split exists yet. |

Each case contains:
1. **Evidence bundle:** structured records (transaction tables, KYC profiles, notes, device logs, screening hits).
2. **Narrative:** a templated SAR-style write-up.
3. **Claims:** character spans in the narrative with a label, an error code (E1–E12) when wrong, and gold evidence IDs.
4. **Case label:** `safe_to_file`, expected disposition and expected abstention.

---

## 3. Collection and generation

1. **Scenario templates:** `ffire_bench/generators/ffire_gen.py` holds one hand-written template per typology, filled with seeded random names and amounts (seed 42).
2. **Narratives:** produced by those templates (`narrative_source: "template:ffire_gen_v1"`). No LLM-written or human-written narratives are included yet.
3. **Error injection:** on odd-numbered cases, one controlled error is inserted with exact span tracking.
4. **Labels:** the labels come from the generator itself (the generator knows which span it changed). `human_reviewed` is `false` and `reviewer_count` is `0` on every case.

### Personal data
None. All names, accounts and entities are invented. They have **not** yet been checked against sanctions or PEP lists for accidental matches with real people. That check is on the roadmap.

---

## 4. Quality controls

**In place:**
- Pydantic schema validation of every case.
- Unit tests for span integrity of injected errors.

**Not yet done (planned):**
- Double human annotation with adjudication.
- Inter-annotator agreement (targets: Cohen's κ ≥ 0.70 on claim labels, ≥ 0.80 on `safe_to_file`).
- Human expert ceiling measurement.
- Practitioner realism review.

---

## 5. Uses and limitations

**Intended:** testing the FFIRE-Bench tooling end to end (generation → runner → scoring → leaderboard) and drafting prompts.

**Known limitations of v0.1:**
- Too small (25 claims) for meaningful confidence intervals or system rankings.
- Templated wording, so systems can overfit to the templates.
- Only two claim labels occur.
- Evidence is structured JSON while claims are prose, so naive string-matching baselines fail by construction.

**Must not be used for:** training systems to evade AML controls, or justifying removal of human oversight on regulatory filings.

---

## 6. Distribution and maintenance

- **Code and data:** this repository. A Hugging Face release is planned but hasn't happened yet.
- **Canary string:** `FFIRE-BENCH-CANARY-v0.1-4f9e8a7c` is embedded in every case.
- **Errata:** logged in `CHANGELOG.md`.
