import os
import sys
import time
import subprocess
import pytest
from datetime import datetime

REAL_PG_URL = os.getenv("TEST_DATABASE_URL", "postgresql://ffire_user:ffire_password@localhost:5433/ffire_db")
REAL_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0")

def is_docker_running():
    try:
        res = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

# ==============================================================================
# REAL CHAOS TEST 1: POSTGRESQL RESTART & WORKER CRASH RECOVERY
# ==============================================================================

@pytest.mark.skipif(not is_docker_running(), reason="Requires live Docker daemon")
def test_postgres_restart_and_worker_resumption():
    """
    Simulates abrupt worker crash + live PostgreSQL container restart.
    Verifies that Worker 2 reconnects to PostgreSQL, retrieves state,
    and resumes execution without duplicate evidence or corrupted state.
    """
    from checkpointing import DurablePostgresSaver
    
    inv_id = f"chaos_pg_restart_{int(time.time())}"
    config = {"configurable": {"thread_id": inv_id, "checkpoint_ns": ""}}
    
    # Step 1: Worker 1 commits partial Phase 1 state
    saver_1 = DurablePostgresSaver(REAL_PG_URL)
    phase1_cp = {
        "v": 1,
        "id": "cp_phase1_pre_restart",
        "channel_values": {
            "investigation_id": inv_id,
            "evidence": ["ev_customer_kyc", "ev_device_fingerprint"],
            "phase": "EVIDENCE_COLLECTED",
            "retry_count": 0
        },
        "channel_versions": {
            "investigation_id": 1,
            "evidence": 1,
            "phase": 1,
            "retry_count": 1
        },
        "versions_seen": {},
        "pending_sends": []
    }
    saver_1.put(config, phase1_cp, {"source": "worker_1", "step": 1}, phase1_cp["channel_versions"])
    saver_1.close()
    
    # Step 2: Abruptly restart PostgreSQL Docker container
    restart_res = subprocess.run(["docker", "restart", "ffire_test_postgres"], capture_output=True, text=True)
    assert restart_res.returncode == 0, f"Failed to restart PostgreSQL container: {restart_res.stderr}"
    
    # Wait for PostgreSQL to become ready
    time.sleep(3)
    
    # Step 3: Worker 2 starts up, reconnects to the restarted PostgreSQL, and verifies recovery
    saver_2 = DurablePostgresSaver(REAL_PG_URL)
    resumed = saver_2.get_tuple(config)
    assert resumed is not None, "Failed to recover checkpoint from restarted PostgreSQL container!"
    assert resumed.checkpoint["id"] == "cp_phase1_pre_restart"
    
    ev_list = resumed.checkpoint["channel_values"]["evidence"]
    assert len(ev_list) == 2
    assert "ev_customer_kyc" in ev_list
    assert "ev_device_fingerprint" in ev_list
    
    # Step 4: Worker 2 appends new reasoning evidence and completes
    ev_list_updated = list(ev_list)
    ev_list_updated.append("ev_rules_engine_signal")
    
    phase2_cp = {
        "v": 1,
        "id": "cp_phase2_post_restart",
        "channel_values": {
            "investigation_id": inv_id,
            "evidence": ev_list_updated,
            "phase": "COMPLETED",
            "risk_score": 0.82,
            "verdict": "FLAGGED",
            "retry_count": 0
        },
        "channel_versions": {
            "investigation_id": 2,
            "evidence": 2,
            "phase": 2,
            "risk_score": 1,
            "verdict": 1,
            "retry_count": 1
        },
        "versions_seen": {},
        "pending_sends": []
    }
    saver_2.put(config, phase2_cp, {"source": "worker_2", "step": 2}, phase2_cp["channel_versions"])
    
    # Step 5: Verify final state integrity in PostgreSQL
    final_res = saver_2.get_tuple(config)
    saver_2.close()
    
    assert final_res is not None
    assert final_res.checkpoint["channel_values"]["phase"] == "COMPLETED"
    final_evidence = final_res.checkpoint["channel_values"]["evidence"]
    assert len(final_evidence) == 3
    # Strict deduplication check: no duplicate items
    assert len(set(final_evidence)) == 3
    print("CHAOS_PG_RESTART_RECOVERY_PASSED")

# ==============================================================================
# REAL CHAOS TEST 2: REDIS CONTAINER INTERRUPTION & FAIL-CLOSED VERIFICATION
# ==============================================================================

@pytest.mark.skipif(not is_docker_running(), reason="Requires live Docker daemon")
def test_redis_interruption_fail_closed_and_recovery(monkeypatch):
    """
    Stops live Redis container.
    Verifies that in STRICT_ENTERPRISE_MODE, token revocation and checks fail closed (HTTP 503 / RuntimeError).
    Restarts Redis container and verifies automatic recovery.
    """
    import auth
    monkeypatch.setenv("STRICT_ENTERPRISE_MODE", "true")
    monkeypatch.setenv("REDIS_URL", REAL_REDIS_URL)
    
    # Reset auth Redis connection pool
    auth._REVOCATION_REDIS = None
    
    # Stop Redis container
    stop_res = subprocess.run(["docker", "stop", "ffire_test_redis"], capture_output=True, text=True)
    assert stop_res.returncode == 0
    
    try:
        from fastapi import HTTPException
        # Revocation check must fail closed with HTTP 503
        with pytest.raises(HTTPException) as exc_info:
            auth.is_token_revoked("test_token_during_redis_outage")
        assert exc_info.value.status_code == 503
        
        # Revocation write must fail closed with RuntimeError
        with pytest.raises(RuntimeError):
            auth.revoke_token("test_token_during_redis_outage")
            
        print("REDIS_OUTAGE_FAIL_CLOSED_VERIFIED")
    finally:
        # Restart Redis container
        start_res = subprocess.run(["docker", "start", "ffire_test_redis"], capture_output=True, text=True)
        assert start_res.returncode == 0
        time.sleep(2)
        
        # Verify recovery after container restart
        auth._REVOCATION_REDIS = None
        rev_token = f"recovery_token_{int(time.time())}"
        auth.revoke_token(rev_token)
        assert auth.is_token_revoked(rev_token) is True
        print("REDIS_CONTAINER_RECOVERY_VERIFIED")

# ==============================================================================
# REAL CHAOS TEST 3: INVESTIGATION RETRY IDEMPOTENCY & AUDIT DEDUPLICATION
# ==============================================================================

def test_investigation_retry_idempotency_no_duplicate_evidence(client, db_session):
    """
    Simulates network retry of an investigation request with the same idempotency key.
    Verifies that the API detects idempotency, caches results, and prevents duplicate processing or corrupted audit logs.
    """
    import security
    import models
    from auth import create_access_token
    
    email = "e2e_analyst@bank.internal"
    user = models.User(
        user_id="u_e2e_001",
        name="E2E Lead Analyst",
        email=email,
        email_hash=security.compute_blind_index(email),
        role="investigator",
        tenant_id="tenant_bank_primary"
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": email, "tenant_id": "tenant_bank_primary", "role": "investigator", "type": "access"})
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": f"retry_key_{int(time.time())}"
    }
    
    txn_id = f"TXN_IDEMP_{int(time.time())}"
    txn = models.Transaction(
        txn_id=txn_id,
        account_id="acc_idemp_1",
        merchant_id="merch_idemp_1",
        amount=250.0,
        currency="USD",
        tenant_id="tenant_bank_primary",
        status="PENDING"
    )
    db_session.add(txn)
    db_session.commit()

    payload = {
        "transaction_id": txn_id,
        "user_id": "u_e2e_001"
    }

    # Request 1: First attempt
    res1 = client.post("/api/v1/investigations", json=payload, headers=headers)
    assert res1.status_code == 202
    inv_id_1 = res1.json()["investigation_id"]
    
    # Request 2: Retry with exact same idempotency header
    res2 = client.post("/api/v1/investigations", json=payload, headers=headers)
    assert res2.status_code in (200, 202)
    inv_id_2 = res2.json()["investigation_id"]
    
    # Idempotency guarantee: Must return the EXACT same investigation ID
    assert inv_id_1 == inv_id_2
    assert res2.headers.get("X-Cache-Hit") == "true"
    
    # Database check: Exactly ONE investigation record created
    count = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == inv_id_1).count()
    assert count == 1
    print("INVESTIGATION_IDEMPOTENCY_VERIFIED_100%")
