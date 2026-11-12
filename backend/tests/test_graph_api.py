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

    # Check metrics. This investigation has no recorded node runs, so the monitor must report
    # nothing as measured: no invented timings, token counts or prompt versions.
    metrics = data["metrics"]
    assert metrics["total_nodes"] == 12
    assert metrics["completed_nodes"] == 0
    assert metrics["total_runtime_ms"] == 0
    assert metrics["total_tokens"] == 0
    assert all(n["measured"] is False and n["duration_ms"] == 0 for n in data["nodes"])


def test_get_investigation_graph_reports_recorded_node_timings(client, db_session):
    """Timings shown by the monitor come from the pipeline's own audit entries."""
    inv = models.Investigation(
        investigation_id="INV-GRAPH-TIMED",
        txn_id="TXN-GRAPH-TIMED",
        status="COMPLETED",
        risk_score=0.4,
        confidence=0.9,
        tenant_id="default_tenant",
    )
    db_session.add(inv)
    db_session.commit()
    for node, ms in (("planner", 12), ("retrieve_customer", 30), ("risk_reasoning", 250), ("risk_reasoning", 150)):
        db_session.add(models.AuditLog(
            investigation_id="INV-GRAPH-TIMED",
            tenant_id="default_tenant",
            action=f"NODE_EXECUTION: {node}",
            details=f"Successfully executed {node} in {ms}ms",
        ))
        db_session.commit()

    data = client.get("/api/v1/graph/INV-GRAPH-TIMED").json()
    by_id = {n["id"]: n for n in data["nodes"]}
    assert by_id["planner"]["duration_ms"] == 12 and by_id["planner"]["status"] == "completed"
    assert by_id["reasoner"]["duration_ms"] == 400  # both runs of risk_reasoning
    assert by_id["retrieve_device"]["measured"] is False and by_id["retrieve_device"]["status"] == "skipped"
    assert data["metrics"]["completed_nodes"] == 3
    assert data["metrics"]["total_runtime_ms"] == 442

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
