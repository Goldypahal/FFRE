import pytest
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models
from graph import (
    retrieve_customer_node,
    retrieve_transaction_node,
    retrieve_merchant_node,
    retrieve_device_node,
    retrieve_location_node,
    velocity_check_node,
    knowledge_lookup_node,
    AgentState
)
from vector_db import get_vector_store


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_models_have_tenant_id():
    """Verify Device, Location, FraudCase, RiskScore, DeadLetterJob all contain tenant_id column."""
    db: Session = SessionLocal()
    try:
        dev = models.Device(os="iOS", ip_address="10.0.0.1", tenant_id="tenant_x")
        dev.fingerprint = "fp_test_123"
        loc = models.Location(country="US", geo_coord="40.7128,-74.0060", tenant_id="tenant_x")
        fc = models.FraudCase(verdict="FRAUD", confidence=Decimal("0.950"), tenant_id="tenant_x")
        rs = models.RiskScore(model_score=Decimal("0.850"), rule_score=Decimal("0.800"), tenant_id="tenant_x")
        dlq = models.DeadLetterJob(transaction_id="txn_test_123", tenant_id="tenant_x")

        db.add_all([dev, loc, fc, rs, dlq])
        db.commit()

        # Query back
        assert db.query(models.Device).filter(models.Device.tenant_id == "tenant_x").first().tenant_id == "tenant_x"
        assert db.query(models.Location).filter(models.Location.tenant_id == "tenant_x").first().tenant_id == "tenant_x"
        assert db.query(models.FraudCase).filter(models.FraudCase.tenant_id == "tenant_x").first().tenant_id == "tenant_x"
        assert db.query(models.RiskScore).filter(models.RiskScore.tenant_id == "tenant_x").first().tenant_id == "tenant_x"
        assert db.query(models.DeadLetterJob).filter(models.DeadLetterJob.tenant_id == "tenant_x").first().tenant_id == "tenant_x"

        # Cross-tenant query should find zero
        assert db.query(models.Device).filter(models.Device.tenant_id == "tenant_other").first() is None
        assert db.query(models.Location).filter(models.Location.tenant_id == "tenant_other").first() is None
    finally:
        db.close()


def test_graph_retrievers_tenant_isolation():
    """Verify that graph retrieval nodes strictly isolate data by tenant_id."""
    db: Session = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        cust_a_id = f"cust_iso_a_{suffix}"
        cust_b_id = f"cust_iso_b_{suffix}"
        acct_a_id = f"acct_iso_a_{suffix}"
        acct_b_id = f"acct_iso_b_{suffix}"
        merch_a_id = f"merch_iso_a_{suffix}"
        merch_b_id = f"merch_iso_b_{suffix}"
        txn_a_id = f"txn_iso_a_{suffix}"
        txn_b_id = f"txn_iso_b_{suffix}"

        # Seed tenant A
        cust_a = models.Customer(customer_id=cust_a_id, tenant_id="tenant_alpha", name="Alice Alpha", kyc_status="VERIFIED", risk_tier="LOW")
        acct_a = models.Account(account_id=acct_a_id, tenant_id="tenant_alpha", customer_id=cust_a_id, account_type="CHECKING", balance=5000.0)
        merch_a = models.Merchant(merchant_id=merch_a_id, tenant_id="tenant_alpha", name="Alpha Store", category="RETAIL", risk_score=Decimal("0.05"))
        txn_a = models.Transaction(txn_id=txn_a_id, tenant_id="tenant_alpha", account_id=acct_a_id, merchant_id=merch_a_id, amount=Decimal("150.00"), currency="USD", status="PENDING")
        dev_a = models.Device(tenant_id="tenant_alpha", customer_id=cust_a_id, os="iOS", ip_address="10.1.1.1")
        dev_a.fingerprint = f"fp_a_{suffix}"
        loc_a = models.Location(tenant_id="tenant_alpha", txn_id=txn_a_id, geo_coord="37.7749,-122.4194", country="US")

        # Seed tenant B
        cust_b = models.Customer(customer_id=cust_b_id, tenant_id="tenant_beta", name="Bob Beta", kyc_status="UNVERIFIED", risk_tier="HIGH")
        acct_b = models.Account(account_id=acct_b_id, tenant_id="tenant_beta", customer_id=cust_b_id, account_type="SAVINGS", balance=100.0)
        merch_b = models.Merchant(merchant_id=merch_b_id, tenant_id="tenant_beta", name="Beta Crypto", category="CRYPTO", risk_score=Decimal("0.90"))
        txn_b = models.Transaction(txn_id=txn_b_id, tenant_id="tenant_beta", account_id=acct_b_id, merchant_id=merch_b_id, amount=Decimal("9999.00"), currency="EUR", status="PENDING")
        dev_b = models.Device(tenant_id="tenant_beta", customer_id=cust_b_id, os="Android", ip_address="10.2.2.2")
        dev_b.fingerprint = f"fp_b_{suffix}"
        loc_b = models.Location(tenant_id="tenant_beta", txn_id=txn_b_id, geo_coord="52.5200,13.4050", country="DE")

        db.add_all([cust_a, acct_a, merch_a, txn_a, dev_a, loc_a, cust_b, acct_b, merch_b, txn_b, dev_b, loc_b])
        db.commit()

        # 1. Tenant Alpha state querying txn_a_id should succeed
        state_alpha = {
            "transaction_id": txn_a_id,
            "tenant_id": "tenant_alpha"
        }
        res_cust = retrieve_customer_node(state_alpha)
        assert res_cust["customer_evidence"]["evidence_status"] == "OK"
        assert res_cust["customer_evidence"]["name"] == "Alice Alpha"

        res_txn = retrieve_transaction_node(state_alpha)
        assert res_txn["transaction_evidence"]["evidence_status"] == "OK"
        assert res_txn["transaction_evidence"]["amount"] == 150.0

        res_merch = retrieve_merchant_node(state_alpha)
        assert res_merch["merchant_evidence"]["evidence_status"] == "OK"
        assert res_merch["merchant_evidence"]["name"] == "Alpha Store"

        res_dev = retrieve_device_node(state_alpha)
        assert res_dev["device_evidence"]["evidence_status"] == "OK"
        assert res_dev["device_evidence"]["os"] == "iOS"

        res_loc = retrieve_location_node(state_alpha)
        assert res_loc["location_evidence"]["evidence_status"] == "OK"
        assert res_loc["location_evidence"]["country"] == "US"

        # 2. Negative test: Tenant Alpha querying txn_b_id must get NOT_FOUND on all retrievers
        state_cross = {
            "transaction_id": txn_b_id,
            "tenant_id": "tenant_alpha"  # Attacking or probing tenant B's transaction
        }
        res_cross_cust = retrieve_customer_node(state_cross)
        assert res_cross_cust["customer_evidence"]["evidence_status"] == "NOT_FOUND"

        res_cross_txn = retrieve_transaction_node(state_cross)
        assert res_cross_txn["transaction_evidence"]["evidence_status"] == "NOT_FOUND"

        res_cross_merch = retrieve_merchant_node(state_cross)
        assert res_cross_merch["merchant_evidence"]["evidence_status"] == "NOT_FOUND"

        res_cross_dev = retrieve_device_node(state_cross)
        assert res_cross_dev["device_evidence"]["evidence_status"] == "NOT_FOUND"

        res_cross_loc = retrieve_location_node(state_cross)
        assert res_cross_loc["location_evidence"]["evidence_status"] == "NOT_FOUND"

        # Velocity check cross-tenant isolation
        state_cross_vel = {
            "transaction_id": txn_b_id,
            "tenant_id": "tenant_alpha"
        }
        res_cross_vel = velocity_check_node(state_cross_vel)
        # Since txn_b doesn't belong to tenant_alpha, velocity count for account must be 0
        assert res_cross_vel["velocity_evidence"]["velocity_count_1h"] == 0

    finally:
        db.close()


def test_vector_db_tenant_isolation():
    """Verify that vector DB methods and graph node enforce tenant isolation."""
    from unittest.mock import MagicMock, patch
    from vector_db import FraudVectorDB

    # Test FraudVectorDB directly with a mock collection
    vdb = FraudVectorDB()
    mock_coll = MagicMock()
    mock_coll.count.return_value = 5
    mock_coll.query.return_value = {
        "documents": [["Test doc Corp 1"]],
        "ids": [["tenant_corp1:case_01"]],
        "metadatas": [[{"case_id": "case_01", "outcome": "FRAUD", "tenant_id": "tenant_corp1"}]],
        "distances": [[0.12]]
    }
    vdb.collection = mock_coll

    # 1. Test add_case includes tenant_id in metadata and prefixed ID
    vdb.add_case("case_test_99", "Fraud description", "FRAUD", tenant_id="tenant_corp1")
    mock_coll.add.assert_called_with(
        documents=["Fraud description"],
        metadatas=[{"case_id": "case_test_99", "outcome": "FRAUD", "tenant_id": "tenant_corp1"}],
        ids=["tenant_corp1:case_test_99"]
    )

    # 2. Test similarity_search passes where={"tenant_id": tenant_id}
    res = vdb.similarity_search("payroll fraud", top_k=3, tenant_id="tenant_corp1")
    mock_coll.query.assert_called_with(
        query_texts=["payroll fraud"],
        n_results=3,
        where={"tenant_id": "tenant_corp1"}
    )
    assert len(res) == 1
    assert res[0]["case_id"] == "tenant_corp1:case_01"
    assert res[0]["outcome"] == "FRAUD"

    # 3. Test knowledge_lookup_node passes state["tenant_id"] to vector_store
    with patch("graph.vector_store.similarity_search") as mock_sim_search:
        mock_sim_search.return_value = [{"case_id": "C-1", "outcome": "FRAUD"}]
        test_state = {
            "tenant_id": "tenant_corp1",
            "device_evidence": {"os": "Linux"},
            "location_evidence": {"country": "US"}
        }
        out_state = knowledge_lookup_node(test_state)
        mock_sim_search.assert_called_once()
        _, kwargs = mock_sim_search.call_args
        assert kwargs.get("tenant_id") == "tenant_corp1"
        assert len(out_state["historical_cases"]) == 1

