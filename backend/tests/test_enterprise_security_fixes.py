import pytest
import datetime
import json
import hashlib
import hmac
import os
from fastapi.testclient import TestClient
import models
from scripts.replay_cli import verify_replay_bundle, run_deterministic_replay


def test_auth_register_bootstrap_and_invitation_flow(client, db_session):
    """
    P0 Remediation: Ensure the first user bootstraps as admin,
    and subsequent users require authenticated, database-backed single-use invitations.
    """
    # 1. First user registers (bootstrap mode -> admin role)
    res_admin = client.post("/api/v1/auth/register", json={
        "name": "Org Admin",
        "email": "admin@primebank.com",
        "password": "Password123!",
        "tenant_id": "tenant_prime"
    })
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    admin_token = admin_data["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Second user attempts registration without invite token -> rejected (403)
    res_unauth = client.post("/api/v1/auth/register", json={
        "name": "Uninvited User",
        "email": "uninvited@evil.com",
        "password": "Password123!",
        "tenant_id": "tenant_prime"
    })
    assert res_unauth.status_code == 403
    assert "Public self-registration is disabled" in res_unauth.json()["detail"]

    # 3. Old hardcoded default invite secret must be strictly rejected
    res_hardcoded = client.post("/api/v1/auth/register", json={
        "name": "Hacker",
        "email": "hacker@evil.com",
        "password": "Password123!",
        "invite_token": "enterprise-admin-invite-secret"
    })
    assert res_hardcoded.status_code == 403
    assert "Invalid, expired, or already-consumed invitation token" in res_hardcoded.json()["detail"]

    # 4. Admin issues valid single-use invitation for an investigator
    res_invite = client.post("/api/v1/admin/invitations", json={
        "email": "lead.investigator@primebank.com",
        "role": "investigator",
        "expires_in_hours": 24
    }, headers=admin_headers)
    assert res_invite.status_code == 200
    invite_data = res_invite.json()
    invite_token = invite_data["token"]
    assert invite_token.startswith("inv_")
    assert invite_data["role"] == "investigator"
    assert invite_data["tenant_id"] == "tenant_prime"

    # 5. User registers with invitation token -> server assigns tenant and role
    res_user = client.post("/api/v1/auth/register", json={
        "name": "Lead Investigator",
        "email": "lead.investigator@primebank.com",
        "password": "Password123!",
        "invite_token": invite_token
    })
    assert res_user.status_code == 200
    user_data = res_user.json()
    assert user_data["tenant_id"] == "tenant_prime"

    # 6. Replay attack: attempt to reuse the invitation token -> rejected (403)
    res_replay = client.post("/api/v1/auth/register", json={
        "name": "Imposter",
        "email": "imposter@primebank.com",
        "password": "Password123!",
        "invite_token": invite_token
    })
    assert res_replay.status_code == 403
    assert "Invalid, expired, or already-consumed invitation token" in res_replay.json()["detail"]


def test_invitation_expiration_and_email_binding(client, db_session, make_invitation):
    """
    P0 Remediation: Verify invitation expiration and email-binding security controls.
    """
    # 1. Bootstrap admin
    client.post("/api/v1/auth/register", json={
        "name": "Admin",
        "email": "admin@bank.com",
        "password": "Password123!"
    })

    # 2. Expired invitation test
    expired_inv = make_invitation(tenant_id="tenant_alpha", role="investigator", expires_in_hours=-1)
    res_exp = client.post("/api/v1/auth/register", json={
        "name": "Late User",
        "email": "late@bank.com",
        "password": "Password123!",
        "invite_token": expired_inv.token
    })
    assert res_exp.status_code == 403
    assert "expired" in res_exp.json()["detail"].lower()

    # 3. Email-restricted invitation test
    bound_inv = make_invitation(tenant_id="tenant_alpha", role="investigator", email="vip@bank.com")
    res_wrong_email = client.post("/api/v1/auth/register", json={
        "name": "Wrong User",
        "email": "other@bank.com",
        "password": "Password123!",
        "invite_token": bound_inv.token
    })
    assert res_wrong_email.status_code == 403
    assert "restricted to vip@bank.com" in res_wrong_email.json()["detail"].lower()


def test_auth_logout_revokes_token(client):
    """
    Ensure /api/v1/auth/logout revokes JWT token in Redis/memory blacklist.
    """
    reg = client.post("/api/v1/auth/register", json={
        "name": "Logout User",
        "email": "logout.test@enterprise.bank",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works
    res1 = client.get("/api/v1/investigations", headers=headers)
    assert res1.status_code == 200

    # Call logout
    res_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert res_logout.status_code == 200
    assert "revoked" in res_logout.json()["message"]

    # Token must now be rejected
    res2 = client.get("/api/v1/investigations", headers=headers)
    assert res2.status_code == 401
    assert "Token has been revoked" in res2.json()["detail"]


def test_investigation_soft_delete_and_legal_hold(client, db_session):
    """
    Finding 9: Ensure investigations support soft delete and legal-hold protection against deletion.
    """
    reg_admin = client.post("/api/v1/auth/register", json={
        "name": "Legal Admin",
        "email": "legal.admin@bank.com",
        "password": "Password123!"
    })
    admin_token = reg_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    inv_id = "inv_legal_hold_test_888"
    inv = models.Investigation(
        investigation_id=inv_id,
        txn_id="txn_legal_888",
        tenant_id="default_tenant",
        status="COMPLETED"
    )
    db_session.add(inv)
    db_session.commit()

    # Apply legal hold
    hold_res = client.post(f"/api/v1/investigations/{inv_id}/legal-hold", json={
        "legal_hold": True,
        "reason": "Subpoena SEC-2026-09"
    }, headers=admin_headers)
    assert hold_res.status_code == 200
    assert hold_res.json()["legal_hold"] is True

    # Blocked deletion while under legal hold
    del_blocked = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert del_blocked.status_code == 400
    assert "under active regulatory legal hold" in del_blocked.json()["detail"]

    # Release legal hold
    client.post(f"/api/v1/investigations/{inv_id}/legal-hold", json={
        "legal_hold": False,
        "reason": "Legal hold resolved"
    }, headers=admin_headers)

    # Soft delete succeeds
    del_ok = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert del_ok.status_code == 200
    assert "soft-deleted successfully" in del_ok.json()["message"]

    # Subsequent fetch returns 404
    get_res = client.get(f"/api/v1/investigations/{inv_id}", headers=admin_headers)
    assert get_res.status_code == 404


def test_verifier_api_hmac_attestation_and_tamper_detection(client):
    """
    Differentiating Feature #1: Independent Verifier API with HMAC-SHA256 signature,
    empty claim rejection, and third-party attestation verification.
    """
    reg = client.post("/api/v1/auth/register", json={
        "name": "Verifier Admin",
        "email": "verifier@enterprise.com",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Empty narrative / zero claims defense -> must return 0.0 grounding and REJECTED_EMPTY
    empty_res = client.post("/api/v1/verifier/evaluate", json={
        "narrative": "   ",
        "evidence": {"amount": 100.0}
    }, headers=headers)
    assert empty_res.status_code == 200
    empty_data = empty_res.json()
    assert empty_data["grounding_score"] == 0.0
    assert empty_data["verification_status"] == "REJECTED_EMPTY"

    # 2. Genuine grounded evaluation
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
    eval_res = client.post("/api/v1/verifier/evaluate", json=payload, headers=headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["grounding_score"] >= 0.70
    assert eval_data["verification_status"] == "PASSED"
    sig = eval_data["cryptographic_attestation"]
    assert sig is not None and len(sig) == 64

    # 3. Third-party attestation verification endpoint succeeds for authentic attestation
    verify_payload = {
        "narrative": payload["narrative"],
        "evidence": payload["evidence"],
        "tenant_id": eval_data["tenant_id"],
        "model_version": "oracle",
        "prompt_version": "guardrails-v1.0",
        "grounding_score": eval_data["grounding_score"],
        "verification_status": eval_data["verification_status"],
        "evaluated_at": eval_data["evaluated_at"],
        "signature": sig
    }
    verify_res = client.post("/api/v1/verifier/verify-attestation", json=verify_payload)
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["tamper_detected"] is False

    # 4. Tampering detection: if someone alters the score or narrative, verification fails
    tampered_payload = dict(verify_payload)
    tampered_payload["grounding_score"] = 0.9999
    tampered_res = client.post("/api/v1/verifier/verify-attestation", json=tampered_payload)
    assert tampered_res.status_code == 200
    tampered_data = tampered_res.json()
    assert tampered_data["is_valid"] is False
    assert tampered_data["tamper_detected"] is True


def test_sealed_replay_bundle_and_offline_execution(client, db_session):
    """
    Differentiating Feature #2: Sealed Replay Bundles with model metadata,
    runtime environment, HMAC signatures, and offline deterministic execution.
    """
    reg = client.post("/api/v1/auth/register", json={
        "name": "Replay User",
        "email": "replay@bank.com",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create investigation
    inv_id = "inv_replay_test_999"
    txn = models.Transaction(txn_id="txn_replay_999", amount=9500.0, channel="WIRE")
    db_session.add(txn)
    inv = models.Investigation(
        investigation_id=inv_id,
        txn_id="txn_replay_999",
        tenant_id="default_tenant",
        status="COMPLETED",
        risk_score=0.65
    )
    db_session.add(inv)
    db_session.commit()

    # Export replay snapshot
    export_res = client.get(f"/api/v1/investigations/{inv_id}/export-replay", headers=headers)
    assert export_res.status_code == 200
    bundle = export_res.json()

    assert "model_metadata" in bundle
    assert "prompt_metadata" in bundle
    assert "runtime_environment" in bundle
    assert "replay_fingerprint" in bundle
    assert "digital_signature" in bundle

    # Verify bundle cryptographically using CLI verification function
    is_valid, errors = verify_replay_bundle(bundle)
    assert is_valid is True, f"Replay verification failed: {errors}"

    # Offline deterministic execution
    reproduced, meta = run_deterministic_replay(bundle)
    assert reproduced is True
    assert meta["is_reproduced"] is True
