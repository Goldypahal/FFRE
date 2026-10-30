# Financial Fraud Investigation Reasoning Engine (FFIRE)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent%20DAG-orange)](https://github.com/langchain-ai/langgraph)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6.svg)](https://www.typescriptlang.org/)

> **"Every claim, checked. Every case, replayable."**  
> FFIRE is the independent, verifiable trust layer for AI-written fraud investigations and regulatory AML compliance.

---

## The Independent Trust Layer for AI Investigations

Under Federal Reserve & OCC Model Risk Guidance (**SR 11-7 / SR 26-2**) and the EU AI Act, financial institutions cannot rely on AI vendors' self-attested confidence scores. Banks are legally required to independently validate and reproduce automated model conclusions.

FFIRE solves this by acting as a **vendor-neutral verification and investigation engine**:
1. **Universal Verifier Sidecar API**: Decomposes any AI narrative (from Hawk, Oracle, in-house LLMs, or custom agents) into atomic factual assertions, scoring evidence support, detecting contradictions, and issuing cryptographically signed verification attestations.
2. **Cryptographically Sealed Replay Bundles**: Every case produces a portable, tamper-evident bundle with SHA-256 hash-chained audit trails that bank risk examiners and validators can re-run offline using `scripts/replay_cli.py`.
3. **Institutional Model Risk Validation Kit**: Auto-generates formal SR 26-2 documentation packs (`scripts/generate_model_validation_kit.py`), including conceptual soundness, challenger benchmarks, ECE/Brier scores, and operational failure boundaries.
4. **Zero-Trust Hardened Architecture**: Enforces administrative invite controls on registration, role enum validation, explicit origin CORS protection, bit-level SHA-256 model supply-chain integrity checks, and BSA 5-year soft-delete retention with regulatory legal holds.

> [!IMPORTANT]
> ### System Scope & Operational Boundary (SRS Alignment)
> - **In Scope**: Post-transaction fraud reasoning, multi-agent LangGraph analysis, universal claim-grounding verification sidecar, SHA-256 audit chaining, offline replay verification CLI, and FinCEN SAR audit dossier preparation with human review.
> - **Out of Scope**: Real-time inline payment switch blocking (FFIRE operates as an advisory post-transaction intelligence engine); direct autonomous electronic filing with FinCEN without human compliance officer authorization.

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Key Enterprise Differentiators](#key-enterprise-differentiators)
- [Zero-Trust Security & Multi-Tenancy](#zero-trust-security--multi-tenancy)
- [Evidence Model & Grounding Guardrails](#evidence-model--grounding-guardrails)
- [Repository Structure](#repository-structure)
- [Quickstart Guide](#quickstart-guide)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Full-Stack with Docker Compose](#full-stack-with-docker-compose)
- [Running Tests & Verification](#running-tests--verification)
- [Configuration Reference](#configuration-reference)
- [API Endpoints Overview](#api-endpoints-overview)
- [Compliance & Traceability](#compliance--traceability)
- [License](#license)

---

## Architectural Overview

```
                      +---------------------------------------+
                      |       React 19 / Vite Frontend        |
                      |   (Apple Human Interface Guidelines)  |
                      +-------------------+-------------------+
                                          | REST / SSE
                                          v
                      +---------------------------------------+
                      |         FastAPI Gateway Layer         |
                      |  - Multi-Tenant JWT & Invite Auth     |
                      |  - Explicit Origin CORS Allowlist     |
                      |  - Distributed Redis Rate Limiting    |
                      |  - Universal Verifier Sidecar API     |
                      |  - Regulatory Legal Hold & Retention  |
                      +-------------------+-------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
+-------------------------------+                 +-------------------------------+
|     Background Task Worker    |                 |  LangGraph Investigation DAG  |
|  - Redis Streams Queue        |                 |  - Planner                    |
|  - Dead Letter Queue (DLQ)    |                 |  - Parallel Retrieval Nodes   |
|  - Exponential Backoff Retry  |                 |  - Multi-Window Velocity      |
+---------------+---------------+                 |  - Rule Engine                |
                |                                 |  - Vector Case Lookup         |
                |                                 |  - Calibrated LightGBM GBDT   |
                |                                 |  - Evidence Critic Agent      |
                |                                 |  - Grounding Guardrails       |
                |                                 +---------------+---------------+
                |                                                 |
                +------------------------+------------------------+
                                         |
                                         v
  +--------------------+   +---------------------+   +--------------------+
  |   PostgreSQL 15    |   |      ChromaDB       |   |      Redis 7       |
  |  - Schema Models   |   |  - Tenant-Isolated  |   |  - Task Broker     |
  |  - Checkpoints     |   |    Vector Store     |   |  - Token Blocklist |
  |  - SHA-256 Audit   |   |  - Historical Case  |   |  - Rate Limits     |
  |    Chaining        |   |    Embeddings       |   |                    |
  +--------------------+   +---------------------+   +--------------------+
```

---

## Key Enterprise Differentiators

### 1. Independent Verifier API (Sidecar)
Any upstream narrative—whether authored by Hawk, Oracle Investigation Hub, or custom LLMs—can be validated against raw transactional facts:
```bash
POST /api/v1/verifier/evaluate
```
Payload:
```json
{
  "narrative": "Transaction amount of 9500 was transferred via WIRE channel by account acc_corp_88.",
  "evidence": {
    "amount": 9500.0,
    "channel": "WIRE",
    "account_id": "acc_corp_88",
    "velocity_count_24h": 6
  },
  "vendor": "oracle"
}
```
Returns claim-level verdicts (`VERIFIED`, `CONTRADICTED`, `UNGROUNDED`), grounding score, and a cryptographic attestation digest.

### 2. Sealed Replay Bundles & Offline CLI
Validators and regulatory examiners can export sealed investigation packages and verify bit-level reproducibility offline without server credentials:
```bash
python scripts/replay_cli.py verify-bundle sample_replay_snapshot.json
```

### 3. Model Risk Management (MRM) Validation Pack
Auto-generate a complete, institutional SR 26-2 compliance pack for internal bank model risk committees:
```bash
python scripts/generate_model_validation_kit.py
```
Output: [docs/MODEL_RISK_VALIDATION_PACK.md](docs/MODEL_RISK_VALIDATION_PACK.md)

---

## Zero-Trust Security & Multi-Tenancy

- **Authenticated Admin Creation & Role Validation**: Public registration enforces unprivileged viewer/investigator roles and default tenant scoping. Administrative registration requires an authorized `ADMIN_INVITE_TOKEN`. All roles are validated against strict enum specifications.
- **Explicit Origin CORS**: Strict environment-configured origin allowlist (`ALLOWED_ORIGINS`) prevents browser credential leakage.
- **Model Supply-Chain Verification**: Serialized ML artifacts (`.joblib`) are verified against expected SHA-256 cryptographic digests in `backend/ml/model_store/registry_manifest.json` prior to deserialization.
- **Distributed Token Revocation**: Logged-out tokens are immediately committed to Redis blocklists (`POST /api/v1/auth/logout`), failing closed across all worker processes.
- **5-Year BSA Retention & Regulatory Legal Hold**: Investigations cannot be purged if an active regulatory inquiry or legal hold is applied (`POST /api/v1/investigations/{id}/legal-hold`). Approved deletions perform an auditable soft-delete with immutable tombstone audit logging.

---

## Quickstart Guide

### Backend Setup

1. **Activate virtual environment**:
   ```bash
   .\backend\.venv\Scripts\Activate.ps1   # Windows
   source backend/.venv/bin/activate     # Linux/macOS
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run the FastAPI development server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   npm install
   npm run build
   npm run dev
   ```

---

## Running Tests & Verification

FFIRE maintains a comprehensive automated test pyramid:

```bash
# Full backend test suite
pytest backend/tests -v

# Enterprise security & regression suite
pytest backend/tests/test_enterprise_security_fixes.py -v

# High availability and Kubernetes manifest tests
pytest backend/tests/test_kubernetes_manifests.py backend/tests/srs/test_srs_ha_deployment.py -v

# Tabular ML inference and autonomous investigator agent
pytest backend/tests/test_fraud_model_phase2.py backend/tests/test_investigation_agent_phase5.py -v
```

---

## API Endpoints Overview

| Method | Endpoint | Description | Tenant-Scoped |
|:---|:---|:---|:---:|
| `POST` | `/api/v1/auth/register` | Register user (admin requires `ADMIN_INVITE_TOKEN`) | Yes |
| `POST` | `/api/v1/auth/login` | Authenticate user and receive JWT access/refresh tokens | Yes |
| `POST` | `/api/v1/auth/logout` | Revoke active access token across distributed Redis cluster | Yes |
| `POST` | `/api/v1/verifier/evaluate` | **Independent Trust Layer Verifier**: Check LLM claims vs evidence | Yes |
| `GET` | `/api/v1/investigations` | List investigations (active cases, filters out soft-deleted) | Yes |
| `POST` | `/api/v1/investigations` | Ingest transaction and initiate multi-agent investigation | Yes |
| `GET` | `/api/v1/investigations/{id}` | Retrieve comprehensive investigation details & reasoning trace | Yes |
| `DELETE` | `/api/v1/investigations/{id}` | Soft-delete case (blocked under active legal hold) | Yes |
| `POST` | `/api/v1/investigations/{id}/legal-hold` | Apply or release regulatory legal hold | Yes |
| `GET`/`POST` | `/api/v1/investigations/{id}/export` | Export investigation as signed PDF or FinCEN SAR JSON | Yes |
| `GET`/`POST` | `/api/v1/investigations/{id}/export-replay` | Export cryptographically sealed case replay bundle | Yes |
| `POST` | `/api/v1/investigations/{id}/verify-replay` | Verify replay bundle against database audit record | Yes |
| `GET` | `/api/v1/evidence` | List digital vault evidence items with SHA-256 digests | Yes |
| `GET` | `/health` | Core system liveness and readiness probe | No |
| `GET` | `/metrics` | Prometheus metrics exposition (AI token usage, latency) | No |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
