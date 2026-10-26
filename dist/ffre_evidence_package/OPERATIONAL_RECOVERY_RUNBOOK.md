# Financial Fraud Investigation Reasoning Engine (FFRE / FFIRE)
# Enterprise Operational Recovery, Reliability & Maintenance Runbook
**Release Candidate Qualification Version**: v1.0.0-RC1  
**Last Updated**: October 2026  
**Target Environments**: Docker Compose & Multi-Pod Kubernetes (Production/Staging)

---

## 1. Architecture Overview & State Boundaries

FFRE maintains a decoupled, resilient architecture split into three durable tiers:

1. **State Persistence & Checkpoints**:
   - Primary Relational Database: PostgreSQL 15 (`ffire_db`).
   - Checkpointer: Native LangGraph PostgreSQL Checkpointer (`checkpoints` and `checkpoint_blobs` tables) with multi-pod connection pooling via `psycopg_pool.ConnectionPool`.
   - Audit Logs: Cryptographic SHA-256 hash-chained immutable audit log table (`audit_log`).
   - Data Protection: AES-256-GCM authenticated encryption for all Customer and User PII with dynamic key derivation and AAD authentication tags.

2. **Distributed Queue & Revocation Cache**:
   - Cache/Broker: Redis 7 (`redis://<host>:6379/0`).
   - Token Revocation: Distributed blocklist using JTI identifiers with fail-closed semantics in `STRICT_ENTERPRISE_MODE=true`.
   - Investigation Queue: Dedicated job worker queues with worker heartbeat monitoring and Dead-Letter Queue (DLQ) support.

3. **Inference & Decision Pipeline**:
   - Multi-agent LangGraph workflow: Planner -> 5 parallel retrieval nodes -> Evidence Verifier -> Multi-window Velocity Engine -> Deterministic Rule Engine -> Vector DB Case Lookup -> Risk Reasoning -> Evidence Critic -> Grounding Validator -> Human Escalation / Report Generation.

---

## 2. PostgreSQL Disaster Recovery & Backup Runbook

### 2.1 Automated Nightly Backup
```bash
# Dump full database including schema, tables, and LangGraph checkpointer dual-tables
pg_dump -h localhost -p 5433 -U ffire_user -d ffire_db \
  -F c -b -v -f "/var/backups/ffire_backup_$(date +%Y%m%d_%H%M%S).dump"
```

### 2.2 Point-In-Time Restoration Procedure
1. Halt active worker pods:
   ```bash
   kubectl scale deployment ffire-worker --replicas=0
   ```
2. Drop active sessions and restore from dump:
   ```bash
   pg_restore -h localhost -p 5433 -U ffire_user -d ffire_db -c -v "/var/backups/ffire_backup_target.dump"
   ```
3. Restart backend and worker pods:
   ```bash
   kubectl scale deployment ffire-worker --replicas=3
   ```
4. Verify checkpointer integrity:
   ```bash
   python scripts/verify_checkpoint_integrity.py
   ```

---

## 3. Database Schema Migrations & Safe Rollback Runbook

### 3.1 Applying Migrations
```bash
# Ensure current database URL is exported
export DATABASE_URL="postgresql://ffire_user:${DB_PASSWORD}@postgres:5432/ffire_db"

# Apply pending schema migrations
alembic upgrade head
```

### 3.2 Rollback Procedure
If a migration fails or must be reversed:
```bash
# Roll back exact 1 step
alembic downgrade -1

# Verify schema revision matches expected target
alembic current
```

---

## 4. Redis Outage & Failover Recovery Runbook

### 4.1 Strict Enterprise Mode Fail-Closed Behavior
When `STRICT_ENTERPRISE_MODE=true`:
- If Redis is unreachable, any attempt to validate a JWT or verify token revocation immediately rejects requests with **HTTP 503 Service Unavailable** (Security First: no revoked token can slip through during cache unavailability).
- Worker jobs encountering Redis disconnection pause queue polling without dropping in-flight jobs.

### 4.2 Recovery Steps Post-Redis Restoral
1. Once Redis container / Sentinel cluster is restored:
   ```bash
   redis-cli -h localhost -p 6379 ping
   # Expected: PONG
   ```
2. Unacknowledged jobs automatically transition from in-flight to processing or retry queue.
3. Verify worker health:
   ```bash
   curl -H "Authorization: Bearer ${ADMIN_TOKEN}" http://localhost:8000/api/v1/admin/worker/health
   ```

---

## 5. Observability, Metrics & SLA Alerting

### 5.1 Prometheus Telemetry
Prometheus scrapes `GET /metrics` every 15 seconds:
- `ffire_llm_tokens_total`: Total tokens consumed grouped by model and tenant.
- `ffire_llm_cost_usd_total`: Cumulative inference cost in USD.
- `ffire_node_execution_seconds`: Histogram of graph node execution latencies.
- `ffire_active_workers`: Gauge of currently active worker threads.

### 5.2 Recommended Alert Rules
| Alert Name | Metric Condition | Severity | Action |
|:---|:---|:---:|:---|
| **HighP95Latency** | `histogram_quantile(0.95, rate(ffire_node_execution_seconds_bucket[5m])) > 5.0` | Warning | Inspect database connection pool & Postgres saver lock |
| **RedisOutageFailsafe** | `rate(http_requests_total{status="503"}[1m]) > 0` | Critical | Check Redis connectivity & cluster failover state |
| **WorkerQueueBacklog** | `ffire_queue_depth > 100` | Warning | Scale worker pods (`kubectl scale deployment ffire-worker --replicas=5`) |
| **PIIEncryptionError** | `rate(ffire_encryption_failures_total[5m]) > 0` | Critical | Inspect master encryption key and AES-256-GCM integrity |

---

## 6. Concurrent Idempotency & Safety Guarantees

1. **Idempotency Header**:
   - Clients must send `Idempotency-Key: <unique-uuid>`.
   - Concurrent submissions with the exact same key return HTTP 202 with the identical `investigation_id`.
   - Exactly one investigation record and one set of side effects are committed to the database.

2. **Durable LangGraph Checkpointing**:
   - Synchronous writes to `checkpoints` and `checkpoint_blobs` ensure no intermediate state loss during node crashes or pod restarts.
   - Worker crashes mid-investigation cleanly resume from the exact last verified checkpoint tuple upon worker restart.
