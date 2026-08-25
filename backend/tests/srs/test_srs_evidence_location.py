import pytest
import models
from main import run_investigation_task

def test_all_five_evidence_sources_saved_to_database(db_session):
    # Setup test entities
    cust = models.Customer(customer_id="c_ev_1", name="Test Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_ev_1", customer_id="c_ev_1")
    merch = models.Merchant(merchant_id="m_ev_1", name="Test Merchant", risk_score=0.01)
    txn = models.Transaction(txn_id="T-EVIDENCE-TEST", account_id="a_ev_1", merchant_id="m_ev_1", amount=250.0, currency="USD", status="PENDING")
    dev = models.Device(device_id="d_ev_1", customer_id="c_ev_1", fingerprint="fingerprint_123", os="iOS")
    loc = models.Location(location_id="l_ev_1", txn_id="T-EVIDENCE-TEST", geo_coord="40.7128,-74.0060", country="US")
    inv = models.Investigation(investigation_id="inv_ev_all", txn_id="T-EVIDENCE-TEST", status="RUNNING")

    db_session.add_all([cust, acct, merch, txn, dev, loc, inv])
    db_session.commit()

    run_investigation_task("inv_ev_all", "T-EVIDENCE-TEST", db=db_session)

    evidence_records = db_session.query(models.Evidence).filter(models.Evidence.investigation_id == "inv_ev_all").all()
    sources = [ev.source for ev in evidence_records]

    assert "customer_evidence" in sources
    assert "transaction_evidence" in sources
    assert "merchant_evidence" in sources
    assert "device_evidence" in sources
    assert "location_evidence" in sources
    assert len(sources) >= 5
