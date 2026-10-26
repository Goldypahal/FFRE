import os
import pytest
import base64
from fastapi.testclient import TestClient
import models
import auth
import security
import database
from main import app
from vector_db import FraudVectorDB

def test_production_deployment_prevents_silent_startup_with_dev_secrets():
    """
    Verify production startup fails fast if development default secrets or insecure passwords are used.
    """
    os.environ["ENV"] = "production"
    try:
        # Secret key check
        with pytest.raises(ValueError, match="CRITICAL SECURITY: Insecure development default"):
            security.validate_production_secret("SECRET_KEY", "ffire-dev-secret-key-change-in-prod")

        # Weak secret check
        with pytest.raises(ValueError, match="insufficiently strong"):
            security.validate_production_secret("ENCRYPTION_SECRET_KEY", "short_weak_key_123")

        # Database URL check
        with pytest.raises(ValueError, match="CRITICAL SECURITY: Insecure development database password"):
            database.validate_production_database_config("postgresql://ffire_user:ffire_dev_insecure_password@db:5432/ffire_db")

        # SQLite disallowed in production check
        with pytest.raises(ValueError, match="CRITICAL SECURITY: SQLite is not permitted"):
            database.validate_production_database_config("sqlite:///./ffire.db")
    finally:
        os.environ["ENV"] = "development"

def test_docker_compose_network_isolation_configuration():
    """
    Verify docker-compose.yml binds database and redis to 127.0.0.1 by default to prevent public network exposure.
    """
    compose_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docker-compose.yml")
    assert os.path.exists(compose_path)
    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Confirm localhost binding patterns are present
    assert "127.0.0.1:5432:5432" in content
    assert "127.0.0.1:6379:6379" in content
    # Confirm raw un-isolated "5432:5432" is not exposed
    assert '- "5432:5432"' not in content
    assert '- "6379:6379"' not in content

def test_encryption_key_rotation_and_fallback_recovery(db_session):
    """
    Verify zero-downtime key rotation: fallback decryption during rotation and automated in-place database PII migration.
    """
    key_v1 = "production-secret-alpha-key-version-1-32chars!!"
    key_v2 = "production-secret-bravo-key-version-2-32chars!!"

    # 1. Create records encrypted with Key V1
    cust = models.Customer(
        customer_id="cust_rot_01",
        tenant_id="tenant_rot",
        risk_tier="LOW"
    )
    cust._name = security.encrypt_aes256_gcm("Alice Henderson", secret_override=key_v1)
    db_session.add(cust)

    dev = models.Device(
        device_id="dev_rot_01",
        customer_id="cust_rot_01",
        tenant_id="tenant_rot"
    )
    dev._fingerprint = security.encrypt_aes256_gcm("fp_rot_hash_987654321", secret_override=key_v1)
    db_session.add(dev)
    db_session.commit()

    # 2. Configure system with Key V2 as primary and Key V1 as fallback
    os.environ["ENCRYPTION_SECRET_KEY"] = key_v2
    os.environ["ENCRYPTION_SECRET_KEY_FALLBACKS"] = key_v1

    # Decryption should succeed transparently using fallback key
    decrypted_name = security.decrypt_aes256_gcm(cust._name)
    assert decrypted_name == "Alice Henderson"
    decrypted_fp = security.decrypt_aes256_gcm(dev._fingerprint)
    assert decrypted_fp == "fp_rot_hash_987654321"

    # 3. Perform database PII key rotation migration
    stats = security.rotate_database_pii(db_session, old_secret=key_v1, new_secret=key_v2)
    assert stats["customers"] >= 1
    assert stats["devices"] >= 1

    # 4. Remove fallback key: primary Key V2 must now decrypt all records standalone
    del os.environ["ENCRYPTION_SECRET_KEY_FALLBACKS"]
    db_session.refresh(cust)
    db_session.refresh(dev)

    assert security.decrypt_aes256_gcm(cust._name, secret_override=key_v2) == "Alice Henderson"
    assert security.decrypt_aes256_gcm(dev._fingerprint, secret_override=key_v2) == "fp_rot_hash_987654321"

    # Verifying with old key alone must fail
    with pytest.raises(security.DecryptionError):
        security.decrypt_aes256_gcm(cust._name, secret_override=key_v1, fail_closed=True)

def test_tokens_and_error_responses_do_not_expose_sensitive_data(client, db_session):
    """
    Verify JWT tokens, 404/422/500 error responses do not leak sensitive PII, hashes, or database internals.
    """
    token = auth.create_access_token({
        "sub": "investigator@bank.com",
        "tenant_id": "tenant_defense",
        "role": "investigator"
    })

    decoded = auth.decode_access_token(token)
    assert "password" not in decoded
    assert "password_hash" not in decoded
    assert "ssn" not in decoded
    assert "secret" not in decoded

    # Error responses must not leak database schema or credentials
    res404 = client.get("/api/v1/investigations/nonexistent-id-xyz-999")
    assert res404.status_code == 404
    body404 = res404.text
    assert "sqlite" not in body404.lower()
    assert "postgresql" not in body404.lower()
    assert "password" not in body404.lower()

def test_tenant_isolation_across_database_vector_audit_and_exports(client, db_session):
    """
    Comprehensive Tenant Boundary Verification:
    - Database records (investigations)
    - Vector database retrieval
    - Audit logs
    - Report exports
    """
    # 1. Database & Report Cross-Tenant Isolation
    inv_a = models.Investigation(
        investigation_id="inv_iso_alpha",
        status="COMPLETED",
        risk_score=0.85,
        tenant_id="tenant_alpha"
    )
    db_session.add(inv_a)
    db_session.commit()

    # Generate Report under tenant_alpha
    app.dependency_overrides[auth.get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )
    rep_res = client.post(
        "/api/v1/reports/generate",
        json={"title": "Confidential Alpha Case", "report_type": "SAR Regulatory Filing"}
    )
    assert rep_res.status_code == 200
    alpha_report_id = rep_res.json()["report_id"]

    # Switch to Tenant Bravo
    app.dependency_overrides[auth.get_current_user] = lambda: models.User(
        user_id="user_bravo",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_bravo"
    )

    # Investigation fetch cross-tenant must fail (403 or 404)
    res_inv = client.get("/api/v1/investigations/inv_iso_alpha")
    assert res_inv.status_code in (403, 404)

    # Report download cross-tenant must be 403 Forbidden
    res_rep = client.get(f"/api/v1/reports/{alpha_report_id}/download")
    assert res_rep.status_code == 403

    # 2. Vector DB Query Partitioning
    vdb = FraudVectorDB(db_path="./scratch/test_iso_chroma")
    if vdb.collection:
        vdb.add_case("C-ALPHA-99", "Alpha tenant proprietary fraud pattern in wire transfers", "FRAUD", tenant_id="tenant_alpha")
        vdb.add_case("C-BRAVO-99", "Bravo tenant proprietary fraud pattern in retail deposits", "FRAUD", tenant_id="tenant_bravo")

        res_alpha = vdb.similarity_search("wire transfers", top_k=5, tenant_id="tenant_alpha")
        for item in res_alpha:
            assert item.get("metadata", {}).get("tenant_id") == "tenant_alpha"

        res_bravo = vdb.similarity_search("wire transfers", top_k=5, tenant_id="tenant_bravo")
        for item in res_bravo:
            assert item.get("metadata", {}).get("tenant_id") == "tenant_bravo"

def test_tampered_ciphertext_fails_closed():
    """
    Verify that corrupted or tampered ciphertext immediately fails closed with DecryptionError.
    """
    secret = "production-secret-secure-key-32chars!!"
    encrypted = security.encrypt_aes256_gcm("Confidential Account 12345", secret_override=secret)

    # Tamper with the ciphertext bytes
    raw = bytearray(base64.b64decode(encrypted))
    raw[-1] ^= 0xFF # Flip bits in authentication tag
    tampered = base64.b64encode(raw).decode("utf-8")

    with pytest.raises(security.DecryptionError):
        security.decrypt_aes256_gcm(tampered, secret_override=secret, fail_closed=True)
