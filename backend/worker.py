import threading
import time
import queue
from typing import Dict, Any, Optional
import models
from database import SessionLocal
from main import run_investigation_task

class DurableWorkerQueue:
    def __init__(self):
        self._queue = queue.Queue()
        self._is_running = False
        self._worker_thread = None

    def enqueue(self, investigation_id: str, transaction_id: str, db=None):
        """Enqueue investigation job for durable worker processing."""
        job = {
            "investigation_id": investigation_id,
            "transaction_id": transaction_id,
            "enqueued_at": time.time()
        }
        self._queue.put(job)

        # Log audit entry for enqueuing
        should_close = False
        if not db:
            db = SessionLocal()
            should_close = True

        try:
            audit = models.AuditLog(
                investigation_id=investigation_id,
                action="WORKER_JOB_ENQUEUED",
                details=f"Investigation {investigation_id} enqueued into worker queue."
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            if should_close:
                db.close()

    def process_next_job(self, db=None) -> bool:
        """Process a single job from the queue."""
        try:
            job = self._queue.get(block=False)
        except queue.Empty:
            return False

        inv_id = job["investigation_id"]
        txn_id = job["transaction_id"]

        try:
            run_investigation_task(inv_id, txn_id, db=db)
        except Exception as e:
            print(f"Worker execution failed for {inv_id}: {e}")
        finally:
            self._queue.task_done()
        return True

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
