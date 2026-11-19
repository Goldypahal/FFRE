# Changelog

All notable changes to the FFIRE / FFIRE-Bench project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - November 2026

### ⚠️ Credibility & Integrity Corrections
- **Fixed Hard-Coded Benchmark PASS Verdicts (Issue B1)**:
  - Corrected `scripts/evaluate_held_out_100_cases.py` which previously emitted static `**PASS**` strings across all metric rows regardless of value.
  - Introduced dynamic threshold evaluation using `configs/targets.yaml`.
  - Added unit test suite `tests/test_report_status_logic.py` enforcing that metric violations (e.g., False-Positive Rate 17.78% vs < 5.0% target, Brier Score 0.1589 vs < 0.10, and KYC escalation 0.0% vs 100%) correctly evaluate to `FAIL`.
  - Regenerated `data/benchmarks/held_out_100_evaluation_report.md` and `.json`. The true status of the held-out 100 corpus is honestly reported as **FAIL (6/10 Targets Met, 4 Violations)**.

### Added
- **FFIRE-Bench Initiative Launched**:
  - Implemented the 3–10 month FFIRE-Bench plan: transitioning from self-reported saturated runs to an independent, vendor-neutral financial investigation verification benchmark.
  - Created `CHARTER.md` and `GOVERNANCE.md` establishing open governance, vendor neutrality, advisory board structure, and licensing terms (CC-BY-4.0 for datasets, Apache-2.0 / MIT for code).
  - Published comprehensive prior-art review in `docs/related_work.md` covering AMLSim, SAML-D, Elliptic++, FEVER, SciFact, RAGTruth, FActScore, FinanceBench, and FinQA.
  - Published 20+ page equivalent annotation guidelines with worked examples for error taxonomy E1–E12 in `docs/annotation_guidelines.md`.
  - Released core Python package `ffire_bench` (`pip install -e .`):
    - `ffire_bench.schema`: Pydantic v2 case & result schema models supporting tracks T1–T6.
    - `ffire_bench.generators`: Typology generator for 8 distinct typologies with deterministic seeds, provenance tracking, and canary embedding (`FFIRE-BENCH-CANARY-v0.1-4f9e8a7c`).
    - `ffire_bench.narratives`: Multi-family narrative generators and controlled error injector with character-level span tracking and severity grading.
    - `ffire_bench.scoring`: Macro-F1, citation F1, cost-weighted scoring (10x penalty for false negative fraud), selective risk-coverage AUC (abstention), 15-bin ECE calibration, and cluster-aware bootstrap 95% confidence intervals.
    - `ffire_bench.runners`: Standardized baseline adapters for trivial baselines, rule-based heuristics, LLM prompt runner, and FFIRE Verifier.
    - `ffire_bench.leaderboard`: Static leaderboard and slice analysis generator.
    - `ffire_bench.cli`: Complete CLI (`ffire-bench eval`, `ffire-bench generate`, `ffire-bench benchmark`, `ffire-bench leaderboard`).
  - Added 20 gold-standard expert-curated evaluation cases in `data/gold_standard_20_cases.json`.
  - Added technical report draft `docs/technical_report_v0.1.md` and dataset datasheet `docs/DATASHEET.md`.

### Security & Hygiene
- **Secrets Audit (Issue B6)**:
  - Audited `k8s/secrets.yaml` and `.env*` files; verified all committed values are sanitised placeholders (`REPLACE_WITH_...`). Documented rotation and management protocols in `docs/SECRETS_AUDIT.md`.
  - Archived one-off inspect and scratch files into `archive/scratch/`.
