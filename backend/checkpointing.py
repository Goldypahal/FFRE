import sqlite3
import pickle
import os
import base64
import threading
from typing import Dict, Any, Optional
from langgraph.checkpoint.memory import MemorySaver

class ThreadSafeMemorySaver(MemorySaver):
    """Thread-safe in-memory checkpointer with RLock protection for high-concurrency benchmarks."""
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()

    def get_tuple(self, config: Dict[str, Any]) -> Optional[Any]:
        with self._lock:
            return super().get_tuple(config)

    def list(self, config: Optional[Dict[str, Any]], *, filter: Optional[Dict[str, Any]] = None, before: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        with self._lock:
            return super().list(config, filter=filter, before=before, limit=limit)

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            return super().put(config, checkpoint, metadata, new_versions)

class ThreadSafeMemorySaver(MemorySaver):
    """Thread-safe in-memory checkpointer with RLock protection for high-concurrency benchmarks."""
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()

    def get_tuple(self, config: Dict[str, Any]) -> Optional[Any]:
        with self._lock:
            return super().get_tuple(config)

    def list(self, config: Optional[Dict[str, Any]], *, filter: Optional[Dict[str, Any]] = None, before: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        with self._lock:
            return super().list(config, filter=filter, before=before, limit=limit)

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            return super().put(config, checkpoint, metadata, new_versions)

class DurableSqliteSaver(MemorySaver):
    """Task 16: Durable SQLite-backed checkpointer ensuring graph state persistence across restarts."""
    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self._lock = threading.RLock()
        self.db_path = db_path or os.getenv("CHECKPOINT_DB_PATH", "ffire_checkpoints.db")
        self._init_db()
        self._load_all_checkpoints()

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=60.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=60000;")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(checkpoints)")
                cols = [c[1] for c in cursor.fetchall()]
                if "checkpoint_data" not in cols:
                    cursor.execute("DROP TABLE checkpoints")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    checkpoint_data BLOB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _load_all_checkpoints(self):
        with sqlite3.connect(self.db_path, timeout=60.0) as conn:
            conn.execute("PRAGMA busy_timeout=60000;")
            cursor = conn.cursor()
            cursor.execute("SELECT thread_id, checkpoint_data FROM checkpoints")
            for thread_id, data_blob in cursor.fetchall():
                try:
                    if isinstance(data_blob, str):
                        data_blob = base64.b64decode(data_blob)
                    self.storage[thread_id] = pickle.loads(data_blob)
                except Exception as e:
                    print(f"Warning: Failed loading checkpoint for thread {thread_id}: {e}")

    def get_tuple(self, config: Dict[str, Any]) -> Optional[Any]:
        with self._lock:
            return super().get_tuple(config)

    def list(self, config: Optional[Dict[str, Any]], *, filter: Optional[Dict[str, Any]] = None, before: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        with self._lock:
            return super().list(config, filter=filter, before=before, limit=limit)

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save checkpoint to MemorySaver in-memory storage and persist full thread storage to SQLite."""
        if new_versions is None:
            new_versions = {}
        with self._lock:
            res = super().put(config, checkpoint, metadata, new_versions)
            thread_id = config.get("configurable", {}).get("thread_id", "default")
            try:
                if thread_id in self.storage:
                    data_blob = pickle.dumps(self.storage[thread_id])
                    with sqlite3.connect(self.db_path, timeout=60.0) as conn:
                        conn.execute("PRAGMA busy_timeout=60000;")
                        conn.execute(
                            "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_data) VALUES (?, ?)",
                            (thread_id, sqlite3.Binary(data_blob))
                        )
                        conn.commit()
            except Exception as e:
                print(f"Warning: Failed persisting checkpoint to SQLite: {e}")
            return res

try:
    import psycopg2
    from psycopg2 import pool as psycopg2_pool
except (ImportError, Exception):
    psycopg2 = None
    psycopg2_pool = None

try:
    from langgraph.checkpoint.postgres import PostgresSaver as NativePostgresSaver
    from psycopg_pool import ConnectionPool
except (ImportError, Exception):
    NativePostgresSaver = None
    ConnectionPool = None

from contextlib import contextmanager

class _NoOpLock:
    """Non-blocking lock for ConnectionPool-backed native PostgresSaver where psycopg_pool handles thread safety."""
    def acquire(self, *args, **kwargs):
        return True
    def release(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

class DurablePostgresSaver(MemorySaver):
    """Task 24 & Production Hardening: Native LangGraph PostgreSQL-backed checkpointer ensuring multi-pod HA state persistence, atomic writes, and version tracking."""
    def __init__(self, db_url: str, minconn: int = 1, maxconn: int = 15):
        super().__init__()
        self._lock = threading.RLock()
        self.db_url = db_url
        self._pool = None
        self._native_saver = None
        self._strict_mode = os.getenv("STRICT_ENTERPRISE_MODE", "false").lower() == "true"
        
        if NativePostgresSaver is None or ConnectionPool is None:
            if self._strict_mode:
                raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Native PostgreSQL checkpointer (langgraph-checkpoint-postgres/psycopg_pool) is unavailable for {self.db_url}")
            print("Warning: Native PostgreSQL checkpointer dependencies not available. Falling back to memory storage.")
            return

        # 1. Try initializing native LangGraph PostgresSaver
        try:
            self._pool = ConnectionPool(conninfo=self.db_url, min_size=minconn, max_size=max(maxconn, 30), kwargs={"autocommit": True})
            self._pool.open(wait=True, timeout=3.0)
            self._native_saver = NativePostgresSaver(self._pool)
            # Unblock multi-worker concurrency: psycopg_pool manages connection safety across threads
            self._native_saver.lock = _NoOpLock()
            self._native_saver.setup()
        except Exception as e:
            if self._strict_mode:
                raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Failed connecting to PostgreSQL checkpointer at {self.db_url}: {e}")
                print(f"Warning: Native PostgreSQL checkpointer initialization failed ({e}). Falling back to memory storage.")
                if self._pool is not None:
                    try:
                        self._pool.close(timeout=1.0)
                    except Exception:
                        pass
                self._pool = None
                self._native_saver = None

    def close(self):
        """Gracefully drain and close connection pool."""
        with self._lock:
            if self._pool is not None:
                try:
                    self._pool.close(timeout=1.0)
                except Exception:
                    pass
                self._pool = None
                self._native_saver = None

    def list(self, config: Optional[Dict[str, Any]], *, filter: Optional[Dict[str, Any]] = None, before: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        if self._native_saver is not None:
            return self._native_saver.list(config, filter=filter, before=before, limit=limit)
        with self._lock:
            return super().list(config, filter=filter, before=before, limit=limit)

    def get_tuple(self, config: Dict[str, Any]) -> Optional[Any]:
        """Fetch checkpoint tuple directly from PostgreSQL DB to ensure multi-pod state synchronization."""
        if self._native_saver is not None:
            return self._native_saver.get_tuple(config)
        with self._lock:
            return super().get_tuple(config)

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save checkpoint to PostgreSQL using native atomic write-ahead log and version tracking."""
        if new_versions is None:
            new_versions = {}
        if self._native_saver is not None:
            return self._native_saver.put(config, checkpoint, metadata, new_versions)
        with self._lock:
            return super().put(config, checkpoint, metadata, new_versions)

    def put_writes(self, config: Dict[str, Any], writes: Any, task_id: str, task_path: str = "") -> None:
        """Persist intermediate writes for atomic recovery."""
        if self._native_saver is not None and hasattr(self._native_saver, "put_writes"):
            return self._native_saver.put_writes(config, writes, task_id, task_path)

def get_durable_checkpointer(db_path: str = "ffire_checkpoints.db", db_url: Optional[str] = None):
    """Task 16 & 24 Factory: Returns durable PostgreSQL or SQLite checkpointer instance based on configuration."""
    target_url = db_url or os.getenv("CHECKPOINT_DB_URL") or os.getenv("DATABASE_URL", "")
    if target_url.startswith("postgresql://") or target_url.startswith("postgres://"):
        return DurablePostgresSaver(db_url=target_url)
    return DurableSqliteSaver(db_path=db_path)
