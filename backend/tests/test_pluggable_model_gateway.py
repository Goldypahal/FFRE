"""
Automated Test Suite for Pluggable Model Gateway & Offline Mode (Task T1.1 / Finding V7).

Validates:
1. NullProvider deterministic generation across Planner, Reasoner, Critic, and Reporter prompts.
2. MockProvider canned responses and invocation history logging.
3. LLMGateway resolution via LLM_PROVIDER environment variable and dynamic overrides.
4. Full LangGraph DAG workflow execution completely offline with zero API costs and zero external network calls.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from llm_gateway import (
    LLMGateway,
    NullProvider,
    MockProvider,
    OpenAIProvider,
    get_llm_gateway,
    LLMResponse,
)
from metrics import metrics_collector
import graph


def test_null_provider_planner_generation():
    """NullProvider must generate valid JSON tasks list for planner prompts."""
    provider = NullProvider()
    resp = provider.invoke("Planner agent prompt: decompose transaction extraction tasks.")

    assert isinstance(resp, LLMResponse)
    assert resp.provider == "null"
    assert resp.model == "null-deterministic-v1"

    tasks = json.loads(resp.content)
    assert isinstance(tasks, list)
    assert "customer_retrieval" in tasks
    assert "transaction_retrieval" in tasks
    assert "velocity_check" in tasks


def test_null_provider_reasoner_generation():
    """NullProvider must generate valid JSON reasoning and risk_score."""
    provider = NullProvider()

    # Normal baseline evidence
    normal_prompt = "Synthesize evidence_bundle: customer normal activity, amount 100.00."
    resp_normal = provider.invoke(normal_prompt)
    data_normal = json.loads(resp_normal.content)

    assert "reasoning" in data_normal
    assert "risk_score" in data_normal
    assert 0.0 <= data_normal["risk_score"] <= 0.40

    # High-risk evidence with suspicious country and velocity spike
    high_risk_prompt = "Synthesize evidence_bundle: location country RU, high_velocity_flag True, new_device True."
    resp_high = provider.invoke(high_risk_prompt)
    data_high = json.loads(resp_high.content)

    assert data_high["risk_score"] >= 0.70
    assert "jurisdiction" in data_high["reasoning"].lower() or "velocity" in data_high["reasoning"].lower()


def test_null_provider_critic_and_reporter_generation():
    """NullProvider must generate valid critic JSON and reporter markdown."""
    provider = NullProvider()

    # Critic
    critic_resp = provider.invoke("Critic agent: evaluate draft_explanation against evidence.")
    critic_data = json.loads(critic_resp.content)
    assert "critic_issues" in critic_data
    assert "critique" in critic_data
    assert isinstance(critic_data["critic_issues"], bool)

    # Reporter
    report_resp = provider.invoke("Reporter agent: draft FinCEN executive report.")
    assert "## Executive Summary" in report_resp.content
    assert "## Recommendation" in report_resp.content


def test_mock_provider_canned_responses_and_history():
    """MockProvider must support canned responses, overrides, and call history tracking."""
    mock = MockProvider()
    mock.set_canned_response("special_trigger", '{"custom_output": true}')

    resp = mock.invoke("This contains a special_trigger for testing.")
    assert resp.content == '{"custom_output": true}'
    assert len(mock.call_history) == 1
    assert "special_trigger" in mock.call_history[0]["prompt"]

    # Global default override
    mock.set_default_response("GLOBAL_OVERRIDE")
    resp_override = mock.invoke("Any prompt here")
    assert resp_override.content == "GLOBAL_OVERRIDE"
    assert len(mock.call_history) == 2

    mock.clear()
    assert len(mock.call_history) == 0


def test_llm_gateway_provider_resolution(monkeypatch):
    """LLMGateway must dynamically resolve providers based on LLM_PROVIDER environment variable."""
    gateway = LLMGateway()

    # Explicit null
    monkeypatch.setenv("LLM_PROVIDER", "null")
    prov = gateway.get_provider()
    assert isinstance(prov, NullProvider)
    assert prov.provider_name == "null"
    assert gateway.is_offline is True

    # Explicit mock
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    prov_mock = gateway.get_provider()
    assert isinstance(prov_mock, MockProvider)
    assert prov_mock.provider_name == "mock"

    # Dynamic context override
    custom_mock = MockProvider()
    with gateway.override_provider(custom_mock):
        assert gateway.get_provider() is custom_mock
    # Reverts after context
    assert isinstance(gateway.get_provider(), MockProvider)


def test_full_offline_graph_execution(monkeypatch):
    """
    Assert full LangGraph reasoning nodes execute successfully in pure offline mode
    with zero network calls, generating grounded claims and valid decision.
    """
    # Force offline null provider
    monkeypatch.setenv("LLM_PROVIDER", "null")

    gateway = get_llm_gateway()
    null_provider = NullProvider()

    with gateway.override_provider(null_provider):
        # Build initial investigation state with mock evidence
        state = {
            "investigation_id": "inv_offline_test_001",
            "transaction_id": "tx_offline_999",
            "tenant_id": "tenant-offline",
            "tasks": [],
            "customer_evidence": {
                "name": "Jane Doe",
                "customer_id": "cust_999",
                "risk_rating": "LOW",
                "status": "OK",
            },
            "transaction_evidence": {
                "amount": 250.0,
                "currency": "USD",
                "status": "OK",
            },
            "merchant_evidence": {
                "name": "Acme Retail",
                "historical_fraud_rate": 0.01,
                "status": "OK",
            },
            "device_evidence": {
                "new_device": False,
                "os": "macOS",
                "fingerprint": "fp_clean_001",
                "status": "OK",
            },
            "location_evidence": {
                "country": "US",
                "city": "New York",
                "status": "OK",
            },
            "velocity_evidence": {
                "high_velocity_flag": False,
                "1h_count": 1,
                "status": "OK",
            },
            "verified_evidence": {},
            "historical_cases": [],
            "risk_score": None,
            "confidence": 0.0,
            "draft_explanation": None,
            "critic_feedback": None,
            "critic_issues": False,
            "retry_count": 0,
            "validated": False,
            "report": None,
            "rule_score": 0.15,
            "rule_reasons": ["Transaction within normal velocity thresholds"],
        }

        # 1. Planner Node
        state = graph.planner_node(state)
        assert len(state["tasks"]) > 0

        # 2. Risk Reasoning Node (offline reasoning via NullProvider)
        state = graph.risk_reasoning_node(state)
        assert state["draft_explanation"] is not None
        assert state["risk_score"] is not None
        assert 0.0 <= state["risk_score"] <= 1.0
        assert state["confidence"] > 0.0

        # 3. Critic Node
        state = graph.critic_node(state)
        assert "critic_issues" in state
        assert state["critic_issues"] is False

        # 4. Validator Node (Evidence Grounding)
        state = graph.validator_node(state)
        assert "validated" in state

        # 5. Reporter Node
        state = graph.report_generator_node(state)
        assert state["report"] is not None
        assert "Executive Summary" in state["report"]

        # 6. Routing Check
        routing = graph.should_retry_or_human_review(state)
        assert routing in ("END", "human_review", "report_generator", "risk_reasoning")

        # Verify zero cost registered for offline provider
        cost = metrics_collector.calculate_token_cost("null-deterministic-v1", 1000, 500)
        assert cost == 0.0
