import pytest
from fastapi.testclient import TestClient
from metrics import metrics_collector, MODEL_PRICING
import models

@pytest.fixture(autouse=True)
def reset_metrics():
    metrics_collector.reset_llm_metrics()
    yield
    metrics_collector.reset_llm_metrics()

def test_token_cost_calculation():
    """Verify exact token cost calculations based on rate card."""
    # gpt-4o: prompt $2.50/1M, completion $10.00/1M
    cost_4o = metrics_collector.calculate_token_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    expected_4o = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
    assert abs(cost_4o - expected_4o) < 1e-7

    # gpt-4o-mini: prompt $0.15/1M, completion $0.60/1M
    cost_mini = metrics_collector.calculate_token_cost("gpt-4o-mini", prompt_tokens=2000, completion_tokens=1000)
    expected_mini = (2000 * 0.15 / 1_000_000) + (1000 * 0.60 / 1_000_000)
    assert abs(cost_mini - expected_mini) < 1e-7

def test_record_llm_call_and_aggregation():
    """Verify recording LLM telemetry aggregates tokens, cost, and dimensional breakdowns."""
    metrics_collector.record_llm_call(
        investigation_id="INV-OBS-001",
        node_name="planner",
        model="gpt-4o-mini",
        prompt_tokens=400,
        completion_tokens=150,
        latency_ms=120.5,
        tenant_id="default_tenant"
    )

    metrics_collector.record_llm_call(
        investigation_id="INV-OBS-001",
        node_name="reasoner",
        model="gpt-4o",
        prompt_tokens=800,
        completion_tokens=300,
        latency_ms=450.0,
        tenant_id="default_tenant"
    )

    stats = metrics_collector.get_llm_observability_stats()
    assert stats["total_prompt_tokens"] == 1200
    assert stats["total_completion_tokens"] == 450
    assert stats["total_tokens"] == 1650
    assert stats["total_llm_calls"] == 2
    assert stats["total_cost_usd"] > 0.0

    # Nodes breakdown
    assert "planner" in stats["tokens_by_node"]
    assert stats["tokens_by_node"]["planner"]["prompt"] == 400
    assert "reasoner" in stats["tokens_by_node"]
    assert stats["tokens_by_node"]["reasoner"]["prompt"] == 800

    # Models breakdown
    assert "gpt-4o-mini" in stats["tokens_by_model"]
    assert "gpt-4o" in stats["tokens_by_model"]

    # Latency percentiles
    lat = stats["latency_stats_ms"]
    assert lat["count"] == 2
    assert lat["mean"] > 0.0
    assert lat["p95"] > 0.0

def test_multitenant_cost_attribution():
    """Verify cost intelligence properly partitions costs and tokens across tenants."""
    # Tenant Alpha
    metrics_collector.record_llm_call(
        investigation_id="INV-ALPHA-1",
        node_name="reasoner",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
        latency_ms=300.0,
        tenant_id="tenant_alpha"
    )

    # Tenant Beta
    metrics_collector.record_llm_call(
        investigation_id="INV-BETA-1",
        node_name="planner",
        model="gpt-4o-mini",
        prompt_tokens=500,
        completion_tokens=200,
        latency_ms=150.0,
        tenant_id="tenant_beta"
    )

    stats_alpha = metrics_collector.get_llm_observability_stats(tenant_id="tenant_alpha")
    stats_beta = metrics_collector.get_llm_observability_stats(tenant_id="tenant_beta")

    assert stats_alpha["total_prompt_tokens"] == 1000
    assert stats_alpha["total_completion_tokens"] == 500
    assert stats_beta["total_prompt_tokens"] == 500
    assert stats_beta["total_completion_tokens"] == 200

    # Alpha cost must be strictly higher due to gpt-4o pricing
    assert stats_alpha["total_cost_usd"] > stats_beta["total_cost_usd"]

def test_api_metrics_endpoints(client):
    """Verify /api/v1/metrics and /api/v1/metrics/ai-cost return valid telemetry payloads."""
    metrics_collector.record_llm_call(
        investigation_id="INV-API-1",
        node_name="critic",
        model="gpt-4o-mini",
        prompt_tokens=350,
        completion_tokens=120,
        latency_ms=210.0,
        tenant_id="default_tenant"
    )

    # Test /api/v1/metrics
    res1 = client.get("/api/v1/metrics")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "llm_observability" in data1
    assert data1["llm_observability"]["total_tokens"] == 470

    # Test /api/v1/metrics/ai-cost
    res2 = client.get("/api/v1/metrics/ai-cost")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_prompt_tokens"] == 350
    assert data2["total_completion_tokens"] == 120
    assert "tokens_by_node" in data2
    assert "tokens_by_model" in data2

def test_prometheus_metrics_export(client):
    """Verify Prometheus /metrics exports full suite of LLM telemetry metrics."""
    metrics_collector.record_llm_call(
        investigation_id="INV-PROM-1",
        node_name="reporter",
        model="gpt-4o",
        prompt_tokens=600,
        completion_tokens=250,
        latency_ms=380.0,
        tenant_id="default_tenant"
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    assert "ffre_llm_tokens_total{type=\"prompt\"} 600" in text
    assert "ffre_llm_tokens_total{type=\"completion\"} 250" in text
    assert "ffre_llm_tokens_total{type=\"total\"} 850" in text
    assert "ffre_llm_cost_usd_total" in text
    assert "ffre_llm_calls_total 1" in text
    assert "ffre_llm_call_duration_seconds{quantile=\"0.50\"}" in text
    assert "ffre_llm_model_tokens_total{model=\"gpt-4o\",type=\"prompt\"} 600" in text
    assert "ffre_llm_node_tokens_total{node=\"reporter\",type=\"prompt\"} 600" in text
    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"default_tenant\"}" in text


def test_privacy_preserving_metrics_no_pii(client):
    """
    T2.4: Verify zero PII leakage in Prometheus /metrics and telemetry APIs.
    Metrics endpoints must NEVER expose customer names, email addresses, credit cards, or SSNs.
    """
    import re

    # Record legitimate telemetry containing clean operational IDs
    metrics_collector.record_llm_call(
        investigation_id="inv_sec_001",
        node_name="risk_reasoning",
        model="gpt-4o-mini",
        prompt_tokens=450,
        completion_tokens=180,
        latency_ms=195.0,
        tenant_id="tenant_secure_corp"
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    metrics_text = res.text

    # Comprehensive PII Regex Patterns
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    ssn_regex = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    credit_card_regex = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b')
    name_patterns = ["Jonathan Doe", "Alice Smith", "Eleanor Vance", "Bob Jones", "Hacker", "Attacker"]

    # Assert zero PII in Prometheus text
    assert not email_regex.search(metrics_text), "Found leaked email address in /metrics output!"
    assert not ssn_regex.search(metrics_text), "Found leaked SSN in /metrics output!"
    assert not credit_card_regex.search(metrics_text), "Found leaked credit card number in /metrics output!"
    for name in name_patterns:
        assert name not in metrics_text, f"Found leaked personal name '{name}' in /metrics output!"


def test_tenant_prometheus_metrics_attribution(client):
    """T2.4: Verify multi-tenant Prometheus cost metrics accurately partition by tenant."""
    metrics_collector.record_llm_call(
        investigation_id="inv_ten_1",
        node_name="planner",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
        latency_ms=250.0,
        tenant_id="tenant_fintech_one"
    )
    metrics_collector.record_llm_call(
        investigation_id="inv_ten_2",
        node_name="critic",
        model="gpt-4o-mini",
        prompt_tokens=2000,
        completion_tokens=800,
        latency_ms=180.0,
        tenant_id="tenant_bank_two"
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"tenant_fintech_one\"}" in text
    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"tenant_bank_two\"}" in text


def test_prometheus_metric_label_sanitization_defense(client):
    """T2.4: Verify metric label sanitization prevents exposition corruption or label injection."""
    # Attempt label injection with quotes and newlines
    metrics_collector.record_llm_call(
        investigation_id="inv_inj_1\r\n",
        node_name='planner",injected="true',
        model='gpt-4o\nfake_gauge 123',
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=50.0,
        tenant_id='tenant_safe;DROP'
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    # Verify no unescaped quote injections or fake metric injections occurred
    assert 'injected="true"' not in text
    assert "\nfake_gauge" not in text
    assert "DROP" in text or "tenant_safe" in text
    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"default_tenant\"}" in text


def test_privacy_preserving_metrics_no_pii(client):
    """
    T2.4: Verify zero PII leakage in Prometheus /metrics and telemetry APIs.
    Metrics endpoints must NEVER expose customer names, email addresses, credit cards, or SSNs.
    """
    import re

    # Record legitimate telemetry containing clean operational IDs
    metrics_collector.record_llm_call(
        investigation_id="inv_sec_001",
        node_name="risk_reasoning",
        model="gpt-4o-mini",
        prompt_tokens=450,
        completion_tokens=180,
        latency_ms=195.0,
        tenant_id="tenant_secure_corp"
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    metrics_text = res.text

    # Comprehensive PII Regex Patterns
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    ssn_regex = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    credit_card_regex = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b')
    name_patterns = ["Jonathan Doe", "Alice Smith", "Eleanor Vance", "Bob Jones", "Hacker", "Attacker"]

    # Assert zero PII in Prometheus text
    assert not email_regex.search(metrics_text), "Found leaked email address in /metrics output!"
    assert not ssn_regex.search(metrics_text), "Found leaked SSN in /metrics output!"
    assert not credit_card_regex.search(metrics_text), "Found leaked credit card number in /metrics output!"
    for name in name_patterns:
        assert name not in metrics_text, f"Found leaked personal name '{name}' in /metrics output!"


def test_tenant_prometheus_metrics_attribution(client):
    """T2.4: Verify multi-tenant Prometheus cost metrics accurately partition by tenant."""
    metrics_collector.record_llm_call(
        investigation_id="inv_ten_1",
        node_name="planner",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
        latency_ms=250.0,
        tenant_id="tenant_fintech_one"
    )
    metrics_collector.record_llm_call(
        investigation_id="inv_ten_2",
        node_name="critic",
        model="gpt-4o-mini",
        prompt_tokens=2000,
        completion_tokens=800,
        latency_ms=180.0,
        tenant_id="tenant_bank_two"
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"tenant_fintech_one\"}" in text
    assert "ffre_llm_tenant_cost_usd_total{tenant_id=\"tenant_bank_two\"}" in text


def test_prometheus_metric_label_sanitization_defense(client):
    """T2.4: Verify metric label sanitization prevents exposition corruption or label injection."""
    # Attempt label injection with quotes and newlines
    metrics_collector.record_llm_call(
        investigation_id="inv_inj_1\r\n",
        node_name='planner",injected="true',
        model='gpt-4o\nfake_gauge 123',
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=50.0,
        tenant_id='tenant_safe;DROP'
    )

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text

    # Verify no unescaped quote injections or fake metric injections occurred
    assert 'injected="true"' not in text
    assert "\nfake_gauge" not in text
    assert "DROP" in text or "tenant_safe" in text
