"""
Parallel PostgreSQL load benchmark for the FFRE backend data layer.

Drives concurrent workers through the application's own SQLAlchemy engine
(``backend/database.py``: same pool size / overflow settings as the app) with a
mixed read/write workload against the ``transaction`` table:

  * write  - insert a transaction row
  * read   - fetch the 20 most recent transactions for a tenant (indexed query)
  * update - change the status of a row this worker inserted

Reports throughput, latency percentiles per operation and error counts, writes a
JSON report, and exits non-zero if the error rate exceeds ``--max-error-rate``.

Usage:
    DATABASE_URL=postgresql://user:pass@localhost:5433/db \
        python benchmarks/pg_load_benchmark.py --workers 16 --duration 30
"""

import argparse
import json
import os
import random
import statistics
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, ROOT)

TENANTS = [f"bench_tenant_{i}" for i in range(4)]


def _percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * pct / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def _worker(worker_id, deadline, mix, run_tag, results, lock):
    import database
    import models
    import timeutil

    rng = random.Random(worker_id)
    own_ids = []
    local = {"write": [], "read": [], "update": []}
    errors = {"write": 0, "read": 0, "update": 0}
    error_samples = []

    while time.perf_counter() < deadline:
        op = rng.choices(["write", "read", "update"], weights=mix)[0]
        if op == "update" and not own_ids:
            op = "write"
        session = database.SessionLocal()
        t0 = time.perf_counter()
        try:
            if op == "write":
                txn_id = f"BENCH_{run_tag}_{worker_id}_{uuid.uuid4().hex[:12]}"
                session.add(models.Transaction(
                    txn_id=txn_id,
                    tenant_id=rng.choice(TENANTS),
                    amount=Decimal(f"{rng.uniform(1, 50000):.2f}"),
                    currency="USD",
                    status="PENDING",
                    timestamp=timeutil.utcnow(),
                    channel=rng.choice(["ACH", "WIRE", "CARD"]),
                    counterparty=f"CP_{rng.randint(1, 500)}",
                ))
                session.commit()
                own_ids.append(txn_id)
            elif op == "read":
                rows = (
                    session.query(models.Transaction)
                    .filter(models.Transaction.tenant_id == rng.choice(TENANTS))
                    .order_by(models.Transaction.timestamp.desc())
                    .limit(20)
                    .all()
                )
                _ = len(rows)
            else:
                txn = session.get(models.Transaction, rng.choice(own_ids))
                if txn is not None:
                    txn.status = rng.choice(["REVIEWED", "FLAGGED", "CLEARED"])
                    session.commit()
            local[op].append((time.perf_counter() - t0) * 1000.0)
        except Exception as exc:  # recorded, never swallowed silently
            session.rollback()
            errors[op] += 1
            if len(error_samples) < 3:
                error_samples.append(f"{op}: {type(exc).__name__}: {exc}"[:300])
        finally:
            session.close()

    with lock:
        for op in local:
            results["latencies"][op].extend(local[op])
            results["errors"][op] += errors[op]
        results["error_samples"].extend(error_samples)
        results["inserted_ids"].extend(own_ids)


def run_benchmark(workers, duration, warmup, mix, cleanup=True):
    import database
    import models

    url = database.SQLALCHEMY_DATABASE_URL
    if not url.startswith("postgresql"):
        raise SystemExit(f"Refusing to run: DATABASE_URL must point to PostgreSQL (got {url.split(':', 1)[0]}).")

    run_tag = uuid.uuid4().hex[:8]
    results = {"latencies": {"write": [], "read": [], "update": []},
               "errors": {"write": 0, "read": 0, "update": 0},
               "error_samples": [], "inserted_ids": []}
    lock = threading.Lock()

    # Warm-up: establish pool connections and caches; results discarded.
    if warmup > 0:
        scratch = {"latencies": {"write": [], "read": [], "update": []},
                   "errors": {"write": 0, "read": 0, "update": 0}, "error_samples": [], "inserted_ids": []}
        deadline = time.perf_counter() + warmup
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for w in range(workers):
                pool.submit(_worker, 10_000 + w, deadline, mix, run_tag + "w", scratch, lock)
        results["inserted_ids"].extend(scratch["inserted_ids"])

    t_start = time.perf_counter()
    deadline = t_start + duration
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_worker, w, deadline, mix, run_tag, results, lock) for w in range(workers)]
        for f in futures:
            f.result()
    elapsed = time.perf_counter() - t_start

    per_op = {}
    total_ok = 0
    for op, lat in results["latencies"].items():
        s = sorted(lat)
        total_ok += len(s)
        per_op[op] = {
            "count": len(s),
            "errors": results["errors"][op],
            "p50_ms": round(_percentile(s, 50), 3) if s else None,
            "p95_ms": round(_percentile(s, 95), 3) if s else None,
            "p99_ms": round(_percentile(s, 99), 3) if s else None,
            "mean_ms": round(statistics.fmean(s), 3) if s else None,
            "max_ms": round(s[-1], 3) if s else None,
        }
    total_err = sum(results["errors"].values())
    attempted = total_ok + total_err

    if cleanup and results["inserted_ids"]:
        session = database.SessionLocal()
        try:
            ids = results["inserted_ids"]
            for i in range(0, len(ids), 1000):
                session.query(models.Transaction).filter(
                    models.Transaction.txn_id.in_(ids[i:i + 1000])
                ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

    engine = database.engine
    return {
        "benchmark": "pg_load_benchmark",
        "database": f"{engine.dialect.name} (server {'.'.join(map(str, engine.dialect.server_version_info or ()))})",
        "pool_size": getattr(engine.pool, "size", lambda: None)(),
        "workers": workers,
        "duration_sec": round(elapsed, 2),
        "warmup_sec": warmup,
        "mix_write_read_update": mix,
        "operations_ok": total_ok,
        "operations_failed": total_err,
        "error_rate": round(total_err / attempted, 6) if attempted else None,
        "throughput_ops_per_sec": round(total_ok / elapsed, 1) if elapsed else None,
        "per_operation": per_op,
        "error_samples": results["error_samples"][:5],
        "rows_cleaned_up": len(results["inserted_ids"]) if cleanup else 0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--duration", type=float, default=30.0, help="measured seconds")
    ap.add_argument("--warmup", type=float, default=3.0, help="unmeasured warm-up seconds")
    ap.add_argument("--mix", default="40,50,10", help="write,read,update weights")
    ap.add_argument("--max-error-rate", type=float, default=0.0)
    ap.add_argument("--output", default=os.path.join(ROOT, "data", "benchmarks", "pg_load_benchmark.json"))
    ap.add_argument("--no-cleanup", action="store_true")
    args = ap.parse_args()

    mix = [float(x) for x in args.mix.split(",")]
    if len(mix) != 3:
        ap.error("--mix needs three comma-separated weights")

    report = run_benchmark(args.workers, args.duration, args.warmup, mix, cleanup=not args.no_cleanup)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({k: v for k, v in report.items() if k != "error_samples"}, indent=2))
    if report["error_samples"]:
        print("Sample errors:", *report["error_samples"], sep="\n  ")
    if report["error_rate"] is None or report["error_rate"] > args.max_error_rate:
        print(f"FAIL: error rate {report['error_rate']} exceeds --max-error-rate {args.max_error_rate}")
        return 1
    print(f"PASS: {report['operations_ok']} operations, error rate {report['error_rate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
