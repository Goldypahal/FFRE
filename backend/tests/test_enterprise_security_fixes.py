import pytest
from fastapi.testclient import TestClient
import models

def test_auth_register_cannot_self_promote_to_admin_without_invite(client):
    """
    P0 Finding 1: Ensure unauthenticated users cannot register as admin without authorized invite token.
    """
    res = client.post("/api/v1/auth/register", json={
        "name": "Attacker Admin",
        "email": "attacker@evil.com",
        "password": "Password123!",
        "role": "admin",
        "tenant_id": "target_tenant"
    })
    assert res.status_code == 403
    assert "Administrative registration is forbidden without a valid admin invite token" in res.json()["detail"]

def test_auth_register_role_enum_validation(client):
    """
    P0 Finding 1: Ensure invalid roles are rejected by enum validation.
    """
    res = client.post("/api/v1/auth/register", json={
        "name": "Invalid Role User",
        "email": "invalid_role@test.com",
        "password": "Password123!",
        "role": "super_root_god_mode"
    })
    assert res.status_code == 400
    assert "Invalid role" in res.json()["detail"]

def test_auth_register_with_invite_token_succeeds(client):
    """
    P0 Finding 1: Ensure admin registration succeeds when authorized invite token is provided.
    """
    res = client.post("/api/v1/auth/register", json={
        "name": "Authorized Admin",
        "email": "authorized.admin@enterprise.bank",
        "password": "Password123!",
        "role": "admin",
        "tenant_id": "tenant_enterprise",
        "invite_token": "enterprise-admin-invite-secret"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["tenant_id"] == "tenant_enterprise"

def test_auth_logout_revokes_token(client):
    """
    Section 3 Discrepancy: Ensure /api/v1/auth/logout revokes JWT token in blacklist.
    """
    # 1. Register a standard investigator
    reg = client.post("/api/v1/auth/register", json={
        "name": "Standard User",
        "email": "logout.test@enterprise.bank",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_enterprise"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify token works
    res1 = client.get("/api/v1/investigations", headers=headers)
    assert res1.status_code == 200

    # 3. Call logout
    res_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert res_logout.status_code == 200
    assert "revoked" in res_logout.json()["message"]

    # 4. Token must now be rejected
    res2 = client.get("/api/v1/investigations", headers=headers)
    assert res2.status_code == 401
    assert "Token has been revoked" in res2.json()["detail"]

def test_investigation_soft_delete_and_legal_hold(client, db_session):
    """
    Finding 9: Ensure investigations support soft delete and legal-hold protection against deletion.
    """
    # 1. Create an admin
    reg_admin = client.post("/api/v1/auth/register", json={
        "name": "Legal Admin",
        "email": "legal.admin@bank.com",
        "password": "Password123!",
        "role": "admin",
        "invite_token": "enterprise-admin-invite-secret"
    })
    admin_token = reg_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Directly seed an investigation in DB
    inv_id = "inv_legal_hold_test_888"
    inv = models.Investigation(
        investigation_id=inv_id,
        txn_id="txn_legal_888",
        tenant_id="default_tenant",
        status="COMPLETED"
    )
    db_session.add(inv)
    db_session.commit()

    # 3. Apply legal hold
    hold_res = client.post(f"/api/v1/investigations/{inv_id}/legal-hold", json={
        "legal_hold": True,
        "reason": "Subpoena SEC-2026-09"
    }, headers=admin_headers)
    assert hold_res.status_code == 200
    assert hold_res.json()["legal_hold"] is True

    # 4. Attempt to delete investigation while under legal hold -> must be blocked (400)
    del_blocked = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert del_blocked.status_code == 400
    assert "under active regulatory legal hold" in del_blocked.json()["detail"]

    # 5. Release legal hold
    client.post(f"/api/v1/investigations/{inv_id}/legal-hold", json={
        "legal_hold": False,
        "reason": "Legal hold resolved"
    }, headers=admin_headers)

    # 6. Delete investigation -> must succeed via compliant soft delete
    del_ok = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert del_ok.status_code == 200
    assert "soft-deleted successfully" in del_ok.json()["message"]

    # 7. Investigation is now 404 on normal fetch
    get_res = client.get(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert get_res.status_code == 404

def test_verifier_api_endpoint(client):
    """
    Rank 1 Differentiating Feature: Independent Trust Layer Verifier API.
    """
    reg = client.post("/api/v1/auth/register", json={
        "name": "Verifier Client",
        "email": "verifier@enterprise.com",
        "password": "Password123!",
        "role": "investigator"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "narrative": "Transaction amount of 9500 was transferred via WIRE channel by account acc_corp_88.",
        "evidence": {
            "amount": 9500.0,
            "channel": "WIRE",
            "account_id": "acc_corp_88",
            "velocity_count_24h": 6
        },
        "vendor": "oracle"
    }

    res = client.post("/api/v1/verifier/evaluate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "grounding_score" in data
    assert "verification_status" in data
    assert "cryptographic_attestation" in data
    assert data["grounding_score"] >= 0.70
