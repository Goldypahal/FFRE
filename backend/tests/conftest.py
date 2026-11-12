import os

os.environ.setdefault('BOOTSTRAP_SECRET_KEY', 'test-bootstrap-secret-enterprise-2026')

import os

import sys

from unittest.mock import MagicMock



# Ensure parent backend directory and workspace root are on sys.path

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

root_dir = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)

if root_dir not in sys.path:

    sys.path.insert(0, root_dir)



# Mock chromadb to prevent network calls/model downloads during tests

sys.modules['chromadb'] = MagicMock()

sys.modules['chromadb.utils'] = MagicMock()



import pytest

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool



from database import Base

from main import app

from fastapi.testclient import TestClient



# Mock the vector store singleton methods to prevent queries on mock DB

from vector_db import vector_store

vector_store.similarity_search = MagicMock(return_value=[])

vector_store.collection = MagicMock()

vector_store.collection.count = MagicMock(return_value=0)



# Test database: a temporary SQLite file, one connection per thread.
# An in-memory database with StaticPool shares a single connection across every thread, so
# concurrent requests (the duplicate-submission and chaos tests) interleave each other's
# transactions and read wrong or half-written rows. A real server never does that, so the
# tests should not either.
import atexit
import shutil
import tempfile
from sqlalchemy import event as _sa_event

_TEST_DB_DIR = tempfile.mkdtemp(prefix="ffire_test_db_")
atexit.register(shutil.rmtree, _TEST_DB_DIR, ignore_errors=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(_TEST_DB_DIR, 'test.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_size=20,
    max_overflow=20,
)


@_sa_event.listens_for(engine, "connect")
def _test_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



import database

import graph

import main

import worker



database.SessionLocal = TestingSessionLocal

graph.SessionLocal = TestingSessionLocal

main.SessionLocal = TestingSessionLocal

worker.SessionLocal = TestingSessionLocal



# Create tables

Base.metadata.create_all(bind=engine)



# Override the get_db dependency to use the test database

def override_get_db():

    db = TestingSessionLocal()

    try:

        yield db

    finally:

        db.close()



app.dependency_overrides[database.get_db] = override_get_db



from fastapi import Request, Depends

from sqlalchemy.orm import Session

from jose import jwt

import auth

from auth import get_current_user

import models

import models



def override_get_current_user(request: Request, db: Session = Depends(override_get_db)):

    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):

        token = auth_header.split(" ")[1]

        return auth.get_current_user(token=token, db=db)

    return models.User(

        user_id="user_1",

        name="Test User",

        email="test@example.com",

        role="investigator",

        tenant_id="default_tenant"

    )

app.dependency_overrides[get_current_user] = override_get_current_user



@pytest.fixture

def client():

    with TestClient(app) as c:

        yield c



@pytest.fixture

def db_session():

    db = TestingSessionLocal()

    try:

        yield db

    finally:

        db.close()



def create_test_invitation(db, tenant_id="default_tenant", role="investigator", email=None, expires_in_hours=48):

    import secrets

    import datetime
    import timeutil

    import hashlib

    token = f"inv_{secrets.token_urlsafe(24)}"

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    inv = models.TenantInvitation(

        token=None,

        token_hash=token_hash,

        tenant_id=tenant_id,

        role=role,

        email=email,

        created_by="test_harness",

        created_at=timeutil.utcnow(),

        expires_at=timeutil.utcnow() + datetime.timedelta(hours=expires_in_hours),

        is_used=False

    )

    db.add(inv)

    db.commit()

    db.refresh(inv)

    inv.token = token

    return inv



@pytest.fixture

def make_invitation(db_session):

    def _make(tenant_id="default_tenant", role="investigator", email=None, expires_in_hours=48):

        return create_test_invitation(db_session, tenant_id, role, email, expires_in_hours)

    return _make



def _flush_test_redis():

    if hasattr(worker, "worker_queue") and worker.worker_queue and worker.worker_queue._redis_client:

        try:

            stream = getattr(worker.worker_queue, "stream_key", "ffre:worker:stream")

            worker.worker_queue._redis_client.delete("ffre:worker:queue", "ffre:worker:processing", "ffre:worker:dlq", stream)

        except Exception:

            pass



@pytest.fixture(autouse=True)

def clean_db():

    from rate_limiter import rate_limiter

    from metrics import metrics_collector

    rate_limiter.reset()

    metrics_collector.reset_llm_metrics()

    app.dependency_overrides[get_current_user] = override_get_current_user

    worker.worker_queue._queue = worker.queue.Queue()

    _flush_test_redis()

    yield

    rate_limiter.reset()

    metrics_collector.reset_llm_metrics()

    app.dependency_overrides[get_current_user] = override_get_current_user

    worker.worker_queue._queue = worker.queue.Queue()

    _flush_test_redis()

    with engine.connect() as conn:

        for table in reversed(Base.metadata.sorted_tables):

            conn.execute(table.delete())

        conn.commit()