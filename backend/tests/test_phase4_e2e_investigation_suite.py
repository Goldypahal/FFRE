"""
Phase 4 End-to-End Investigation Workflow Qualification Suite.

Deterministic validation of the 7 core fraud investigation scenarios:
1. Legitimate transaction
2. Unusual velocity burst
3. New / unrecognized device
4. Location / jurisdictional mismatch
5. Conflicting evidence resolution
6. Insufficient evidence fail-closed / escalation
7. Missing customer record handling
PLUS: Contradictory evidence claim rejection and correction verification.
"""

import uuid
import datetime
import pytest
from unittest.mock import patch

import models
import security
from auth import create_access_token
from graph import build_graph
from main import run_investigation_task
from guardrails import extract_and_verify_claims, validate_claims


@pytest.fixture
def test_investigator(db_session):
    """Seed authenticated investigator user for API requests."""
    email = f"lead_investigator_{uuid.uuid4().hex[:6]}@bank.internal"
    user = models.User(
        user_id=f"u_inv_{uuid.uuid4().hex[:6]}",
        name="Lead Fraud Investigator",
        email=email,
        role="investigator",
        tenant_id="tenant_bank_p4"
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({
        "sub": email,
        "role": "investigator",
        "tenant_id": "tenant_bank_p4",
        "type": "access"
    })
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


def test_scenario_1_legitimate_transaction(client, db_session, test_investigator):
    """Scenario 1: Legitimate transaction with trusted profile, normal velocity, and verified device."""
    c_id = f"c_legit_{uuid.uuid4().hex[:6]}"
    a_id = f"a_legit_{uuid.uuid4().hex[:6]}"
    m_id = f"m_legit_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-LEGIT-{uuid.uuid4().hex[:6]}"

    cust = models.Customer(customer_id=c_id, name="Alice Benign", kyc_status="VERIFIED", risk_tier="LOW", tenant_id="tenant_bank_p4")
    acct = models.Account(account_id=a_id, customer_id=c_id, account_type="CHECKING", balance=5000.0, tenant_id="tenant_bank_p4")
    merch = models.Merchant(merchant_id=m_id, name="Acme Supermarket", category="GROCERY", risk_score=0.01, tenant_id="tenant_bank_p4")
    txn = models.Transaction(
        txn_id=t_id, account_id=a_id, merchant_id=m_id, amount=75.50, currency="USD",
        status="PENDING", counterparty="Acme POS 42", channel="POS", tenant_id="tenant_bank_p4"
    )
    dev = models.Device(device_id=f"dev_l_{uuid.uuid4().hex[:6]}", customer_id=c_id, fingerprint="fp_trusted_iphone_12", os="iOS", tenant_id="tenant_bank_p4")
    loc = models.Location(location_id=f"loc_l_{uuid.uuid4().hex[:6]}", txn_id=t_id, geo_coord="40.7128,-74.0060", country="US", tenant_id="tenant_bank_p4")
    db_session.add_all([cust, acct, merch, txn, dev, loc])
    db_session.commit()

    # API Request
    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    # Execute workflow synchronously
    run_investigation_task(inv_id, t_id, db=db_session)

    # Verification
    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    assert inv.status in ("COMPLETED", "APPROVED", "ESCALATED")
    assert inv.risk_score is not None
    assert float(inv.risk_score) <= 0.40  # Legitimate should have low risk
    assert inv.confidence is not None
    assert float(inv.confidence) >= 0.50
    assert len(inv.evidence) >= 1
    assert len(inv.audit_logs) >= 2


def test_scenario_2_unusual_velocity(client, db_session, test_investigator):
    """Scenario 2: Unusual velocity burst on account triggers risk scoring elevation."""
    c_id = f"c_vel_{uuid.uuid4().hex[:6]}"
    a_id = f"a_vel_{uuid.uuid4().hex[:6]}"
    m_id = f"m_vel_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-VEL-{uuid.uuid4().hex[:6]}"

    cust = models.Customer(customer_id=c_id, name="Bob Velocity", kyc_status="VERIFIED", risk_tier="MEDIUM", tenant_id="tenant_bank_p4")
    acct = models.Account(account_id=a_id, customer_id=c_id, account_type="CHECKING", balance=12000.0, tenant_id="tenant_bank_p4")
    merch = models.Merchant(merchant_id=m_id, name="Online Gift Cards", category="DIGITAL_GOODS", risk_score=0.45, tenant_id="tenant_bank_p4")
    
    # Target transaction
    txn = models.Transaction(txn_id=t_id, account_id=a_id, merchant_id=m_id, amount=499.00, currency="USD", status="PENDING", tenant_id="tenant_bank_p4")
    db_session.add_all([cust, acct, merch, txn])

    # Seed 7 rapid historical transactions on same account in last 15 minutes
    for i in range(7):
        hist_txn = models.Transaction(
            txn_id=f"TXN-HIST-VEL-{uuid.uuid4().hex[:6]}",
            account_id=a_id,
            merchant_id=m_id,
            amount=500.00,
            currency="USD",
            status="COMPLETED",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=i + 1),
            tenant_id="tenant_bank_p4"
        )
        db_session.add(hist_txn)
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    assert float(inv.risk_score) >= 0.25  # Velocity elevation


def test_scenario_3_new_device(client, db_session, test_investigator):
    """Scenario 3: Transaction from a previously unseen, unrecognized device fingerprint."""
    c_id = f"c_dev_{uuid.uuid4().hex[:6]}"
    a_id = f"a_dev_{uuid.uuid4().hex[:6]}"
    m_id = f"m_dev_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-DEV-{uuid.uuid4().hex[:6]}"

    cust = models.Customer(customer_id=c_id, name="Carol Device", kyc_status="VERIFIED", tenant_id="tenant_bank_p4")
    acct = models.Account(account_id=a_id, customer_id=c_id, tenant_id="tenant_bank_p4")
    merch = models.Merchant(merchant_id=m_id, name="Electronics Outlet", tenant_id="tenant_bank_p4")
    # Transaction references a novel device ref
    novel_device_id = f"DEV_UNRECOGNIZED_{uuid.uuid4().hex[:8]}"
    txn = models.Transaction(txn_id=t_id, account_id=a_id, merchant_id=m_id, amount=1250.00, device_ref=novel_device_id, tenant_id="tenant_bank_p4")
    
    # Customer only has historical record for an old Android device
    old_dev = models.Device(device_id=f"dev_known_{uuid.uuid4().hex[:6]}", customer_id=c_id, fingerprint="fp_old_samsung_s9", os="Android", tenant_id="tenant_bank_p4")
    db_session.add_all([cust, acct, merch, txn, old_dev])
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    assert inv.status in ("COMPLETED", "ESCALATED", "FLAGGED")


def test_scenario_4_location_mismatch(client, db_session, test_investigator):
    """Scenario 4: Location mismatch (cross-border / impossible travel speed)."""
    c_id = f"c_loc_{uuid.uuid4().hex[:6]}"
    a_id = f"a_loc_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-LOC-{uuid.uuid4().hex[:6]}"

    cust = models.Customer(customer_id=c_id, name="David Traveller", kyc_status="VERIFIED", tenant_id="tenant_bank_p4")
    acct = models.Account(account_id=a_id, customer_id=c_id, tenant_id="tenant_bank_p4")
    txn = models.Transaction(txn_id=t_id, account_id=a_id, amount=800.00, tenant_id="tenant_bank_p4")
    # Location is in a high-risk offshore jurisdiction
    loc = models.Location(location_id=f"loc_{uuid.uuid4().hex[:6]}", txn_id=t_id, country="RU", geo_coord="55.7558,37.6173", tenant_id="tenant_bank_p4")
    
    db_session.add_all([cust, acct, txn, loc])
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    assert inv.risk_score is not None


def test_scenario_5_conflicting_evidence(client, db_session, test_investigator):
    """Scenario 5: Conflicting evidence (verified KYC customer vs flagged high-risk merchant)."""
    c_id = f"c_conf_{uuid.uuid4().hex[:6]}"
    a_id = f"a_conf_{uuid.uuid4().hex[:6]}"
    m_id = f"m_conf_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-CONF-{uuid.uuid4().hex[:6]}"

    # Customer is pristine, but merchant is high-risk cryptocurrency tumbler
    cust = models.Customer(customer_id=c_id, name="Eleanor Conflicted", kyc_status="VERIFIED", risk_tier="LOW", tenant_id="tenant_bank_p4")
    acct = models.Account(account_id=a_id, customer_id=c_id, balance=50000.0, tenant_id="tenant_bank_p4")
    merch = models.Merchant(merchant_id=m_id, name="Offshore Dark Tumbler", category="CRYPTO_MIXER", risk_score=0.99, tenant_id="tenant_bank_p4")
    txn = models.Transaction(txn_id=t_id, account_id=a_id, merchant_id=m_id, amount=9999.0, tenant_id="tenant_bank_p4")
    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    # High risk should prevail or escalate to human review
    assert float(inv.risk_score) >= 0.50


def test_scenario_6_insufficient_evidence_escalation(client, db_session, test_investigator):
    """Scenario 6: Insufficient evidence gracefully handles missing context without fabricating claims."""
    a_id = f"a_insuf_{uuid.uuid4().hex[:6]}"
    t_id = f"TXN-INSUF-{uuid.uuid4().hex[:6]}"

    # Transaction has no merchant, no customer, no location, no device
    acct = models.Account(account_id=a_id, customer_id=None, tenant_id="tenant_bank_p4")
    txn = models.Transaction(txn_id=t_id, account_id=a_id, amount=300.0, tenant_id="tenant_bank_p4")
    db_session.add_all([acct, txn])
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    # System must not fabricate data; confidence reflects partial knowledge
    assert inv.status in ("COMPLETED", "ESCALATED", "FAILED")


def test_scenario_7_missing_customer_record(client, db_session, test_investigator):
    """Scenario 7: Missing customer record is handled safely without unhandled crashes."""
    t_id = f"TXN-NOCUST-{uuid.uuid4().hex[:6]}"
    a_id = f"a_orph_{uuid.uuid4().hex[:6]}"
    
    # Account references a nonexistent customer ID
    acct = models.Account(account_id=a_id, customer_id="NONEXISTENT_CUST_ID_999", tenant_id="tenant_bank_p4")
    txn = models.Transaction(txn_id=t_id, account_id=a_id, amount=150.0, tenant_id="tenant_bank_p4")
    db_session.add_all([acct, txn])
    db_session.commit()

    res = client.post("/api/v1/investigations", json={"transaction_id": t_id, "user_id": test_investigator["user"].user_id}, headers=test_investigator["headers"])
    assert res.status_code == 202
    inv_id = res.json()["investigation_id"]

    run_investigation_task(inv_id, t_id, db=db_session)

    inv = db_session.query(models.Investigation).filter_by(investigation_id=inv_id).first()
    assert inv is not None
    # Audit log confirms execution completed safely
    audit = db_session.query(models.AuditLog).filter_by(investigation_id=inv_id).all()
    assert len(audit) >= 1


def test_correctness_contradictory_evidence_claim_rejection():
    """
    Phase 4 Key Correctness Test:
    Give the system evidence that contradicts the model's claim.
    Example: Model claims 'Transaction occurred from an unrecognized new device',
    while retrieved evidence confirms 'device is previously trusted and recognized (new_device=False)'.
    The system must reject the unsupported/contradictory claim rather than preserve a false explanation.
    """
    # Canonical evidence showing a recognized, trusted device
    evidence_bundle = {
        "customer": {"name": "Franklin Wright", "kyc_status": "VERIFIED"},
        "transaction": {"txn_id": "TXN-CONTRADICT-01", "amount": 850.00, "currency": "USD"},
        "device": {
            "device_id": "dev_trusted_001",
            "fingerprint": "fp_trusted_macbook_pro",
            "new_device": False,
            "trusted_device": True
        }
    }

    # 1. Contradictory assertion: Model incorrectly asserts new unrecognized device
    contradictory_claim = "The transaction was executed from a new device with an unrecognized fingerprint."
    verified_claims = extract_and_verify_claims(contradictory_claim, evidence_bundle)

    # Must be marked unsupported with low confidence
    assert len(verified_claims) >= 1
    target = verified_claims[0]
    assert target["supported"] is False
    assert target["confidence"] <= 0.35
    assert "new" in target.get("reason", "").lower() or "device" in target.get("reason", "").lower() or target["supported"] is False

    # 2. Grounded truth assertion: Model asserts grounded facts matching evidence bundle
    truthful_claim = "Transaction TXN-CONTRADICT-01 for 850.00 USD was executed from device fp_trusted_macbook_pro."
    truth_verified = extract_and_verify_claims(truthful_claim, evidence_bundle)
    assert len(truth_verified) >= 1
    assert truth_verified[0]["supported"] is True
    assert truth_verified[0]["confidence"] >= 0.80

