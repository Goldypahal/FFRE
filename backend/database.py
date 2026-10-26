import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from sqlalchemy.pool import QueuePool

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ffire.db")

def validate_production_database_config(db_url: str):
    env = os.getenv("ENV", "development").lower()
    if env in ("production", "prod"):
        if "ffire_dev_insecure_password" in db_url or "dev_insecure" in db_url.lower():
            raise ValueError("CRITICAL SECURITY: Insecure development database password detected in DATABASE_URL in production mode!")
        if db_url.startswith("sqlite"):
            raise ValueError("CRITICAL SECURITY: SQLite is not permitted for production deployments. A production PostgreSQL instance must be configured!")

validate_production_database_config(SQLALCHEMY_DATABASE_URL)

engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 60.0}
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "30"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
else:
    # Production PostgreSQL / TimescaleDB Enterprise Pooling (Chapter 48)
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "50"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    engine_kwargs["pool_timeout"] = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=60000;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
            try:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.commit()
            except Exception:
                pass
            for stmt in [
                "ALTER TABLE investigation ADD COLUMN idempotency_key VARCHAR",
                "ALTER TABLE investigation ADD COLUMN request_fingerprint VARCHAR(64)",
                "DROP INDEX IF EXISTS uq_investigation_idempotency_key;",
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;",
                "ALTER TABLE investigation ADD COLUMN updated_at DATETIME",
                "ALTER TABLE customer ADD COLUMN created_at DATETIME",
                "ALTER TABLE account ADD COLUMN created_at DATETIME",
                "ALTER TABLE account ADD COLUMN balance NUMERIC(12, 2)",
                "ALTER TABLE account ADD COLUMN account_type VARCHAR",
                "ALTER TABLE merchant ADD COLUMN category VARCHAR",
            ]:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    pass
            for tbl in ["users", "customer", "account", "merchant", "device", "location", "evidence", "fraud_case", "risk_score", "dead_letter_job", "\"transaction\"", "investigation", "audit_log", "rule", "action_log", "prompts", "prompt_versions", "reports"]:
                try:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN tenant_id VARCHAR(50) DEFAULT 'default_tenant'"))
                    conn.commit()
                except Exception:
                    pass
            for col, col_type in [
                ("previous_hash", "VARCHAR(64)"),
                ("entry_hash", "VARCHAR(64)"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE audit_log ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
            for col, col_type in [
                ("email_hash", "VARCHAR(64)"),
                ("status", "VARCHAR(20) DEFAULT 'ACTIVE'"),
                ("last_login", "DATETIME"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
            for col, col_type in [
                ("ip_address", "VARCHAR(45)"),
                ("os", "VARCHAR(50)"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE device ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
            for col, col_type in [
                ("geo_coord", "VARCHAR(100)"),
                ("country", "VARCHAR(50)"),
                ("txn_id", "VARCHAR"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE location ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
            for col, col_type in [
                ("counterparty", "VARCHAR(255)"),
                ("channel", "VARCHAR(50)"),
                ("ip_address", "VARCHAR(45)"),
                ("device_ref", "VARCHAR(100)"),
                ("timestamp", "DATETIME"),
                ("currency", "VARCHAR(10) DEFAULT 'USD'"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE \"transaction\" ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass
        else:
            # PostgreSQL schema migration support
            for stmt in [
                "ALTER TABLE investigation ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR",
                "ALTER TABLE investigation ADD COLUMN IF NOT EXISTS request_fingerprint VARCHAR(64)",
                "DROP INDEX IF EXISTS uq_investigation_idempotency_key;",
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;",
                "ALTER TABLE investigation ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
                "ALTER TABLE customer ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
                "ALTER TABLE account ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
                "ALTER TABLE account ADD COLUMN IF NOT EXISTS balance NUMERIC(12, 2)",
                "ALTER TABLE account ADD COLUMN IF NOT EXISTS account_type VARCHAR",
                "ALTER TABLE merchant ADD COLUMN IF NOT EXISTS category VARCHAR",
            ]:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for tbl in ["users", "customer", "account", "merchant", "device", "location", "evidence", "fraud_case", "risk_score", "dead_letter_job", "\"transaction\"", "investigation", "audit_log", "rule", "action_log", "prompts", "prompt_versions", "reports"]:
                try:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) DEFAULT 'default_tenant'"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for col, col_type in [
                ("previous_hash", "VARCHAR(64)"),
                ("entry_hash", "VARCHAR(64)"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for col, col_type in [
                ("email_hash", "VARCHAR(64)"),
                ("status", "VARCHAR(20) DEFAULT 'ACTIVE'"),
                ("last_login", "TIMESTAMP"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for col, col_type in [
                ("ip_address", "VARCHAR(45)"),
                ("os", "VARCHAR(50)"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE device ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for col, col_type in [
                ("geo_coord", "VARCHAR(100)"),
                ("country", "VARCHAR(50)"),
                ("txn_id", "VARCHAR"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE location ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            for col, col_type in [
                ("counterparty", "VARCHAR(255)"),
                ("channel", "VARCHAR(50)"),
                ("ip_address", "VARCHAR(45)"),
                ("device_ref", "VARCHAR(100)"),
                ("timestamp", "TIMESTAMP"),
                ("currency", "VARCHAR(10) DEFAULT 'USD'"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE \"transaction\" ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    conn.rollback()

init_db()
