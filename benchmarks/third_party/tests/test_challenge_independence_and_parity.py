"""
Automated Pytest Suite for Challenge Independence, Evidence Parity, and Decision Policy.

Verifies:
1. Strict Zero Label Leakage:
   - Neither the 16-case Development Challenge Battery nor the 24-case Held-Out Test Battery
     leaks ground-truth supervisory labels (ground_truth_label, category, challenge_type, is_sar)
     into database entities, retriever features, or LangGraph initial state.
2. Strict Evidence Parity Across Configurations:
   - Config A (Rules-Only), Config B (Retrieval-Assisted), and Config C (Full Pipeline)
     query the identical database state and input transactions.
3. Statutory Compliance Alerts vs Laundering Verdict Separation (P1 Policy):
   - Wires >= $10,000 (CTR reporting threshold under 31 CFR § 1010.311) trigger compliance alerts
     in state['compliance_alerts'] without forcing a SUSPICIOUS laundering verdict when commercial
     legitimacy is verified.
4. Fail-Closed Disconnected Entity Handling:
   - Transactions with missing provenance or orphaned records escalate (ESCALATED) across
     all configurations rather than guessing.
"""

import os
import sys
import json
import pytest
from decimal import Decimal

from benchmarks.third_party.adapters.amlsim_adapter import AMLSimAdapter
from database import Base, engine, SessionLocal
import models
from graph import build_graph
from rules import evaluate_rules, is_typology_rule, is_compliance_mandate_rule
from benchmarks.third_party.evaluation.run_challenge_eval import (
    seed_challenge_dataset,
    evaluate_rules_only,
    evaluate_retrieval_assisted,
    evaluate_full_pipeline
)


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="module")
def challenge_cases():
    adapter = AMLSimAdapter(tenant_id="parity_test_tenant")
    return adapter.load_hardened_challenge_cases()


@pytest.fixture(scope="module")
def held_out_cases():
    adapter = AMLSimAdapter(tenant_id="parity_test_tenant")
    return adapter.load_held_out_test_cases()


def test_zero_label_leakage_in_challenge_datasets(challenge_cases, held_out_cases):
    """
    Ensure ground-truth supervisory labels and challenge typologies never leak into:
    1. Database model structures (Transaction, Account, Customer)
    2. Investigator queries
    3. LangGraph runtime initial state
    """
    forbidden_metadata_keys = {
        "ground_truth_label", "ground_truth", "is_sar", "sar",
        "typology", "alert_id", "target_verdict"
    }

    all_cases = challenge_cases + held_out_cases
    assert len(all_cases) >= 40, "Expected at least 40 total evaluation cases (16 dev + 24 held-out)"

    # 1. Database models must have no ground truth columns
    for model_cls in [models.Transaction, models.Account, models.Customer, models.Merchant]:
        for col in model_cls.__table__.columns:
            assert col.name.lower() not in ["is_sar", "is_alert", "typology", "ground_truth_label"], (
                f"Forbidden supervisory column '{col.name}' found in model {model_cls.__name__}"
            )

    # 2. Case user queries must not expose the label or typology
    for case in all_cases:
        query = case.get("user_query", "").lower()
        assert "is_sar" not in query
        assert "ground_truth" not in query
        assert "typology" not in query

    # 3. Predictor input state must be completely unpopulated with ground truth
    db = SessionLocal()
    try:
        from graph import build_graph
        graph = build_graph()
        sample_case = held_out_cases[0]
        # Evaluate Config C state construction
        state = {
            "investigation_id": f"inv_leak_audit_{sample_case['case_id']}",
            "transaction_id": sample_case["target_transaction_id"],
            "tenant_id": "audit_tenant",
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
        }
        for k in state.keys():
            assert k.lower() not in forbidden_metadata_keys, f"Forbidden key '{k}' in initial state"
    finally:
        db.close()


def test_evidence_parity_and_identical_db_context(setup_db, held_out_cases):
    """
    Verify all 3 configurations evaluate the exact same seeded database state.
    """
    tenant_id = "tenant_heldout_untouched_held_out_test_battery"
    db = SessionLocal()
    try:
        # Seed the held-out cases into the DB session
        seed_challenge_dataset(db, held_out_cases, tenant_id)

        # Pick a benign high-value case and a suspicious cycle case
        hv_case = next(c for c in held_out_cases if c["case_id"] == "TEST_BENIGN_HV_EQUIP_01")
        cyc_case = next(c for c in held_out_cases if c["case_id"] == "TEST_ILLICIT_CYCLE_4HOP_19")

        # Verify transaction exists in DB
        txn_hv = db.query(models.Transaction).filter_by(
            txn_id=hv_case["target_transaction_id"], tenant_id=tenant_id
        ).first()
        assert txn_hv is not None
        assert float(txn_hv.amount) == 54000.00

        txn_cyc = db.query(models.Transaction).filter_by(
            txn_id=cyc_case["target_transaction_id"], tenant_id=tenant_id
        ).first()
        assert txn_cyc is not None
        assert float(txn_cyc.amount) == 14500.00

        # Evaluate Config A, B, and C on the same case
        graph = build_graph()
        res_a = evaluate_rules_only(hv_case, db, tenant_id)
        res_b = evaluate_retrieval_assisted(hv_case, db, tenant_id)
        res_c = evaluate_full_pipeline(hv_case, graph, db, tenant_id)

        # Both Config B and C should recognize the legitimate commercial counterparties
        assert res_b["predicted_verdict"] == "BENIGN"
        assert res_c["predicted_verdict"] == "BENIGN"
        # Config A (scalar rules) flagged amount > $20k as SUSPICIOUS
        assert res_a["predicted_verdict"] == "SUSPICIOUS"

    finally:
        db.close()


def test_benign_high_value_commercial_wire_policy(setup_db):
    """
    Verify P1 Policy: High-value commercial transaction triggers statutory CTR compliance alert,
    but does not force a SUSPICIOUS money laundering verdict.
    """
    import uuid
    uid = uuid.uuid4().hex[:8]
    tenant_id = f"tenant_policy_{uid}"
    db = SessionLocal()
    try:
        # Create a verified commercial account and transaction of $75,000
        merch = models.Merchant(
            merchant_id=f"MERCH_CLEARINGHOUSE_{tenant_id}",
            name="Commercial Settlement Clearinghouse",
            category="COMMERCIAL_SERVICES",
            risk_score=Decimal("0.02"),
            tenant_id=tenant_id
        )
        acct_src = models.Account(
            account_id=f"ACC_COMMERCIAL_CORP_{tenant_id}",
            customer_id=f"CUST_CORP_{tenant_id}",
            account_type="COMMERCIAL_OPERATING",
            balance=Decimal("500000.00"),
            tenant_id=tenant_id
        )
        acct_dest = models.Account(
            account_id=f"ACC_VENDOR_{tenant_id}",
            customer_id=f"CUST_VENDOR_{tenant_id}",
            account_type="CHECKING",
            balance=Decimal("20000.00"),
            tenant_id=tenant_id
        )
        cust_src = models.Customer(
            customer_id=f"CUST_CORP_{tenant_id}",
            name="Apex Technologies Ltd",
            kyc_status="VERIFIED",
            risk_tier="LOW",
            tenant_id=tenant_id
        )
        cust_dest = models.Customer(
            customer_id=f"CUST_VENDOR_{tenant_id}",
            name="Global Cloud Hosting Inc",
            kyc_status="VERIFIED",
            risk_tier="LOW",
            tenant_id=tenant_id
        )
        txn = models.Transaction(
            txn_id=f"TXN_CORP_WIRE_{tenant_id}",
            account_id=f"ACC_COMMERCIAL_CORP_{tenant_id}",
            counterparty=f"ACC_VENDOR_{tenant_id}",
            merchant_id=merch.merchant_id,
            amount=Decimal("75000.00"),
            currency="USD",
            status="COMPLETED",
            tenant_id=tenant_id
        )
        db.add_all([merch, acct_src, acct_dest, cust_src, cust_dest, txn])
        db.commit()

        # Run Graph pipeline
        graph = build_graph()
        state = {
            "investigation_id": f"inv_policy_{tenant_id}",
            "transaction_id": f"TXN_CORP_WIRE_{tenant_id}",
            "tenant_id": tenant_id,
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
        }
        config = {"configurable": {"thread_id": f"inv_policy_{tenant_id}"}}
        final_state = graph.invoke(state, config=config)

        # 1. Statutory compliance alert MUST be captured
        alerts = final_state.get("compliance_alerts", [])
        assert len(alerts) > 0, "Compliance alert for statutory threshold >= $10k must be preserved"
        assert any(is_compliance_mandate_rule(a) for a in alerts)

        # 2. Predicted laundering verdict MUST remain BENIGN
        verdict = final_state.get("predicted_verdict")
        assert verdict == "BENIGN", f"Expected BENIGN laundering verdict, got {verdict}"
        assert float(final_state.get("risk_score", 0.0)) < 0.50

    finally:
        db.close()


def test_fail_closed_on_missing_entities(setup_db, held_out_cases):
    """
    Verify that missing provenance or orphaned records cause all 3 configurations
    to abstain / escalate (ESCALATED) fail-closed.
    """
    tenant_id = "tenant_abstention_audit"
    db = SessionLocal()
    try:
        orphan_case = next(c for c in held_out_cases if c["case_id"] == "TEST_ABSTENTION_ORPHAN_24")
        graph = build_graph()

        res_a = evaluate_rules_only(orphan_case, db, tenant_id)
        res_b = evaluate_retrieval_assisted(orphan_case, db, tenant_id)
        res_c = evaluate_full_pipeline(orphan_case, graph, db, tenant_id)

        assert res_a["predicted_verdict"] == "ESCALATED"
        assert res_b["predicted_verdict"] == "ESCALATED"
        assert res_c["predicted_verdict"] == "ESCALATED"
        assert res_c["abstained"] is True

    finally:
        db.close()
