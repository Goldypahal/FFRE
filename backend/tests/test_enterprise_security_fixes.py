import pytest

import datetime

import json

import hashlib

import hmac

import os

from fastapi.testclient import TestClient

import models

from scripts.replay_cli import verify_replay_bundle, run_deterministic_replay



BOOTSTRAP_SECRET = "test-bootstrap-secret-enterprise-2026"





def test_auth_register_bootstrap_and_invitation_flow(client, db_session):

    """

    P0 Remediation: Ensure unauthenticated users cannot self-register as admin or pick tenants,

    initial admin must bootstrap with external BOOTSTRAP_SECRET_KEY,

    and subsequent users require authenticated, database-backed single-use invitations.

    """

    # 1. Attempting public registration on empty DB without invitation must fail (403)

    res_public_blocked = client.post("/api/v1/auth/register", json={

        "name": "Attacker",

        "email": "attacker@evil.com",

        "password": "Password123!",

        "tenant_id": "tenant_prime"

    })

    assert res_public_blocked.status_code == 403

    assert "Public self-registration is disabled" in res_public_blocked.json()["detail"]



    # 2. Attempting bootstrap with invalid secret must fail (403)

    res_bad_secret = client.post("/api/v1/auth/bootstrap", json={

        "name": "Org Admin",

        "email": "admin@primebank.com",

        "password": "Password123!",

        "tenant_id": "tenant_prime",

        "bootstrap_secret": "wrong-secret-value"

    })

    assert res_bad_secret.status_code == 403

    assert "Invalid or missing bootstrap secret" in res_bad_secret.json()["detail"]



    # 3. Legitimate administrator bootstraps with external BOOTSTRAP_SECRET_KEY

    res_admin = client.post("/api/v1/auth/bootstrap", json={

        "name": "Org Admin",

        "email": "admin@primebank.com",

        "password": "Password123!",

        "tenant_id": "tenant_prime",

        "bootstrap_secret": BOOTSTRAP_SECRET

    })

    assert res_admin.status_code == 200

    admin_data = res_admin.json()

    admin_token = admin_data["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}



    # 4. Subsequent bootstrap attempts must be rejected (400) because users already exist

    res_second_bootstrap = client.post("/api/v1/auth/bootstrap", json={

        "name": "Second Admin",

        "email": "admin2@primebank.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

    })

    assert res_second_bootstrap.status_code == 400

    assert "already contains registered users" in res_second_bootstrap.json()["detail"]



    # 5. User attempts registration without invite token -> rejected (403)

    res_unauth = client.post("/api/v1/auth/register", json={

        "name": "Uninvited User",

        "email": "uninvited@evil.com",

        "password": "Password123!",

        "tenant_id": "tenant_prime"

    })

    assert res_unauth.status_code == 403

    assert "Public self-registration is disabled" in res_unauth.json()["detail"]



    # 6. Old hardcoded default invite secret must be strictly rejected

    res_hardcoded = client.post("/api/v1/auth/register", json={

        "name": "Hacker",

        "email": "hacker@evil.com",

        "password": "Password123!",

        "invite_token": "enterprise-admin-invite-secret"

    })

    assert res_hardcoded.status_code == 403

    assert "Invalid, expired, or already-consumed invitation token" in res_hardcoded.json()["detail"]



    # 7. Admin issues valid single-use invitation for an investigator

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



    # 8. User registers with invitation token -> server assigns tenant and role

    res_user = client.post("/api/v1/auth/register", json={

        "name": "Lead Investigator",

        "email": "lead.investigator@primebank.com",

        "password": "Password123!",

        "invite_token": invite_token

    })

    assert res_user.status_code == 200

    user_data = res_user.json()

    assert user_data["tenant_id"] == "tenant_prime"



    # 9. Replay attack: attempt to reuse the invitation token -> rejected (403)

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

    client.post("/api/v1/auth/bootstrap", json={

        "name": "Admin",

        "email": "admin@bank.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

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

    assert "restricted to vip@bank.com" in res_wrong_email.json()["detail"]



    # 4. Correct email succeeds

    res_right_email = client.post("/api/v1/auth/register", json={

        "name": "VIP User",

        "email": "vip@bank.com",

        "password": "Password123!",

        "invite_token": bound_inv.token

    })

    assert res_right_email.status_code == 200

    assert res_right_email.json()["tenant_id"] == "tenant_alpha"





def test_auth_logout_revokes_token(client):

    """

    Finding Remediation: Test that logging out adds the JWT to the revocation blocklist,

    making subsequent requests with that token return 401 Unauthorized.

    """

    reg = client.post("/api/v1/auth/bootstrap", json={

        "name": "Logout Tester",

        "email": "logout.test@example.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

    })

    token = reg.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}



    # Verify token works

    get_res = client.get("/api/v1/investigations/non_existent_id", headers=headers)

    assert get_res.status_code in [404, 200]



    # Logout to revoke

    logout_res = client.post("/api/v1/auth/logout", headers=headers)

    assert logout_res.status_code == 200



    # Token must now be rejected

    after_res = client.get("/api/v1/investigations/non_existent_id", headers=headers)

    assert after_res.status_code == 401

    assert "revoked" in after_res.json()["detail"].lower()





def test_investigation_soft_delete_and_legal_hold(client, db_session):

    """

    Finding Remediation: Ensure investigations are soft-deleted, tombstones are recorded,

    and investigations under active legal hold cannot be deleted.

    """

    reg = client.post("/api/v1/auth/bootstrap", json={

        "name": "Admin User",

        "email": "admin.del@bank.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

    })

    admin_token = reg.json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}



    # Create investigation

    inv_id = "inv_test_soft_del_001"

    inv = models.Investigation(

        investigation_id=inv_id,

        txn_id="TXN-DEL-01",

        tenant_id="tenant_prime",

        status="QUEUED"

    )

    db_session.add(inv)

    db_session.commit()



    # 1. Apply legal hold

    hold_res = client.post(

        f"/api/v1/investigations/{inv_id}/legal-hold",

        json={"legal_hold": True, "reason": "SEC Subpoena #84920"},

        headers=admin_headers

    )

    assert hold_res.status_code == 200

    assert hold_res.json()["legal_hold"] is True



    # 2. Deletion under legal hold must fail (409 Conflict)

    del_blocked = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)

    assert del_blocked.status_code == 409

    assert "legal hold" in del_blocked.json()["detail"].lower()



    # 3. Release legal hold

    release_res = client.post(

        f"/api/v1/investigations/{inv_id}/legal-hold",

        json={"legal_hold": False, "reason": "Subpoena cleared"},

        headers=admin_headers

    )

    assert release_res.status_code == 200



    # 4. Soft deletion succeeds

    del_ok = client.delete(f"/api/v1/investigations/{inv_id}", headers=admin_headers)

    assert del_ok.status_code == 200

    assert del_ok.json()["status"] in ["success", "soft_deleted"]



    # Subsequent fetch returns 404

    get_res = client.get(f"/api/v1/investigations/{inv_id}", headers=admin_headers)

    assert get_res.status_code == 404





def test_verifier_api_ed25519_attestation_and_tamper_detection(client):

    """

    Differentiating Feature #1: Independent Verifier API with Ed25519 asymmetric signature,

    public key distribution, empty claim rejection, and third-party attestation verification.

    """

    reg = client.post("/api/v1/auth/bootstrap", json={

        "name": "Verifier Admin",

        "email": "verifier@enterprise.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

    })

    token = reg.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}



    # 1. Public key distribution endpoint

    pk_res = client.get("/api/v1/verifier/public-key")

    assert pk_res.status_code == 200

    pk_data = pk_res.json()

    assert pk_data["algorithm"] == "Ed25519"

    assert "public_key_hex" in pk_data

    assert "public_key_pem" in pk_data



    # 2. Empty narrative / zero claims defense -> must return 0.0 grounding and REJECTED_EMPTY

    empty_res = client.post("/api/v1/verifier/evaluate", json={

        "narrative": "   ",

        "evidence": {"amount": 100.0}

    }, headers=headers)

    assert empty_res.status_code == 200

    empty_data = empty_res.json()

    assert empty_data["grounding_score"] == 0.0

    assert empty_data["verification_status"] == "REJECTED_EMPTY"



    # 3. Genuine grounded evaluation

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

    assert sig is not None and len(sig) == 128  # Ed25519 is 64 bytes = 128 hex chars



    # 4. Third-party attestation verification endpoint succeeds for authentic attestation

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



    # 5. Third-party attestation verification succeeds with explicit public_key_hex

    verify_payload_explicit_pk = dict(verify_payload)

    verify_payload_explicit_pk["public_key_hex"] = pk_data["public_key_hex"]

    verify_res_pk = client.post("/api/v1/verifier/verify-attestation", json=verify_payload_explicit_pk)

    assert verify_res_pk.status_code == 200

    assert verify_res_pk.json()["is_valid"] is True



    # 6. Tampering detection: if someone alters the score or narrative, verification fails

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

    runtime environment, Ed25519/HMAC signatures, and offline deterministic execution.

    """

    reg = client.post("/api/v1/auth/bootstrap", json={

        "name": "Replay User",

        "email": "replay@bank.com",

        "password": "Password123!",

        "bootstrap_secret": BOOTSTRAP_SECRET

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



    # Offline deterministic execution with real rules and inference

    reproduced, meta = run_deterministic_replay(bundle)

    assert reproduced is True

    assert meta["is_reproduced"] is True

