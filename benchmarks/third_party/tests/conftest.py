import os
import sys
import pytest

# Ensure workspace root and backend directory are in sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
backend_path = os.path.join(root_path, "backend")

if root_path not in sys.path:
    sys.path.insert(0, root_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from database import engine, Base, SessionLocal


@pytest.fixture(scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_test_db):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
