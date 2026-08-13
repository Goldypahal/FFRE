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

    # Retrieve and verify
    retrieved_user = db_session.query(User).filter(User.user_id == user_id).first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"
    assert retrieved_user.role == "analyst"
    assert retrieved_user.email == "test@example.com"

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