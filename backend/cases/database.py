"""
Persistent Historical Case Database Store (Phase 3).

Stores rich multi-dimensional historical fraud cases in an indexed SQLite database
supporting high-speed metadata filtering and structured retrieval.
"""

import os
import json
import sqlite3
import threading
from typing import Dict, Any, List, Optional

from backend.cases.schema import HistoricalCase, HybridSearchQuery


class HistoricalCaseStore:
    """Thread-safe SQLite database for historical fraud investigations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(backend_dir, "data", "historical_cases.db")

        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS historical_cases (
                        case_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        customer_id TEXT,
                        customer_name TEXT,
                        account_type TEXT,
                        kyc_status TEXT,
                        customer_risk_tier TEXT,
                        merchant_name TEXT,
                        merchant_category TEXT,
                        device_os TEXT,
                        country TEXT,
                        is_vpn INTEGER,
                        is_new_device INTEGER,
                        velocity_1h_count INTEGER,
                        velocity_24h_count INTEGER,
                        cycle_score REAL,
                        scatter_gather_score REAL,
                        disposition TEXT NOT NULL,
                        typology TEXT NOT NULL,
                        ground_truth_score REAL NOT NULL,
                        narrative TEXT NOT NULL,
                        case_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (tenant_id, case_id)
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_tenant_disp ON historical_cases(tenant_id, disposition)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_tenant_amt ON historical_cases(tenant_id, amount)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_tenant_chan ON historical_cases(tenant_id, channel)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_tenant_typo ON historical_cases(tenant_id, typology)")
                conn.commit()

    def add_case(self, case: HistoricalCase) -> str:
        """Persists a single HistoricalCase."""
        with self._lock:
            with self._get_connection() as conn:
                t = case.transaction
                c = case.customer
                m = case.merchant
                d = case.device
                l = case.location
                b = case.behavior
                o = case.outcome

                conn.execute("""
                    INSERT OR REPLACE INTO historical_cases (
                        case_id, tenant_id, amount, currency, channel, timestamp,
                        customer_id, customer_name, account_type, kyc_status, customer_risk_tier,
                        merchant_name, merchant_category, device_os, country, is_vpn, is_new_device,
                        velocity_1h_count, velocity_24h_count, cycle_score, scatter_gather_score,
                        disposition, typology, ground_truth_score, narrative, case_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case.case_id, case.tenant_id, t.amount, t.currency, t.channel, t.timestamp,
                    c.customer_id, c.name, c.account_type, c.kyc_status, c.risk_tier,
                    m.name, m.category, d.os, l.country, 1 if d.is_vpn else 0, 1 if d.is_new_device else 0,
                    b.velocity_1h_count, b.velocity_24h_count, b.cycle_score, b.scatter_gather_score,
                    o.disposition, o.typology, o.ground_truth_score, o.narrative,
                    json.dumps(case.to_dict()), case.created_at
                ))
                conn.commit()
        return case.case_id

    def add_cases(self, cases: List[HistoricalCase]) -> int:
        """Batch insert or replace historical cases."""
        with self._lock:
            with self._get_connection() as conn:
                for case in cases:
                    t = case.transaction
                    c = case.customer
                    m = case.merchant
                    d = case.device
                    l = case.location
                    b = case.behavior
                    o = case.outcome

                    conn.execute("""
                        INSERT OR REPLACE INTO historical_cases (
                            case_id, tenant_id, amount, currency, channel, timestamp,
                            customer_id, customer_name, account_type, kyc_status, customer_risk_tier,
                            merchant_name, merchant_category, device_os, country, is_vpn, is_new_device,
                            velocity_1h_count, velocity_24h_count, cycle_score, scatter_gather_score,
                            disposition, typology, ground_truth_score, narrative, case_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        case.case_id, case.tenant_id, t.amount, t.currency, t.channel, t.timestamp,
                        c.customer_id, c.name, c.account_type, c.kyc_status, c.risk_tier,
                        m.name, m.category, d.os, l.country, 1 if d.is_vpn else 0, 1 if d.is_new_device else 0,
                        b.velocity_1h_count, b.velocity_24h_count, b.cycle_score, b.scatter_gather_score,
                        o.disposition, o.typology, o.ground_truth_score, o.narrative,
                        json.dumps(case.to_dict()), case.created_at
                    ))
                conn.commit()
        return len(cases)

    def get_case(self, case_id: str, tenant_id: str = "default_tenant") -> Optional[HistoricalCase]:
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT case_json FROM historical_cases WHERE case_id = ? AND tenant_id = ?",
                    (case_id, tenant_id)
                )
                row = cur.fetchone()
                if row:
                    return HistoricalCase.from_dict(json.loads(row["case_json"]))
        return None

    def list_cases(self, tenant_id: str = "default_tenant", limit: int = 100) -> List[HistoricalCase]:
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT case_json FROM historical_cases WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                    (tenant_id, limit)
                )
                return [HistoricalCase.from_dict(json.loads(r["case_json"])) for r in cur.fetchall()]

    def filter_candidates(self, query: HybridSearchQuery) -> List[HistoricalCase]:
        """
        Metadata Filtering (Step 1 of Hybrid Search):
        Applies strict predicate pushdown in SQL.
        """
        clauses = ["tenant_id = ?"]
        params: List[Any] = [query.tenant_id]

        if query.channel:
            clauses.append("channel = ?")
            params.append(query.channel.upper())

        if query.currency:
            clauses.append("currency = ?")
            params.append(query.currency.upper())

        if query.min_amount is not None:
            clauses.append("amount >= ?")
            params.append(query.min_amount)

        if query.max_amount is not None:
            clauses.append("amount <= ?")
            params.append(query.max_amount)

        if query.filter_dispositions:
            placeholders = ",".join("?" for _ in query.filter_dispositions)
            clauses.append(f"disposition IN ({placeholders})")
            params.extend(query.filter_dispositions)

        if query.filter_typologies:
            placeholders = ",".join("?" for _ in query.filter_typologies)
            clauses.append(f"typology IN ({placeholders})")
            params.extend(query.filter_typologies)

        sql = f"SELECT case_json FROM historical_cases WHERE {' AND '.join(clauses)}"

        with self._lock:
            with self._get_connection() as conn:
                cur = conn.execute(sql, params)
                return [HistoricalCase.from_dict(json.loads(r["case_json"])) for r in cur.fetchall()]

    def count(self, tenant_id: Optional[str] = None) -> int:
        with self._lock:
            with self._get_connection() as conn:
                if tenant_id:
                    cur = conn.execute("SELECT COUNT(*) AS cnt FROM historical_cases WHERE tenant_id = ?", (tenant_id,))
                else:
                    cur = conn.execute("SELECT COUNT(*) AS cnt FROM historical_cases")
                return int(cur.fetchone()["cnt"])

    def clear(self, tenant_id: Optional[str] = None):
        with self._lock:
            with self._get_connection() as conn:
                if tenant_id:
                    conn.execute("DELETE FROM historical_cases WHERE tenant_id = ?", (tenant_id,))
                else:
                    conn.execute("DELETE FROM historical_cases")
                conn.commit()


_global_case_store: Optional[HistoricalCaseStore] = None
_case_store_lock = threading.Lock()


def get_case_store(db_path: Optional[str] = None) -> HistoricalCaseStore:
    global _global_case_store
    if _global_case_store is None:
        with _case_store_lock:
            if _global_case_store is None:
                _global_case_store = HistoricalCaseStore(db_path=db_path)
    return _global_case_store
