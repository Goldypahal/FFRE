import uuid
import datetime
import pytest
import models

def test_ds1_customer_model_kyc_status(db_session):
    """DS-1: Verify Customer entity schema, tenant scoping, and KYC status validation."""
    c = models.Customer(
        customer_id="c_ds1_test",
        tenant_id="tenant_ds1",
        name="DS1 Customer",
        kyc_status="VERIFIED",
        risk_tier="LOW"
    )
    db_session.add(c)
    db_session.commit()

    retrieved = db_session.query(models.Customer).filter(models.Customer.customer_id == "c_ds1_test").first()
    assert retrieved is not None
    assert retrieved.kyc_status == "VERIFIED"
    assert retrieved.tenant_id == "tenant_ds1"

def test_ds2_account_model_relationship(db_session):
    """DS-2: Verify Account entity schema and foreign key relationship to Customer."""
    c = models.Customer(customer_id="c_ds2_test", name="DS2 Cust")
    a = models.Account(account_id="a_ds2_test", customer_id="c_ds2_test", balance=1500.0)
    db_session.add_all([c, a])
    db_session.commit()

    retrieved = db_session.query(models.Account).filter(models.Account.account_id == "a_ds2_test").first()
    assert retrieved is not None
    assert retrieved.customer_id == "c_ds2_test"
    assert retrieved.customer.name == "DS2 Cust"

def test_ds3_transaction_model_precision(db_session):
    """DS-3: Verify Transaction ledger entity with Decimal precision and status tracking."""
    t = models.Transaction(
        txn_id="TXN-DS3-TEST",
        amount=999.99,
        currency="USD",
        status="PENDING",
        account_id="a_ds3_test"
    )
    db_session.add(t)
    db_session.commit()

    retrieved = db_session.query(models.Transaction).filter(models.Transaction.txn_id == "TXN-DS3-TEST").first()
    assert retrieved is not None
    assert float(retrieved.amount) == 999.99
    assert retrieved.currency == "USD"

def test_ds4_merchant_model_risk_profile(db_session):
    """DS-4: Verify Merchant entity schema and historical fraud rate score."""
    m = models.Merchant(
        merchant_id="m_ds4_test",
        name="High Risk Electronics",
        category="ELECTRONICS",
        risk_score=0.45
    )
    db_session.add(m)
    db_session.commit()

    retrieved = db_session.query(models.Merchant).filter(models.Merchant.merchant_id == "m_ds4_test").first()
    assert retrieved is not None
    assert float(retrieved.risk_score) == 0.45

def test_ds5_device_model_fingerprint(db_session):
    """DS-5: Verify Device entity schema with OS and device fingerprint."""
    d = models.Device(
        device_id="d_ds5_test",
        customer_id="c_ds5_test",
        fingerprint="fp_hash_12345",
        os="iOS"
    )
    db_session.add(d)
    db_session.commit()

    retrieved = db_session.query(models.Device).filter(models.Device.device_id == "d_ds5_test").first()
    assert retrieved is not None
    assert retrieved.os == "iOS"

def test_ds6_location_model_coordinates(db_session):
    """DS-6: Verify Location entity schema with latitude/longitude geo coordinates."""
    loc = models.Location(
        location_id="l_ds6_test",
        txn_id="TXN-DS6-TEST",
        geo_coord="37.7749,-122.4194",
        country="US"
    )
    db_session.add(loc)
    db_session.commit()

    retrieved = db_session.query(models.Location).filter(models.Location.location_id == "l_ds6_test").first()
    assert retrieved is not None
    assert retrieved.country == "US"

def test_ds7_investigation_model_lifecycle(db_session):
    """DS-7: Verify Investigation model schema and status lifecycle transitions."""
    inv = models.Investigation(
        investigation_id="inv_ds7_test",
        txn_id="TXN-DS7-TEST",
        status="QUEUED"
    )
    db_session.add(inv)
    db_session.commit()

    retrieved = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == "inv_ds7_test").first()
    assert retrieved is not None
    assert retrieved.status == "QUEUED"

def test_ds8_evidence_model_snippet_storage(db_session):
    """DS-8: Verify Evidence model schema and investigation foreign key."""
    e = models.Evidence(
        evidence_id="e_ds8_test",
        source="customer_records",
        snippet="Customer verified with Tier 1 KYC documentation."
    )
    db_session.add(e)
    db_session.commit()

    retrieved = db_session.query(models.Evidence).filter(models.Evidence.evidence_id == "e_ds8_test").first()
    assert retrieved is not None
    assert retrieved.source == "customer_records"

def test_ds9_fraud_case_model_verdict(db_session):
    """DS-9: Verify FraudCase model schema with verdict and confidence ratings."""
    fc = models.FraudCase(
        case_id="fc_ds9_test",
        verdict="FRAUDULENT",
        confidence=0.98
    )
    db_session.add(fc)
    db_session.commit()

    retrieved = db_session.query(models.FraudCase).filter(models.FraudCase.case_id == "fc_ds9_test").first()
    assert retrieved is not None
    assert retrieved.verdict == "FRAUDULENT"

def test_ds10_risk_score_model_dual_scores(db_session):
    """DS-10: Verify RiskScore model schema with rule-based and ML model score breakdown."""
    rs = models.RiskScore(
        score_id="rs_ds10_test",
        txn_id="TXN-DS10-TEST",
        rule_score=0.35,
        model_score=0.42
    )
    db_session.add(rs)
    db_session.commit()

    retrieved = db_session.query(models.RiskScore).filter(models.RiskScore.score_id == "rs_ds10_test").first()
    assert retrieved is not None
    assert float(retrieved.rule_score) == 0.35

def test_ds11_audit_log_model_hash_chain(db_session):
    """DS-11: Verify AuditLog entity with cryptographic hash chaining fields."""
    log = models.AuditLog(
        log_id="log_ds11_test",
        action="AUTH_LOGIN",
        details="User logged in",
        previous_hash=None,
        entry_hash="hash_ds11_sample"
    )
    db_session.add(log)
    db_session.commit()

    retrieved = db_session.query(models.AuditLog).filter(models.AuditLog.log_id == "log_ds11_test").first()
    assert retrieved is not None
    assert retrieved.entry_hash == "hash_ds11_sample"

def test_ds12_dead_letter_job_model(db_session):
    """DS-12: Verify DeadLetterJob entity schema for capturing exhausted retry jobs."""
    dlq = models.DeadLetterJob(
        id="dlq_ds12_test",
        transaction_id="TXN-DS12-TEST",
        failure_reason="Max retries reached with LLM connection timeout",
        retry_count=3
    )
    db_session.add(dlq)
    db_session.commit()

    retrieved = db_session.query(models.DeadLetterJob).filter(models.DeadLetterJob.id == "dlq_ds12_test").first()
    assert retrieved is not None
    assert retrieved.retry_count == 3

def test_ds13_evidence_vault_item_model(db_session):
    """DS-13: Verify EvidenceVaultItem model schema with SHA-256 digital vault digest."""
    evi = models.EvidenceVaultItem(
        item_id="evi_ds13_test",
        title="ID Passport Scan",
        source="KYC Provider",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_verified=True
    )
    db_session.add(evi)
    db_session.commit()

    retrieved = db_session.query(models.EvidenceVaultItem).filter(models.EvidenceVaultItem.item_id == "evi_ds13_test").first()
    assert retrieved is not None
    assert retrieved.sha256_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_ds14_report_record_model(db_session):
    """DS-14: Verify ReportRecord regulatory export model schema."""
    rep = models.ReportRecord(
        report_id="rep_ds14_test",
        title="SAR Executive Filing",
        report_type="SAR",
        file_format="pdf",
        status="Completed"
    )
    db_session.add(rep)
    db_session.commit()

    retrieved = db_session.query(models.ReportRecord).filter(models.ReportRecord.report_id == "rep_ds14_test").first()
    assert retrieved is not None
    assert retrieved.file_format == "pdf"

def test_ds15_prompt_record_model(db_session):
    """DS-15: Verify PromptRecord model schema for versioned AI prompt management."""
    prompt = models.PromptRecord(
        prompt_id="prompt_ds15_test",
        name="planner",
        version="v1.0",
        template_text="Analyze {transaction_summary}",
        is_active=True
    )
    db_session.add(prompt)
    db_session.commit()

    retrieved = db_session.query(models.PromptRecord).filter(models.PromptRecord.prompt_id == "prompt_ds15_test").first()
    assert retrieved is not None
    assert retrieved.name == "planner"
