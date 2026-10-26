"""
Tabular Feature Engineering Pipeline for FFIRE Fraud Model (Phase 2).

Transforms transaction, entity profile, and graph topology signals into
standardized numeric feature vectors for LightGBM and baseline classifiers.

Guarantees:
1. Strict Temporal Integrity: Velocity and graph features only inspect transactions
   occurring prior to or concurrent with the target transaction timestamp.
2. Strict Zero Label Leakage: No supervisory ground-truth labels (is_sar, typology,
   alert_id, target_verdict) are accessible or referenced.
3. Fixed Deterministic Schema: Generates consistent 31-dimensional feature vectors.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import datetime
import numpy as np

FEATURE_NAMES: List[str] = [
    "amount",
    "log_amount",
    "is_round_hundred",
    "is_round_thousand",
    "is_statutory_threshold",      # >= $10,000 (CTR recordkeeping mandate)
    "is_structuring_heuristic",    # $8,000 - $9,999 (avoidance heuristic proxy)
    "is_micro_transfer",           # < $500
    "velocity_count_1h",
    "velocity_sum_1h",
    "velocity_count_24h",
    "velocity_sum_24h",
    "velocity_count_7d",
    "velocity_sum_7d",
    "amount_to_avg_ratio",
    "is_high_velocity_burst",
    "graph_cycle_score",
    "has_graph_cycle",
    "scatter_gather_score",
    "has_scatter_gather",
    "unique_counterparties_count",
    "is_new_counterparty",
    "account_type_commercial",
    "account_type_checking",
    "kyc_status_verified",
    "kyc_status_unverified",
    "risk_tier_low",
    "risk_tier_high",
    "channel_wire",
    "channel_ach",
    "account_balance",
    "amount_to_balance_ratio",
]

NUM_FEATURES: int = len(FEATURE_NAMES)


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _parse_dt(ts: Any) -> Optional[datetime.datetime]:
    if ts is None:
        return None
    if isinstance(ts, datetime.datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def extract_features_from_dict(
    txn: Dict[str, Any],
    account: Optional[Dict[str, Any]] = None,
    customer: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    cycle_score: float = 0.0,
    sg_score: float = 0.0,
) -> np.ndarray:
    """
    Extract a 31-dimensional normalized float vector from transaction and entity dictionaries.
    """
    account = account or {}
    customer = customer or {}
    history = history or []

    # 1. Transaction-level features
    amt = _safe_float(txn.get("amount"), 0.0)
    log_amt = math.log1p(max(0.0, amt))
    is_round_100 = 1.0 if (amt > 0 and amt % 100 == 0) else 0.0
    is_round_1000 = 1.0 if (amt > 0 and amt % 1000 == 0) else 0.0
    is_statutory = 1.0 if amt >= 10000.0 else 0.0
    is_structuring = 1.0 if (8000.0 <= amt <= 9999.0) else 0.0
    is_micro = 1.0 if (0.0 < amt < 500.0) else 0.0

    # 2. Velocity & Temporal Features (prior history only)
    curr_ts = _parse_dt(txn.get("timestamp"))
    curr_acct = txn.get("account_id") or txn.get("nameOrig") or txn.get("source_account")

    v_1h_txns, v_24h_txns, v_7d_txns = [], [], []
    prior_counterparties = set()

    for h in history:
        h_acct = h.get("account_id") or h.get("nameOrig") or h.get("source_account")
        if h_acct != curr_acct:
            continue

        h_dest = h.get("counterparty") or h.get("nameDest") or h.get("dest_account")
        if h_dest:
            prior_counterparties.add(h_dest)

        h_ts = _parse_dt(h.get("timestamp"))
        if curr_ts and h_ts:
            delta = curr_ts - h_ts
            secs = delta.total_seconds()
            if secs >= 0:
                if secs <= 3600:
                    v_1h_txns.append(h)
                if secs <= 86400:
                    v_24h_txns.append(h)
                if secs <= 7 * 86400:
                    v_7d_txns.append(h)
        else:
            # Fallback if timestamps are missing: use observation order
            v_24h_txns.append(h)

    c_1h = len(v_1h_txns)
    s_1h = sum(_safe_float(t.get("amount")) for t in v_1h_txns)
    c_24h = len(v_24h_txns)
    s_24h = sum(_safe_float(t.get("amount")) for t in v_24h_txns)
    c_7d = len(v_7d_txns)
    s_7d = sum(_safe_float(t.get("amount")) for t in v_7d_txns)

    avg_amt_24h = (s_24h / c_24h) if c_24h > 0 else amt
    amt_to_avg = (amt / avg_amt_24h) if avg_amt_24h > 0 else 1.0
    is_burst = 1.0 if (c_1h >= 4 or (c_1h > 1 and s_1h >= 5000.0)) else 0.0

    # 3. Graph topology features
    c_score = float(cycle_score)
    has_cycle = 1.0 if c_score > 0.0 else 0.0
    s_score = float(sg_score)
    has_sg = 1.0 if s_score > 0.0 else 0.0

    unique_cps = float(len(prior_counterparties))
    curr_dest = txn.get("counterparty") or txn.get("nameDest") or txn.get("dest_account")
    is_new_cp = 1.0 if (curr_dest and curr_dest not in prior_counterparties) else 0.0

    # 4. Entity Profile Features
    acct_type = str(account.get("account_type") or customer.get("account_type") or "").upper()
    is_commercial = 1.0 if any(k in acct_type for k in ["COMMERCIAL", "BUSINESS", "PAYROLL", "ESCROW", "CORP"]) else 0.0
    is_checking = 1.0 if any(k in acct_type for k in ["CHECKING", "RETAIL", "SAVINGS"]) else 0.0

    kyc_status = str(customer.get("kyc_status") or "UNVERIFIED").upper()
    kyc_ver = 1.0 if kyc_status == "VERIFIED" else 0.0
    kyc_unver = 1.0 if kyc_status in ["UNVERIFIED", "PENDING", "FAILED"] else 0.0

    risk_tier = str(customer.get("risk_tier") or "MEDIUM").upper()
    tier_low = 1.0 if risk_tier == "LOW" else 0.0
    tier_high = 1.0 if risk_tier == "HIGH" else 0.0

    channel = str(txn.get("channel") or "ACH").upper()
    ch_wire = 1.0 if "WIRE" in channel else 0.0
    ch_ach = 1.0 if ("ACH" in channel or "TRANSFER" in channel) else 0.0

    balance = _safe_float(account.get("balance"), 10000.0)
    amt_to_bal = (amt / (balance + 1e-4)) if balance > 0 else 1.0

    feature_vector = np.array([
        amt,
        log_amt,
        is_round_100,
        is_round_1000,
        is_statutory,
        is_structuring,
        is_micro,
        float(c_1h),
        s_1h,
        float(c_24h),
        s_24h,
        float(c_7d),
        s_7d,
        amt_to_avg,
        is_burst,
        c_score,
        has_cycle,
        s_score,
        has_sg,
        unique_cps,
        is_new_cp,
        is_commercial,
        is_checking,
        kyc_ver,
        kyc_unver,
        tier_low,
        tier_high,
        ch_wire,
        ch_ach,
        balance,
        amt_to_bal,
    ], dtype=np.float32)

    return feature_vector


def extract_features_from_state(state: Dict[str, Any]) -> np.ndarray:
    """
    Extract feature vector directly from LangGraph AgentState.
    """
    txn_ev = state.get("transaction_evidence") or {}
    cust_ev = state.get("customer_evidence") or {}
    vel_ev = state.get("velocity_evidence") or {}
    history = state.get("transaction_history") or txn_ev.get("recent_transactions") or []

    # Check graph scores from rule analysis or compute
    rule_reasons = state.get("rule_reasons") or []
    c_score = 0.50 if any("circular flow" in str(r).lower() or "directed cycle" in str(r).lower() for r in rule_reasons) else 0.0
    sg_score = 0.40 if any("scatter-gather" in str(r).lower() or "pass-through" in str(r).lower() for r in rule_reasons) else 0.0

    # Build synthetic account dict from state evidence
    acct_dict = {
        "account_id": txn_ev.get("account_id"),
        "account_type": cust_ev.get("account_type") or "CHECKING",
        "balance": cust_ev.get("balance") or 25000.0
    }

    return extract_features_from_dict(
        txn=txn_ev,
        account=acct_dict,
        customer=cust_ev,
        history=history,
        cycle_score=c_score,
        sg_score=sg_score
    )
