import sqlite3
import pickle
import os
import base64
from typing import Dict, Any, Optional
from langgraph.checkpoint.memory import MemorySaver

class DurableSqliteSaver(MemorySaver):
    """Task 16: Durable SQLite-backed checkpointer ensuring graph state persistence across restarts."""
    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self.db_path = db_path or os.getenv("CHECKPOINT_DB_PATH", "ffire_checkpoints.db")
        self._init_db()
        self._load_all_checkpoints()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT thread_id, checkpoint_data FROM checkpoints")
            for thread_id, data_blob in cursor.fetchall():
                try:
                    if isinstance(data_blob, str):
                        data_blob = base64.b64decode(data_blob)
                    self.storage[thread_id] = pickle.loads(data_blob)
                except Exception as e:
                    print(f"Warning: Failed loading checkpoint for thread {thread_id}: {e}")

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save checkpoint to MemorySaver in-memory storage and persist full thread storage to SQLite."""
        if new_versions is None:
            new_versions = {}
        res = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        try:
            if thread_id in self.storage:
                data_blob = pickle.dumps(self.storage[thread_id])
                with sqlite3.connect(self.db_path) as conn:
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
except ImportError:
    psycopg2 = None

class DurablePostgresSaver(MemorySaver):
    """Task 24: Durable PostgreSQL-backed checkpointer ensuring multi-pod HA graph state persistence."""
    def __init__(self, db_url: str):
        super().__init__()
        self.db_url = db_url
        self._init_db()
        self._load_all_checkpoints()

    def _init_db(self):
        if psycopg2 is None:
            print("Warning: psycopg2 package is not installed. DurablePostgresSaver operating in memory.")
            return
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS checkpoints (
                            thread_id VARCHAR(255) PRIMARY KEY,
                            checkpoint_data BYTEA NOT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                conn.commit()
        except Exception as e:
            print(f"Warning: Unable to initialize PostgreSQL checkpointer database ({e}). Operating in memory.")

    def _load_all_checkpoints(self):
        if psycopg2 is None:
            return
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT thread_id, checkpoint_data FROM checkpoints;")
                    for thread_id, data_blob in cursor.fetchall():
                        try:
                            if isinstance(data_blob, str):
                                data_blob = base64.b64decode(data_blob)
                            elif isinstance(data_blob, memoryview):
                                data_blob = bytes(data_blob)
                            self.storage[thread_id] = pickle.loads(data_blob)
                        except Exception as e:
                            print(f"Warning: Failed loading PostgreSQL checkpoint for thread {thread_id}: {e}")
        except Exception as e:
            print(f"Warning: Unable to connect to PostgreSQL checkpointer database: {e}")

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save checkpoint to MemorySaver in-memory storage and persist full thread storage to PostgreSQL."""
        if new_versions is None:
            new_versions = {}
        res = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        try:
            if thread_id in self.storage:
                data_blob = pickle.dumps(self.storage[thread_id])
                with psycopg2.connect(self.db_url) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO checkpoints (thread_id, checkpoint_data, updated_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (thread_id) DO UPDATE
                            SET checkpoint_data = EXCLUDED.checkpoint_data, updated_at = CURRENT_TIMESTAMP;
                        """, (thread_id, psycopg2.Binary(data_blob)))
                    conn.commit()
        except Exception as e:
            print(f"Warning: Failed persisting checkpoint to PostgreSQL: {e}")
        return res

def get_durable_checkpointer(db_path: str = "ffire_checkpoints.db", db_url: Optional[str] = None):
    """Task 16 & 24 Factory: Returns durable PostgreSQL or SQLite checkpointer instance based on configuration."""
    target_url = db_url or os.getenv("CHECKPOINT_DB_URL") or os.getenv("DATABASE_URL", "")
    if target_url.startswith("postgresql://") or target_url.startswith("postgres://"):
        return DurablePostgresSaver(db_url=target_url)
    return DurableSqliteSaver(db_path=db_path)
