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

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

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
    token = f"inv_{secrets.token_urlsafe(24)}"
    inv = models.TenantInvitation(
        token=token,
        tenant_id=tenant_id,
        role=role,
        email=email,
        created_by="test_harness",
        created_at=datetime.datetime.utcnow(),
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours),
        is_used=False
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

@pytest.fixture
def make_invitation(db_session):
    def _make(tenant_id="default_tenant", role="investigator", email=None, expires_in_hours=48):
        return create_test_invitation(db_session, tenant_id, role, email, expires_in_hours)
    return _make

@pytest.fixture(autouse=True)
def clean_db():
    from rate_limiter import rate_limiter
    from metrics import metrics_collector
    rate_limiter.reset()
    metrics_collector.reset_llm_metrics()
    app.dependency_overrides[get_current_user] = override_get_current_user
    worker.worker_queue._queue = worker.queue.Queue()
    yield
    rate_limiter.reset()
    metrics_collector.reset_llm_metrics()
    app.dependency_overrides[get_current_user] = override_get_current_user
    worker.worker_queue._queue = worker.queue.Queue()
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()