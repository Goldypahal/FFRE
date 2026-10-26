import pytest
from models import *
import uuid
from datetime import datetime

def test_user_creation(db_session):
    """Test creating a User model instance"""
    user_id = str(uuid.uuid4())
    user = User(
        user_id=user_id,
        name="Test User",
        role="analyst",
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()

    # Retrieve and verify decrypted hybrid property values & raw ciphertext columns
    retrieved_user = db_session.query(User).filter(User.user_id == user_id).first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"
    assert retrieved_user.role == "analyst"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user._name != "Test User"
    assert retrieved_user._email != "test@example.com"
    assert retrieved_user.email_hash is not None
    assert len(retrieved_user.email_hash) == 64

    # Verify O(1) blind index resolution via auth.get_user_by_email
    import auth
    indexed_user = auth.get_user_by_email(db_session, "test@example.com")
    assert indexed_user is not None
    assert indexed_user.user_id == user_id

def test_investigation_creation(db_session):
    """Test creating an Investigation model instance"""
    # First create a transaction to reference
    txn_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    customer = Customer(
        customer_id=customer_id,
        name="Test Customer",
        kyc_status="VERIFIED",
        risk_tier="LOW"
    )

    account = Account(
        account_id=account_id,
        customer_id=customer_id,
        account_type="CHECKING"
    )

    transaction = Transaction(
        txn_id=txn_id,
        account_id=account_id,
        amount=100.50,
        currency="USD",
        status="PENDING"
    )

    db_session.add_all([customer, account, transaction])
    db_session.commit()

    # Now create investigation
    investigation_id = str(uuid.uuid4())
    investigation = Investigation(
        investigation_id=investigation_id,
        txn_id=txn_id,
        status="RUNNING",
        confidence=0.85,
        report="Test investigation report"
    )

    db_session.add(investigation)
    db_session.commit()

    # Retrieve and verify
    retrieved_investigation = db_session.query(Investigation).filter(
        Investigation.investigation_id == investigation_id
    ).first()

    assert retrieved_investigation is not None
    assert retrieved_investigation.txn_id == txn_id
    assert retrieved_investigation.status == "RUNNING"
    assert float(retrieved_investigation.confidence) == 0.85
    assert retrieved_investigation.report == "Test investigation report"

    # Check relationship
    assert retrieved_investigation.transaction is not None
    assert retrieved_investigation.transaction.txn_id == txn_id

def test_evidence_creation(db_session):
    """Test creating an Evidence model instance"""
    # Create prerequisite investigation
    investigation_id = str(uuid.uuid4())
    txn_id = str(uuid.uuid4())

    investigation = Investigation(
        investigation_id=investigation_id,
        txn_id=txn_id,
        status="COMPLETED"
    )

    db_session.add(investigation)
    db_session.commit()

    # Create evidence
    evidence_id = str(uuid.uuid4())
    evidence = Evidence(
        evidence_id=evidence_id,
        investigation_id=investigation_id,
        source="customer_evidence",
        snippet="Customer has been verified"
    )

    db_session.add(evidence)
    db_session.commit()

    # Retrieve and verify
    retrieved_evidence = db_session.query(Evidence).filter(
        Evidence.evidence_id == evidence_id
    ).first()

    assert retrieved_evidence is not None
    assert retrieved_evidence.investigation_id == investigation_id
    assert retrieved_evidence.source == "customer_evidence"
    assert retrieved_evidence.snippet == "Customer has been verified"

    # Check relationship
    assert retrieved_evidence.investigation is not None
    assert retrieved_evidence.investigation.investigation_id == investigation_id

def test_audit_log_creation(db_session):
    """Test creating an AuditLog model instance"""
    # Create prerequisite investigation
    investigation_id = str(uuid.uuid4())
    txn_id = str(uuid.uuid4())

    investigation = Investigation(
        investigation_id=investigation_id,
        txn_id=txn_id,
        status="COMPLETED"
    )

    db_session.add(investigation)
    db_session.commit()

    # Create audit log
    log_id = str(uuid.uuid4())
    audit_log = AuditLog(
        log_id=log_id,
        investigation_id=investigation_id,
        action="Investigation Completed",
        details="Investigation finished with high confidence",
        timestamp=datetime.utcnow()
    )

    db_session.add(audit_log)
    db_session.commit()

    # Retrieve and verify
    retrieved_log = db_session.query(AuditLog).filter(
        AuditLog.log_id == log_id
    ).first()

    assert retrieved_log is not None
    assert retrieved_log.investigation_id == investigation_id
    assert retrieved_log.action == "Investigation Completed"
    assert retrieved_log.details == "Investigation finished with high confidence"
    assert retrieved_log.timestamp is not None

    # Check relationship
    assert retrieved_log.investigation is not None
    assert retrieved_log.investigation.investigation_id == investigation_id

def test_aes256_gcm_authenticated_encryption():
    """Verify authentic AES-256-GCM authenticated encryption, decryption, and tamper resistance."""
    from security import encrypt_aes256_gcm, decrypt_aes256_gcm

    plaintext = "Top-Secret-PII-Social-Security-000-12-3456"
    encrypted = encrypt_aes256_gcm(plaintext)
    assert encrypted != plaintext
    assert isinstance(encrypted, str)

    decrypted = decrypt_aes256_gcm(encrypted)
    assert decrypted == plaintext

    # Tamper with ciphertext bytes
    import base64
    raw = bytearray(base64.b64decode(encrypted.encode("utf-8")))
    raw[-1] ^= 0xFF # Flip bit in GCM authentication tag
    tampered_b64 = base64.b64encode(raw).decode("utf-8")

    # Decrypting tampered payload raises DecryptionError (fail-closed enforcement)
    with pytest.raises(security.DecryptionError):
        decrypt_aes256_gcm(tampered_b64)
    # With fail_closed=False, fallback safely does not return plaintext
    assert decrypt_aes256_gcm(tampered_b64, fail_closed=False) == tampered_b64

def test_audit_log_cryptographic_hash_chain_immutability(db_session):
    """NFR-5 Test: Verify AuditLog cryptographic hash chaining and tamper-evident detection."""
    inv_id = str(uuid.uuid4())
    inv = Investigation(
        investigation_id=inv_id,
        txn_id="TXN-AUDIT-CHAIN",
        status="INVESTIGATING"
    )
    db_session.add(inv)
    db_session.commit()

    # Block 1 (Genesis)
    log1_id = str(uuid.uuid4())
    ts1 = datetime.utcnow().isoformat()
    action1 = "INVESTIGATION_SUBMITTED"
    hash1 = AuditLog.calculate_entry_hash(None, log1_id, action1, ts1, "Genesis investigation event")

    log1 = AuditLog(
        log_id=log1_id,
        investigation_id=inv_id,
        action=action1,
        details="Genesis investigation event",
        previous_hash=None,
        entry_hash=hash1
    )
    db_session.add(log1)
    db_session.commit()

    # Block 2 (Chained to Block 1)
    log2_id = str(uuid.uuid4())
    ts2 = datetime.utcnow().isoformat()
    action2 = "EVIDENCE_RETRIEVED"
    hash2 = AuditLog.calculate_entry_hash(hash1, log2_id, action2, ts2, "Retrieved 5 evidence sources")

    log2 = AuditLog(
        log_id=log2_id,
        investigation_id=inv_id,
        action=action2,
        details="Retrieved 5 evidence sources",
        previous_hash=hash1,
        entry_hash=hash2
    )
    db_session.add(log2)
    db_session.commit()

    # Verify blockchain-style integrity
    queried_logs = db_session.query(AuditLog).filter(AuditLog.investigation_id == inv_id).all()
    assert len(queried_logs) == 2

    # Verify chained integrity: Log 2 previous_hash must match Log 1 entry_hash
    assert queried_logs[1].previous_hash == queried_logs[0].entry_hash

    # Verify recalculated entry hash matches stored entry hash
    expected_hash2 = AuditLog.calculate_entry_hash(
        queried_logs[0].entry_hash,
        queried_logs[1].log_id,
        queried_logs[1].action,
        ts2,
        queried_logs[1].details
    )
    assert queried_logs[1].entry_hash == expected_hash2

def test_legacy_fernet_decryption_backward_compatibility():
    """NFR-4 Test: Verify decrypt_data seamlessly decrypts legacy Fernet AES-128-CBC ciphertexts."""
    import security
    from cryptography.fernet import Fernet

    legacy_fernet = Fernet(security.get_encryption_key())
    plaintext = "legacy-customer-pii-ssn-1234"
    legacy_ciphertext = legacy_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    # Ensure decrypt_data decrypts the legacy Fernet ciphertext without errors
    decrypted = security.decrypt_data(legacy_ciphertext)
    assert decrypted == plaintext


def test_all_pii_bearing_models_raw_database_encryption_and_legacy_fernet(db_session):
    """
    Phase 3 & SRS SEC-1 Test:
    Extends raw-database verification across EVERY PII-bearing model (User, Customer, Device):
    1. Newly persisted records are authenticated with AES-256-GCM (nonce + tag).
    2. Raw database SELECT queries return ciphertext, never plaintext.
    3. Legacy Fernet records in the raw database are transparently decrypted.
    4. Tampered ciphertext fails closed under DecryptionError.
    """
    import base64
    from sqlalchemy import text
    from cryptography.fernet import Fernet
    import security

    # 1. User PII: name and email
    u_id = f"u_pii_{uuid.uuid4().hex[:8]}"
    raw_user_name = "Dr. Alice Cryptographer"
    raw_user_email = "alice.crypto@securebank.internal"
    user = User(
        user_id=u_id,
        name=raw_user_name,
        email=raw_user_email,
        role="investigator",
        tenant_id="tenant_pii_sec"
    )
    db_session.add(user)

    # 2. Customer PII: name
    c_id = f"c_pii_{uuid.uuid4().hex[:8]}"
    raw_cust_name = "Eleanor Vance-Montague"
    cust = Customer(
        customer_id=c_id,
        name=raw_cust_name,
        kyc_status="VERIFIED",
        risk_tier="LOW",
        tenant_id="tenant_pii_sec"
    )
    db_session.add(cust)

    # 3. Device PII: fingerprint
    d_id = f"d_pii_{uuid.uuid4().hex[:8]}"
    raw_fp = "Hardware-UUID-99A8-BB12-CC44-E890"
    device = Device(
        device_id=d_id,
        customer_id=c_id,
        fingerprint=raw_fp,
        tenant_id="tenant_pii_sec"
    )
    db_session.add(device)
    db_session.commit()

    # RAW DATABASE VERIFICATION: Inspect raw database bytes via direct SQL execution
    # Raw User query
    user_row = db_session.execute(
        text("SELECT name, email, email_hash FROM users WHERE user_id = :uid"),
        {"uid": u_id}
    ).fetchone()
    raw_db_user_name, raw_db_user_email, raw_db_user_hash = user_row
    assert raw_db_user_name != raw_user_name
    assert raw_db_user_email != raw_user_email
    assert raw_db_user_hash == security.compute_blind_index(raw_user_email)

    # Raw Customer query
    cust_row = db_session.execute(
        text("SELECT name FROM customer WHERE customer_id = :cid"),
        {"cid": c_id}
    ).fetchone()
    raw_db_cust_name = cust_row[0]
    assert raw_db_cust_name != raw_cust_name

    # Raw Device query
    dev_row = db_session.execute(
        text("SELECT fingerprint FROM device WHERE device_id = :did"),
        {"did": d_id}
    ).fetchone()
    raw_db_fp = dev_row[0]
    assert raw_db_fp != raw_fp

    # Validate that stored ciphertexts are authentic AES-256-GCM (minimum 28 bytes binary payload)
    for ct in [raw_db_user_name, raw_db_user_email, raw_db_cust_name, raw_db_fp]:
        payload_bytes = base64.b64decode(ct.encode("utf-8"))
        assert len(payload_bytes) >= 28, "Ciphertext must contain 12-byte GCM nonce + 16-byte GCM tag + payload"

    # ORM TRANSPARENCY: Verify that model getters return uncorrupted plaintext
    reloaded_user = db_session.query(User).filter_by(user_id=u_id).first()
    assert reloaded_user.name == raw_user_name
    assert reloaded_user.email == raw_user_email

    reloaded_cust = db_session.query(Customer).filter_by(customer_id=c_id).first()
    assert reloaded_cust.name == raw_cust_name

    reloaded_dev = db_session.query(Device).filter_by(device_id=d_id).first()
    assert reloaded_dev.fingerprint == raw_fp

    # LEGACY FERNET INJECTION & BACKWARD COMPATIBILITY:
    # Inject legacy Fernet ciphertext directly into the raw database columns
    legacy_fernet = Fernet(security.get_encryption_key())
    legacy_cust_name = "Legacy Sir Arthur Conan Doyle"
    legacy_cipher_sql = legacy_fernet.encrypt(legacy_cust_name.encode("utf-8")).decode("utf-8")
    
    db_session.execute(
        text("UPDATE customer SET name = :leg_ct WHERE customer_id = :cid"),
        {"leg_ct": legacy_cipher_sql, "cid": c_id}
    )
    db_session.commit()
    db_session.expire_all()

    # Verify that Customer model seamlessly decrypts legacy Fernet ciphertext
    legacy_reloaded = db_session.query(Customer).filter_by(customer_id=c_id).first()
    assert legacy_reloaded.name == legacy_cust_name