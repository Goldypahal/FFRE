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

init_db()
