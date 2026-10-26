import pytest
import uuid
import datetime
import hashlib
import json
from decimal import Decimal
from fastapi.testclient import TestClient

import models
import auth
from main import app, get_db, generate_replay_snapshot


@pytest.fixture
def auth_tenant_alpha():
    user = models.User(
        user_id="user_alpha_001",
        tenant_id="tenant_alpha",
        role="investigator",
        status="active"
    )
    user.name = "Analyst Alpha"
    user.email = "alpha@tenant-a.com"
    return user


@pytest.fixture
def auth_tenant_beta():
    user = models.User(
        user_id="user_beta_001",
        tenant_id="tenant_beta",
        role="investigator",
        status="active"
    )
    user.name = "Analyst Beta"
    user.email = "beta@tenant-b.com"
    return user


@pytest.fixture
def seeded_investigation(db_session):
    """Seed an investigation with complete relational dependencies and chained audit logs."""
    txn_id = f"TXN-REPLAY-{uuid.uuid4().hex[:8]}"
    inv_id = f"INV-REPLAY-{uuid.uuid4().hex[:8]}"
    acct_id = f"ACCT-{uuid.uuid4().hex[:8]}"
    cust_id = f"CUST-{uuid.uuid4().hex[:8]}"
    merch_id = f"MERCH-{uuid.uuid4().hex[:8]}"

    cust = models.Customer(
        customer_id=cust_id,
        tenant_id="tenant_alpha",
        kyc_status="VERIFIED",
        risk_tier="LOW"
    )
    cust.name = "Alice Replay"
    cust.email = "alice.replay@example.com"
    db_session.add(cust)

    acct = models.Account(
        account_id=acct_id,
        tenant_id="tenant_alpha",
        customer_id=cust_id,
        account_type="CHECKING",
        balance=Decimal("15000.00")
    )
    db_session.add(acct)

    merch = models.Merchant(
        merchant_id=merch_id,
        tenant_id="tenant_alpha",
        name="Reliable Electronics",
        category="RETAIL"
    )
    db_session.add(merch)

    txn = models.Transaction(
        txn_id=txn_id,
        tenant_id="tenant_alpha",
        account_id=acct_id,
        merchant_id=merch_id,
        amount=Decimal("450.00"),
        currency="USD",
        status="COMPLETED",
        channel="web",
        ip_address="192.168.1.100"
    )
    db_session.add(txn)

    inv = models.Investigation(
        investigation_id=inv_id,
        tenant_id="tenant_alpha",
        txn_id=txn_id,
        status="COMPLETED",
        risk_score=Decimal("0.125"),
        confidence=Decimal("0.950"),
        report="Legitimate low-risk transaction."
    )
    db_session.add(inv)
    db_session.commit()

    # Create chained audit logs
    log1 = models.AuditLog(
        investigation_id=inv_id,
        tenant_id="tenant_alpha",
        action="INVESTIGATION_STARTED",
        details="Initial submission received and validated"
    )
    db_session.add(log1)
    db_session.commit()

    log2 = models.AuditLog(
        investigation_id=inv_id,
        tenant_id="tenant_alpha",
        action="EVIDENCE_EVALUATED",
        details="Customer KYC verified and historical transaction patterns checked"
    )
    db_session.add(log2)
    db_session.commit()

    log3 = models.AuditLog(
        investigation_id=inv_id,
        tenant_id="tenant_alpha",
        action="DECISION_APPROVED",
        details="Autonomously approved with calibrated risk score 0.125"
    )
    db_session.add(log3)
    db_session.commit()

    return inv


def test_audit_log_verify_chain_unit():
    """Unit test: AuditLog.verify_chain detects valid chains, broken links, tampered details, and invalid genesis."""
    log1_id = str(uuid.uuid4())
    ts1 = datetime.datetime.utcnow().isoformat()
    h1 = models.AuditLog.calculate_entry_hash(None, log1_id, "ACT_INIT", ts1, "Genesis details")
    entry1 = {
        "log_id": log1_id,
        "action": "ACT_INIT",
        "timestamp": ts1,
        "previous_hash": None,
        "entry_hash": h1,
        "details": "Genesis details"
    }

    log2_id = str(uuid.uuid4())
    ts2 = datetime.datetime.utcnow().isoformat()
    h2 = models.AuditLog.calculate_entry_hash(h1, log2_id, "ACT_STEP2", ts2, "Step 2 details")
    entry2 = {
        "log_id": log2_id,
        "action": "ACT_STEP2",
        "timestamp": ts2,
        "previous_hash": h1,
        "entry_hash": h2,
        "details": "Step 2 details"
    }

    # 1. Valid chain
    is_valid, errors = models.AuditLog.verify_chain([entry1, entry2])
    assert is_valid is True
    assert len(errors) == 0

    # 2. Tampered detail in entry 2
    tampered_entry2 = dict(entry2, details="Altered malicious details")
    is_valid, errors = models.AuditLog.verify_chain([entry1, tampered_entry2])
    assert is_valid is False
    assert any("Tampered entry hash" in e for e in errors)

    # 3. Broken link between entry 1 and entry 2
    broken_entry2 = dict(entry2, previous_hash="bad_hash_pointer_1234567890")
    is_valid, errors = models.AuditLog.verify_chain([entry1, broken_entry2])
    assert is_valid is False
    assert any("Broken chain link" in e for e in errors)

    # 4. Invalid genesis previous_hash
    invalid_genesis = dict(entry1, previous_hash="not_genesis_hash")
    is_valid, errors = models.AuditLog.verify_chain([invalid_genesis, entry2])
    assert is_valid is False
    assert any("Genesis log" in e for e in errors)


def test_replay_snapshot_export_and_fingerprint(db_session, auth_tenant_alpha, seeded_investigation):
    """Test POST and GET export-replay endpoints return canonical snapshot with matching SHA-256 fingerprint."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id

    # 1. Test POST export-replay
    resp = client.post(f"/api/v1/investigations/{inv_id}/export-replay")
    assert resp.status_code == 200
    data = resp.json()

    assert data["snapshot_version"] == "1.0.0"
    assert data["investigation_id"] == inv_id
    assert data["tenant_id"] == "tenant_alpha"
    assert data["audit_chain_valid"] is True
    assert len(data["audit_chain_errors"]) == 0
    assert len(data["audit_logs"]) >= 3

    # Verify X-Replay-Fingerprint header matches body
    fp_header = resp.headers.get("X-Replay-Fingerprint")
    assert fp_header is not None
    assert fp_header == data["replay_fingerprint"]

    # Verify canonical recalculation of fingerprint
    copy_payload = dict(data)
    copy_payload.pop("replay_fingerprint", None)
    canonical_repr = json.dumps(copy_payload, sort_keys=True, separators=(',', ':'))
    computed_fp = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()
    assert computed_fp == data["replay_fingerprint"]

    # 2. Test GET export-replay
    get_resp = client.get(f"/api/v1/investigations/{inv_id}/export-replay")
    assert get_resp.status_code == 200
    assert get_resp.headers.get("X-Replay-Fingerprint") == get_resp.json()["replay_fingerprint"]

    app.dependency_overrides.clear()


def test_replay_snapshot_verify_unadulterated_success(db_session, auth_tenant_alpha, seeded_investigation):
    """Test POST verify-replay passes unadulterated snapshot cleanly."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id

    # Export
    export_resp = client.post(f"/api/v1/investigations/{inv_id}/export-replay")
    assert export_resp.status_code == 200
    snapshot = export_resp.json()

    # Verify unadulterated
    verify_resp = client.post(f"/api/v1/investigations/{inv_id}/verify-replay", json=snapshot)
    assert verify_resp.status_code == 200
    result = verify_resp.json()

    assert result["is_valid"] is True
    assert result["tamper_detected"] is False
    assert result["audit_chain_valid"] is True
    assert len(result["mismatch_reasons"]) == 0
    assert result["replay_fingerprint"] == snapshot["replay_fingerprint"]

    app.dependency_overrides.clear()


def test_replay_snapshot_verify_fingerprint_tampering(db_session, auth_tenant_alpha, seeded_investigation):
    """Test POST verify-replay rejects snapshot if payload is altered without updating fingerprint."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id
    export_resp = client.post(f"/api/v1/investigations/{inv_id}/export-replay")
    snapshot = export_resp.json()

    # Tamper with investigation status in snapshot
    tampered_snapshot = dict(snapshot)
    tampered_snapshot["investigation"]["status"] = "ESCALATED"

    verify_resp = client.post(f"/api/v1/investigations/{inv_id}/verify-replay", json=tampered_snapshot)
    assert verify_resp.status_code == 200
    result = verify_resp.json()

    assert result["is_valid"] is False
    assert result["tamper_detected"] is True
    assert any("Fingerprint mismatch" in r for r in result["mismatch_reasons"])

    app.dependency_overrides.clear()


def test_replay_snapshot_verify_database_mismatch(db_session, auth_tenant_alpha, seeded_investigation):
    """Test POST verify-replay rejects snapshot if fingerprint is updated but data diverges from database."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id
    export_resp = client.post(f"/api/v1/investigations/{inv_id}/export-replay")
    snapshot = export_resp.json()

    # Mutate risk score and recompute fingerprint so internal fingerprint matches
    snapshot["investigation"]["risk_score"] = 0.888
    copy_p = dict(snapshot)
    copy_p.pop("replay_fingerprint", None)
    canonical_repr = json.dumps(copy_p, sort_keys=True, separators=(',', ':'))
    snapshot["replay_fingerprint"] = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()

    verify_resp = client.post(f"/api/v1/investigations/{inv_id}/verify-replay", json=snapshot)
    assert verify_resp.status_code == 200
    result = verify_resp.json()

    assert result["is_valid"] is False
    assert result["tamper_detected"] is True
    assert any("Risk score mismatch" in r for r in result["mismatch_reasons"])

    app.dependency_overrides.clear()


def test_replay_snapshot_verify_audit_log_tampering(db_session, auth_tenant_alpha, seeded_investigation):
    """Test POST verify-replay detects audit chain corruption even if snapshot fingerprint is regenerated."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id
    export_resp = client.post(f"/api/v1/investigations/{inv_id}/export-replay")
    snapshot = export_resp.json()

    # Tamper with middle audit log details
    snapshot["audit_logs"][1]["details"] = "Forged details unauthorized"
    # Recompute snapshot fingerprint
    copy_p = dict(snapshot)
    copy_p.pop("replay_fingerprint", None)
    canonical_repr = json.dumps(copy_p, sort_keys=True, separators=(',', ':'))
    snapshot["replay_fingerprint"] = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()

    verify_resp = client.post(f"/api/v1/investigations/{inv_id}/verify-replay", json=snapshot)
    assert verify_resp.status_code == 200
    result = verify_resp.json()

    assert result["is_valid"] is False
    assert result["audit_chain_valid"] is False
    assert result["tamper_detected"] is True
    assert any("Tampered entry hash" in r for r in result["mismatch_reasons"])

    app.dependency_overrides.clear()


def test_replay_snapshot_cross_tenant_isolation(db_session, auth_tenant_alpha, auth_tenant_beta, seeded_investigation):
    """Test cross-tenant isolation: Tenant Beta cannot export or verify Tenant Alpha's replay snapshots."""
    app.dependency_overrides[get_db] = lambda: db_session
    inv_id = seeded_investigation.investigation_id

    # 1. Tenant Alpha exports legitimate snapshot
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client_alpha = TestClient(app)
    export_resp = client_alpha.post(f"/api/v1/investigations/{inv_id}/export-replay")
    assert export_resp.status_code == 200
    snapshot = export_resp.json()

    # 2. Tenant Beta attempts to export Tenant Alpha's investigation -> 403 Forbidden
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_beta
    client_beta = TestClient(app)
    forbidden_export = client_beta.post(f"/api/v1/investigations/{inv_id}/export-replay")
    assert forbidden_export.status_code == 403

    # 3. Tenant Beta attempts to verify Tenant Alpha's snapshot -> 403 Forbidden
    forbidden_verify = client_beta.post(f"/api/v1/investigations/{inv_id}/verify-replay", json=snapshot)
    assert forbidden_verify.status_code == 403

    app.dependency_overrides.clear()


def test_audit_chain_endpoint(db_session, auth_tenant_alpha, seeded_investigation):
    """Test GET /api/v1/investigations/{id}/audit-chain returns valid hash chain entries."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth.get_current_user] = lambda: auth_tenant_alpha
    client = TestClient(app)

    inv_id = seeded_investigation.investigation_id
    resp = client.get(f"/api/v1/investigations/{inv_id}/audit-chain")
    assert resp.status_code == 200
    data = resp.json()

    assert data["investigation_id"] == inv_id
    assert data["tenant_id"] == "tenant_alpha"
    assert data["chain_length"] >= 3
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0

    entries = data["entries"]
    assert len(entries) >= 3
    # Check chain linkage across entries
    assert entries[0]["previous_hash"] is None or entries[0]["previous_hash"] == "GENESIS"
    for i in range(1, len(entries)):
        assert entries[i]["previous_hash"] == entries[i - 1]["entry_hash"]
        assert entries[i]["entry_hash"] is not None

    app.dependency_overrides.clear()
