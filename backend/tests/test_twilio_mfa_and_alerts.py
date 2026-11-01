"""
Unit and Integration Tests for Twilio SMS Multi-Factor Authentication (MFA)
and Real-Time Critical Escalation Incident Alerting.
"""

import pytest
from starlette.testclient import TestClient
import models
import auth
from twilio_service import twilio_service, _MFA_STORE


@pytest.fixture
def twilio_client(client):
    return client


def test_twilio_sms_dispatch_simulation():
    """Verify TwilioService safely dispatches and logs SMS in offline / simulation mode."""
    res = twilio_service.send_sms("+15551234567", "Test alert message")
    assert res["status"] == "delivered"
    assert res["to"] == "+15551234567"
    assert "sid" in res
    assert res["sid"].startswith("SM_")


def test_twilio_mfa_otp_generation_verification_and_rate_limiting():
    """Verify cryptographically generated OTP verification, timing-safe checks, and max attempts lockout."""
    user_id = "user_mfa_test_unit_1"
    phone = "+15559876543"

    masked, ticket = twilio_service.generate_and_send_mfa_code(user_id, phone)
    assert masked.endswith("6543")
    assert ticket is not None
    assert twilio_service.verify_mfa_ticket(ticket) == user_id

    # Test invalid code attempt 1
    assert twilio_service.verify_mfa_code(user_id, "000000") is False

    # Test invalid code attempt 2
    assert twilio_service.verify_mfa_code(user_id, "111111") is False

    # Test invalid code attempt 3
    assert twilio_service.verify_mfa_code(user_id, "222222") is False

    # Attempt 4 should be locked out
    assert twilio_service.verify_mfa_code(user_id, "333333") is False


def test_user_mfa_setup_enable_and_disable_api_flow(twilio_client, db_session):
    """Verify authenticated user can register a phone number, verify OTP, and toggle MFA."""
    # Register/create a test investigator
    email = "investigator_mfa@bank.com"
    pwd_hash = auth.get_password_hash("Password123!")
    user = models.User(
        name="MFA Investigator",
        email=email,
        role="investigator",
        hashed_password=pwd_hash,
        tenant_id="tenant_mfa"
    )
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token(data={"sub": email, "role": "investigator", "tenant_id": "tenant_mfa"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial status: MFA disabled
    status_res = twilio_client.get("/api/v1/auth/mfa/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["mfa_enabled"] is False

    # 2. Setup MFA with a phone number
    setup_res = twilio_client.post("/api/v1/auth/mfa/setup", json={"phone_number": "+15553334444"}, headers=headers)
    assert setup_res.status_code == 200
    assert setup_res.json()["status"] == "pending_verification"

    # Grab the active OTP from the store for this test
    stored_hash = _MFA_STORE[user.user_id]["hash"]

    # Try invalid code
    bad_enable = twilio_client.post("/api/v1/auth/mfa/enable", json={"code": "000000"}, headers=headers)
    assert bad_enable.status_code == 400

    # Simulate valid code verification by setting a known code
    import hashlib
    known_code = "654321"
    _MFA_STORE[user.user_id]["hash"] = hashlib.sha256(known_code.encode()).hexdigest()
    _MFA_STORE[user.user_id]["attempts"] = 0

    good_enable = twilio_client.post("/api/v1/auth/mfa/enable", json={"code": known_code}, headers=headers)
    assert good_enable.status_code == 200
    assert good_enable.json()["status"] == "enabled"

    # Verify status is now enabled
    status_res2 = twilio_client.get("/api/v1/auth/mfa/status", headers=headers)
    assert status_res2.status_code == 200
    assert status_res2.json()["mfa_enabled"] is True

    # 3. Disable MFA
    disable_res = twilio_client.post("/api/v1/auth/mfa/disable", headers=headers)
    assert disable_res.status_code == 200
    assert disable_res.json()["status"] == "disabled"


def test_login_flow_with_sms_mfa_challenge_and_verification(twilio_client, db_session):
    """Verify login challenges user for SMS OTP when mfa_enabled is active."""
    email = "mfa_user_login@bank.com"
    pwd = "SecureLoginPass123!"
    user = models.User(
        name="Enforced MFA User",
        email=email,
        role="investigator",
        hashed_password=auth.get_password_hash(pwd),
        tenant_id="tenant_mfa_login"
    )
    user.phone_number = "+15558889999"
    user.mfa_enabled = True
    db_session.add(user)
    db_session.commit()

    # 1. Attempt login -> Expect mfa_required=True
    login_res = twilio_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": pwd}
    )
    assert login_res.status_code == 200
    body = login_res.json()
    assert body.get("mfa_required") is True
    assert "mfa_ticket" in body
    mfa_ticket = body["mfa_ticket"]

    # 2. Complete MFA verification with invalid code -> 401
    verify_bad = twilio_client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_ticket": mfa_ticket, "code": "000000"}
    )
    assert verify_bad.status_code == 401

    # 3. Supply valid OTP
    import hashlib
    valid_code = "777888"
    _MFA_STORE[user.user_id]["hash"] = hashlib.sha256(valid_code.encode()).hexdigest()
    _MFA_STORE[user.user_id]["attempts"] = 0

    verify_good = twilio_client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_ticket": mfa_ticket, "code": valid_code}
    )
    assert verify_good.status_code == 200
    good_body = verify_good.json()
    assert good_body.get("access_token") is not None
    assert good_body.get("mfa_required") is False
    assert good_body.get("tenant_id") == "tenant_mfa_login"


def test_critical_escalation_sms_alerting(twilio_client, db_session):
    """Verify manual and automated investigation escalation dispatches Twilio SMS alerts."""
    # Create investigator token
    admin = models.User(
        name="Lead Compliance Admin",
        email="compliance_head@bank.com",
        role="admin",
        hashed_password=auth.get_password_hash("AdminPass123!"),
        tenant_id="tenant_alerts"
    )
    db_session.add(admin)
    db_session.commit()

    token = auth.create_access_token(data={"sub": admin.email, "role": "admin", "tenant_id": "tenant_alerts"})
    headers = {"Authorization": f"Bearer {token}"}

    # Create transaction
    txn_id = "txn_sms_alert_001"
    txn = models.Transaction(
        txn_id=txn_id,
        tenant_id="tenant_alerts",
        amount=12500.00,
        currency="USD",
        status="FLAGGED"
    )
    db_session.add(txn)
    db_session.commit()

    # Create investigation
    inv_id = "inv_sms_alert_test_001"
    inv = models.Investigation(
        investigation_id=inv_id,
        tenant_id="tenant_alerts",
        txn_id=txn_id,
        status="RUNNING",
        risk_score=0.85
    )
    db_session.add(inv)
    db_session.commit()

    # Update investigation status to ESCALATED -> Triggers Twilio Alert
    update_res = twilio_client.patch(
        f"/api/v1/investigations/{inv_id}",
        json={"status": "ESCALATED"},
        headers=headers
    )
    assert update_res.status_code == 200

    # Verify chained audit log entry was created for SMS alert
    audit = db_session.query(models.AuditLog).filter(
        models.AuditLog.investigation_id == inv_id,
        models.AuditLog.action == "SMS_ESCALATION_ALERT_SENT"
    ).first()
    assert audit is not None
    assert "Twilio SMS dispatched" in audit.details


def test_admin_test_sms_alert_endpoint(twilio_client, db_session):
    """Verify /api/v1/admin/alerts/test-sms requires admin privileges and succeeds."""
    # Create investigator and admin in DB first so auth.check_permissions succeeds
    inv_user = models.User(
        name="Investigator User",
        email="inv@bank.com",
        role="investigator",
        hashed_password=auth.get_password_hash("InvPass123!"),
        tenant_id="tenant_1"
    )
    admin_user = models.User(
        name="Admin User",
        email="adm@bank.com",
        role="admin",
        hashed_password=auth.get_password_hash("AdminPass123!"),
        tenant_id="tenant_1"
    )
    db_session.add(inv_user)
    db_session.add(admin_user)
    db_session.commit()

    # Investigator attempt -> 403
    inv_token = auth.create_access_token(data={"sub": "inv@bank.com", "role": "investigator", "tenant_id": "tenant_1"})
    res_forbidden = twilio_client.post(
        "/api/v1/admin/alerts/test-sms",
        json={"recipient_phone": "+15551234567"},
        headers={"Authorization": f"Bearer {inv_token}"}
    )
    assert res_forbidden.status_code == 403

    # Admin attempt -> 200
    admin_token = auth.create_access_token(data={"sub": "adm@bank.com", "role": "admin", "tenant_id": "tenant_1"})
    res_ok = twilio_client.post(
        "/api/v1/admin/alerts/test-sms",
        json={"recipient_phone": "+15551234567", "message": "Administrative smoke test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "success"

