"""
Tests for Task T0.2: Removal of Mock Data Creation (V1 Finding)
Verifies:
1. Unknown/typo transaction ID returns HTTP 404 and creates NO database records.
2. Cross-tenant transaction ID returns generic HTTP 404 without existence leak.
3. Pre-existing seeded transaction succeeds with HTTP 202.
"""

import pytest
import models
from auth import get_current_user
from main import app
from scripts.seed_demo_data import seed_transaction


def test_unknown_transaction_returns_404_and_creates_no_records(client, db_session):
    """Verify unknown or typo transaction ID returns 404 and does not create mock records."""
    # Count existing rows before request
    initial_cust_count = db_session.query(models.Customer).count()
    initial_acct_count = db_session.query(models.Account).count()
    initial_merch_count = db_session.query(models.Merchant).count()
    initial_txn_count = db_session.query(models.Transaction).count()
    initial_inv_count = db_session.query(models.Investigation).count()

    response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "TXN_TYPO_NONEXISTENT_999",
            "user_id": "user_typo_test"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"

    # Verify zero database rows were created on a miss
    db_session.expire_all()
    assert db_session.query(models.Customer).count() == initial_cust_count
    assert db_session.query(models.Account).count() == initial_acct_count
    assert db_session.query(models.Merchant).count() == initial_merch_count
    assert db_session.query(models.Transaction).count() == initial_txn_count
    assert db_session.query(models.Investigation).count() == initial_inv_count


def test_cross_tenant_transaction_returns_404_without_existence_leak(client, db_session):
    """Verify transaction in tenant_beta returns 404 to tenant_alpha without revealing existence."""
    # Seed transaction in tenant_beta
    seed_transaction(db_session, "TXN_PRIVATE_B", tenant_id="tenant_beta")

    # Authenticate as user in tenant_alpha
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "TXN_PRIVATE_B",
            "user_id": "user_alpha"
        }
    )

    # Must return exact same generic 404 error
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"

    # Verify tenant_alpha cannot initiate investigation for tenant_beta transaction
    inv = db_session.query(models.Investigation).filter(models.Investigation.txn_id == "TXN_PRIVATE_B").first()
    assert inv is None

    # Reset override
    app.dependency_overrides.pop(get_current_user, None)


def test_valid_seeded_transaction_succeeds(client, db_session):
    """Verify properly seeded transaction creates investigation normally."""
    seed_transaction(db_session, "TXN_VALID_001", tenant_id="default_tenant")

    response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "TXN_VALID_001",
            "user_id": "user_valid"
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert data["transaction_id"] == "TXN_VALID_001"
    assert "investigation_id" in data
