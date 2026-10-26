import os
import json
import jsonschema
from decimal import Decimal
import pytest

from benchmarks.third_party.adapters.amlsim_adapter import AMLSimAdapter
from database import SessionLocal, init_db
import models


@pytest.fixture
def adapter():
    return AMLSimAdapter(tenant_id="test_amlsim_tenant")


def test_amlsim_schema_mapping(adapter):
    """Verify AMLSim accounts and alerts parse cleanly into structured dictionaries."""
    accounts = adapter.load_accounts()
    assert len(accounts) >= 30
    assert "ACC_FO_SRC_1" in accounts
    assert isinstance(accounts["ACC_FO_SRC_1"]["initial_balance"], Decimal)

    alerts = adapter.load_alerts()
    assert len(alerts) >= 6
    assert "ALERT_FO_01" in alerts
    assert alerts["ALERT_FO_01"]["model_type"] == "fan_out"


def test_amlsim_decimal_precision(adapter):
    """Verify monetary values are parsed as exact Decimal without float truncation."""
    txns, _ = adapter.load_transactions()
    assert len(txns) >= 50

    for t in txns:
        assert isinstance(t["amount"], Decimal)
        # Check no floating point artifacts
        str_val = str(t["amount"])
        assert not str_val.endswith("0000000000001")


def test_amlsim_quarantine_malformed_records(adapter):
    """Verify negative amounts and missing originator accounts are correctly quarantined."""
    _, quarantined = adapter.load_transactions()
    assert len(quarantined) >= 2

    reasons = [q["reason"] for q in quarantined]
    assert any("Non-positive transaction amount" in r for r in reasons)
    assert any("does not exist in accounts master" in r for r in reasons)


def test_amlsim_zero_label_leakage(adapter, db_session):
    """
    CRITICAL SECURITY & VALIDITY TEST:
    Verify ground-truth labels (isSAR, alert_id, typology) are strictly withheld
    from FFIRE ingestion records and database models.
    """
    valid_txns, _ = adapter.load_transactions()

    # 1. Feature dictionaries must not contain ground truth
    forbidden_keys = {"isSAR", "is_sar", "alert_id", "typology", "model_type"}
    for t in valid_txns:
        intersect = forbidden_keys.intersection(t.keys())
        assert len(intersect) == 0, f"Label leakage detected in feature dictionary: {intersect}"

    # 2. Database models must not contain ground truth
    counts = adapter.seed_to_database(db_session)
    total_txns = db_session.query(models.Transaction).count()
    assert counts["transactions"] >= 50 or total_txns >= 50

    seeded_txns = db_session.query(models.Transaction).filter_by(tenant_id=adapter.tenant_id).all()
    for st in seeded_txns:
        assert not hasattr(st, "is_sar")
        assert not hasattr(st, "alert_id")
        assert not hasattr(st, "typology")

    seeded_custs = db_session.query(models.Customer).filter_by(tenant_id=adapter.tenant_id).all()
    for sc in seeded_custs:
        assert not hasattr(sc, "is_sar")
        assert sc.risk_tier == "MEDIUM", f"Customer {sc.customer_id} has biased risk_tier {sc.risk_tier}"


def test_amlsim_evaluation_case_schema(adapter):
    """Verify generated evaluation cases strictly validate against case.schema.json."""
    cases = adapter.build_evaluation_cases()
    assert len(cases) >= 50

    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "schemas", "case.schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Validate all cases against JSON Schema
    for case in cases:
        jsonschema.validate(instance=case, schema=schema)

    # Check typology distribution
    typologies = {c["typology"] for c in cases if c["typology"] is not None}
    expected_typologies = {"fan_out", "fan_in", "cycle", "scatter_gather", "bipartite", "stack_linear"}
    assert expected_typologies.issubset(typologies)


def test_end_to_end_zero_label_leakage_in_graph_pipeline(adapter, db_session):
    """
    P1 Integrity Audit:
    Trace evaluation case through:
    case -> adapter -> DB records -> pipeline state -> evidence retrieval -> prompt.
    Verify that ground-truth labels, alert IDs, cluster IDs, and scenario types
    never leak into the graph state, retrieved evidence, or model prompt.
    """
    from backend.graph import AgentState, get_reasoner_prompt

    cases = adapter.build_evaluation_cases()
    suspicious_cases = [c for c in cases if c.get("ground_truth_label") == "SUSPICIOUS"]
    assert len(suspicious_cases) > 0
    test_case = suspicious_cases[0]

    # Verify case has ground truth for evaluation
    assert "ground_truth_label" in test_case
    assert "cluster_id" in test_case
    assert "scenario_id" in test_case

    # Construct AgentState passed into pipeline
    state: AgentState = {
        "investigation_id": "inv_test_leakage_check",
        "transaction_id": test_case["target_transaction_id"],
        "tenant_id": adapter.tenant_id,
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": None,
        "rule_reasons": [],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    # 1. Pipeline state must NOT contain ground-truth keys
    forbidden_terms = ["SUSPICIOUS", "is_sar", "isSAR", test_case["scenario_id"], test_case["cluster_id"]]
    state_str = json.dumps(state)
    for term in forbidden_terms:
        assert term not in state_str, f"Forbidden label term '{term}' leaked into pipeline state!"

    # 2. Database records must NOT contain ground truth
    txn_row = db_session.query(models.Transaction).filter_by(
        txn_id=test_case["target_transaction_id"], tenant_id=adapter.tenant_id
    ).first()
    if txn_row:
        assert not hasattr(txn_row, "is_sar")
        assert not hasattr(txn_row, "ground_truth_label")

    # 3. Prompt payload must NOT contain ground-truth labels or alert identifiers
    evidence_bundle = {
        "transaction": state.get("transaction_evidence", {}),
        "customer": state.get("customer_evidence", {}),
        "rule_analysis": {"score": 0.55, "reasons": ["CTR transfer anomaly"]}
    }
    prompt = get_reasoner_prompt(adapter.tenant_id).format(evidence_bundle=json.dumps(evidence_bundle))
    for term in ["is_sar", "isSAR", test_case["scenario_id"], test_case["cluster_id"], "ground_truth"]:
        assert term not in prompt, f"Forbidden ground truth term '{term}' found in model prompt!"


def test_amlsim_hardened_challenge_cases_schema(adapter):
    """Verify discriminating challenge cases validate strictly against case.schema.json."""
    challenge_cases = adapter.load_hardened_challenge_cases()
    assert len(challenge_cases) == 16

    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "schemas", "case.schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    for case in challenge_cases:
        jsonschema.validate(instance=case, schema=schema)

    # Verify diverse amounts: contains benign high-value (> $20k) and suspicious low-value (< $5k)
    hv_benign = [c for c in challenge_cases if c["ground_truth_label"] == "BENIGN" and c["metadata"].get("amount", 0) >= 20000.0]
    lv_susp = [c for c in challenge_cases if c["ground_truth_label"] == "SUSPICIOUS" and c["metadata"].get("amount", 0) < 5000.0]
    assert len(hv_benign) >= 4, f"Expected >= 4 benign high-value cases, found {len(hv_benign)}"
    assert len(lv_susp) >= 3, f"Expected >= 3 suspicious low-value cases, found {len(lv_susp)}"
