"""
FFIRE Enterprise Versioned Schema Migration Engine.
Provides deterministic, ordered, transactional, and idempotent schema migrations
with PostgreSQL advisory locks to guarantee safe multi-worker concurrency.
"""

import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Callable
from sqlalchemy import text, Engine, Connection

logger = logging.getLogger("ffire.migrations")

# PostgreSQL advisory lock ID for FFRE migration synchronization (32-bit signed integer)
MIGRATION_ADVISORY_LOCK_ID = 884901


def get_current_utc_timestamp() -> str:
    """Return ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def ensure_migration_table(conn: Connection, is_sqlite: bool):
    """Ensure the schema_migrations tracking table exists."""
    if is_sqlite:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                applied_at VARCHAR(64) NOT NULL,
                checksum VARCHAR(64) NOT NULL
            );
        """))
    else:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(64) NOT NULL
            );
        """))
    conn.commit()


def get_applied_versions(conn: Connection) -> List[int]:
    """Retrieve list of already applied migration versions."""
    result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version ASC"))
    return [row[0] for row in result.fetchall()]


def table_exists(conn: Connection, is_sqlite: bool, table: str) -> bool:
    """Check if a table exists in the database."""
    # Errors propagate: a lookup failure must not be mistaken for "table absent",
    # which would silently skip the migration step and still record it as applied.
    clean_table = table.strip('"')
    if is_sqlite:
        r = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"), {"t": clean_table}).fetchone()
    else:
        r = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=:t"), {"t": clean_table}).fetchone()
    return r is not None


def column_exists(conn: Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table (SQLite specific helper)."""
    clean_table = table.strip('"')
    rows = conn.execute(text(f'PRAGMA table_info("{clean_table}")')).fetchall()
    return column in [r[1] for r in rows]


def safe_add_column(conn: Connection, is_sqlite: bool, table: str, column: str, col_type: str):
    """Add a column if the table exists and the column does not already exist."""
    if not table_exists(conn, is_sqlite, table):
        return

    # Existence is checked up front, so any exception here is a real failure
    # and must abort the migration rather than be recorded as applied.
    if is_sqlite:
        if not column_exists(conn, table, column):
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
    else:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"))


# Definition of versioned migrations: (version, name, up_func_sqlite, up_func_postgres)
def migration_001_initial_tables(conn: Connection, is_sqlite: bool):
    # Base tables are typically created via models Base.metadata.create_all
    pass


def migration_002_investigation_idempotency(conn: Connection, is_sqlite: bool):
    safe_add_column(conn, is_sqlite, "investigation", "idempotency_key", "VARCHAR")
    safe_add_column(conn, is_sqlite, "investigation", "request_fingerprint", "VARCHAR(64)")
    safe_add_column(conn, is_sqlite, "investigation", "updated_at", "DATETIME" if is_sqlite else "TIMESTAMP")
    if table_exists(conn, is_sqlite, "investigation"):
        conn.execute(text("DROP INDEX IF EXISTS uq_investigation_idempotency_key;"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;"))


def migration_003_customer_account_merchant_extensions(conn: Connection, is_sqlite: bool):
    safe_add_column(conn, is_sqlite, "customer", "created_at", "DATETIME" if is_sqlite else "TIMESTAMP")
    safe_add_column(conn, is_sqlite, "account", "created_at", "DATETIME" if is_sqlite else "TIMESTAMP")
    safe_add_column(conn, is_sqlite, "account", "balance", "NUMERIC(12, 2)")
    safe_add_column(conn, is_sqlite, "account", "account_type", "VARCHAR")
    safe_add_column(conn, is_sqlite, "merchant", "category", "VARCHAR")


def migration_004_multitenancy_columns(conn: Connection, is_sqlite: bool):
    tables = [
        "users", "customer", "account", "merchant", "device", "location",
        "evidence", "fraud_case", "risk_score", "dead_letter_job",
        "\"transaction\"", "investigation", "audit_log", "rule", "action_log",
        "prompts", "prompt_versions", "reports"
    ]
    for tbl in tables:
        safe_add_column(conn, is_sqlite, tbl, "tenant_id", "VARCHAR(50) DEFAULT 'default_tenant'")


def migration_005_audit_log_hash_chains(conn: Connection, is_sqlite: bool):
    for col in ["previous_hash", "entry_hash"]:
        safe_add_column(conn, is_sqlite, "audit_log", col, "VARCHAR(64)")


def migration_006_user_security_and_device_telemetry(conn: Connection, is_sqlite: bool):
    # users table
    safe_add_column(conn, is_sqlite, "users", "email_hash", "VARCHAR(64)")
    safe_add_column(conn, is_sqlite, "users", "status", "VARCHAR(20) DEFAULT 'ACTIVE'")
    safe_add_column(conn, is_sqlite, "users", "last_login", "DATETIME" if is_sqlite else "TIMESTAMP")

    # device table
    safe_add_column(conn, is_sqlite, "device", "ip_address", "VARCHAR(45)")
    safe_add_column(conn, is_sqlite, "device", "os", "VARCHAR(50)")

    # location table
    safe_add_column(conn, is_sqlite, "location", "geo_coord", "VARCHAR(100)")
    safe_add_column(conn, is_sqlite, "location", "country", "VARCHAR(50)")
    safe_add_column(conn, is_sqlite, "location", "txn_id", "VARCHAR")


def migration_007_transaction_metadata(conn: Connection, is_sqlite: bool):
    safe_add_column(conn, is_sqlite, "\"transaction\"", "counterparty", "VARCHAR(255)")
    safe_add_column(conn, is_sqlite, "\"transaction\"", "channel", "VARCHAR(50)")
    safe_add_column(conn, is_sqlite, "\"transaction\"", "ip_address", "VARCHAR(45)")
    safe_add_column(conn, is_sqlite, "\"transaction\"", "device_ref", "VARCHAR(100)")
    safe_add_column(conn, is_sqlite, "\"transaction\"", "timestamp", "DATETIME" if is_sqlite else "TIMESTAMP")
    safe_add_column(conn, is_sqlite, "\"transaction\"", "currency", "VARCHAR(10) DEFAULT 'USD'")


def migration_008_tenant_invitations_token_hash(conn: Connection, is_sqlite: bool):
    if not table_exists(conn, is_sqlite, "tenant_invitations"):
        if is_sqlite:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenant_invitations (
                    invitation_id VARCHAR(64) PRIMARY KEY,
                    token VARCHAR(128),
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    tenant_id VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'investigator',
                    created_by VARCHAR(100) NOT NULL,
                    created_at DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT 0,
                    used_at DATETIME,
                    used_by VARCHAR(255)
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_tenant_id ON tenant_invitations (tenant_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_is_used ON tenant_invitations (is_used);"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_invitations_token_hash ON tenant_invitations (token_hash);"))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenant_invitations (
                    invitation_id VARCHAR(64) PRIMARY KEY,
                    token VARCHAR(128),
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    tenant_id VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'investigator',
                    created_by VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT FALSE,
                    used_at TIMESTAMP WITHOUT TIME ZONE,
                    used_by VARCHAR(255)
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_tenant_id ON tenant_invitations (tenant_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_is_used ON tenant_invitations (is_used);"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_invitations_token_hash ON tenant_invitations (token_hash);"))
    else:
        safe_add_column(conn, is_sqlite, "tenant_invitations", "token_hash", "VARCHAR(64)")
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_invitations_token_hash ON tenant_invitations (token_hash);"))


def migration_010_backfill_and_enforce_invitation_token_hash(conn: Connection, is_sqlite: bool):
    """
    Migration 010: Backfills legacy invitation token_hash, strictly verifies zero nulls,
    and scrubs plaintext tokens from storage at rest. Fails deployment on any error.
    """
    if table_exists(conn, is_sqlite, "tenant_invitations"):
        import hashlib
        # 1. Backfill legacy records
        rows = conn.execute(text("SELECT invitation_id, token FROM tenant_invitations WHERE token_hash IS NULL OR token_hash = ''")).fetchall()
        for r in rows:
            inv_id, raw_tok = r[0], r[1]
            if raw_tok:
                th = hashlib.sha256(raw_tok.encode("utf-8")).hexdigest()
                conn.execute(
                    text("UPDATE tenant_invitations SET token_hash = :th, token = NULL WHERE invitation_id = :iid"),
                    {"th": th, "iid": inv_id}
                )

        # 2. Verify zero null token_hashes
        null_count = conn.execute(text("SELECT COUNT(*) FROM tenant_invitations WHERE token_hash IS NULL OR token_hash = ''")).scalar()
        if null_count and null_count > 0:
            raise RuntimeError(f"Migration 010 failure: {null_count} tenant invitation records lack token_hash!")

        # 3. Scrub any remaining plaintext tokens
        conn.execute(text("UPDATE tenant_invitations SET token = NULL WHERE token IS NOT NULL"))

        # 4. Ensure unique index on token_hash (a failure here aborts the migration)
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_invitations_token_hash ON tenant_invitations (token_hash);"))


# Canonical SQLite DDL for tenant_invitations, used to rebuild legacy tables whose
# token_hash column was added as nullable (SQLite cannot ALTER COLUMN ... SET NOT NULL).
_SQLITE_TENANT_INVITATIONS_DDL = """
    CREATE TABLE {name} (
        invitation_id VARCHAR(64) PRIMARY KEY,
        token VARCHAR(128),
        token_hash VARCHAR(64) NOT NULL UNIQUE,
        tenant_id VARCHAR(50) NOT NULL,
        email VARCHAR(255),
        role VARCHAR(50) NOT NULL DEFAULT 'investigator',
        created_by VARCHAR(100) NOT NULL,
        created_at DATETIME NOT NULL,
        expires_at DATETIME NOT NULL,
        is_used BOOLEAN NOT NULL DEFAULT 0,
        used_at DATETIME,
        used_by VARCHAR(255)
    )
"""


def verify_invitation_token_hash_constraints(conn: Connection) -> None:
    """
    Assert tenant_invitations.token_hash is NOT NULL and covered by a unique index
    or unique constraint on exactly (token_hash); raise RuntimeError otherwise.
    Shared by the internal engine and Alembic revision e7f8a9b0c1d2 so both
    migration systems guarantee the same schema.
    """
    from sqlalchemy import inspect as sa_inspect

    insp = sa_inspect(conn)
    if "tenant_invitations" not in insp.get_table_names():
        return

    cols = {c["name"]: c for c in insp.get_columns("tenant_invitations")}
    if "token_hash" not in cols:
        raise RuntimeError("tenant_invitations.token_hash column is missing")
    if cols["token_hash"]["nullable"]:
        raise RuntimeError("tenant_invitations.token_hash is nullable; NOT NULL is not enforced")

    unique_on_hash = any(
        ix.get("unique") and list(ix.get("column_names") or []) == ["token_hash"]
        for ix in insp.get_indexes("tenant_invitations")
    ) or any(
        list(uc.get("column_names") or []) == ["token_hash"]
        for uc in insp.get_unique_constraints("tenant_invitations")
    )
    if not unique_on_hash:
        raise RuntimeError("tenant_invitations.token_hash has no unique index or unique constraint")


def _sqlite_token_hash_is_not_null(conn: Connection) -> bool:
    for row in conn.execute(text('PRAGMA table_info("tenant_invitations")')).fetchall():
        if row[1] == "token_hash":
            return bool(row[3])
    return False


def migration_011_enforce_invitation_token_hash_constraints(conn: Connection, is_sqlite: bool):
    """
    Migration 011: bring the internal engine to parity with Alembic revision
    e7f8a9b0c1d2 (token_hash NOT NULL + unique index) and verify both exist.
    Kept separate from 010 because 010 is already recorded as applied on existing
    databases and would never re-run.
    """
    if not table_exists(conn, is_sqlite, "tenant_invitations"):
        return

    null_count = conn.execute(text(
        "SELECT COUNT(*) FROM tenant_invitations WHERE token_hash IS NULL OR token_hash = ''"
    )).scalar()
    if null_count:
        raise RuntimeError(f"Migration 011 failure: {null_count} tenant invitation records lack token_hash")

    if is_sqlite:
        if not _sqlite_token_hash_is_not_null(conn):
            existing_cols = [r[1] for r in conn.execute(text('PRAGMA table_info("tenant_invitations")')).fetchall()]
            conn.execute(text("DROP TABLE IF EXISTS tenant_invitations__rebuild"))
            conn.execute(text(_SQLITE_TENANT_INVITATIONS_DDL.format(name="tenant_invitations__rebuild")))
            target_cols = [r[1] for r in conn.execute(text('PRAGMA table_info("tenant_invitations__rebuild")')).fetchall()]
            shared = ", ".join(c for c in target_cols if c in existing_cols)
            conn.execute(text(f"INSERT INTO tenant_invitations__rebuild ({shared}) SELECT {shared} FROM tenant_invitations"))
            conn.execute(text("DROP TABLE tenant_invitations"))
            conn.execute(text("ALTER TABLE tenant_invitations__rebuild RENAME TO tenant_invitations"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_tenant_id ON tenant_invitations (tenant_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_invitations_is_used ON tenant_invitations (is_used);"))
    else:
        conn.execute(text("ALTER TABLE tenant_invitations ALTER COLUMN token_hash SET NOT NULL"))

    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_invitations_token_hash ON tenant_invitations (token_hash);"))
    verify_invitation_token_hash_constraints(conn)


def migration_009_user_mfa_and_phone(conn: Connection, is_sqlite: bool):
    safe_add_column(conn, is_sqlite, "users", "phone_number", "VARCHAR(255)")
    safe_add_column(conn, is_sqlite, "users", "mfa_enabled", "BOOLEAN DEFAULT 0" if is_sqlite else "BOOLEAN DEFAULT FALSE")


MIGRATIONS: List[Tuple[int, str, Callable[[Connection, bool], None]]] = [
    (1, "initial_schema_baseline", migration_001_initial_tables),
    (2, "investigation_idempotency_and_fingerprint", migration_002_investigation_idempotency),
    (3, "customer_account_merchant_extensions", migration_003_customer_account_merchant_extensions),
    (4, "multitenancy_isolation_columns", migration_004_multitenancy_columns),
    (5, "audit_log_cryptographic_hash_chains", migration_005_audit_log_hash_chains),
    (6, "user_security_and_device_telemetry", migration_006_user_security_and_device_telemetry),
    (7, "transaction_metadata_and_counterparty", migration_007_transaction_metadata),
    (8, "tenant_invitations_token_hash", migration_008_tenant_invitations_token_hash),
    (9, "user_mfa_and_phone", migration_009_user_mfa_and_phone),
    (10, "backfill_and_enforce_invitation_token_hash", migration_010_backfill_and_enforce_invitation_token_hash),
    (11, "enforce_invitation_token_hash_constraints", migration_011_enforce_invitation_token_hash_constraints),
]


def run_migrations(engine: Engine) -> int:
    """
    Execute pending versioned migrations under transaction with advisory lock.
    Returns the number of newly applied migrations.
    """
    is_sqlite = engine.url.drivername.startswith("sqlite")
    applied_count = 0

    with engine.connect() as conn:
        # 1. Acquire advisory lock if PostgreSQL
        locked = False
        if not is_sqlite:
            try:
                lock_res = conn.execute(text(f"SELECT pg_try_advisory_lock({MIGRATION_ADVISORY_LOCK_ID})")).scalar()
                if not lock_res:
                    logger.info("Another process holds migration advisory lock; waiting...")
                    conn.execute(text(f"SELECT pg_advisory_lock({MIGRATION_ADVISORY_LOCK_ID})"))
                locked = True
            except Exception as e:
                # Proceeding unsynchronized risks concurrent DDL from several workers.
                logger.error(f"Could not acquire PostgreSQL advisory lock: {e}")
                raise RuntimeError("Unable to acquire migration advisory lock; aborting migrations") from e

        try:
            # 2. Ensure tracking table exists
            ensure_migration_table(conn, is_sqlite)
            applied_versions = set(get_applied_versions(conn))

            # 3. Apply pending migrations in strict sequential order
            for version, name, func in MIGRATIONS:
                if version not in applied_versions:
                    logger.info(f"Applying migration {version:03d}_{name}...")
                    try:
                        func(conn, is_sqlite)
                        checksum = hashlib.sha256(f"{version}:{name}".encode("utf-8")).hexdigest()
                        applied_at = get_current_utc_timestamp()
                        conn.execute(
                            text("INSERT INTO schema_migrations (version, name, applied_at, checksum) VALUES (:v, :n, :a, :c)"),
                            {"v": version, "n": name, "a": applied_at, "c": checksum}
                        )
                        conn.commit()
                        applied_count += 1
                        logger.info(f"Successfully applied migration {version:03d}_{name}")
                    except Exception as exc:
                        conn.rollback()
                        logger.error(f"Migration {version:03d}_{name} failed: {exc}")
                        raise RuntimeError(f"Database migration failed at {version:03d}_{name}: {exc}") from exc
        finally:
            # 4. Release advisory lock if PostgreSQL
            if locked:
                try:
                    conn.execute(text(f"SELECT pg_advisory_unlock({MIGRATION_ADVISORY_LOCK_ID})"))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Error releasing advisory lock: {e}")

    return applied_count
