import pytest
import models

def test_audit_logs_creation_and_ordering(db_session):
    inv_id = "inv_audit_test"
    inv = models.Investigation(investigation_id=inv_id, txn_id="txn_aud_1", status="RUNNING")
    db_session.add(inv)
    db_session.commit()

    log1 = models.AuditLog(investigation_id=inv_id, action="NODE_EXECUTION: planner", details="Executed planner")
    log2 = models.AuditLog(investigation_id=inv_id, action="DECISION: retry", details="Validation failed attempt 1")
    log3 = models.AuditLog(investigation_id=inv_id, action="HUMAN_REVIEW: APPROVE", details="Approved by analyst")

    db_session.add_all([log1, log2, log3])
    db_session.commit()

    fetched = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == inv_id).first()
    assert len(fetched.audit_logs) == 3
    actions = [log.action for log in fetched.audit_logs]
    assert actions == ["NODE_EXECUTION: planner", "DECISION: retry", "HUMAN_REVIEW: APPROVE"]
