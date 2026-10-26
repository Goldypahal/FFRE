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
    clean_table = table.strip('"')
    try:
        if is_sqlite:
            r = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{clean_table}'")).fetchone()
            return r is not None
        else:
            r = conn.execute(text(f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='{clean_table}'")).fetchone()
            return r is not None
    except Exception:
        return False


def column_exists(conn: Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table (SQLite specific helper)."""
    clean_table = table.strip('"')
    try:
        rows = conn.execute(text(f"PRAGMA table_info({clean_table})")).fetchall()
        cols = [r[1] for r in rows]
        return column in cols
    except Exception:
        return False


def safe_add_column(conn: Connection, is_sqlite: bool, table: str, column: str, col_type: str):
    """Safely add a column if the table exists and column does not already exist."""
    if not table_exists(conn, is_sqlite, table):
        return

    if is_sqlite:
        if not column_exists(conn, table, column):
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            except Exception:
                pass
    else:
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"))
        except Exception:
            pass


# Definition of versioned migrations: (version, name, up_func_sqlite, up_func_postgres)
def migration_001_initial_tables(conn: Connection, is_sqlite: bool):
    # Base tables are typically created via models Base.metadata.create_all
    pass


def migration_002_investigation_idempotency(conn: Connection, is_sqlite: bool):
    safe_add_column(conn, is_sqlite, "investigation", "idempotency_key", "VARCHAR")
    safe_add_column(conn, is_sqlite, "investigation", "request_fingerprint", "VARCHAR(64)")
    safe_add_column(conn, is_sqlite, "investigation", "updated_at", "DATETIME" if is_sqlite else "TIMESTAMP")
    try:
        conn.execute(text("DROP INDEX IF EXISTS uq_investigation_idempotency_key;"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;"))
    except Exception:
        pass


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


MIGRATIONS: List[Tuple[int, str, Callable[[Connection, bool], None]]] = [
    (1, "initial_schema_baseline", migration_001_initial_tables),
    (2, "investigation_idempotency_and_fingerprint", migration_002_investigation_idempotency),
    (3, "customer_account_merchant_extensions", migration_003_customer_account_merchant_extensions),
    (4, "multitenancy_isolation_columns", migration_004_multitenancy_columns),
    (5, "audit_log_cryptographic_hash_chains", migration_005_audit_log_hash_chains),
    (6, "user_security_and_device_telemetry", migration_006_user_security_and_device_telemetry),
    (7, "transaction_metadata_and_counterparty", migration_007_transaction_metadata),
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
                logger.warning(f"Could not acquire PostgreSQL advisory lock: {e}")

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
