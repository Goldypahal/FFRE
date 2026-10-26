"""
Comprehensive Test Suite for Phase 3: Real Historical Case System & 4-Way Hybrid Search.

Validates:
1. 7-part HistoricalCase schema completeness (Transaction + Customer + Merchant + Device + Location + Behavior + Outcome).
2. HistoricalCaseStore persistence, indexing, and SQL metadata filtering.
3. 4-way HybridSearchEngine (Metadata Filtering + Vector Sim + Temporal Sim + Risk Sim).
4. Multi-tenancy isolation and predicate pushdown.
5. Seamless integration with LangGraph knowledge_lookup_node.
"""

import os
import datetime
import pytest
import numpy as np

from backend.cases.schema import (
    TransactionFeatures,
    CustomerFeatures,
    MerchantFeatures,
    DeviceFeatures,
    LocationFeatures,
    BehaviorFeatures,
    CaseOutcome,
    HistoricalCase,
    HybridSearchQuery,
    HybridSearchResult,
)
from backend.cases.database import HistoricalCaseStore
from backend.cases.hybrid_search import HybridSearchEngine
from backend.cases.seeder import seed_large_case_database


@pytest.fixture
def temp_case_store(tmp_path):
    db_file = str(tmp_path / "test_cases.db")
    store = HistoricalCaseStore(db_path=db_file)
    seed_large_case_database(store, tenant_id="test_tenant", clear_existing=True)
    return store


def test_historical_case_schema_completeness():
    """Validates that HistoricalCase encapsulates all 7 mandatory sections."""
    case = HistoricalCase(
        case_id="TEST_CASE_001",
        tenant_id="test_tenant",
        transaction=TransactionFeatures(amount=25000.0, channel="WIRE", currency="USD", timestamp="2026-01-15T12:00:00+00:00"),
        customer=CustomerFeatures(customer_id="C100", name="Acme Logistics", account_type="COMMERCIAL", balance=500000.0),
        merchant=MerchantFeatures(name="Global Freight", category="TRANSPORT"),
        device=DeviceFeatures(os="Linux", is_vpn=False, is_new_device=False),
        location=LocationFeatures(country="US", city="Chicago"),
        behavior=BehaviorFeatures(velocity_1h_count=1, velocity_sum_1h=25000.0, cycle_score=0.0),
        outcome=CaseOutcome(disposition="CLEARED_CTR", typology="benign_commercial", narrative="Routine freight wire", ground_truth_score=0.02)
    )

    data = case.to_dict()
    assert "transaction" in data
    assert "customer" in data
    assert "merchant" in data
    assert "device" in data
    assert "location" in data
    assert "behavior" in data
    assert "outcome" in data

    # Reconstruct from dict
    restored = HistoricalCase.from_dict(data)
    assert restored.case_id == "TEST_CASE_001"
    assert restored.transaction.amount == 25000.0
    assert restored.customer.name == "Acme Logistics"
    assert restored.outcome.disposition == "CLEARED_CTR"


def test_historical_case_store_persistence_and_filtering(temp_case_store):
    """Tests SQLite persistence, count, and SQL metadata filtering."""
    assert temp_case_store.count(tenant_id="test_tenant") >= 120

    # Filter by channel WIRE and minimum amount $50,000
    q = HybridSearchQuery(
        channel="WIRE",
        min_amount=50000.0,
        tenant_id="test_tenant"
    )
    wires = temp_case_store.filter_candidates(q)
    assert len(wires) > 0
    for w in wires:
        assert w.transaction.channel == "WIRE"
        assert w.transaction.amount >= 50000.0
        assert w.tenant_id == "test_tenant"

    # Filter by disposition CONFIRMED_FRAUD
    q_fraud = HybridSearchQuery(
        filter_dispositions=["CONFIRMED_FRAUD"],
        tenant_id="test_tenant"
    )
    fraud_cases = temp_case_store.filter_candidates(q_fraud)
    assert len(fraud_cases) > 0
    for f in fraud_cases:
        assert f.outcome.disposition == "CONFIRMED_FRAUD"


def test_hybrid_search_vector_similarity(temp_case_store):
    """Validates that distinct semantic queries accurately match relevant case narratives."""
    engine = HybridSearchEngine(store=temp_case_store)

    q = HybridSearchQuery(
        query_text="Tor Browser unknown OS from high-risk jurisdiction Russia credential stuffing password reset",
        tenant_id="test_tenant",
        weight_vector=1.0,
        weight_temporal=0.0,
        weight_risk=0.0,
        top_k=3
    )
    results = engine.search(q)
    assert len(results) > 0

    top_hit = results[0]
    assert top_hit.case.outcome.typology == "account_takeover"
    assert top_hit.vector_similarity > 0.20
    assert "account takeover" in top_hit.case.outcome.narrative.lower() or "ato" in top_hit.case.outcome.narrative.lower()


def test_hybrid_search_temporal_similarity(temp_case_store):
    """Validates exponential temporal decay: recent cases score higher than distant cases."""
    engine = HybridSearchEngine(store=temp_case_store, decay_half_life_days=30.0)

    # Query timestamp at base time
    t_now = datetime.datetime(2026, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # Case 1 day prior vs case 120 days prior
    case_recent = HistoricalCase(
        case_id="TEMP_RECENT",
        tenant_id="test_tenant",
        transaction=TransactionFeatures(amount=1000.0, timestamp=(t_now - datetime.timedelta(days=1)).isoformat()),
        outcome=CaseOutcome(disposition="BENIGN", typology="none", narrative="test recent", ground_truth_score=0.1)
    )
    case_distant = HistoricalCase(
        case_id="TEMP_DISTANT",
        tenant_id="test_tenant",
        transaction=TransactionFeatures(amount=1000.0, timestamp=(t_now - datetime.timedelta(days=120)).isoformat()),
        outcome=CaseOutcome(disposition="BENIGN", typology="none", narrative="test distant", ground_truth_score=0.1)
    )

    sim_recent = engine._compute_temporal_similarity(t_now, case_recent)
    sim_distant = engine._compute_temporal_similarity(t_now, case_distant)

    assert sim_recent > 0.95
    assert sim_distant < 0.05
    assert sim_recent > sim_distant


def test_hybrid_search_risk_similarity(temp_case_store):
    """Validates that risk profile matching accurately aligns estimated vs precedent risk."""
    engine = HybridSearchEngine(store=temp_case_store)

    q_low_risk = HybridSearchQuery(transaction_amount=85000.0, channel="WIRE", estimated_risk=0.05, tenant_id="test_tenant")
    q_high_risk = HybridSearchQuery(transaction_amount=9500.0, channel="ACH", estimated_risk=0.90, tenant_id="test_tenant")

    case_benign = HistoricalCase(
        case_id="BENIGN_REF",
        transaction=TransactionFeatures(amount=85000.0, channel="WIRE"),
        outcome=CaseOutcome(disposition="CLEARED_CTR", typology="commercial", narrative="benign wire", ground_truth_score=0.02)
    )
    case_fraud = HistoricalCase(
        case_id="FRAUD_REF",
        transaction=TransactionFeatures(amount=9500.0, channel="ACH"),
        outcome=CaseOutcome(disposition="CONFIRMED_FRAUD", typology="structuring", narrative="smurfing", ground_truth_score=0.95)
    )

    # Low risk query should align strongly with benign case
    sim_low_benign = engine._compute_risk_similarity(q_low_risk, 0.05, case_benign)
    sim_low_fraud = engine._compute_risk_similarity(q_low_risk, 0.05, case_fraud)
    assert sim_low_benign > sim_low_fraud

    # High risk query should align strongly with fraud case
    sim_high_fraud = engine._compute_risk_similarity(q_high_risk, 0.90, case_fraud)
    sim_high_benign = engine._compute_risk_similarity(q_high_risk, 0.90, case_benign)
    assert sim_high_fraud > sim_high_benign


def test_hybrid_search_4way_ranking_and_metadata_filter(temp_case_store):
    """Executes full 4-stage search: Metadata filtering + Vector + Temporal + Risk."""
    engine = HybridSearchEngine(store=temp_case_store)

    query = HybridSearchQuery(
        query_text="structuring intentional avoidance under statutory CTR 10k threshold",
        transaction_amount=9200.0,
        channel="ACH",
        estimated_risk=0.75,
        tenant_id="test_tenant",
        min_amount=8000.0,
        max_amount=10000.0,
        top_k=5,
        weight_vector=0.40,
        weight_temporal=0.20,
        weight_risk=0.40
    )

    results = engine.search(query)
    assert len(results) > 0
    assert len(results) <= 5

    # All returned cases must satisfy the metadata filter constraints
    for r in results:
        assert 8000.0 <= r.case.transaction.amount <= 10000.0
        assert r.case.transaction.channel == "ACH"
        assert r.hybrid_score > 0.0
        assert r.vector_similarity >= 0.0
        assert r.temporal_similarity >= 0.0
        assert r.risk_similarity >= 0.0
        assert "Hybrid Match" in r.explanation

    # Assert results are monotonically sorted by hybrid_score descending
    scores = [r.hybrid_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_langgraph_knowledge_lookup_node_integration():
    """Tests knowledge_lookup_node execution in LangGraph with 4-way hybrid search."""
    from backend.graph import knowledge_lookup_node, AgentState
    from backend.cases.seeder import seed_large_case_database
    from backend.cases.database import get_case_store

    # Ensure store is seeded for default_tenant
    store = get_case_store()
    if store.count(tenant_id="default_tenant") == 0:
        seed_large_case_database(store, tenant_id="default_tenant")

    state: AgentState = {
        "investigation_id": "INV_HYBRID_TEST_01",
        "transaction_id": "TXN_HYBRID_01",
        "tenant_id": "default_tenant",
        "tasks": ["knowledge_lookup"],
        "customer_evidence": {"name": "Industrial Logistics LLC", "account_type": "COMMERCIAL"},
        "transaction_evidence": {
            "txn_id": "TXN_HYBRID_01",
            "amount": 85000.0,
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": "2026-01-15T12:00:00+00:00"
        },
        "merchant_evidence": {"name": "Global Minerals"},
        "device_evidence": {"os": "Linux"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.20,
        "rule_reasons": [],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
        "compliance_alerts": None,
        "has_typology_alert": None,
        "predicted_verdict": None,
        "workflow_status": None,
        "ml_risk_score": None,
        "ml_calibrated_probability": None,
        "ml_top_features": None,
        "ml_model_id": None,
    }

    # Execute knowledge_lookup_node
    res_state = knowledge_lookup_node(state)

    cases = res_state.get("historical_cases", [])
    assert len(cases) > 0
    top_case = cases[0]

    # Verify structured hybrid attributes
    assert "case_id" in top_case
    assert "similarity" in top_case
    assert "hybrid_score" in top_case
    assert "vector_similarity" in top_case
    assert "temporal_similarity" in top_case
    assert "risk_similarity" in top_case
    assert "disposition" in top_case
    assert "explanation" in top_case
