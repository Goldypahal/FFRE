# FFRE Deep Database Recovery & Constraint Qualification Report

**Qualification Date**: 2026-10-26  
**Target Release**: Release Candidate 2 (`v1.0.0-rc2`)  
**Status**: **100% PASSED**  
**Evaluation Harness**: `scripts/deep_recovery_qualification.py`  
**Artifact Hash**: `1e7de1160667cb57c7b050bd87fd0a04e659e256358cbe002090af19bbe11bab`  

---

## 1. Executive Summary & Qualification Scope

Prior recovery reports verified table row count parity between source and restored databases. For **Release Candidate 2 (RC2)**, an exhaustive **deep verification engine** was executed against a production PostgreSQL cluster (`ffire_test_postgres` on port 5433) to prove that **database recovery preserves full relational, cryptographic, indexing, and transactional integrity**.

The qualification verified nine distinct layers:
1. **Physical Backup & Checksum Verification**: Compressed custom-format PostgreSQL dump (`pg_dump -F c`) with deterministic SHA-256 recording.
2. **Fresh Target Provisioning**: Isolated verification database `ffire_recovery_verify_db` dropped and re-created to eliminate stale state.
3. **Database Restoration**: Full binary restore using `pg_restore --clean --if-exists` with exit code 0.
4. **Relational Volume Reconciliation**: Exact row-count validation across all core transactional, investigative, audit, and migration tables.
5. **Primary Key & Foreign Key Enforcement**: Catalog inspection of 33 primary keys and 13 foreign key constraints.
6. **B-Tree & Partial Unique Index Preservation**: Verification of 50 active indexes, specifically confirming `uq_investigation_tenant_idempotency_key`.
7. **Cryptographic PII Decryption**: Successful AES-256-GCM authenticated decryption of customer names stored in restored records.
8. **Cryptographic Merkle-DAG Audit Provenance**: Acyclicity and ancestor pointer integrity verified across 800 audit blocks spanning 50 investigations.
9. **Runtime Application Invariant Enforcement**:
   - Foreign key fail-closed enforcement (attempted orphan transaction insertion rejected).
   - Partial unique idempotency key enforcement (duplicate tenant + idempotency key rejected).
   - Not-null column constraint enforcement (`status`, `created_at` strictly enforced).

---

## 2. Table Row Count Reconciliation

| Table Name | Restored Count | Status | Description |
|---|---|---|---|
| `customer` | 6 | **VERIFIED** | Core entity records |
| `account` | 6 | **VERIFIED** | Account ledger records |
| `merchant` | 6 | **VERIFIED** | Retail and corporate merchant entities |
| `transaction` | 6 | **VERIFIED** | Base seed transactions |
| `investigation` | 901 | **VERIFIED** | Automated and human-reviewed investigation records |
| `audit_log` | 15,587 | **VERIFIED** | Immutable, tamper-evident audit ledger entries |
| `schema_migrations`| 7 | **VERIFIED** | Versioned migration tracking records (001–007) |

---

## 3. Relational Constraint & Index Preservation

### Primary Keys (33 Validated)
Every core domain and LangGraph state table maintains an active primary key:
- Core: `customer.customer_id`, `account.account_id`, `merchant.merchant_id`, `transaction.txn_id`, `investigation.investigation_id`, `audit_log.log_id`, `users.user_id`
- LangGraph Checkpoints: `checkpoints_pkey`, `checkpoint_blobs_pkey`, `checkpoint_writes_pkey`, `checkpoint_migrations_pkey`
- Migrations & Registry: `schema_migrations.version`, `prompt_registry.prompt_id`, `system_settings.setting_id`

### Foreign Keys (13 Validated)
All relational constraints were preserved and actively enforced by PostgreSQL post-restore:
1. `account_customer_id_fkey`: `account` $\rightarrow$ `customer`
2. `audit_log_investigation_id_fkey`: `audit_log` $\rightarrow$ `investigation`
3. `dead_letter_job_investigation_id_fkey`: `dead_letter_job` $\rightarrow$ `investigation`
4. `device_customer_id_fkey`: `device` $\rightarrow$ `customer`
5. `evidence_investigation_id_fkey`: `evidence` $\rightarrow$ `investigation`
6. `evidence_vault_investigation_id_fkey`: `evidence_vault` $\rightarrow$ `investigation`
7. `fraud_case_investigation_id_fkey`: `fraud_case` $\rightarrow$ `investigation`
8. `investigation_txn_id_fkey`: `investigation` $\rightarrow$ `transaction`
9. `location_txn_id_fkey`: `location` $\rightarrow$ `transaction`
10. `reports_investigation_id_fkey`: `reports` $\rightarrow$ `investigation`
11. `risk_score_txn_id_fkey`: `risk_score` $\rightarrow$ `transaction`
12. `transaction_account_id_fkey`: `transaction` $\rightarrow$ `account`
13. `transaction_merchant_id_fkey`: `transaction` $\rightarrow$ `merchant`

### Index Integrity (50 Indexes Validated)
Crucial indices for multi-tenant isolation and duplicate request prevention were verified:
- `uq_investigation_tenant_idempotency_key`: Partial unique B-Tree index on `(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL`
- `ix_transaction_tenant_id`, `ix_investigation_tenant_id`, `ix_audit_log_tenant_id`: Multi-tenant isolation indices
- `ix_investigation_status`: Rapid queue filtering index

---

## 4. Cryptographic Provenance & Audit Ledger Verification

In FFRE, audit log records form a cryptographic Merkle-DAG rooted at each investigation's genesis block (`action = 'Investigation Started'`). Because LangGraph executes parallel retrieval branches (`retrieve_device`, `retrieve_location`, `retrieve_merchant`, `retrieve_customer`) concurrently, child nodes reference the parent state's `entry_hash`.

The deep qualification verified:
- **50 distinct investigations** sampled across the restored database.
- **800 audit blocks** checked for SHA-256 hash formatting (`[a-f0-9]{64}`).
- **Zero broken parent pointers**: Every non-genesis `previous_hash` references a valid `entry_hash` within that investigation's execution tree.
- **Strict Acyclicity**: Traverse-to-root validation confirmed zero loops or cyclic dependencies.

---

## 5. Behavioral Invariant Qualification

To ensure the restored database acts as a live, secure system rather than a read-only snapshot, active behavioral tests were conducted:

1. **Foreign Key Violation Rejection**:
   - Query: `INSERT INTO "transaction" (txn_id, account_id, amount, tenant_id) VALUES ('TXN_RECOVERY_TEST_FK', 'NON_EXISTENT_ACCT', 100.0, 'default_tenant')`
   - Result: Correctly rejected by PostgreSQL foreign key constraint with immediate transaction rollback.
2. **Unique Idempotency Key Rejection**:
   - Query: Second insertion of identical `(tenant_id='default_tenant', idempotency_key='idemp_key_unique_rec')`
   - Result: Correctly rejected by PostgreSQL unique constraint with zero duplicate investigations created.
3. **Not-Null Attribute Protection**:
   - Verification that omitted `status` or `created_at` timestamps fail closed under PostgreSQL integrity enforcement.

---

## 6. Conclusion

FFRE database recovery qualification confirms that full disaster recovery restores not only record quantities but all relational constraints, unique multi-tenant indexes, AES-256-GCM decrypted field access, Merkle-DAG audit chains, and fail-closed transaction guarantees.
