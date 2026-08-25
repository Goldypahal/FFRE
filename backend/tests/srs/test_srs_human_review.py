import pytest
import models

def test_human_review_approve_workflow(client, db_session):
    inv = models.Investigation(
        investigation_id="inv_hr_app",
        txn_id="txn_hr_1",
        status="ESCALATED",
        confidence=0.60,
        risk_score=0.75,
        report="## HUMAN REVIEW ESCALATION REPORT\nRequires analyst review."
    )
    db_session.add(inv)
    db_session.commit()

    response = client.post(
        f"/api/v1/investigations/inv_hr_app/review",
        json={"action": "APPROVE", "notes": "Verified customer identity via phone callback."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_status"] == "CLOSED_APPROVE"
    assert data["investigation"]["risk_score"] == 0.10
    assert "Human Analyst Resolution" in data["investigation"]["report"]
    assert "Verified customer identity" in data["investigation"]["report"]

    # Check audit log
    audit_logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == "inv_hr_app").all()
    actions = [al.action for al in audit_logs]
    assert any("HUMAN_REVIEW: APPROVE" in a for a in actions)

def test_human_review_reject_workflow(client, db_session):
    inv = models.Investigation(
        investigation_id="inv_hr_rej",
        txn_id="txn_hr_2",
        status="ESCALATED",
        confidence=0.55,
        risk_score=0.82,
        report="## HUMAN REVIEW ESCALATION REPORT\nHigh risk flagged."
    )
    db_session.add(inv)
    db_session.commit()

    response = client.post(
        f"/api/v1/investigations/inv_hr_rej/review",
        json={"action": "REJECT", "notes": "Confirmed fraudulent activity from compromised IP range."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_status"] == "CLOSED_REJECT"
    assert data["investigation"]["risk_score"] == 0.95
    assert "Confirmed fraudulent activity" in data["investigation"]["report"]

    # Check audit log
    audit_logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == "inv_hr_rej").all()
    actions = [al.action for al in audit_logs]
    assert any("HUMAN_REVIEW: REJECT" in a for a in actions)
