import pytest
from fastapi.testclient import TestClient
import models

def test_get_investigation_graph_topology(client, db_session):
    """Verify GET /api/v1/graph/{id} returns full 12-node DAG topology and metrics."""
    inv = models.Investigation(
        investigation_id="INV-GRAPH-001",
        txn_id="TXN-GRAPH-999",
        status="COMPLETED",
        confidence=0.94,
        risk_score=0.88,
        report="High-confidence synthetic identity takeover confirmed.",
        tenant_id="default_tenant"
    )
    ev = models.Evidence(
        evidence_id="ev_graph_1",
        investigation_id="INV-GRAPH-001",
        source="customer_evidence",
        snippet="KYC status VERIFIED, account age 4 years",
        tenant_id="default_tenant"
    )
    db_session.add_all([inv, ev])
    db_session.commit()

    res = client.get("/api/v1/graph/INV-GRAPH-001")
    assert res.status_code == 200
    data = res.json()

    assert data["investigation_id"] == "INV-GRAPH-001"
    assert data["status"] == "COMPLETED"
    assert "nodes" in data
    assert len(data["nodes"]) == 12

    node_ids = [n["id"] for n in data["nodes"]]
    assert "planner" in node_ids
    assert "retrieve_customer" in node_ids
    assert "retrieve_transaction" in node_ids
    assert "retrieve_merchant" in node_ids
    assert "retrieve_device" in node_ids
    assert "retrieve_location" in node_ids
    assert "evidence_aggregator" in node_ids
    assert "evidence_validator" in node_ids
    assert "reasoner" in node_ids
    assert "critic" in node_ids
    assert "confidence_calculator" in node_ids
    assert "reporter" in node_ids

    # Check metrics
    metrics = data["metrics"]
    assert metrics["total_nodes"] == 12
    assert metrics["completed_nodes"] == 12
    assert metrics["total_tokens"] > 0
    assert metrics["total_runtime_ms"] > 0

def test_get_investigation_graph_multitenant_isolation(client, db_session):
    """Verify tenant isolation prohibits viewing graph topology of foreign tenant."""
    inv_foreign = models.Investigation(
        investigation_id="INV-FOREIGN-001",
        txn_id="TXN-FOREIGN-888",
        status="COMPLETED",
        tenant_id="foreign_tenant_xyz"
    )
    db_session.add(inv_foreign)
    db_session.commit()

    res = client.get("/api/v1/graph/INV-FOREIGN-001")
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_get_investigation_graph_not_found(client):
    """Verify 404 for nonexistent investigation graph."""
    res = client.get("/api/v1/graph/NON_EXISTENT_CASE")
    assert res.status_code == 404
