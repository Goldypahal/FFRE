import os
import sys
from unittest.mock import MagicMock

# Ensure parent backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency in the main app
from database import get_db
app.dependency_overrides[get_db] = override_get_db

# Override get_current_user to bypass authentication in tests
from auth import get_current_user
import models
def override_get_current_user():
    return models.User(
        user_id="user_1",
        name="Test User",
        email="test@example.com",
        role="investigator"
    )
app.dependency_overrides[get_current_user] = override_get_current_user

# Create tables
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()