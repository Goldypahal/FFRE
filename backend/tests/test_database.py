from database import engine, Base, SessionLocal
from sqlalchemy import text
import pytest

def test_database_connection():
    """Test that we can connect to the database"""
    # For SQLite in-memory DB in tests, this should work
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_create_tables():
    """Test that tables can be created"""
    # This should not raise an exception
    Base.metadata.create_all(bind=engine)

    # Check that we can create a session
    session = SessionLocal()
    try:
        # Simple query to verify connection works
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        session.close()

def test_session_local():
    """Test that SessionLocal creates working sessions"""
    session = SessionLocal()
    try:
        # Execute a simple query
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        session.close()