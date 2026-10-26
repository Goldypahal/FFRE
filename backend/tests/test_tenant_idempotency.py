"""
Tests for Task T0.3: Tenant-Scoped Idempotency & SHA-256 Request Fingerprinting (Finding V2)
Verifies:
1. Cross-tenant isolation: Tenant A and Tenant B can reuse the same idempotency key without collision.
2. Exact replay: Replay with identical payload returns cached investigation with X-Cache-Hit: true.
3. Payload tampering / collision: Replay with the same idempotency key but altered payload returns HTTP 409 Conflict.
4. Default key generation: Derives secure SHA-256 default key incorporating tenant, txn, and user.
"""

import pytest
import models
from auth import get_current_user
from main import app
from scripts.seed_demo_data import seed_transaction


def test_tenant_scoped_idempotency_allows_same_key_across_tenants(client, db_session):
    """Verify Tenant A and Tenant B can use the identical idempotency key without blocking each other."""
    # Seed transactions for both tenants
    seed_transaction(db_session, "TXN_TENANT_A_1", tenant_id="tenant_alpha")
    seed_transaction(db_session, "TXN_TENANT_B_1", tenant_id="tenant_beta")

    # Step 1: Request from Tenant Alpha with key "SHARED_KEY_999"
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    resp_a = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TENANT_A_1", "user_id": "user_alpha"},
        headers={"Idempotency-Key": "SHARED_KEY_999"}
    )
    assert resp_a.status_code == 202
    data_a = resp_a.json()
    assert "investigation_id" in data_a

    # Step 2: Request from Tenant Beta with SAME key "SHARED_KEY_999"
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )

    resp_b = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TENANT_B_1", "user_id": "user_beta"},
        headers={"Idempotency-Key": "SHARED_KEY_999"}
    )
    assert resp_b.status_code == 202
    data_b = resp_b.json()
    assert "investigation_id" in data_b
    assert data_a["investigation_id"] != data_b["investigation_id"]

    # Verify both records exist in DB under their respective tenants
    inv_a = db_session.query(models.Investigation).filter_by(investigation_id=data_a["investigation_id"]).first()
    inv_b = db_session.query(models.Investigation).filter_by(investigation_id=data_b["investigation_id"]).first()
    assert inv_a is not None and inv_a.tenant_id == "tenant_alpha"
    assert inv_b is not None and inv_b.tenant_id == "tenant_beta"
    assert inv_a.idempotency_key == "idemp_SHARED_KEY_999"
    assert inv_b.idempotency_key == "idemp_SHARED_KEY_999"


def test_idempotency_cache_hit_returns_existing_investigation(client, db_session):
    """Verify repeating identical request returns cached investigation with X-Cache-Hit header."""
    seed_transaction(db_session, "TXN_REPLAY_1", tenant_id="tenant_alpha")

    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    # First submission
    resp1 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_REPLAY_1", "user_id": "user_alpha"},
        headers={"Idempotency-Key": "REPLAY_KEY_001"}
    )
    assert resp1.status_code == 202
    inv_id_1 = resp1.json()["investigation_id"]

    # Replay with identical payload and key
    resp2 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_REPLAY_1", "user_id": "user_alpha"},
        headers={"Idempotency-Key": "REPLAY_KEY_001"}
    )
    assert resp2.status_code == 202
    assert resp2.headers.get("X-Cache-Hit") == "true"
    assert resp2.json()["investigation_id"] == inv_id_1


def test_idempotency_collision_different_payload_returns_409(client, db_session):
    """Verify reusing an idempotency key with an altered payload raises HTTP 409 Conflict."""
    seed_transaction(db_session, "TXN_TAMPER_1", tenant_id="tenant_alpha")
    seed_transaction(db_session, "TXN_TAMPER_2", tenant_id="tenant_alpha")

    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    # First submission with key "TAMPER_KEY"
    resp1 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TAMPER_1", "user_id": "user_original"},
        headers={"Idempotency-Key": "TAMPER_KEY"}
    )
    assert resp1.status_code == 202

    # Second submission with SAME key but different user_id in payload
    resp2 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TAMPER_1", "user_id": "user_altered"},
        headers={"Idempotency-Key": "TAMPER_KEY"}
    )
    assert resp2.status_code == 409
    assert "Idempotency key reused with different payload" in resp2.json()["detail"]


def test_default_key_derivation_without_header(client, db_session):
    """Verify automatic SHA-256 idempotency key generation when header is omitted."""
    seed_transaction(db_session, "TXN_AUTO_KEY_1", tenant_id="tenant_alpha")

    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_auto",
        name="Auto User",
        email="auto@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    # First call without Idempotency-Key header
    resp1 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_AUTO_KEY_1", "user_id": "user_auto"}
    )
    assert resp1.status_code == 202
    inv_id = resp1.json()["investigation_id"]

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    # Verify key is SHA-256 derived (64 hex characters after 'idemp_')
    assert inv.idempotency_key.startswith("idemp_")
    assert len(inv.idempotency_key) == len("idemp_") + 64
    assert inv.request_fingerprint is not None
    assert len(inv.request_fingerprint) == 64

    # Second call without header should hit cache
    resp2 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_AUTO_KEY_1", "user_id": "user_auto"}
    )
    assert resp2.status_code == 202
    assert resp2.headers.get("X-Cache-Hit") == "true"
    assert resp2.json()["investigation_id"] == inv_id
