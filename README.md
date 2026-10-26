# Financial Fraud Investigation Reasoning Engine (FFIRE)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent%20DAG-orange)](https://github.com/langchain-ai/langgraph)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org/)

**FFIRE** (Financial Fraud Investigation Reasoning Engine) is an enterprise-grade, explainable fraud investigation and decision-support platform designed for post-transaction risk analysis, multi-agent reasoning, evidence-backed dossier generation, and human-in-the-loop compliance review.

FFIRE orchestrates stateful, multi-agent directed acyclic graphs (DAGs) using **LangGraph**, backed by **FastAPI**, **PostgreSQL** (with native checkpointer persistence), **ChromaDB** for vector similarity search over historical fraud patterns, **Redis** for distributed task queues and token revocation, and an **Apple-style React/TypeScript** operations console.

> [!IMPORTANT]
> ### System Scope & Operational Boundary (SRS Alignment)
> - **In Scope (Current Release)**: Explainable fraud investigation and decision support; deterministic evidence retrieval and multi-window velocity aggregation; LangGraph multi-agent reasoning with critic and grounding guardrails; evidence-backed investigation dossiers with human-in-the-loop review routing; AES-256-GCM PII encryption at rest and SHA-256 audit hash chaining.
> - **Out of Scope (Current Release)**: Real-time inline payment blocking / autonomous transaction interdiction (FFRE operates as an advisory investigation platform, not an inline payment gateway switch); automated electronic direct regulatory submission/filing with FinCEN (FFRE generates structured SAR-ready audit dossiers for review and authorization by licensed human compliance officers).

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Zero-Trust Security & Multi-Tenancy](#zero-trust-security--multi-tenancy)
- [Evidence Model & Grounding Guardrails](#evidence-model--grounding-guardrails)
- [Repository Structure](#repository-structure)
- [Quickstart Guide](#quickstart-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Full-Stack with Docker Compose](#full-stack-with-docker-compose)
- [Running Tests & Verification](#running-tests--verification)
- [Configuration Reference](#configuration-reference)
- [API Endpoints Overview](#api-endpoints-overview)
- [Compliance & Traceability](#compliance--traceability)

---

## Architectural Overview

```
                      +---------------------------------------+
                      |       React 18 / Vite Frontend        |
                      |   (Apple Human Interface Guidelines)   |
                      +-------------------+-------------------+
                                          | REST / WebSockets
                                          v
                      +---------------------------------------+
                      |         FastAPI Gateway Layer         |
                      |  - Multi-Tenant JWT / MFA Auth        |
                      |  - Rate Limiting (SlowAPI)            |
                      |  - Distributed JTI Token Revocation   |
                      |  - Tenant-Scoped Request Validation   |
                      +-------------------+-------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
                v                                                   v
+-------------------------------+                   +-------------------------------+
|     Background Task Worker    |                   |  LangGraph Investigation DAG  |
|  - Redis Streams / Celery     |                   |  - Planner                    |
|  - Dead Letter Queue (DLQ)    |                   |  - Parallel Retrieval Nodes   |
|  - Exponential Backoff Retry  |                   |  - Multi-Window Velocity      |
+---------------+---------------+                   |  - Rule Engine                |
                |                                   |  - Vector Case Lookup         |
                |                                   |  - Risk Reasoning Agent       |
                |                                   |  - Evidence Critic Agent      |
                |                                   |  - Grounding Guardrail        |
                |                                   +---------------+---------------+
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v
  +--------------------+   +---------------------+   +--------------------+
  |   PostgreSQL 15    |   |      ChromaDB       |   |      Redis 7       |
  |  - Schema Models   |   |  - Tenant Isolated  |   |  - JTI Revocation  |
  |  - LangGraph State |   |    Vector Store     |   |  - Task Broker     |
  |  - Audit Log Hash  |   |  - Historical Case  |   |  - Rate Limits     |
  |    Chaining (SHA)  |   |    Embeddings       |   |                    |
  +--------------------+   +---------------------+   +--------------------+
```

The investigation engine operates as a multi-step LangGraph workflow:
1. **Planner Node**: Deconstructs the transaction context and assigns targeted extraction tasks.
2. **Parallel Retrieval Nodes**: Queries customer, transaction, merchant, device, and location stores with fail-closed bounds.
3. **Multi-Window Velocity Engine**: Analyzes transaction frequency and volume across 1-hour, 24-hour, and 7-day sliding windows.
4. **Deterministic Rule Engine**: Evaluates AML thresholds, velocity spikes, and high-risk geo-velocity violations.
5. **Vector Case Lookup**: Computes similarity against historical confirmed fraud typologies (scoped by `tenant_id`).
6. **Risk Reasoning Agent**: Evaluates gathered evidence, assigns calibrated risk scores and severity tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
7. **Evidence Critic Agent**: Audits generated claims against retrieved evidence to eliminate hallucinations.
8. **Grounding Guardrails**: Extracts verifiable claims and verifies field-level facts (amounts, devices, locations) before approving output.
9. **SAR / Report Compiler**: Assembles immutable, auditor-grade FinCEN-compliant Suspicious Activity Reports (SAR).

---

## Zero-Trust Security & Multi-Tenancy

FFIRE is engineered under strict zero-trust banking principles:

- **Complete Multi-Tenant Isolation**: Every database entity (`User`, `Customer`, `Transaction`, `Investigation`, `Device`, `Location`, `FraudCase`, `AuditLog`, `DeadLetterJob`) is scoped with a non-nullable `tenant_id`. Cross-tenant queries are blocked at both the ORM and vector search levels (`where={"tenant_id": tenant_id}`).
- **Tenant-Scoped Idempotency**: Investigations require a composite unique key: `(tenant_id, source_system, external_id)` or `(tenant_id, investigation_id)`. Re-submitting the same payload returns the existing investigation, preventing duplicate runs and race conditions across distributed workers.
- **Dual-Tier Authenticated Encryption**:
  - **AES-256-GCM** (Primary): All sensitive Customer and User PII (names, emails, phone numbers, device fingerprints) is encrypted using authenticated AES-256-GCM with dynamic key derivation and unique nonces.
  - **Fernet Fallback**: Backward-compatible transparent decryption for legacy AES-128-CBC records.
  - **Blind Indexing**: Constant-time O(1) searches on encrypted emails using HMAC-SHA256 (`email_hash`) without leaking plaintext in database query logs.
- **Immutable Cryptographic Audit Logging**: Every administrative action, investigation state change, and escalation is appended to `audit_log` with SHA-256 hash chaining (`current_hash = SHA256(prev_hash + record_data)`), creating a tamper-evident blockchain-style record.
- **Distributed Token Revocation**: JWT revocations are tracked in Redis via unique `jti` tokens. Under `STRICT_ENTERPRISE_MODE=true`, token verification fails closed with HTTP 503 if Redis is unreachable.
- **Fail-Fast Secret Hygiene**: No hardcoded production passwords or cryptographic keys in configuration or manifests. All secrets are sourced via environment variables (`.env`).

---

## Evidence Model & Grounding Guardrails

- **Fail-Closed Evidence Model**: Missing transactions, customers, or devices never synthesize mock data or silently assume defaults. Nodes populate an explicit `UNAVAILABLE` or `NOT_FOUND` structured evidence state and flag missing dependencies.
- **No Invented Risk Scores**: Investigations in progress maintain `risk_score = None`. Synthetic defaults (such as `0.0` or placeholder integers) are strictly disallowed until reasoning completes.
- **Structured Claim Verification**: Claims generated by reasoning agents are decomposed into structured records:
  ```json
  {
    "claim": "Customer initiated wire of $4500 from IP 192.168.1.5",
    "evidence_source": "transaction_record",
    "matched_entity": "TX-1002",
    "supported": true,
    "confidence": 0.95,
    "verification_reason": "Transaction amount 4500.0 matches evidence TX-1002 within tolerance."
  }
  ```
- **Factual Grounding & Rejection**:
  - Amount assertions must match evidence within numeric tolerance.
  - Customer names, locations, and device IDs are verified against retrieved records.
  - Unsupported claims receive calibrated confidence (`<= 0.25`) and are flagged for human analyst review.
- **Prompt Injection Defense**: Multi-layer sanitization against delimiter breakout attacks, markdown injection, and JSON attribute tampering on untrusted evidence inputs.

---

## Repository Structure

```
FFRE/
├── backend/                       # FastAPI application & reasoning engine
│   ├── alembic/                   # Database migration environment
│   │   └── versions/              # Migration scripts (tenant_id, blind index, etc.)
│   ├── tests/                     # Automated pytest test suites
│   │   ├── srs/                   # 174 SRS functional verification tests
│   │   ├── test_tenant_idempotency.py
│   │   ├── test_tenant_isolation_complete.py
│   │   ├── test_no_invented_scores.py
│   │   ├── test_fail_closed_retrieval.py
│   │   ├── test_grounding_guardrails_structured.py
│   │   ├── test_secret_hygiene.py
│   │   └── ...                    # Domain, auth, worker, security tests
│   ├── auth.py                    # JWT, MFA/TOTP, role permissions, revocation
│   ├── database.py                # SQLAlchemy engine, session lifecycle, pooling
│   ├── graph.py                   # LangGraph multi-agent DAG workflow
│   ├── guardrails.py              # Claim verification, prompt injection defense
│   ├── main.py                    # FastAPI routes, middleware, lifespan
│   ├── models.py                  # Declarative SQLAlchemy ORM models
│   ├── security.py                # AES-256-GCM encryption, blind indexing, hashing
│   ├── vector_db.py               # ChromaDB multi-tenant client proxy
│   └── worker.py                  # Redis worker daemon & dead-letter queue
├── frontend/                      # React 18 + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/            # Apple-style UI component library
│   │   ├── pages/                 # Investigations, Evidence, Reports, Admin, etc.
│   │   └── tests/                 # Vitest component & UI unit tests
│   ├── package.json
│   └── vite.config.ts
├── docs/                          # Architecture, gap register & runbooks
│   ├── impl/                      # Workbook hardening plan, state, & decisions
│   ├── FFIRE_GAP_REGISTER.md      # Master enterprise gap register
│   └── OPERATIONAL_RECOVERY_RUNBOOK.md # Disaster recovery & operations runbook
├── k8s/                           # Production Kubernetes manifests (HA, HPA, TLS)
├── scripts/                       # Operational & audit CLI utilities
│   ├── srs_audit_engine.py        # Independent SRS compliance audit engine
│   ├── seed_demo_data.py          # Deterministic demo data seeder
│   └── build_final_evidence_package.py # Deterministic packaging script
├── docker-compose.yml             # Local multi-service orchestration
├── .env.example                   # Master environment configuration template
└── README.md                      # Project documentation (this file)
```

---

## Quickstart Guide

### Prerequisites

- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: 18+ and **npm**: 9+
- **Docker & Docker Compose** (optional for local full-stack containerization)

---

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Goldypahal/FFRE.git
   cd FFRE
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv backend\.venv
   .\backend\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env to adjust database URL, keys, or use development defaults
   ```

5. **Initialize the database & seed demo data**:
   ```bash
   python scripts/seed_demo_data.py
   ```

6. **Run the FastAPI development server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

The backend API is now accessible at `http://localhost:8000`.  
Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the frontend test suite**:
   ```bash
   npm run test
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```

The frontend application is now accessible at `http://localhost:5173`.

---

### Full-Stack with Docker Compose

To launch the complete production-like topology (PostgreSQL, Redis, ChromaDB, FastAPI backend, background worker, and Nginx frontend):

```bash
docker compose up -d
```

Verify service health:
```bash
docker compose ps
curl http://localhost:8000/health
```

---

## Running Tests & Verification

FFIRE enforces a comprehensive automated test pyramid with zero mock dependencies in core assertions:

### Run Full Backend Test Suite
```bash
pytest backend/tests -v
```

### Run Hardening & Zero-Trust Test Suites
```bash
# T0.2 (V1): Mock-data removal & 404 enforcement on unknown transactions
pytest backend/tests/test_mock_data_removal.py -v

# T0.3 (V2): Tenant-scoped idempotency & fingerprinting collision safety
pytest backend/tests/test_tenant_idempotency.py -v

# T0.4 (V3): No invented risk scores prior to reasoning completion
pytest backend/tests/test_no_invented_scores.py -v

# T0.5 (V4): Fail-closed evidence retrieval & clean session lifecycle
pytest backend/tests/test_fail_closed_retrieval.py -v

# T0.6 (V5): Tenant isolation across all models & vector store
pytest backend/tests/test_tenant_isolation_complete.py -v

# T0.7 (V6): Calibrated structured claims & prompt injection defense
pytest backend/tests/test_grounding_guardrails_structured.py -v

# T0.8 (V9): Working tree secret & PII hygiene validation
pytest backend/tests/test_secret_hygiene.py -v
```

### Run SRS Compliance & Audit Traceability
```bash
python scripts/srs_audit_engine.py
```

### Run Frontend Unit Tests
```bash
cd frontend && npm run test
```

---

## Configuration Reference

Key configuration options defined in `.env.example`:

| Environment Variable | Default | Description |
|:---|:---|:---|
| `DATABASE_URL` | `sqlite:///./ffire.db` | SQLAlchemy connection string (PostgreSQL or SQLite). |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker and token revocation URL. |
| `SECRET_KEY` | *(dev fallback)* | Cryptographic key for signing JWT tokens. |
| `ENCRYPTION_SECRET_KEY` | *(dev fallback)* | AES-256-GCM 32-byte key for encrypting PII at rest. |
| `STRICT_ENTERPRISE_MODE` | `false` | When `true`, fail-closed if Redis or checkpointer is offline. |
| `OPENAI_API_KEY` | `""` | Optional key for external LLM inference. |
| `VECTOR_DB_DIR` | `./chroma_db` | Storage path for ChromaDB vector embeddings. |
| `DEFAULT_TENANT_ID` | `tenant-default` | Default tenant identifier for fallback routing. |
| `RATE_LIMIT_PER_MINUTE` | `100` | Global per-IP rate limit for API endpoints. |
| `LOG_LEVEL` | `INFO` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## API Endpoints Overview

| Method | Endpoint | Description | Tenant-Scoped |
|:---|:---|:---|:---:|
| `POST` | `/api/v1/auth/login` | Authenticate user and receive JWT access/refresh tokens | Yes |
| `POST` | `/api/v1/auth/refresh` | Refresh access token using rotating refresh token | Yes |
| `POST` | `/api/v1/auth/logout` | Revoke active token in Redis JTI blocklist | Yes |
| `GET` | `/api/v1/investigations` | List investigations with pagination and status filters | Yes |
| `POST` | `/api/v1/investigations` | Ingest transaction and create/retrieve investigation (idempotent) | Yes |
| `GET` | `/api/v1/investigations/{id}` | Retrieve comprehensive investigation details & reasoning trace | Yes |
| `POST` | `/api/v1/investigations/{id}/review` | Human analyst decision review (approve, escalate, dismiss) | Yes |
| `GET` | `/api/v1/investigations/{id}/export` | Export investigation as signed PDF or FinCEN SAR JSON | Yes |
| `GET` | `/api/v1/graph/{id}` | Inspect 12-node LangGraph execution topology and state | Yes |
| `GET` | `/api/v1/evidence` | List digital vault evidence items with cryptographic digests | Yes |
| `POST` | `/api/v1/evidence/upload` | Upload and hash-verify digital evidence file | Yes |
| `GET` | `/api/v1/analytics/summary` | Real-time risk aggregations, volume trends, and KPIs | Yes |
| `GET` | `/api/v1/admin/audit-logs` | Retrieve SHA-256 hash-chained immutable audit log | Yes |
| `GET` | `/api/v1/worker/health` | Redis worker status, in-flight jobs, and DLQ depth | Yes |
| `GET` | `/health` | Core system liveness and readiness probe | No |
| `GET` | `/metrics` | Prometheus metrics exposition (AI token usage, latency) | No |

---

## Compliance & Traceability

FFIRE complies with the requirements defined in `FFIRE_SRS.txt`:
- **NFR-1**: High-throughput investigation processing with bounded latency.
- **NFR-4**: Dual-tier AES-256-GCM encryption for all sensitive PII at rest.
- **NFR-5**: SHA-256 cryptographic hash-chaining for immutable audit logs.
- **NFR-6**: Fail-closed enterprise security mode preventing unauthorized token pass-through.
- **SA-1..20 / DS-1..15 / OP-1..19 / LG-1..20**: Complete granular automated test coverage verified by `scripts/srs_audit_engine.py`.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
