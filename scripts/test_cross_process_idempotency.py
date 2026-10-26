import os
import sys
import time
import multiprocessing
from typing import Dict, Any

# Ensure backend directory on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

PG_URL = os.getenv("DATABASE_URL", "postgresql://ffire_user:ffire_password@localhost:5433/ffire_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
os.environ["DATABASE_URL"] = PG_URL
os.environ["REDIS_URL"] = REDIS_URL

from fastapi.testclient import TestClient
import models
from database import SessionLocal, init_db
from main import app

def worker_process_submit(idemp_key: str, user_id: str, txn_id: str) -> Dict[str, Any]:
    """Independent process submitting an investigation request with a shared idempotency key."""
    client = TestClient(app)
    
    # Authenticate to get a valid token
    reg_res = client.post("/api/v1/auth/register", json={
        "name": f"Proc User {user_id}",
        "email": f"proc_{user_id}_{int(time.time()*1000)}@compliance-test.com",
        "password": "Password123!",
        "role": "investigator"
    })
    token = reg_res.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idemp_key
    }
    payload = {
        "transaction_id": txn_id,
        "user_id": user_id
    }
    
    t0 = time.perf_counter()
    resp = client.post("/api/v1/investigations", json=payload, headers=headers)
    dur = time.perf_counter() - t0
    
    return {
        "user_id": user_id,
        "status_code": resp.status_code,
        "investigation_id": resp.json().get("investigation_id"),
        "cache_hit": resp.headers.get("X-Cache-Hit"),
        "duration_sec": dur
    }

def run_cross_process_idempotency_test():
    print("=" * 80)
    print("CROSS-PROCESS DISTRIBUTED IDEMPOTENCY TEST (Separate Python Processes)")
    print(f"Database: {PG_URL}")
    print("=" * 80)

    init_db()

    # Shared test transaction and customer
    db = SessionLocal()
    txn_id = "TXN_PROC_IDEMP_001"
    try:
        cust = db.query(models.Customer).filter(models.Customer.customer_id == "c_proc_idemp").first()
        if not cust:
            cust = models.Customer(customer_id="c_proc_idemp", name="Idemp Corp", kyc_status="VERIFIED")
            acct = models.Account(account_id="a_proc_idemp", customer_id="c_proc_idemp")
            merch = models.Merchant(merchant_id="m_proc_idemp", name="Idemp Merch", risk_score=0.01)
            txn = models.Transaction(txn_id=txn_id, account_id="a_proc_idemp", merchant_id="m_proc_idemp", amount=999.0, currency="USD", status="PENDING")
            db.add_all([cust, acct, merch, txn])
            db.commit()
    finally:
        db.close()

    shared_idemp_key = f"proc_race_key_{int(time.time())}"
    num_processes = 6
    print(f"\n[Launching {num_processes} separate OS processes concurrently racing with Idempotency-Key: {shared_idemp_key}]...")

    with multiprocessing.Pool(processes=num_processes) as pool:
        async_results = [
            pool.apply_async(worker_process_submit, (shared_idemp_key, f"proc_user_{i}", txn_id))
            for i in range(num_processes)
        ]
        results = [res.get(timeout=30) for res in async_results]

    print("\n[Results from concurrent processes]:")
    for r in results:
        print(f"  Process {r['user_id']}: status={r['status_code']}, inv_id={r['investigation_id']}, X-Cache-Hit={r['cache_hit']}, latency={r['duration_sec']*1000:.1f}ms")

    # Assertions
    status_codes = [r["status_code"] for r in results]
    inv_ids = [r["investigation_id"] for r in results]

    assert all(code == 202 for code in status_codes), f"Not all processes returned 202! Codes: {status_codes}"
    assert len(set(inv_ids)) == 1, f"Multiple distinct investigation IDs returned! IDs: {set(inv_ids)}"

    # Direct database verification in PostgreSQL
    db = SessionLocal()
    try:
        matching_records = db.query(models.Investigation).filter(
            models.Investigation.idempotency_key == f"idemp_{shared_idemp_key}"
        ).all()
        print(f"\n[PostgreSQL Database Audit]:")
        print(f"  Exact matching records in 'investigation' table: {len(matching_records)}")
        assert len(matching_records) == 1, f"Database has {len(matching_records)} records instead of exactly 1!"
        assert matching_records[0].investigation_id == inv_ids[0]
        print(f"  Committed Investigation ID: {matching_records[0].investigation_id}")
    finally:
        db.close()

    print("\n[SUCCESS] Distributed cross-process idempotency guaranteed by PostgreSQL unique constraint!")
    return True

if __name__ == "__main__":
    multiprocessing.freeze_support()
    success = run_cross_process_idempotency_test()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if success else 1)


