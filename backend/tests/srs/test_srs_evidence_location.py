import pytest
import models
from main import run_investigation_task

def test_all_five_evidence_sources_saved_to_database(client, db_session):
    response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "T-EVIDENCE-TEST",
            "user_id": "user_1"
        }
    )
    assert response.status_code == 202
    inv_id = response.json()["investigation_id"]

    # Explicitly run investigation task with db_session so evidence is saved directly in test session
    run_investigation_task(inv_id, "T-EVIDENCE-TEST", db=db_session)

    # Fetch recorded evidence
    evidence_records = db_session.query(models.Evidence).filter(models.Evidence.investigation_id == inv_id).all()
    sources = [ev.source for ev in evidence_records]

    assert "customer_evidence" in sources
    assert "transaction_evidence" in sources
    assert "merchant_evidence" in sources
    assert "device_evidence" in sources
    assert "location_evidence" in sources
    assert len(sources) >= 5
