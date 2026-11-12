"""
Regression tests for defects found in the November 2026 audit that had no test of their own.
Each test fails on the code as it was before the fix.
"""
import os

import pytest
from langgraph.checkpoint.memory import MemorySaver

import auth
import graph
import guardrails
import models
import security


def _state(investigation_id: str) -> dict:
    return {
        "investigation_id": investigation_id, "transaction_id": "tx-none", "tenant_id": "default_tenant",
        "tasks": [], "customer_evidence": {}, "transaction_evidence": {}, "merchant_evidence": {},
        "device_evidence": {}, "location_evidence": {}, "historical_cases": [], "risk_score": None,
        "confidence": None, "validated": False, "retry_count": 0, "report": None,
    }


def test_cancelled_investigation_ends_instead_of_looping(db_session):
    """A cancelled run used to spin until the recursion limit, writing thousands of audit rows."""
    db_session.add(models.Investigation(investigation_id="inv_reg_cancel", status="CANCELLED", tenant_id="default_tenant"))
    db_session.commit()
    app = graph.build_graph(checkpointer=MemorySaver())
    result = app.invoke(_state("inv_reg_cancel"), config={"configurable": {"thread_id": "reg-cancel"}, "recursion_limit": 60})
    assert result.get("workflow_status") == "CANCELLED"
    rows = db_session.query(models.AuditLog).filter_by(investigation_id="inv_reg_cancel").count()
    assert rows < 40


def test_critic_that_never_approves_is_bounded(db_session, monkeypatch):
    """The critic cycle counter must live in graph state, or the loop never reaches its limit."""
    class _Reply:
        content = '{"critic_issues": true, "critique": "x", "reasoning": "Summary of the investigation risk.", "risk_score": 0.2}'

    class _AlwaysObjects:
        model_name = "fake"
        calls = 0

        def invoke(self, prompt):
            _AlwaysObjects.calls += 1
            return _Reply()

    monkeypatch.setattr(graph, "llm", _AlwaysObjects())
    db_session.add(models.Investigation(investigation_id="inv_reg_critic", status="RUNNING", tenant_id="default_tenant"))
    db_session.commit()
    app = graph.build_graph(checkpointer=MemorySaver())
    result = app.invoke(_state("inv_reg_critic"), config={"configurable": {"thread_id": "reg-critic"}, "recursion_limit": 60})
    assert result.get("critic_cycle_count", 0) >= 2
    assert _AlwaysObjects.calls <= 12


@pytest.mark.parametrize("sentence", [
    "The customer is a known terrorist financier and the risk is extreme.",
    "The beneficiary is located in France according to our analysis.",
    "Analysis shows prior fraud convictions for this individual.",
    "The amount of 6 USD was sent.",
])
def test_verifier_rejects_invented_claims(sentence):
    evidence = {
        "transaction": {"amount": 9500, "currency": "USD", "account_id": "acc_corp_88", "status": "COMPLETED"},
        "velocity": {"count_24h": 6},
        "location": {"country": "RU"},
    }
    claim = guardrails.extract_and_verify_claims(sentence, evidence)[0]
    assert claim["supported"] is False, claim["verification_reason"]


def test_verifier_does_not_treat_cost_or_most_as_an_operating_system():
    evidence = {"transaction": {"amount": 9500, "currency": "USD"}}
    claim = guardrails.extract_and_verify_claims("The total cost was $9,500.00 for most of the period.", evidence)[0]
    assert "device" not in claim["verification_reason"].lower()


def test_currency_conflict_is_a_contradiction_not_a_gap():
    evidence = {"transaction": {"amount": 9500, "currency": "USD"}}
    claim = guardrails.extract_and_verify_claims("The transaction amount was 9,500 EUR.", evidence)[0]
    assert claim["status"] == "CONTRADICTED"


def test_production_never_falls_back_to_the_development_key(monkeypatch):
    """ENVIRONMENT=production (not only ENV) must make a missing secret an error."""
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("STRICT_ENTERPRISE_MODE", "false")
    with pytest.raises(ValueError):
        security.validate_production_secret("ENCRYPTION_SECRET_KEY", None)
    with pytest.raises(ValueError):
        security.validate_production_secret("SECRET_KEY", "REPLACE_WITH_SECURE_JWT_SECRET_KEY")


def test_logout_marker_revokes_earlier_tokens_only():
    token = auth.create_refresh_token({"sub": "regress@example.com"})
    assert auth.decode_refresh_token(token)["sub"] == "regress@example.com"
    auth.revoke_user_sessions("regress@example.com")
    with pytest.raises(Exception):
        auth.decode_refresh_token(token)
    import time
    time.sleep(0.01)
    fresh = auth.create_refresh_token({"sub": "regress@example.com"})
    assert auth.decode_refresh_token(fresh)["sub"] == "regress@example.com"


def test_key_rotation_skips_values_it_cannot_decrypt(db_session):
    """A value that fails to decrypt with the old key must be left alone, not encrypted again."""
    cust = models.Customer(customer_id="cust_rot_1", tenant_id="default_tenant")
    cust._name = security.encrypt_aes256_gcm("Rotation Person", secret_override="some-other-old-secret-entirely-000000")
    db_session.add(cust)
    db_session.commit()
    before = cust._name
    stats = security.rotate_database_pii(db_session, old_secret="wrong-old-secret-00000000000000000000", new_secret="new-secret-000000000000000000000000000")
    db_session.refresh(cust)
    assert cust._name == before
    assert stats["skipped"] >= 1
