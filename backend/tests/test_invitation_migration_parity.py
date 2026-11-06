"""
Invitation token_hash migration parity and fail-closed startup tests.

Exercises both migration systems against *legacy* databases (nullable token_hash,
plaintext tokens at rest) rather than only fresh schemas, and verifies that
database initialization failures stop the process instead of being swallowed.
"""
import hashlib
import os
import subprocess
import sys
import textwrap

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

import migrations

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEGACY_TABLE_DDL = """
    CREATE TABLE tenant_invitations (
        invitation_id VARCHAR(64) PRIMARY KEY,
        token VARCHAR(128),
        token_hash VARCHAR(64),
        tenant_id VARCHAR(50) NOT NULL,
        email VARCHAR(255),
        role VARCHAR(50) NOT NULL DEFAULT 'investigator',
        created_by VARCHAR(100) NOT NULL,
        created_at DATETIME NOT NULL,
        expires_at DATETIME NOT NULL,
        is_used BOOLEAN NOT NULL DEFAULT 0,
        used_at DATETIME,
        used_by VARCHAR(255)
    )
"""


def _insert_invitation(conn, inv_id, token=None, token_hash=None, tenant="tenant_a"):
    conn.execute(
        text(
            "INSERT INTO tenant_invitations (invitation_id, token, token_hash, tenant_id, role, created_by, created_at, expires_at, is_used) "
            "VALUES (:i, :t, :h, :tenant, 'investigator', 'admin', '2026-01-01 00:00:00', '2026-01-03 00:00:00', 0)"
        ),
        {"i": inv_id, "t": token, "h": token_hash, "tenant": tenant},
    )


def _legacy_engine(tmp_path, with_unique_index=False):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        conn.execute(text(LEGACY_TABLE_DDL))
        if with_unique_index:
            conn.execute(text("CREATE UNIQUE INDEX ix_tenant_invitations_token_hash ON tenant_invitations (token_hash)"))
        _insert_invitation(conn, "inv-legacy-1", token="legacy-plaintext-token-1")
        _insert_invitation(conn, "inv-legacy-2", token="legacy-plaintext-token-2")
        _insert_invitation(conn, "inv-modern", token_hash=hashlib.sha256(b"modern").hexdigest())
    return engine


def _mark_applied(engine, up_to_version):
    with engine.connect() as conn:
        migrations.ensure_migration_table(conn, is_sqlite=True)
        for version, name, _ in migrations.MIGRATIONS:
            if version <= up_to_version:
                conn.execute(
                    text("INSERT INTO schema_migrations (version, name, applied_at, checksum) VALUES (:v, :n, 'x', 'x')"),
                    {"v": version, "n": name},
                )
        conn.commit()


def _assert_hardened(engine):
    with engine.connect() as conn:
        rows = {r[0]: (r[1], r[2]) for r in conn.execute(text("SELECT invitation_id, token, token_hash FROM tenant_invitations"))}
        migrations.verify_invitation_token_hash_constraints(conn)

    assert rows["inv-legacy-1"] == (None, hashlib.sha256(b"legacy-plaintext-token-1").hexdigest())
    assert rows["inv-legacy-2"] == (None, hashlib.sha256(b"legacy-plaintext-token-2").hexdigest())
    assert rows["inv-modern"][1] == hashlib.sha256(b"modern").hexdigest()

    # NOT NULL is enforced by the database, not just by application code.
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            _insert_invitation(conn, "inv-null-hash", token_hash=None)

    # Uniqueness is enforced by the database.
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            _insert_invitation(conn, "inv-dup-hash", token_hash=hashlib.sha256(b"modern").hexdigest())


@pytest.mark.parametrize("already_applied", [9, 10])
def test_internal_migrations_harden_legacy_invitations(tmp_path, already_applied):
    """Legacy DB at v9 (pre-backfill) or v10 (backfilled but still nullable) reaches parity."""
    engine = _legacy_engine(tmp_path)
    if already_applied == 10:
        # Simulate a DB where the old migration 010 ran: hashes backfilled, column still nullable.
        with engine.begin() as conn:
            for inv in ("inv-legacy-1", "inv-legacy-2"):
                tok = f"legacy-plaintext-token-{inv[-1]}"
                conn.execute(
                    text("UPDATE tenant_invitations SET token_hash=:h, token=NULL WHERE invitation_id=:i"),
                    {"h": hashlib.sha256(tok.encode()).hexdigest(), "i": inv},
                )
    _mark_applied(engine, already_applied)

    applied = migrations.run_migrations(engine)

    assert applied == len(migrations.MIGRATIONS) - already_applied
    _assert_hardened(engine)
    engine.dispose()


def test_internal_migration_fails_closed_on_unrecoverable_legacy_row(tmp_path):
    engine = _legacy_engine(tmp_path)
    with engine.begin() as conn:
        _insert_invitation(conn, "inv-orphan", token=None, token_hash=None)
    _mark_applied(engine, 9)

    with pytest.raises(RuntimeError, match="010"):
        migrations.run_migrations(engine)

    with engine.connect() as conn:
        versions = {r[0] for r in conn.execute(text("SELECT version FROM schema_migrations"))}
    assert 10 not in versions and 11 not in versions
    engine.dispose()


def test_verify_detects_missing_unique_index(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'nounique.db'}")
    with engine.begin() as conn:
        conn.execute(text(LEGACY_TABLE_DDL.replace("token_hash VARCHAR(64),", "token_hash VARCHAR(64) NOT NULL,")))
    with engine.connect() as conn:
        with pytest.raises(RuntimeError, match="unique"):
            migrations.verify_invitation_token_hash_constraints(conn)
    engine.dispose()


@pytest.mark.parametrize("with_unique_index", [True, False])
def test_alembic_revision_hardens_legacy_invitations(tmp_path, monkeypatch, with_unique_index):
    """Run Alembic e6f7a8b9c0d1 -> head against legacy data, with and without the d5f6 index."""
    from alembic import command
    from alembic.config import Config

    engine = _legacy_engine(tmp_path, with_unique_index=with_unique_index)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
        conn.execute(text("INSERT INTO alembic_version VALUES ('e6f7a8b9c0d1')"))

    monkeypatch.setenv("DATABASE_URL", str(engine.url))
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.config_file_name = None  # keep pytest's logging configuration intact
    command.upgrade(cfg, "head")

    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "e7f8a9b0c1d2"
    _assert_hardened(engine)
    engine.dispose()


def _import_database(env_overrides, tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("ENV", "ENVIRONMENT", "FFRE_SKIP_DB_INIT", "FFRE_DB_INIT_FAIL_OPEN")}
    env.update(env_overrides)
    env["PYTHONPATH"] = BACKEND_DIR
    code = textwrap.dedent("""
        import database
        print("IMPORTED")
    """)
    return subprocess.run([sys.executable, "-c", code], cwd=str(tmp_path), env=env, capture_output=True, text=True, timeout=120)


def _broken_sqlite_url(tmp_path):
    # Parent directory does not exist, so SQLite cannot open the database file.
    return f"sqlite:///{tmp_path / 'missing_dir' / 'ffre.db'}"


def test_database_import_fails_closed_when_init_fails(tmp_path):
    result = _import_database({"DATABASE_URL": _broken_sqlite_url(tmp_path)}, tmp_path)
    assert result.returncode != 0
    assert "IMPORTED" not in result.stdout
    assert "Database initialization or migration failed" in result.stderr


def test_database_import_fail_open_is_explicit_and_logged_outside_production(tmp_path):
    result = _import_database({"DATABASE_URL": _broken_sqlite_url(tmp_path), "FFRE_DB_INIT_FAIL_OPEN": "1"}, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "IMPORTED" in result.stdout
    assert "FFRE_DB_INIT_FAIL_OPEN" in result.stderr


@pytest.mark.parametrize("env_var", ["ENV", "ENVIRONMENT"])
def test_database_fail_open_rejected_in_production(tmp_path, env_var):
    result = _import_database({
        env_var: "production",
        "DATABASE_URL": "postgresql://ffre_user:strong-secret@127.0.0.1:1/ffre",
        "FFRE_DB_INIT_FAIL_OPEN": "1",
    }, tmp_path)
    assert result.returncode != 0
    assert "not permitted in production" in result.stderr


def test_database_explicit_skip_is_logged(tmp_path):
    result = _import_database({"DATABASE_URL": _broken_sqlite_url(tmp_path), "FFRE_SKIP_DB_INIT": "1"}, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "FFRE_SKIP_DB_INIT" in result.stderr
