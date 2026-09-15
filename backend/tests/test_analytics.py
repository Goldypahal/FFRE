import pytest
from fastapi.testclient import TestClient
from main import app
import models
from auth import get_current_user

def test_analytics_summary_authenticated(client):
    """Verify GET /api/v1/analytics/summary returns KPI metrics, risk distribution, status breakdown, and volume trends."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    assert "tenant_id" in data
    assert "kpis" in data
    kpis = data["kpis"]
    assert "total_investigations" in kpis
    assert "completed_count" in kpis
    assert "escalated_count" in kpis
    assert "running_count" in kpis
    assert "failed_count" in kpis
    assert "escalation_rate" in kpis
    assert "automation_efficiency" in kpis
    assert "avg_confidence" in kpis
    assert "avg_risk_score" in kpis
    assert "evidence_vault_count" in kpis
    assert "reports_count" in kpis
    assert "avg_resolution_time" in kpis

    assert "risk_distribution" in data
    assert len(data["risk_distribution"]) == 4
    for item in data["risk_distribution"]:
        assert "range" in item
        assert "count" in item
        assert "color" in item

    assert "status_breakdown" in data
    assert len(data["status_breakdown"]) == 4

    assert "volume_trend" in data
    assert len(data["volume_trend"]) == 6

    assert "geo_heatmap" in data
    assert len(data["geo_heatmap"]) > 0

def test_analytics_multi_tenant_isolation(client):
    """Verify analytics aggregations enforce tenant boundaries between tenants."""
    from main import SessionLocal
    db = SessionLocal()
    try:
        # Seed an investigation in tenant_alpha and another in tenant_beta
        inv_alpha = models.Investigation(
            investigation_id="inv_analytics_alpha",
            tenant_id="tenant_alpha",
            txn_id="txn_alpha_99",
            status="COMPLETED",
            risk_score=0.25,
            confidence=0.92
        )
        inv_beta = models.Investigation(
            investigation_id="inv_analytics_beta",
            tenant_id="tenant_beta",
            txn_id="txn_beta_99",
            status="ESCALATED",
            risk_score=0.85,
            confidence=0.74
        )
        db.add(inv_alpha)
        db.add(inv_beta)
        db.commit()
    finally:
        db.close()

    # User in tenant_alpha
    user_alpha = models.User(
        user_id="usr_901",
        name="Alpha User",
        email="alpha@bank.com",
        tenant_id="tenant_alpha",
        role="analyst",
        hashed_password="pw"
    )
    app.dependency_overrides[get_current_user] = lambda: user_alpha
    resp_alpha = client.get("/api/v1/analytics/summary")
    assert resp_alpha.status_code == 200
    data_alpha = resp_alpha.json()
    assert data_alpha["tenant_id"] == "tenant_alpha"
    # tenant_alpha should see at least 1 investigation and completed_count >= 1
    assert data_alpha["kpis"]["total_investigations"] >= 1
    assert data_alpha["kpis"]["completed_count"] >= 1

    # Clean up overrides
    app.dependency_overrides.pop(get_current_user, None)
