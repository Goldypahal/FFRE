"""
Automated Test Suite for Transaction Ingestion Connector & CSV Import (Task T1.2 / Finding V8).

Validates:
1. Batch JSON ingestion with metadata fields (counterparty, channel, ip_address, device_ref).
2. Quarantine validation & accounting: negative amounts, invalid channels, malformed timestamps, absent accounts.
3. CSV format parsing via both multipart/form-data and text/csv uploads.
4. Idempotency: re-ingestion skips duplicates cleanly without modifying existing records or failing the batch.
5. Strict multi-tenant isolation on transaction ingestion and retrieval.
"""

import io
import json
import pytest
from fastapi.testclient import TestClient

from main import app
from database import get_db, SessionLocal
import models
import auth

client = TestClient(app)


def set_auth_user(role: str = "investigator", tenant_id: str = "tenant-ingest-alpha"):
    user = models.User(
        user_id=f"user_{tenant_id}",
        name=f"User {tenant_id}",
        email=f"user@{tenant_id}.com",
        role=role,
        tenant_id=tenant_id
    )
    app.dependency_overrides[auth.get_current_user] = lambda: user
    return user


@pytest.fixture(autouse=True)
def clean_auth_overrides():
    yield
    app.dependency_overrides.pop(auth.get_current_user, None)


@pytest.fixture
def ingestion_db():
    db = SessionLocal()
    try:
        tenant_a = "tenant-ingest-alpha"
        tenant_b = "tenant-ingest-beta"

        # Ensure customers exist
        cust_a = db.query(models.Customer).filter(models.Customer.customer_id == "cust_ingest_a").first()
        if not cust_a:
            cust_a = models.Customer(
                customer_id="cust_ingest_a",
                tenant_id=tenant_a,
                name="Alice Ingest"
            )
            db.add(cust_a)

        cust_b = db.query(models.Customer).filter(models.Customer.customer_id == "cust_ingest_b").first()
        if not cust_b:
            cust_b = models.Customer(
                customer_id="cust_ingest_b",
                tenant_id=tenant_b,
                name="Bob Ingest"
            )
            db.add(cust_b)

        # Ensure accounts exist
        acct_a = db.query(models.Account).filter(models.Account.account_id == "acct_ingest_a").first()
        if not acct_a:
            acct_a = models.Account(
                account_id="acct_ingest_a",
                customer_id="cust_ingest_a",
                tenant_id=tenant_a,
                account_type="CHECKING",
                balance=10000.0
            )
            db.add(acct_a)

        acct_b = db.query(models.Account).filter(models.Account.account_id == "acct_ingest_b").first()
        if not acct_b:
            acct_b = models.Account(
                account_id="acct_ingest_b",
                customer_id="cust_ingest_b",
                tenant_id=tenant_b,
                account_type="SAVINGS",
                balance=5000.0
            )
            db.add(acct_b)

        db.commit()
        yield db
    finally:
        db.close()


def test_batch_json_ingestion_valid(ingestion_db):
    """Batch JSON ingestion persists transactions with new metadata fields and correct accounting."""
    set_auth_user("investigator", "tenant-ingest-alpha")

    payload = {
        "transactions": [
            {
                "txn_id": "tx_batch_valid_01",
                "account_id": "acct_ingest_a",
                "amount": 150.50,
                "currency": "USD",
                "channel": "mobile",
                "counterparty": "Acme Supermarket",
                "ip_address": "192.168.1.100",
                "device_ref": "dev_iphone_15",
                "timestamp": "2026-10-22T10:00:00Z"
            },
            {
                "txn_id": "tx_batch_valid_02",
                "account_id": "acct_ingest_a",
                "amount": 99.99,
                "currency": "EUR",
                "channel": "web",
                "counterparty": "Global Stream Inc",
                "ip_address": "10.0.0.5",
                "device_ref": "dev_macbook_pro"
            }
        ]
    }

    res = client.post("/api/v1/transactions/ingest", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total_records"] == 2
    assert data["ingested"] == 2
    assert data["quarantined"] == 0
    assert data["skipped_duplicates"] == 0

    # Verify directly in database
    db_txn = ingestion_db.query(models.Transaction).filter(models.Transaction.txn_id == "tx_batch_valid_01").first()
    assert db_txn is not None
    assert db_txn.tenant_id == "tenant-ingest-alpha"
    assert float(db_txn.amount) == 150.50
    assert db_txn.currency == "USD"
    assert db_txn.channel == "mobile"
    assert db_txn.counterparty == "Acme Supermarket"
    assert db_txn.ip_address == "192.168.1.100"
    assert db_txn.device_ref == "dev_iphone_15"


def test_quarantine_accounting_on_invalid_records(ingestion_db):
    """Invalid records must be quarantined with descriptive reasons without failing valid records."""
    set_auth_user("investigator", "tenant-ingest-alpha")

    payload = {
        "transactions": [
            {
                "txn_id": "tx_quarantine_good",
                "account_id": "acct_ingest_a",
                "amount": 42.00,
                "channel": "pos"
            },
            {
                "txn_id": "tx_bad_amount_neg",
                "account_id": "acct_ingest_a",
                "amount": -50.00,
                "channel": "atm"
            },
            {
                "txn_id": "tx_bad_channel",
                "account_id": "acct_ingest_a",
                "amount": 100.00,
                "channel": "telepathy_channel"
            },
            {
                "txn_id": "tx_bad_acct",
                "account_id": "acct_non_existent_999",
                "amount": 200.00,
                "channel": "web"
            },
            {
                "txn_id": "tx_bad_timestamp",
                "account_id": "acct_ingest_a",
                "amount": 75.00,
                "timestamp": "invalid_date_not_iso"
            }
        ]
    }

    res = client.post("/api/v1/transactions/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_records"] == 5
    assert data["ingested"] == 1
    assert data["quarantined"] == 4
    assert len(data["quarantine_reasons"]) == 4

    reasons = [r["reason"] for r in data["quarantine_reasons"]]
    assert any("strictly positive" in r for r in reasons)
    assert any("channel" in r.lower() for r in reasons)
    assert any("does not exist" in r.lower() for r in reasons)
    assert any("timestamp" in r.lower() for r in reasons)

    # Verify the good transaction was successfully committed
    good_txn = ingestion_db.query(models.Transaction).filter(models.Transaction.txn_id == "tx_quarantine_good").first()
    assert good_txn is not None
    assert float(good_txn.amount) == 42.00


def test_idempotent_reingestion_skips_duplicates(ingestion_db):
    """Re-ingesting existing transactions must skip duplicates cleanly without corrupting records."""
    set_auth_user("investigator", "tenant-ingest-alpha")

    payload = {
        "transactions": [
            {
                "txn_id": "tx_idempotent_01",
                "account_id": "acct_ingest_a",
                "amount": 500.00,
                "channel": "api"
            }
        ]
    }

    # First pass: ingested
    res1 = client.post("/api/v1/transactions/ingest", json=payload)
    assert res1.status_code == 200
    assert res1.json()["ingested"] == 1
    assert res1.json()["skipped_duplicates"] == 0

    # Second pass: duplicate skipped
    res2 = client.post("/api/v1/transactions/ingest", json=payload)
    assert res2.status_code == 200
    assert res2.json()["ingested"] == 0
    assert res2.json()["skipped_duplicates"] == 1
    assert res2.json()["quarantined"] == 0


def test_csv_ingestion_multipart_and_raw_text(ingestion_db):
    """Ingestion endpoint must support CSV uploads via both multipart form-data and raw text/csv."""
    set_auth_user("investigator", "tenant-ingest-alpha")

    # 1. Raw text/csv upload
    csv_content = (
        "txn_id,account_id,amount,currency,channel,counterparty,ip_address\n"
        "tx_csv_raw_01,acct_ingest_a,310.25,USD,web,Amazon Services,172.16.0.4\n"
        "tx_csv_raw_02,acct_ingest_a,45.00,USD,pos,Starbucks Coffee,172.16.0.5\n"
    )
    headers_csv = {
        "Content-Type": "text/csv"
    }

    res_raw = client.post("/api/v1/transactions/ingest", content=csv_content.encode("utf-8"), headers=headers_csv)
    assert res_raw.status_code == 200, res_raw.text
    data_raw = res_raw.json()
    assert data_raw["total_records"] == 2
    assert data_raw["ingested"] == 2
    assert data_raw["quarantined"] == 0

    # 2. Multipart form-data file upload
    csv_file_content = (
        "txn_id,account_id,amount,currency,channel,counterparty\n"
        "tx_csv_multipart_01,acct_ingest_a,1250.00,USD,wire,Pacific Escrow\n"
        "tx_csv_multipart_bad,acct_ingest_a,-10.00,USD,pos,Bad Coffee\n"
    )
    files = {"file": ("batch.csv", io.BytesIO(csv_file_content.encode("utf-8")), "text/csv")}

    res_multipart = client.post("/api/v1/transactions/ingest", files=files)
    assert res_multipart.status_code == 200, res_multipart.text
    data_mp = res_multipart.json()
    assert data_mp["total_records"] == 2
    assert data_mp["ingested"] == 1
    assert data_mp["quarantined"] == 1


def test_cross_tenant_ingestion_isolation(ingestion_db):
    """Tenant A cannot ingest transactions into Tenant B's accounts, nor access Tenant B's transactions."""
    set_auth_user("investigator", "tenant-ingest-beta")

    # Ingest valid transaction for Tenant B
    res_b = client.post(
        "/api/v1/transactions/ingest",
        json={
            "transactions": [
                {
                    "txn_id": "tx_beta_isolated_01",
                    "account_id": "acct_ingest_b",
                    "amount": 750.00,
                    "channel": "web"
                }
            ]
        }
    )
    assert res_b.status_code == 200
    assert res_b.json()["ingested"] == 1

    # Switch to Tenant A
    set_auth_user("investigator", "tenant-ingest-alpha")

    # Tenant A attempts to ingest transaction into Tenant B's account: must be quarantined
    res_cross = client.post(
        "/api/v1/transactions/ingest",
        json={
            "transactions": [
                {
                    "txn_id": "tx_cross_attack_01",
                    "account_id": "acct_ingest_b",
                    "amount": 999.00,
                    "channel": "mobile"
                }
            ]
        }
    )
    assert res_cross.status_code == 200
    assert res_cross.json()["quarantined"] == 1
    assert "Cross-tenant violation" in res_cross.json()["quarantine_reasons"][0]["reason"]

    # Tenant A attempts to retrieve Tenant B's transaction by ID: must return 403 Forbidden
    res_get_cross = client.get("/api/v1/transactions/tx_beta_isolated_01")
    assert res_get_cross.status_code == 403

    # Tenant B can retrieve their own transaction
    set_auth_user("investigator", "tenant-ingest-beta")
    res_get_b = client.get("/api/v1/transactions/tx_beta_isolated_01")
    assert res_get_b.status_code == 200
    assert res_get_b.json()["txn_id"] == "tx_beta_isolated_01"
