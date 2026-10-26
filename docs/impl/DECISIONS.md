---

## T1.3: Bi-Directional PII Redaction Tokenizer & Prompt Privacy Protection
- **Date & Task**: 2026-10-22, Task T1.3
- **Decision**:
  1. Implemented `PIITokenizer` class in `backend/security.py`:
     - Explicit entity registration (`register_entity(value, entity_type)`) storing mappings in an internal bidirectional vault (`_token_to_value` and `_value_to_token`).
     - Supported entity types: `CUSTOMER_NAME`, `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `ACCOUNT_ID`, `IP_ADDRESS`, `DEVICE_ID`.
     - Regex-based automated entity detection for common PII formats (RFC emails, E.164 / US phone numbers, SSNs, Luhn-compatible credit card numbers, IPv4/IPv6 addresses).
     - Longest-match precedence: sorts candidate substrings by length descending before regex substitution to prevent partial-substring corruption (e.g. "Jonathan Doe" before "John").
     - Bi-directional translation: `redact_text(text)` substitutes sensitive values with surrogate tokens like `<CUSTOMER_NAME_1>`, `<ACCOUNT_ID_1>`; `rehydrate_text(text)` and `rehydrate_data(obj)` cleanly restore original values.
     - Serializable vault persistence: `export_vault()` and `import_vault(data)` allow vault transfer across checkpoints and workflow states.
  2. Integrated `PIITokenizer` into LangGraph reasoning loop (`backend/graph.py`):
     - Added `pii_vault: Optional[Dict[str, str]] = None` to `AgentState` schema.
     - In `risk_reasoning_node`, `critic_node`, and `report_generator_node`: registered all extracted customer names, account IDs, merchant identifiers, IPs, and device fingerprints into the active tokenizer before calling `llm.invoke()`.
     - Zero plaintext PII reaches external/internal LLM gateways: prompts are strictly redacted with surrogate tokens before model invocation.
     - LLM responses are rehydrated so downstream reports, logs, and human-facing explanations preserve true entity names accurately.
  3. Created automated test suite `backend/tests/test_pii_tokenizer.py` covering explicit and pattern redaction, longest-match precedence, vault export/restoration, and mock LLM prompt redaction verification (4/4 PASS).
- **Rationale**: Financial compliance (GLBA, GDPR, PCI-DSS) strictly prohibits sending customer names, account numbers, SSNs, and card numbers in plaintext to cloud or third-party AI models. A reversible surrogate tokenizer guarantees zero PII leaks to model gateways while preserving complete syntactic structure and context for fraud reasoning.
- **Alternatives Considered & Rejected**:
  - *One-way hashing (SHA-256)*: Rejected because hashed values look like random hex strings to language models and cannot be rehydrated back into readable compliance dossiers for human analysts.
  ## T2.1: Comprehensive Open Benchmark Package & Performance Runner
- **Date & Task**: 2026-10-23, Task T2.1
- **Decision**:
  1. Created standalone, self-contained benchmark suite in `benchmarks/` package:
     - Synthetic data generator (`benchmarks/generators/synthetic_data.py`): seeded deterministic RNG generator producing 6 real-world fraud archetypes (`BENIGN`, `HIGH_VELOCITY_BURST`, `GEOGRAPHIC_IMPOSSIBILITY`, `AMOUNT_ANOMALY`, `NEW_DEVICE_ATO`, `STRUCTURING_SMURFING`), with relational DB seeding and CSV/JSON export.
     - Reproducible manifests (`benchmarks/manifests/`): `standard_load.json`, `stress_load.json`, `soak_load.json` defining concurrency tiers [1, 5, 10, 20], trial counts, transaction volumes, and performance SLAs.
     - Metric report generator (`benchmarks/runners/report_generator.py`): calculates exact percentiles (p50, p90, p95, p99), min, max, throughput ops/sec, error rates, and generates cross-platform Markdown tables and structured JSON outputs.
     - LangGraph engine runner (`benchmarks/runners/engine_benchmark.py`): concurrency testing directly across compiled LangGraph workflows using `ThreadSafeMemorySaver` and `NullProvider`.
     - Full-stack API runner (`benchmarks/runners/api_benchmark.py`): tests FastAPI HTTP endpoints (`/api/v1/investigations`) using Starlette TestClient with tenant isolation.
     - Checkpoint safety auditor (`benchmarks/runners/checkpoint_safety.py`): verifies thread isolation, state non-leakage, lineage monotonicity, and state corruption detection.
     - CLI runner (`benchmarks/cli.py`): supports `--manifest`, `--mode`, `--tiers`, `--smoke`, and `--seed`.
  2. Added `ThreadSafeMemorySaver` to `backend/checkpointing.py` for thread-safe in-memory state persistence during concurrent benchmark trials.
  3. Added column fallbacks to `backend/database.py` to ensure schema stability across legacy SQLite databases.
  4. Created automated test suite `backend/tests/test_benchmarks_package.py` covering synthetic generation, file exports, manifest schema validation, percentile math, checkpoint auditor safety, and smoke benchmark runs (6/6 PASS).
- **Rationale**: An enterprise fraud investigation engine requires rigorous, open, repeatable performance and concurrency benchmarks. Standardized load manifests and deterministic synthetic generators enable continuous SLA verification without depending on proprietary datasets or cloud resources.
- **Alternatives Considered & Rejected**:
  ---

## T2.2: Deterministic Claim-Mutation Verifier Suite & Grounding Hardening
- **Date & Task**: 2026-10-23, Task T2.2
- **Decision**:
  1. Enhanced `extract_and_verify_claims` in `backend/guardrails.py`:
     - Numerical verification: strict floating-point tolerance of `1e-4` (0.0001) to reliably catch 1-cent tampering ($425.50 vs $425.51), 10x scaling, and arbitrary amounts.
     - Device & OS conflict verification: direct OS token recognition ("Android", "iOS", "Windows", "Linux", "MacOS") without requiring literal "OS" keyword; flags conflicting OS against evidence device, flags unknown OS when evidence OS is known, and flags fabricated "new device" claims when evidence indicates existing device.
     - Merchant & high-risk category detection: broadly inspects vendor names and categories ("crypto", "gambling", "darknet", "firearms", "wire transfer", "highrisk electronics", "apex crypto", "offshore exchange") and flags them if absent from evidence corpus.
     - Velocity burst verification: asserts that rapid burst / smurfing claims are grounded only when `high_velocity_flag` is True.
     - Precedence & isolation: preserves specific failure reasons and lowest calibrated confidence scores (<= 0.25) across pipeline stages, preventing generic fallback rules from overwriting detailed entity conflict diagnostics.
  2. Implemented comprehensive test suite in `backend/tests/test_claim_mutation.py`:
     - `test_amount_mutation_rejection`: 1-cent tampering, 10x scaling, large arbitrary amounts, exact float matching.
     - `test_merchant_and_category_mutation_rejection`: fabricated high-risk categories (crypto, gambling, darknet).
     - `test_location_and_jurisdiction_mutation_rejection`: offshore/Zurich, sanctioned countries (Russia), missing location evidence.
     - `test_customer_identity_mutation_rejection`: conflicting customer names (Bob Jones, John Doe) and adversary claims.
     - `test_device_and_os_mutation_rejection`: conflicting OS (Android vs iOS), unknown OS, fabricated new device.
     - `test_velocity_and_temporal_mutation_rejection`: fabricated velocity spikes and smurfing claims.
     - `test_adversarial_hallucination_and_fabrication_rejection`: explicit hallucinated markers and external typology fabrications.
     - `test_metamorphic_mutation_monotonicity`: proves metamorphic property that mutating any grounded attribute strictly decreases confidence and flips supported to False, and reverting immediately restores validity.
     - `test_boundary_conditions_and_multi_sentence_isolation`: tests empty drafts, null bundles, and multi-sentence isolation.
  3. All 9 tests in `test_claim_mutation.py` and 4 tests in `test_grounding_guardrails_structured.py` pass 100% in under 0.15s.
---

## T2.3: Scenario Suite (Production & Chaos Hardening)
- **Date & Task**: 2026-10-23, Task T2.3
- **Decision**:
  1. Implemented dedicated operational chaos and scenario suite in `backend/tests/test_workbook_scenarios.py`:
     - Scenario 1 (Network partition / degraded evidence): simulated network connection drop/partition during DB retrieval; verified fail-closed contract returning `evidence_status: UNAVAILABLE`, halting auto-close, escalating to human review with clean session closure (Finding V4).
     - Scenario 2 (Corrupted checkpointer recovery): simulated malformed/unparseable checkpoint records; verified `CheckpointSafetyAuditor` flags corrupted threads, isolates uncorrupted thread lineages, and avoids crash propagation across concurrent executions.
     - Scenario 3 (Worker retry exhaustion & DLQ routing): simulated persistent downstream worker execution failure; verified worker transitions through `RETRYING` up to `MAX_JOB_RETRIES` (3), marks investigation `FAILED`, creates `models.DeadLetterJob` with failure reason, logs `models.AuditLog` action `DEAD_LETTER_QUEUE`, and updates queue telemetry.
     - Scenario 4 (Multi-tenant collision defense under contention): verified two distinct tenants submitting investigations with identical idempotency keys run in complete isolation with distinct investigation IDs, and negative isolation returns HTTP 403/404 when attempting cross-tenant retrieval (Finding V5).
     - Scenario 5 (Mixed-integrity batch ingestion): verified batch ingestion of 8 mixed transactions (3 valid, 4 quarantined for non-positive amounts, invalid currency, bad channel, non-existent account, and 1 duplicate) returns exact accounting `{ total_records: 8, ingested: 3, quarantined: 4, skipped_duplicates: 1 }` without rolling back valid rows (Finding V8).
     - Scenario 6 (Hostile idempotency payload alteration): verified that replaying an existing idempotency key with modified transaction payload returns HTTP 409 Conflict with `"Idempotency key reused with different payload"` without mutating the original investigation record (Finding V2).
     - Scenario 7 (Unscored investigation null-score immutability): verified that an unscored investigation transitioning across lifecycle states (`QUEUED` -> `ESCALATED` -> `WAITING_HUMAN`) immutably preserves `risk_score: null` without fabricating dummy scores like 0.85 or 0.50 (Finding V3).
  2. All 7 scenarios pass 100% in 5.29s; combined Phase 2 test suite (26 tests) passes in 6.01s.
---

## T2.4: AI Observability & Privacy-Preserving Prometheus Telemetry
- **Date & Task**: 2026-10-23, Task T2.4
- **Decision**:
  1. Enhanced `backend/metrics.py::MetricsCollector`:
     - Label sanitization: sanitized `node_name`, `model`, and `tenant_id` to strictly alphanumeric, hyphen, and underscore tokens (`[^a-zA-Z0-9_\-]`), neutralizing metric injection attacks and ensuring RFC-compliant Prometheus exposition syntax.
     - PII protection in telemetry: stripped control characters and prevented raw customer names, emails, card numbers, or SSNs from being accepted into metric labels or recent invocation records.
     - Multi-tenant attribution: partitioned token usage (`_tokens_by_tenant`) and costs (`_cost_by_tenant`) with granular prompt and completion token accounting.
  2. Enhanced `backend/main.py::get_prometheus_metrics`:
     - Added tenant-level metrics export: `ffre_llm_tenant_cost_usd_total{tenant_id="..."}` with sanitized tenant labels.
     - Standard Prometheus metrics suite: `ffre_investigation_duration_seconds`, `ffre_investigations_total`, `ffre_llm_tokens_total`, `ffre_llm_cost_usd_total`, `ffre_llm_calls_total`, `ffre_llm_call_duration_seconds`, `ffre_llm_model_tokens_total`, `ffre_llm_node_tokens_total`.
  3. Extended test suite in `backend/tests/test_ai_observability.py`:
     - `test_privacy_preserving_metrics_no_pii`: verified zero email addresses, SSNs, credit cards, or customer names appear anywhere in `/metrics` text or `/api/v1/metrics/ai-cost` JSON.
     - `test_tenant_prometheus_metrics_attribution`: verified multi-tenant Prometheus metrics partition accurately by tenant.
     - `test_prometheus_metric_label_sanitization_defense`: verified injection attempts (quotes, newlines, semicolons) are stripped and cannot corrupt the Prometheus parser.
  4. All 8 tests in `test_ai_observability.py` pass 100% in 0.19s.
- **Rationale**: Production observability must deliver actionable cost intelligence and latency metrics without compromising customer privacy or violating regulatory standards (GDPR, PCI-DSS, GLBA). Metric label sanitization prevents malicious callers from manipulating telemetry buffers.
- **Alternatives Considered & Rejected**:
  - *Embedding transaction IDs or raw prompt snippets in Prometheus labels*: Rejected because high-cardinality metric labels cause memory bloat in Prometheus servers and risk leaking sensitive PII.

---

## T3.1: Immutable Replay Snapshots & Cryptographic Audit Verification
- **Date & Task**: 2026-10-23, Task T3.1
- **Decision**:
  1. Enhanced `models.AuditLog` with cryptographic hash chain integrity and auto-chaining:
     - Implemented `AuditLog.verify_chain(cls, logs)`: verifies chain continuity (`previous_hash` of each block matches `entry_hash` of predecessor) and recalculates SHA-256 entry hashes against stored hashes across both model instances and deserialized JSON dictionaries.
     - Added SQLAlchemy `@event.listens_for(AuditLog, 'before_insert')` hook: automatically queries previous entry hash for the investigation, establishes the chain link, and computes `entry_hash` dynamically, while preserving explicit hashes set by test fixtures.
  2. Implemented replay export endpoint `POST` & `GET /api/v1/investigations/{investigation_id}/export-replay`:
     - Builds canonical JSON snapshot bundle containing investigation attributes, transaction details, evidence vault records, and chronologically ordered audit logs.
     - Verifies cryptographic audit chain validity at export time.
     - Computes deterministic SHA-256 `replay_fingerprint` across canonical sorted JSON (`separators=(',', ':')`, `sort_keys=True`).
     - Returns snapshot with HTTP header `X-Replay-Fingerprint` and response model `ReplaySnapshotResponse`.
  3. Implemented replay verification endpoint `POST /api/v1/investigations/{investigation_id}/verify-replay`:
     - Enforces strict multi-tenant authorization (cross-tenant verification attempts raise HTTP 403).
     - Verifies snapshot fingerprint integrity by recalculating SHA-256 over canonical snapshot content; flags tampering if mismatched.
     - Verifies audit log cryptographic chain integrity via `AuditLog.verify_chain`; flags broken links or altered actions/details.
     - Verifies snapshot data fidelity against active database state (transaction ID, risk score float precision within 1e-4, status).
     - Returns `ReplayVerifyResponse` detailing validity, detected tampering reasons, and audit chain status.
  4. Implemented audit chain inspection endpoint `GET /api/v1/investigations/{investigation_id}/audit-chain`:
     - Returns full chronological audit trail with validation status, chain length, and individual entry hash metadata.
  5. Implemented comprehensive test suite in `backend/tests/test_replay_snapshots.py`:
     - `test_audit_log_verify_chain_unit`: verifies detection of broken links, tampered details, and invalid genesis.
     - `test_replay_snapshot_export_and_fingerprint`: verifies canonical fingerprint recalculation and header parity.
     - `test_replay_snapshot_verify_unadulterated_success`: verifies clean verification pass.
     - `test_replay_snapshot_verify_fingerprint_tampering`: detects payload alterations without updated fingerprint.
     - `test_replay_snapshot_verify_database_mismatch`: detects mutated risk score even when internal snapshot fingerprint is regenerated.
     - `test_replay_snapshot_verify_audit_log_tampering`: detects audit log tampering in regenerated snapshot.
     - `test_replay_snapshot_cross_tenant_isolation`: negative test proving Tenant Beta cannot export or verify Tenant Alpha's snapshots (403 Forbidden).
     - `test_audit_chain_endpoint`: verifies audit chain route returns intact chain with valid linkage.
  6. All 8 tests pass 100% in 0.81s; combined regression subset (52 tests) passes in 13.34s.
- **Rationale**: Regulatory compliance (SOX, GLBA, GDPR Article 30) and forensic financial crime investigations require non-repudiable, tamper-evident records. Exportable canonical replay snapshots with SHA-256 fingerprinting allow external compliance auditors to verify investigation authenticity offline without giving them access to live production databases.
- **Alternatives Considered & Rejected**:
  - *Exporting raw database dumps*: Rejected because raw DB dumps contain multi-tenant data, internal primary key identifiers, and unredacted system internals.
  - *Relying only on database-level timestamps without hash chaining*: Rejected because timestamps in mutable SQL tables can be modified by database administrators; cryptographic hash chains provide immutable proof of chronological ordering.---

## T0.9: Comprehensive README & Documentation Sync (Finding V10)
- **Date & Task**: 2026-10-22, Task T0.9
- **Decision**:
  1. Created a comprehensive root `README.md` documenting:
     - Multi-agent LangGraph workflow architecture and subsystem topology.
     - Zero-trust security and multi-tenancy model (tenant composite keys, AES-256-GCM authenticated encryption, HMAC-SHA256 blind indexing, fail-closed Redis JTI token revocation, immutable SHA-256 audit log chaining).
     - Fail-closed evidence retrieval and structured claim grounding model.
     - Clean clone and quickstart instructions for Python backend, React frontend, and Docker Compose.
     - Complete test suite invocation guide, environment configuration reference, and API endpoint catalog.
  2. Synchronized `docs/FFIRE_GAP_REGISTER.md` by recording Workbook Hardening Findings (V1–V10) as GAP-020 through GAP-027, mapping their root causes, severity, automated test validations, and resolution commits.
  3. Synchronized `docs/WALKTHROUGH.md` with cross-references to the root README, audit walkthrough, gap register, disaster recovery runbook, and hardening implementation logs.
- **Rationale**: A repository without an accurate, comprehensive root README and synchronized documentation increases operational friction, obscures architectural security controls, and impedes automated evaluation and clean-clone onboarding.
- **Alternatives Considered & Rejected**:
  - *Keeping documentation fragmented across scattered notes*: Rejected because enterprise auditability requires a single source of truth at the repository root with synchronized sub-documentation.

---

## T1.1: Pluggable Model Gateway & Offline Mode (Finding V7)
- **Date & Task**: 2026-10-22, Task T1.1
- **Decision**:
  1. Implemented `backend/llm_gateway.py` with standard `LLMResponse` and `BaseLLMProvider` abstractions, supporting `openai`, `anthropic`, `ollama`, `null`, and `mock` backends.
  2. Created `NullProvider`: a deterministic, zero-cost, offline provider that inspects prompt context (Planner, Reasoner, Critic, Reporter) and generates valid structured JSON schemas and markdown reports without network calls or external API keys.
  3. Created `MockProvider`: extends `NullProvider` with canned response injection, default response override, and invocation history tracking for unit and integration testing.
  4. Updated `backend/metrics.py` to add zero-cost pricing for `null`, `null-deterministic-v1`, `mock`, `mock-v1`, and `ollama` models so offline runs calculate accurately to $0.00.
  5. Refactored `backend/graph.py` to query `llm_gateway` instead of hardcoding `ChatOpenAI(model="gpt-4o-mini")`, and dynamically record model names via `getattr(llm, "model_name", "gpt-4o-mini")`.
  6. Documented `LLM_PROVIDER` and `LLM_MODEL` in `.env.example` and `backend/.env.example`.
  7. Created automated test suite `backend/tests/test_pluggable_model_gateway.py` asserting planner JSON lists, reasoner risk scores, critic schemas, canned mock responses, environment resolution, and end-to-end LangGraph execution in pure offline mode (6/6 PASS).
- **Rationale**: Relying on external third-party LLM APIs with hardcoded model strings introduces significant latency, operational cost, non-determinism, and network failure points during testing and evaluation. A pluggable model gateway allows the entire reasoning engine to operate air-gapped with zero external dependencies.
- **Alternatives Considered & Rejected**:
  - *Mocking with pytest `unittest.mock.patch` only in test files*: Rejected because production and air-gapped on-premise environments also require an offline rule-backed mode without touching test fixtures or mutating Python bytecode.

---

## T1.2: Transaction Ingestion Connector & CSV Import (Finding V8)
- **Date & Task**: 2026-10-22, Task T1.2
- **Decision**:
  1. Extended `models.Transaction` with key transactional context columns: `counterparty` (String(255)), `channel` (String(50)), `ip_address` (String(45)), `device_ref` (String(100)), and enforced a non-nullable default for `currency = Column(String(10), nullable=False, default="USD")`.
  2. Implemented reversible Alembic migration `89a1b2c3d4e5_add_transaction_ingestion_columns.py` and added SQLite ALTER TABLE fallback in `database.py::init_db()`.
  3. Implemented batch ingestion endpoint `POST /api/v1/transactions/ingest` in `backend/main.py`:
     - Content-Type agnostic: seamlessly handles `application/json` (arrays or objects with `transactions`), `multipart/form-data` (file uploads), and raw `text/csv` payloads.
     - Full ingestion accounting returning `{ "total_records": N, "ingested": M, "quarantined": Q, "skipped_duplicates": S, "quarantine_reasons": [...] }`.
     - Strict data hygiene and quarantine validation: rejects non-positive amounts, invalid channels, malformed non-ISO timestamps, missing/non-existent accounts, and invalid currency codes without crashing the batch.
     - Strict tenant scoping: prevents cross-tenant ingestion into accounts belonging to other tenants.
     - Idempotency: duplicate transactions matching existing `(tenant_id, txn_id)` are counted as `skipped_duplicates` without creating duplicate records or causing SQL integrity errors.
  4. Added companion retrieval endpoints: `GET /api/v1/transactions` and `GET /api/v1/transactions/{txn_id}` with tenant-scoped filtering.
  5. Implemented comprehensive test suite in `backend/tests/test_transaction_ingestion.py` covering JSON batch ingestion, quarantine accounting, idempotency skipping, CSV uploads (multipart and raw), and cross-tenant isolation (5/5 PASS).
- **Rationale**: Real-world fraud detection pipelines ingest transactions via batch streams and file exports. Providing a unified JSON/CSV ingestion connector with robust quarantine accounting and multi-tenant safety prevents bad inputs from crashing ingestion workers.
- **Alternatives Considered & Rejected**:
  - *Failing the entire batch on first invalid record*: Rejected because enterprise batch pipelines must isolate corrupted records into quarantine and commit valid records to maintain system throughput.

---

## T1.3: Bi-Directional PII Redaction Tokenizer & Prompt Privacy Protection
- **Date & Task**: 2026-10-22, Task T1.3
- **Decision**:
  1. Implemented `PIITokenizer` class in `backend/security.py`:
     - Explicit entity registration (`register_entity(value, entity_type)`) storing mappings in an internal bidirectional vault (`_token_to_value` and `_value_to_token`).
     - Supported entity types: `CUSTOMER_NAME`, `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `ACCOUNT_ID`, `IP_ADDRESS`, `DEVICE_ID`.
     - Regex-based automated entity detection for common PII formats (RFC emails, E.164 / US phone numbers, SSNs, Luhn-compatible credit card numbers, IPv4/IPv6 addresses).
     - Longest-match precedence: sorts candidate substrings by length descending before regex substitution to prevent partial-substring corruption (e.g. "Jonathan Doe" before "John").
     - Bi-directional translation: `redact_text(text)` substitutes sensitive values with surrogate tokens like `<CUSTOMER_NAME_1>`, `<ACCOUNT_ID_1>`; `rehydrate_text(text)` and `rehydrate_data(obj)` cleanly restore original values.
     - Serializable vault persistence: `export_vault()` and `import_vault(data)` allow vault transfer across checkpoints and workflow states.
  2. Integrated `PIITokenizer` into LangGraph reasoning loop (`backend/graph.py`):
     - Added `pii_vault: Optional[Dict[str, str]] = None` to `AgentState` schema.
     - In `risk_reasoning_node`, `critic_node`, and `report_generator_node`: registered all extracted customer names, account IDs, merchant identifiers, IPs, and device fingerprints into the active tokenizer before calling `llm.invoke()`.
     - Zero plaintext PII reaches external/internal LLM gateways: prompts are strictly redacted with surrogate tokens before model invocation.
     - LLM responses are rehydrated so downstream reports, logs, and human-facing explanations preserve true entity names accurately.
  3. Created automated test suite `backend/tests/test_pii_tokenizer.py` covering explicit and pattern redaction, longest-match precedence, vault export/restoration, and mock LLM prompt redaction verification (4/4 PASS).
- **Rationale**: Financial compliance (GLBA, GDPR, PCI-DSS) strictly prohibits sending customer names, account numbers, SSNs, and card numbers in plaintext to cloud or third-party AI models. A reversible surrogate tokenizer guarantees zero PII leaks to model gateways while preserving complete syntactic structure and context for fraud reasoning.
- **Alternatives Considered & Rejected**:
  - *One-way hashing (SHA-256)*: Rejected because hashed values look like random hex strings to language models and cannot be rehydrated back into readable compliance dossiers for human analysts.
  - *Generic static masking (e.g., "[REDACTED]")*: Rejected because multiple distinct entities would collide into "[REDACTED]", destroying relational reasoning (e.g., distinguishing between sender account vs receiver account).# Architecture & Implementation Decisions

This document logs all key decisions made during autonomous execution of the FFIRE workbook hardening and open benchmark program.
Each entry records:
- **Date & Task**: Task ID and timestamp
- **Decision**: What was decided
- **Rationale**: Why this choice was selected
- **Alternatives Considered & Rejected**: What alternatives were evaluated and why they were not chosen

---

## Initial State
- **Date**: 2026-10-22
- **Branch**: `impl/workbook-hardening`
- **Baseline Commit**: `3616fd726a9c1c1eb34720738638621a78ea9f26` (HEAD of v1.0.0-rc1)

---

## T0.2: Remove Mock-Data Creation (Finding V1)
- **Date & Task**: 2026-10-22, Task T0.2
- **Decision**: Removed the automatic synthetic entity generation block in `backend/main.py::create_investigation` (which previously auto-created "Alex Johnson (Demo)", "HighRisk Electronics", and a $4250.00 transaction on any missing transaction ID). Submitting an unknown or other-tenant transaction ID now strictly raises HTTP 404 with generic detail `"Transaction not found"`. Added `scripts/seed_demo_data.py` to provide explicit, opt-in synthetic fixtures for tests, docs, and benchmarks.
- **Rationale**: Silently fabricating production records on a typo or missing transaction ID violates data integrity, leaks un-scoped demo records into tenant databases, and allows callers to run investigations on fabricated entities. Returning a generic 404 prevents existence enumeration attacks across tenants.
- **Alternatives Considered & Rejected**:
  - *Auto-creating records only when a demo flag is passed*: Rejected because production endpoints must never create transactions on the fly; ingestion must be explicit.
  - *Returning 400 Bad Request*: Rejected because 404 Not Found is the REST standard when the referenced resource (`transaction_id`) does not exist in the caller's scope.
