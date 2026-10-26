"""
LangGraph Integration Bridge for Graph Fraud Detection (Phase 4).

Constructs a FraudGraph from AgentState evidence bundles and transaction history,
detects suspicious clusters (device sharing rings, IP syndicates, circular laundering),
and outputs structured graph cluster evidence and risk signals.
"""

from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal

from backend.graph_fraud.schema import (
    CustomerNode,
    AccountNode,
    TransactionNode,
    DeviceNode,
    IPNode,
    MerchantNode,
    LocationNode,
)
from backend.graph_fraud.graph_engine import FraudGraph
from backend.graph_fraud.cluster_detection import ClusterDetector


def build_fraud_graph_from_state(state: Dict[str, Any]) -> FraudGraph:
    """
    Constructs a heterogeneous FraudGraph from LangGraph AgentState evidence.
    """
    tenant_id = state.get("tenant_id") or "default_tenant"
    fg = FraudGraph(tenant_id=tenant_id)

    txn_ev = state.get("transaction_evidence") or {}
    cust_ev = state.get("customer_evidence") or {}
    dev_ev = state.get("device_evidence") or {}
    loc_ev = state.get("location_evidence") or {}
    merch_ev = state.get("merchant_evidence") or {}
    history = state.get("transaction_history") or []

    # 1. Target Transaction
    txn_id = state.get("transaction_id") or txn_ev.get("txn_id") or "TXN_TARGET"
    amt = float(txn_ev.get("amount") or 0.0)
    channel = txn_ev.get("channel") or "ACH"
    src_acct = txn_ev.get("account_id") or "ACCT_SOURCE"
    dest_id = txn_ev.get("counterparty") or txn_ev.get("dest_account") or "ACCT_DEST"

    fg.add_transaction(TransactionNode(
        id=txn_id,
        amount=amt,
        currency=txn_ev.get("currency") or "USD",
        timestamp=txn_ev.get("timestamp") or "",
        channel=channel
    ))

    # 2. Source Customer & Account
    cust_id = cust_ev.get("customer_id") or f"CUST_{src_acct}"
    fg.add_customer(CustomerNode(
        id=cust_id,
        name=cust_ev.get("name") or "Source Customer",
        kyc_status=cust_ev.get("kyc_status") or "VERIFIED",
        risk_tier=cust_ev.get("risk_tier") or "LOW"
    ))
    fg.add_account(AccountNode(
        id=src_acct,
        account_type=cust_ev.get("account_type") or "CHECKING",
        balance=float(cust_ev.get("balance") or 10000.0)
    ))
    fg.add_owns(cust_id, src_acct)

    # 3. Beneficiary (Account or Merchant)
    if merch_ev and merch_ev.get("name"):
        m_id = merch_ev.get("merchant_id") or f"MERCH_{dest_id}"
        fg.add_merchant(MerchantNode(
            id=m_id,
            name=merch_ev.get("name"),
            category=merch_ev.get("category") or "RETAIL",
            risk_score=float(merch_ev.get("historical_fraud_rate") or 0.0)
        ))
        fg.add_transacted_with(src_acct, txn_id, m_id, amt, txn_ev.get("timestamp", ""), channel)
    else:
        fg.add_account(AccountNode(id=dest_id, account_type="CHECKING", balance=5000.0))
        fg.add_transacted_with(src_acct, txn_id, dest_id, amt, txn_ev.get("timestamp", ""), channel)

    # 4. Device & IP Infrastructure
    if dev_ev:
        dev_id = dev_ev.get("device_id") or dev_ev.get("fingerprint") or f"DEV_{dev_ev.get('os', 'UNK')}"
        fg.add_device(DeviceNode(
            id=dev_id,
            os=dev_ev.get("os") or "Unknown OS",
            fingerprint=dev_ev.get("fingerprint")
        ))
        fg.add_uses(src_acct, dev_id, infrastructure_type="device")

        if dev_ev.get("ip_address"):
            ip_val = dev_ev["ip_address"]
            ip_id = f"IP_{ip_val}"
            fg.add_ip(IPNode(
                id=ip_id,
                ip_address=ip_val,
                is_vpn=bool(dev_ev.get("is_vpn")),
                is_tor=bool(dev_ev.get("is_tor"))
            ))
            fg.add_uses(src_acct, ip_id, infrastructure_type="ip")

    # 5. Location
    if loc_ev and loc_ev.get("country"):
        country = loc_ev.get("country")
        loc_id = f"LOC_{country}"
        fg.add_location(LocationNode(
            id=loc_id,
            country=country,
            city=loc_ev.get("city"),
            is_high_risk=country in ["RU", "KP", "IR", "SY"]
        ))
        fg.add_located_at(txn_id, loc_id)

    # 6. Multi-Hop Transaction History
    for idx, h in enumerate(history):
        h_id = h.get("txn_id") or f"HIST_TXN_{idx}"
        h_src = h.get("account_id") or h.get("nameOrig") or h.get("source_account")
        h_dest = h.get("counterparty") or h.get("nameDest") or h.get("dest_account")
        h_amt = float(h.get("amount") or 0.0)

        if not h_src or not h_dest or h_amt <= 0.0:
            continue

        if h_src not in fg.g:
            fg.add_account(AccountNode(id=h_src, account_type="CHECKING", balance=10000.0))
        if h_dest not in fg.g:
            fg.add_account(AccountNode(id=h_dest, account_type="CHECKING", balance=10000.0))

        if h_id not in fg.g:
            fg.add_transaction(TransactionNode(
                id=h_id,
                amount=h_amt,
                currency=h.get("currency") or "USD",
                timestamp=h.get("timestamp") or "",
                channel=h.get("channel") or "ACH"
            ))

        fg.add_transacted_with(h_src, h_id, h_dest, h_amt, h.get("timestamp", ""), h.get("channel", "ACH"))

        # Link device or IP in history if present
        if h.get("device_id"):
            d_node_id = h["device_id"]
            if d_node_id not in fg.g:
                fg.add_device(DeviceNode(id=d_node_id, os="Unknown"))
            fg.add_uses(h_src, d_node_id, infrastructure_type="device")

        if h.get("ip_address"):
            ip_node_id = f"IP_{h['ip_address']}"
            if ip_node_id not in fg.g:
                fg.add_ip(IPNode(id=ip_node_id, ip_address=h["ip_address"]))
            fg.add_uses(h_src, ip_node_id, infrastructure_type="ip")

    return fg


def analyze_graph_fraud_clusters(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes graph cluster detection on AgentState evidence.
    Returns:
    {
        "cluster_risk_score": float,
        "clusters": List[Dict[str, Any]],
        "risk_signals": List[Dict[str, Any]],
        "derived_edges": Dict[str, int]
    }
    """
    fg = build_fraud_graph_from_state(state)
    dev_edges, ip_edges = fg.derive_shared_infrastructure_edges()

    detector = ClusterDetector(fg)
    txn_id = state.get("transaction_id") or state.get("transaction_evidence", {}).get("txn_id")

    cluster_risk = 0.0
    clusters = []
    signals = []

    if txn_id and txn_id in fg.g:
        cluster_risk, clusters_obj, signals = detector.evaluate_transaction_cluster_risk(txn_id, radius=2)
        clusters = [c.to_dict() for c in clusters_obj]
    else:
        # Evaluate global clusters if target txn not found in ego projection
        all_c = detector.detect_all_clusters()
        if all_c:
            cluster_risk = max(c.risk_score for c in all_c)
            clusters = [c.to_dict() for c in all_c[:5]]
            for c in all_c[:5]:
                for s in c.signals:
                    signals.append({
                        "signal": s,
                        "severity": c.risk_score,
                        "source": "graph_cluster_detector",
                        "evidence": {"cluster_id": c.cluster_id, "explanation": c.explanation}
                    })

    return {
        "cluster_risk_score": cluster_risk,
        "clusters": clusters,
        "risk_signals": signals,
        "derived_edges": {
            "shares_device_edges": dev_edges,
            "shares_ip_edges": ip_edges
        },
        "graph_stats": {
            "total_nodes": fg.num_nodes,
            "total_edges": fg.num_edges
        }
    }
