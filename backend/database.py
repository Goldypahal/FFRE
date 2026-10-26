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
    # Calibrated production connection budget: default 10 connections + 5 overflow per worker
    # Across 4 Uvicorn workers: 4 * 15 = 60 max connections, comfortably within PostgreSQL 100-connection limit.
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "5"))
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
    """
    Initialize database tables and execute pending versioned migrations.
    Idempotent and synchronized via advisory locks for safe multi-worker concurrency.
    """
    import models
    import migrations
    Base.metadata.create_all(bind=engine)
    migrations.run_migrations(engine)

init_db()
