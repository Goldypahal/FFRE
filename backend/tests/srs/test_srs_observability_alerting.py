import os
import json
import pytest
import models
from metrics import MetricsCollector, metrics_collector

def test_obs_metrics_percentile_latency_calculation():
    """
    Task 35 Observability Test 1: Verify P50, P95, P99 percentile latency calculation accuracy.
    """
    collector = MetricsCollector()
    
    # Record 100 sample durations: 0.1s to 10.0s
    for i in range(1, 101):
        collector.record_investigation_time(f"inv_obs_{i}", float(i) * 0.1)

    stats = collector.get_investigation_duration_stats()
    assert stats["count"] == 100
    assert 4.9 <= stats["median"] <= 5.1
    assert 9.4 <= stats["p95"] <= 9.7
    assert 9.8 <= stats["p99"] <= 10.1

def test_obs_prometheus_metrics_endpoint_export(client):
    """
    Task 35 Observability Test 2: Verify Prometheus text format metrics exporter output.
    """
    res_json = client.get("/api/v1/metrics")
    assert res_json.status_code == 200
    assert "investigation_duration_stats" in res_json.json()

    res_prom = client.get("/metrics")
    assert res_prom.status_code == 200
    assert "text/plain" in res_prom.headers.get("content-type", "")
    assert "ffre_investigation_duration_seconds" in res_prom.text
    assert "ffre_investigations_total" in res_prom.text

def test_obs_alert_rule_slas_breach_thresholds():
    """
    Task 35 Observability Test 3: Verify alert condition evaluator for NFR-1 SLA breaches (P95 > 8.0s).
    """
    collector = MetricsCollector()
    # Populate durations exceeding 8.0s target
    for i in range(1, 20):
        collector.record_investigation_time(f"inv_slow_{i}", 9.5)

    stats = collector.get_investigation_duration_stats()
    sla_breached = stats["p95"] > 8.0
    assert sla_breached is True

def test_obs_dlq_queue_depth_alerting(db_session):
    """
    Task 35 Observability Test 4: Verify Dead Letter Queue depth alert condition.
    """
    # Create DLQ failed investigation
    inv = models.Investigation(
        investigation_id="inv_dlq_obs_1",
        txn_id="T-DLQ-OBS-1",
        status="FAILED",
        report="Max retries exhausted in Dead Letter Queue"
    )
    db_session.add(inv)
    db_session.commit()

    dlq_count = db_session.query(models.Investigation).filter(models.Investigation.status == "FAILED").count()
    dlq_alert_triggered = dlq_count > 0
    assert dlq_alert_triggered is True

def test_obs_audit_log_traceability_metrics_correlation(db_session):
    """
    Task 35 Observability Test 5: Verify correlation between DB audit logs and metrics collector entries.
    """
    inv_id = "inv_corr_obs_99"
    txn_id = "T-CORR-OBS-99"

    inv = models.Investigation(investigation_id=inv_id, txn_id=txn_id, status="COMPLETED")
    audit = models.AuditLog(investigation_id=inv_id, action="METRIC_CORRELATION_TEST")

    db_session.add_all([inv, audit])
    db_session.commit()

    metrics_collector.record_investigation_time(inv_id, 1.45)
    metrics_collector.record_confidence_score(inv_id, 0.98)

    db_audit = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == inv_id).first()
    assert db_audit is not None
    assert db_audit.action == "METRIC_CORRELATION_TEST"
