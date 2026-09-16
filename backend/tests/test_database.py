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

def test_alembic_migrations_configuration():
    """Test that Alembic migration environment is valid and script directory discovers revision head."""
    import os
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    assert os.path.exists(ini_path)

    alembic_cfg = Config(ini_path)
    script_dir = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script_dir.get_current_head()
    assert head_rev is not None
    assert head_rev == "338f66162493"

def test_production_postgres_pool_configuration():
    """Verify PostgreSQL engine initialization respects enterprise pooling parameters."""
    import os
    from database import engine_kwargs
    # Check that sqlite has QueuePool configured with pool_size >= 20
    assert "pool_size" in engine_kwargs
    assert engine_kwargs["pool_size"] >= 20