import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from sqlalchemy.pool import QueuePool

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ffire.db")

engine_kwargs = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 60.0}
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "30"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
else:
    # Production PostgreSQL / TimescaleDB Enterprise Pooling (Chapter 48)
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "20"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "10"))
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
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE investigation ADD COLUMN idempotency_key VARCHAR"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE investigation ADD COLUMN request_fingerprint VARCHAR(64)"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("DROP INDEX IF EXISTS uq_investigation_idempotency_key;"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE investigation ADD COLUMN request_fingerprint VARCHAR(64)"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("DROP INDEX IF EXISTS uq_investigation_idempotency_key;"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_investigation_tenant_idempotency_key ON investigation (tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE investigation ADD COLUMN updated_at DATETIME"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE customer ADD COLUMN created_at DATETIME"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE account ADD COLUMN created_at DATETIME"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE account ADD COLUMN balance NUMERIC(12, 2)"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE account ADD COLUMN account_type VARCHAR"))
                conn.commit()
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE merchant ADD COLUMN category VARCHAR"))
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

init_db()
