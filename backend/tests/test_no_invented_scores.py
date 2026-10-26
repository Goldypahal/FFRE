"""
Tests for Task T0.4: No Invented Risk Scores (Finding V3)
Verifies:
1. build_investigation_response returns risk_score=None when investigation.risk_score is None, across all statuses.
2. GET /api/v1/investigations/{id} returns null for unscored investigations without fabrication.
3. Genuine risk scores (e.g., 0.85, 0.42) are preserved exactly as computed by reasoning / rule engine.
"""

import pytest
import models
from main import build_investigation_response, app
from auth import get_current_user
from scripts.seed_demo_data import seed_transaction


def test_build_investigation_response_preserves_none_risk_score(db_session):
    """Verify that build_investigation_response returns None for risk_score when DB value is None."""
    statuses = ["ESCALATED", "CLOSED_REJECT", "CLOSED_APPROVE", "COMPLETED", "RUNNING", "QUEUED", "WAITING_HUMAN"]

    for st in statuses:
        inv = models.Investigation(
            investigation_id=f"inv_unscored_{st.lower()}",
            txn_id="TXN_UNSCORED_TEST",
            status=st,
            risk_score=None,
            confidence=None,
            report="Test report"
        )
        resp = build_investigation_response(inv, db_session)
        assert resp.risk_score is None, f"Expected risk_score to be None for status {st}, got {resp.risk_score}"


def test_build_investigation_response_preserves_actual_risk_score(db_session):
    """Verify that build_investigation_response preserves genuine scores."""
    scores = [0.0, 0.15, 0.42, 0.75, 0.88, 1.0]

    for score in scores:
        inv = models.Investigation(
            investigation_id=f"inv_scored_{int(score*100)}",
            txn_id="TXN_SCORED_TEST",
            status="COMPLETED",
            risk_score=score,
            confidence=0.9,
            report="Scored test"
        )
        resp = build_investigation_response(inv, db_session)
        assert resp.risk_score == pytest.approx(score, 0.001)


def test_api_get_investigation_returns_null_risk_score(client, db_session):
    """Verify GET /api/v1/investigations/{id} returns JSON null when risk_score is unset."""
    seed_transaction(db_session, "TXN_NULL_SCORE_1", tenant_id="tenant_alpha")

    inv = models.Investigation(
        investigation_id="INV_NULL_SCORE_TEST",
        txn_id="TXN_NULL_SCORE_1",
        status="ESCALATED",
        risk_score=None,
        confidence=None,
        tenant_id="tenant_alpha"
    )
    db_session.add(inv)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    response = client.get(f"/api/v1/investigations/{inv.investigation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] is None
    assert data["status"] == "ESCALATED"
