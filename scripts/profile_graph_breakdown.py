import os
import sys
import time
import json
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

PG_URL = os.getenv("DATABASE_URL", "postgresql://ffire_user:ffire_password@localhost:5433/ffire_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
os.environ["DATABASE_URL"] = PG_URL
os.environ["REDIS_URL"] = REDIS_URL

import models
from database import SessionLocal, init_db
from checkpointing import DurablePostgresSaver
from graph import build_graph

def profile_investigation():
    init_db()
    saver = DurablePostgresSaver(PG_URL)
    
    # Instrument checkpointing put and get_tuple
    orig_put = saver.put
    orig_put_writes = saver.put_writes
    orig_get_tuple = saver.get_tuple

    ckpt_timings = {"put": [], "put_writes": [], "get_tuple": []}

    def timed_put(*args, **kwargs):
        t0 = time.perf_counter()
        res = orig_put(*args, **kwargs)
        ckpt_timings["put"].append(time.perf_counter() - t0)
        return res

    def timed_put_writes(*args, **kwargs):
        t0 = time.perf_counter()
        res = orig_put_writes(*args, **kwargs)
        ckpt_timings["put_writes"].append(time.perf_counter() - t0)
        return res

    def timed_get_tuple(*args, **kwargs):
        t0 = time.perf_counter()
        res = orig_get_tuple(*args, **kwargs)
        ckpt_timings["get_tuple"].append(time.perf_counter() - t0)
        return res

    saver.put = timed_put
    saver.put_writes = timed_put_writes
    saver.get_tuple = timed_get_tuple

    graph_app = build_graph(checkpointer=saver)

    inv_id = f"prof_{int(time.time())}"
    db = SessionLocal()
    try:
        inv_record = models.Investigation(
            investigation_id=inv_id,
            txn_id="TXN_BENCH_PG_001",
            status="QUEUED",
            tenant_id="default_tenant"
        )
        db.add(inv_record)
        db.commit()
    finally:
        db.close()

    state = {
        "investigation_id": inv_id,
        "transaction_id": "TXN_BENCH_PG_001",
        "customer_id": "c_bench",
        "account_id": "a_bench",
        "merchant_id": "m_bench",
        "evidence": [],
        "historical_cases": [],
        "execution_trace": [],
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": inv_id}}

    t_total_start = time.perf_counter()
    res = graph_app.invoke(state, config=config)
    t_total = time.perf_counter() - t_total_start

    # Query audit logs for node timings
    db = SessionLocal()
    audit_entries = []
    try:
        logs = db.query(models.AuditLog).filter(models.AuditLog.investigation_id == inv_id).order_by(models.AuditLog.timestamp.asc()).all()
        for log in logs:
            audit_entries.append((log.action, log.details))
    finally:
        db.close()

    saver.close()

    print(f"Total investigation execution time: {t_total*1000:.2f} ms")
    print(f"\n--- Checkpoint writes & reads ---")
    print(f"put calls: {len(ckpt_timings['put'])}, total time: {sum(ckpt_timings['put'])*1000:.2f} ms, mean: {(statistics.mean(ckpt_timings['put'])*1000 if ckpt_timings['put'] else 0):.2f} ms")
    print(f"put_writes calls: {len(ckpt_timings['put_writes'])}, total time: {sum(ckpt_timings['put_writes'])*1000:.2f} ms")
    print(f"get_tuple calls: {len(ckpt_timings['get_tuple'])}, total time: {sum(ckpt_timings['get_tuple'])*1000:.2f} ms")

    print(f"\n--- Audit log node execution details ---")
    for action, details in audit_entries:
        print(f"  {action}: {details}")

if __name__ == "__main__":
    profile_investigation()
