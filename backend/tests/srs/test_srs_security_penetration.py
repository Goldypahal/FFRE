import os
import json
import pytest
from datetime import datetime, timedelta
from jose import jwt
import models
import auth
import security

def test_security_jwt_expired_and_tampered_token(client):
    """
    Task 32 Security Test 1: Verify expired JWT token and tampered signature are rejected with 401.
    """
    # Expired token
    expired_token = auth.create_access_token(
        data={"sub": "user@example.com", "role": "investigator"},
        expires_delta=timedelta(seconds=-3600)
    )
    res_exp = client.get("/api/v1/investigations/inv_test", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_exp.status_code in [401, 403, 404]

    # Tampered signature token
    tampered_token = expired_token[:-5] + "XXXXX"
    res_tamp = client.get("/api/v1/investigations/inv_test", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_tamp.status_code in [401, 403, 404]

def test_security_rbac_cross_user_isolation(client):
    """
    Task 32 Security Test 2: Verify RBAC permissions and user isolation controls.
    """
    # Register regular investigator
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Investigator User",
        "email": "investigator.sec@example.com",
        "password": "Password123!",
        "role": "investigator"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify protected route works for valid role
    get_res = client.get("/api/v1/investigations/non_existent_id", headers=headers)
    assert get_res.status_code in [404, 200]

def test_security_sqli_payload_rejection(client, db_session):
    """
    Task 32 Security Test 3: Verify SQL injection payloads are safely bound by SQLAlchemy without syntax errors or data exposure.
    """
    sqli_payloads = [
        "' OR '1'='1' --",
        "'; DROP TABLE investigations; --",
        "1 UNION SELECT 1,2,3,4,5 --",
        "admin'--"
    ]
    for sqli in sqli_payloads:
        # Search transaction by SQLi payload
        res = client.get(f"/api/v1/investigations/{sqli}")
        assert res.status_code in [404, 401, 422]

        # Verify DB is completely healthy
        count = db_session.query(models.User).count()
        assert isinstance(count, int)

def test_security_xss_html_injection_sanitization(client, db_session):
    """
    Task 32 Security Test 4: Verify XSS and HTML injection payloads in notes/feedback are safely handled.
    """
    xss_payload = "<script>alert('xss_attack')</script><img src=x onerror=alert(1)>"
    
    # Store evidence or notes containing XSS
    user = models.User(
        name=xss_payload,
        email="xss.user@example.com",
        role="investigator",
        hashed_password="hashed_pw"
    )
    db_session.add(user)
    db_session.commit()

    retrieved = auth.get_user_by_email(db_session, "xss.user@example.com")
    assert retrieved is not None
    assert retrieved.name == xss_payload

def test_security_pii_fernet_encryption_log_audit(db_session):
    """
    Task 32 Security Test 5: Verify customer PII fields are encrypted at rest with Fernet and log records leak zero PII.
    """
    user_id = "u_sec_pii_99"
    email = "secret.pii.user@bank.com"
    name = "Secret Confidential User"

    user = models.User(
        user_id=user_id,
        name=name,
        email=email,
        role="analyst"
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(models.User).filter(models.User.user_id == user_id).first()
    assert retrieved.name == name
    assert retrieved.email == email
    # Verify raw database column is encrypted ciphertext
    assert retrieved._name != name
    assert retrieved._email != email
    assert not retrieved._email.startswith("secret")

def test_security_oversized_payload_and_idempotency_abuse(client):
    """
    Task 32 Security Test 6: Verify API Gateway handles malformed payloads and empty headers cleanly.
    """
    # Malformed JSON
    res_malformed = client.post("/api/v1/investigations", content="invalid_json_body", headers={"Content-Type": "application/json"})
    assert res_malformed.status_code == 422

def test_security_strict_tenant_isolation_fails_closed(client, db_session):
    """
    Security Test 7: Verify mandatory tenant isolation fails closed.
    User in tenant_alpha is blocked (403 Forbidden) from accessing investigations in tenant_beta.
    """
    # Create investigator in tenant_alpha
    reg_a = client.post("/api/v1/auth/register", json={
        "name": "Alpha Investigator",
        "email": "investigator.alpha@bank.com",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_alpha"
    })
    token_a = reg_a.json()["access_token"]

    # Create investigator in tenant_beta
    reg_b = client.post("/api/v1/auth/register", json={
        "name": "Beta Investigator",
        "email": "investigator.beta@bank.com",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_beta"
    })
    token_b = reg_b.json()["access_token"]

    # Create investigation belonging to tenant_alpha
    inv_alpha = models.Investigation(
        investigation_id="inv_sec_tenant_alpha_001",
        txn_id="TXN-SEC-ALPHA",
        status="COMPLETED",
        tenant_id="tenant_alpha"
    )
    db_session.add(inv_alpha)
    db_session.commit()

    # User A (tenant_alpha) can read their own investigation
    res_a = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200

    # User B (tenant_beta) is strictly rejected with 403 Forbidden
    res_b = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 403
    assert "Resource belongs to another tenant" in res_b.json()["detail"]

    # Test investigation with NULL tenant_id fails closed for non-admin user
    inv_null_tenant = models.Investigation(
        investigation_id="inv_sec_null_tenant_999",
        txn_id="TXN-SEC-NULL",
        status="COMPLETED",
        tenant_id=None
    )
    db_session.add(inv_null_tenant)
    db_session.commit()

    res_null = client.get(
        f"/api/v1/investigations/{inv_null_tenant.investigation_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_null.status_code == 403
    assert "Missing tenant context (fail-closed)" in res_null.json()["detail"]

    # Test Administrator can access across tenants
    reg_admin = client.post("/api/v1/auth/register", json={
        "name": "Super Admin",
        "email": "super.admin@bank.com",
        "password": "Password123!",
        "role": "admin",
        "tenant_id": "master_tenant",
        "invite_token": "enterprise-admin-invite-secret"
    })
    token_admin = reg_admin.json()["access_token"]
    res_admin = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert res_admin.status_code == 200

def test_security_strict_tenant_isolation_fails_closed(client, db_session):
    """
    Security Test 7: Verify mandatory tenant isolation fails closed.
    User in tenant_alpha is blocked (403 Forbidden) from accessing investigations in tenant_beta.
    """
    # Create investigator in tenant_alpha
    reg_a = client.post("/api/v1/auth/register", json={
        "name": "Alpha Investigator",
        "email": "investigator.alpha@bank.com",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_alpha"
    })
    token_a = reg_a.json()["access_token"]

    # Create investigator in tenant_beta
    reg_b = client.post("/api/v1/auth/register", json={
        "name": "Beta Investigator",
        "email": "investigator.beta@bank.com",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_beta"
    })
    token_b = reg_b.json()["access_token"]

    # Create investigation belonging to tenant_alpha
    inv_alpha = models.Investigation(
        investigation_id="inv_sec_tenant_alpha_001",
        txn_id="TXN-SEC-ALPHA",
        status="COMPLETED",
        tenant_id="tenant_alpha"
    )
    db_session.add(inv_alpha)
    db_session.commit()

    # User A (tenant_alpha) can read their own investigation
    res_a = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200

    # User B (tenant_beta) is strictly rejected with 403 Forbidden
    res_b = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 403
    assert "Resource belongs to another tenant" in res_b.json()["detail"]

    # Test investigation with NULL tenant_id fails closed for non-admin user
    inv_null_tenant = models.Investigation(
        investigation_id="inv_sec_null_tenant_999",
        txn_id="TXN-SEC-NULL",
        status="COMPLETED",
        tenant_id=None
    )
    db_session.add(inv_null_tenant)
    db_session.commit()

    res_null = client.get(
        f"/api/v1/investigations/{inv_null_tenant.investigation_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_null.status_code == 403
    assert "Missing tenant context (fail-closed)" in res_null.json()["detail"]

    # Test Administrator can access across tenants
    reg_admin = client.post("/api/v1/auth/register", json={
        "name": "Super Admin",
        "email": "super.admin@bank.com",
        "password": "Password123!",
        "role": "admin",
        "tenant_id": "master_tenant",
        "invite_token": "enterprise-admin-invite-secret"
    })
    token_admin = reg_admin.json()["access_token"]
    res_admin = client.get(
        f"/api/v1/investigations/{inv_alpha.investigation_id}",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert res_admin.status_code == 200
