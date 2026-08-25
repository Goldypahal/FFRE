import pytest
import models
from main import build_investigation_response

def test_risk_score_exact_value_returned(db_session):
    # Test high risk score calculated by LangGraph
    inv_high = models.Investigation(
        investigation_id="inv_risk_high",
        txn_id="txn_rh",
        status="COMPLETED",
        confidence=0.91,
        risk_score=0.87,
        report="High risk report"
    )
    db_session.add(inv_high)
    db_session.commit()

    resp_high = build_investigation_response(inv_high, db_session)
    assert resp_high.risk_score == 0.87

    # Test medium risk score calculated by LangGraph
    inv_med = models.Investigation(
        investigation_id="inv_risk_med",
        txn_id="txn_rm",
        status="COMPLETED",
        confidence=0.88,
        risk_score=0.43,
        report="Medium risk report"
    )
    db_session.add(inv_med)
    db_session.commit()

    resp_med = build_investigation_response(inv_med, db_session)
    assert resp_med.risk_score == 0.43

    # Test low risk score calculated by LangGraph
    inv_low = models.Investigation(
        investigation_id="inv_risk_low",
        txn_id="txn_rl",
        status="COMPLETED",
        confidence=0.96,
        risk_score=0.12,
        report="Low risk report"
    )
    db_session.add(inv_low)
    db_session.commit()

    resp_low = build_investigation_response(inv_low, db_session)
    assert resp_low.risk_score == 0.12

def test_risk_score_preservation_across_status_changes(db_session):
    inv = models.Investigation(
        investigation_id="inv_status_change",
        txn_id="txn_sc",
        status="ESCALATED",
        confidence=0.65,
        risk_score=0.78,
        report="Escalated report"
    )
    db_session.add(inv)
    db_session.commit()

    resp = build_investigation_response(inv, db_session)
    assert resp.risk_score == 0.78
