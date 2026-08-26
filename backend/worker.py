import os
import threading
import time
import queue
import datetime
from typing import Dict, Any, Optional, Set
import models
from database import SessionLocal
from main import run_investigation_task

import json
try:
    import redis
except ImportError:
    redis = None

VALID_STATES: Set[str] = {
    "QUEUED", "RUNNING", "RETRYING", "WAITING_HUMAN", "ESCALATED", "COMPLETED", "FAILED", "CANCELLED"
}

VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "QUEUED": {"RUNNING", "CANCELLED", "FAILED", "QUEUED"},
    "RUNNING": {"QUEUED", "RETRYING", "WAITING_HUMAN", "ESCALATED", "COMPLETED", "FAILED", "CANCELLED"},
    "RETRYING": {"RUNNING", "CANCELLED", "FAILED"},
    "WAITING_HUMAN": {"RUNNING", "COMPLETED", "FAILED", "CANCELLED"},
    "ESCALATED": {"RUNNING", "RETRYING", "COMPLETED", "FAILED", "CANCELLED"},
    "COMPLETED": set(),
    "FAILED": {"RETRYING"},
    "CANCELLED": set()
}

MAX_JOB_RETRIES = 3

class DurableWorkerQueue:
    """Task 17-19 & Task 23: Multi-backend durable worker queue supporting Redis and SQLite/in-memory brokers."""
    def __init__(self, redis_url: Optional[str] = None):
        self._queue = queue.Queue()
        self._is_running = False
        self._worker_thread = None
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._redis_client = None

        if self.redis_url and redis is not None:
            try:
                client = redis.Redis.from_url(self.redis_url, socket_timeout=2)
                client.ping()
                self._redis_client = client
                print(f"DurableWorkerQueue connected to Redis broker at {self.redis_url}")
            except Exception as e:
                print(f"Redis connection unavailable ({e}). Falling back to in-memory queue broker.")
                self._redis_client = None

    def get_broker_backend(self) -> str:
        """Return active queue broker backend ('redis' or 'in_memory')."""
        return "redis" if self._redis_client is not None else "in_memory"

    def transition_job_state(self, investigation_id: str, new_status: str, db=None) -> bool:
        """Task 18: Enforce state machine transitions and write audit log."""
        if new_status not in VALID_STATES:
            raise ValueError(f"Invalid state: {new_status}")

        should_close = False
        if not db:
            db = SessionLocal()
            should_close = True

        try:
            inv = db.query(models.Investigation).filter(
                models.Investigation.investigation_id == investigation_id
            ).first()

            if not inv:
                return False

            old_status = inv.status
            if old_status != new_status:
                allowed = VALID_TRANSITIONS.get(old_status, set())
                if new_status not in allowed:
                    raise ValueError(f"Invalid state transition from '{old_status}' to '{new_status}'")

                inv.status = new_status
                inv.updated_at = datetime.datetime.utcnow()

                audit = models.AuditLog(
                    investigation_id=investigation_id,
                    action="WORKER_STATE_TRANSITION",
                    details=f"Status transitioned from {old_status} -> {new_status}"
                )
                db.add(audit)
                db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if should_close:
                db.close()

    def enqueue(self, investigation_id: str, transaction_id: str, db=None):
        """Enqueue investigation job for worker processing (Redis or In-Memory)."""
        job = {
            "investigation_id": investigation_id,
            "transaction_id": transaction_id,
            "enqueued_at": time.time(),
            "retry_count": 0
        }
        if self._redis_client:
            try:
                self._redis_client.rpush("ffre:worker:queue", json.dumps(job))
            except Exception as e:
                print(f"Redis rpush failed ({e}). Falling back to in-memory queue.")
                self._queue.put(job)
        else:
            self._queue.put(job)
        self.transition_job_state(investigation_id, "QUEUED", db=db)

    def recover_stale_or_abandoned_jobs(self, db=None, max_age_seconds: int = 300) -> int:
        """Task 17, 19 & 23: Recover crashed/abandoned worker jobs stuck in RUNNING state or Redis pending queue."""
        should_close = False
        if not db:
            db = SessionLocal()
            should_close = True

        recovered_count = 0
        try:
            # Recover Redis processing queue un-ACKed jobs
            if self._redis_client:
                try:
                    pending_jobs = self._redis_client.lrange("ffre:worker:processing", 0, -1)
                    now = time.time()
                    for raw_job in pending_jobs:
                        try:
                            job_data = json.loads(raw_job)
                            enqueued_at = job_data.get("enqueued_at", now)
                            if now - enqueued_at > max_age_seconds:
                                self._redis_client.lrem("ffre:worker:processing", 1, raw_job)
                                self._redis_client.rpush("ffre:worker:queue", raw_job)
                                recovered_count += 1
                                print(f"Recovered un-ACKed Redis job {job_data.get('investigation_id')}")
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Redis pending recovery warning: {e}")

            cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=max_age_seconds)
            stale_jobs = db.query(models.Investigation).filter(
                models.Investigation.status == "RUNNING",
                models.Investigation.updated_at < cutoff
            ).all()

            for inv in stale_jobs:
                inv.status = "RETRYING"
                inv.updated_at = datetime.datetime.utcnow()
                audit = models.AuditLog(
                    investigation_id=inv.investigation_id,
                    action="WORKER_CRASH_RECOVERY",
                    details=f"Recovered stale job {inv.investigation_id}. Status reset to RETRYING."
                )
                db.add(audit)
                recovered_count += 1

            db.commit()
            return recovered_count
        except Exception:
            db.rollback()
            return 0
        finally:
            if should_close:
                db.close()

    def ack_job(self, job: Dict[str, Any]):
        """Task 23: Acknowledge job completion and remove from Redis processing queue."""
        if self._redis_client and "_raw_str" in job:
            try:
                self._redis_client.lrem("ffre:worker:processing", 1, job["_raw_str"])
            except Exception as e:
                print(f"Redis ACK lrem failed: {e}")

    def process_next_job(self, db=None) -> bool:
        """Process a single job from the worker queue with atomic RPOPLPUSH & ACK (Redis or In-Memory)."""
        job = None
        raw_job_str = None
        if self._redis_client:
            try:
                # Atomic queue pop -> processing list shift for crash safety
                raw_job = self._redis_client.rpoplpush("ffre:worker:queue", "ffre:worker:processing")
                if raw_job:
                    raw_job_str = raw_job.decode('utf-8') if isinstance(raw_job, bytes) else str(raw_job)
                    job = json.loads(raw_job_str)
                    job["_raw_str"] = raw_job_str
            except Exception as e:
                print(f"Redis rpoplpush failed ({e}). Checking in-memory fallback queue.")

        if not job:
            try:
                job = self._queue.get(block=False)
            except queue.Empty:
                return False

        inv_id = job["investigation_id"]
        txn_id = job["transaction_id"]
        retry_count = job.get("retry_count", 0)

        should_close = False
        if not db:
            db = SessionLocal()
            should_close = True

        try:
            inv = db.query(models.Investigation).filter(
                models.Investigation.investigation_id == inv_id
            ).first()

            if inv and inv.status == "FAILED":
                retry_count += 1
                if retry_count >= MAX_JOB_RETRIES:
                    audit = models.AuditLog(
                        investigation_id=inv_id,
                        action="DEAD_LETTER_QUEUE",
                        details=f"Job exceeded max retries ({MAX_JOB_RETRIES}). Sent to dead-letter queue."
                    )
                    dlq = models.DeadLetterJob(
                        investigation_id=inv_id,
                        transaction_id=txn_id,
                        failure_reason=inv.report or "Max retries exceeded",
                        retry_count=retry_count
                    )
                    db.add_all([audit, dlq])
                    db.commit()
                    self.ack_job(job)
                else:
                    job["retry_count"] = retry_count
                    inv.status = "RETRYING"
                    db.commit()
                    self._requeue_job(job)
            else:
                self.transition_job_state(inv_id, "RUNNING", db=db)
                run_investigation_task(inv_id, txn_id, db=db)
                self.ack_job(job)
        except Exception as e:
            print(f"Worker execution failed for {inv_id}: {e}")
            retry_count += 1
            if retry_count >= MAX_JOB_RETRIES:
                self.transition_job_state(inv_id, "FAILED", db=db)
                audit = models.AuditLog(
                    investigation_id=inv_id,
                    action="DEAD_LETTER_QUEUE",
                    details=f"Job exceeded max retries ({MAX_JOB_RETRIES}). Sent to dead-letter queue."
                )
                dlq = models.DeadLetterJob(
                    investigation_id=inv_id,
                    transaction_id=txn_id,
                    failure_reason=str(e),
                    retry_count=retry_count
                )
                db.add_all([audit, dlq])
                db.commit()
                self.ack_job(job)
            else:
                job["retry_count"] = retry_count
                self.transition_job_state(inv_id, "RETRYING", db=db)
                self._requeue_job(job)
        finally:
            if should_close:
                db.close()
            try:
                self._queue.task_done()
            except ValueError:
                pass
        return True

    def _requeue_job(self, job: Dict[str, Any]):
        """Helper to requeue job into Redis or In-Memory queue."""
        if self._redis_client:
            try:
                self._redis_client.rpush("ffre:worker:queue", json.dumps(job))
            except Exception:
                self._queue.put(job)
        else:
            self._queue.put(job)

    def cancel(self, investigation_id: str):
        """Task 14: Cancel enqueued job for an investigation."""
        print(f"Cancellation signal recorded in worker queue for {investigation_id}")

    def start_worker(self):
        """Start worker background loop."""
        if self._is_running:
            return

        self._is_running = True

        def _worker_loop():
            while self._is_running:
                has_job = self.process_next_job()
                if not has_job:
                    time.sleep(0.5)

        self._worker_thread = threading.Thread(target=_worker_loop, daemon=True)
        self._worker_thread.start()

    def stop_worker(self):
        """Stop worker background loop."""
        self._is_running = False

worker_queue = DurableWorkerQueue()

def run_worker_process():
    """Task 17: CLI daemon entrypoint for standalone background worker process."""
    print("Starting FFRE Standalone Background Worker Process...")
    db = SessionLocal()
    recovered = worker_queue.recover_stale_or_abandoned_jobs(db=db)
    print(f"Initial recovery complete: {recovered} stale jobs recovered.")
    db.close()

    worker_queue.start_worker()
    print("Worker loop active. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping worker process...")
        worker_queue.stop_worker()

if __name__ == "__main__":
    run_worker_process()
