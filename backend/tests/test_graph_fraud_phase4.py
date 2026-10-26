"""
Automated Test Suite for Phase 4: Heterogeneous Graph Fraud Detection & Cluster Analysis.

Validates:
1. 7 Node Types: Customer, Account, Transaction, Device, IP, Merchant, Location.
2. 6 Relationship Types: OWNS, USES, TRANSACTED_WITH, LOCATED_AT, SHARES_DEVICE, SHARES_IP.
3. Synthetic Infrastructure Edge Derivation: SHARES_DEVICE and SHARES_IP.
4. Device-Sharing Syndicate Ring Detection.
5. IP-Sharing / Tor Anonymity Proxy Syndicate Detection.
6. Multi-Hop Circular Money Laundering Detection (A -> B -> C -> A).
7. Scatter-Gather Mule Dispersion & Aggregation Hub Detection.
8. Ego-Subgraph Extraction & Cytoscape.js Visualization Serialization.
9. End-to-end integration with LangGraph rule_engine_node.
"""

import pytest
from backend.graph_fraud.schema import (
    NodeType,
    EdgeType,
    CustomerNode,
    AccountNode,
    TransactionNode,
    DeviceNode,
    IPNode,
    MerchantNode,
    LocationNode,
    SuspiciousCluster,
)
from backend.graph_fraud.graph_engine import FraudGraph
from backend.graph_fraud.cluster_detection import ClusterDetector
from backend.graph_fraud.integration import analyze_graph_fraud_clusters, build_fraud_graph_from_state


def test_heterogeneous_graph_schema_construction():
    """Validates construction of all 7 node types and 6 relationship types."""
    fg = FraudGraph(tenant_id="test_tenant")

    # Add 7 Node Types
    fg.add_customer(CustomerNode(id="CUST_01", name="Alice Doe", kyc_status="VERIFIED", risk_tier="LOW"))
    fg.add_account(AccountNode(id="ACCT_01", account_type="CHECKING", balance=25000.0))
    fg.add_account(AccountNode(id="ACCT_02", account_type="CHECKING", balance=15000.0))
    fg.add_transaction(TransactionNode(id="TXN_01", amount=5000.0, channel="ACH", timestamp="2026-01-15T12:00:00+00:00"))
    fg.add_device(DeviceNode(id="DEV_01", os="iOS", fingerprint="fp_abc123"))
    fg.add_ip(IPNode(id="IP_01", ip_address="192.168.1.100", is_vpn=False, is_tor=False))
    fg.add_merchant(MerchantNode(id="MERCH_01", name="Acme Electronics", category="RETAIL", risk_score=0.02))
    fg.add_location(LocationNode(id="LOC_01", country="US", city="Seattle", is_high_risk=False))

    assert fg.num_nodes == 8

    # Add 6 Relationship Types
    fg.add_owns("CUST_01", "ACCT_01")
    fg.add_uses("ACCT_01", "DEV_01", infrastructure_type="device")
    fg.add_uses("ACCT_01", "IP_01", infrastructure_type="ip")
    fg.add_transacted_with("ACCT_01", "TXN_01", "ACCT_02", amount=5000.0, timestamp="2026-01-15T12:00:00+00:00", channel="ACH")
    fg.add_located_at("TXN_01", "LOC_01")
    fg.add_shares_device("ACCT_01", "ACCT_02", "DEV_01")
    fg.add_shares_ip("ACCT_01", "ACCT_02", "192.168.1.100")

    assert fg.num_edges >= 7
    # Verify edge relationships
    rels = {data.get("rel") for _, _, data in fg.g.edges(data=True)}
    assert EdgeType.OWNS.value in rels
    assert EdgeType.USES.value in rels
    assert EdgeType.TRANSACTED_WITH.value in rels
    assert EdgeType.LOCATED_AT.value in rels
    assert EdgeType.SHARES_DEVICE.value in rels
    assert EdgeType.SHARES_IP.value in rels


def test_derive_shared_infrastructure_edges():
    """Validates automatic synthesis of SHARES_DEVICE and SHARES_IP relationships."""
    fg = FraudGraph(tenant_id="test_tenant")

    # 3 accounts using the same device DEV_SHARED
    fg.add_device(DeviceNode(id="DEV_SHARED", os="Android"))
    for i in range(3):
        a_id = f"ACCT_{i}"
        fg.add_account(AccountNode(id=a_id))
        fg.add_uses(a_id, "DEV_SHARED", infrastructure_type="device")

    # 2 accounts using the same IP
    fg.add_ip(IPNode(id="IP_SHARED", ip_address="10.0.0.1", is_vpn=True))
    fg.add_uses("ACCT_0", "IP_SHARED", infrastructure_type="ip")
    fg.add_uses("ACCT_1", "IP_SHARED", infrastructure_type="ip")

    dev_edges, ip_edges = fg.derive_shared_infrastructure_edges()

    # 3 accounts pairwise = 3 pairs * 2 directions = 6 directed edges
    assert dev_edges == 6
    # 2 accounts pairwise = 1 pair * 2 directions = 2 directed edges
    assert ip_edges == 2

    assert fg.g.has_edge("ACCT_0", "ACCT_1")
    assert fg.g.has_edge("ACCT_1", "ACCT_2")


def test_device_sharing_syndicate_ring_detection():
    """Detects multi-account device sharing syndicate ring with unverified KYC."""
    fg = FraudGraph(tenant_id="test_tenant")
    dev_id = "DEV_MULE_HUB"
    fg.add_device(DeviceNode(id=dev_id, os="Linux"))

    for i in range(4):
        a_id = f"MULE_ACCT_{i}"
        fg.add_account(AccountNode(id=a_id))
        fg.add_customer(CustomerNode(id=f"CUST_{i}", name=f"Mule {i}", kyc_status="UNVERIFIED", risk_tier="HIGH"))
        fg.add_owns(f"CUST_{i}", a_id)
        fg.add_uses(a_id, dev_id, infrastructure_type="device")

    fg.derive_shared_infrastructure_edges()
    detector = ClusterDetector(fg)
    clusters = detector.detect_device_sharing_rings(min_accounts=2)

    assert len(clusters) == 1
    ring = clusters[0]
    assert ring.cluster_type == "device_sharing_ring"
    assert ring.risk_score >= 0.85
    assert ring.metrics["accounts_count"] == 4
    assert ring.metrics["unverified_kyc_count"] == 4
    assert "SHARED_DEVICE_RING_DETECTED" in ring.signals


def test_ip_sharing_syndicate_proxy_detection():
    """Detects anonymous proxy / Tor syndicate cluster."""
    fg = FraudGraph(tenant_id="test_tenant")
    ip_id = "IP_TOR_EXIT"
    fg.add_ip(IPNode(id=ip_id, ip_address="185.220.101.5", is_vpn=False, is_tor=True))

    for i in range(3):
        a_id = f"BOT_ACCT_{i}"
        fg.add_account(AccountNode(id=a_id))
        fg.add_uses(a_id, ip_id, infrastructure_type="ip")

    fg.derive_shared_infrastructure_edges()
    detector = ClusterDetector(fg)
    clusters = detector.detect_ip_sharing_syndicates()

    assert len(clusters) == 1
    proxy_cluster = clusters[0]
    assert proxy_cluster.cluster_type == "ip_syndicate"
    assert proxy_cluster.risk_score >= 0.90
    assert proxy_cluster.metrics["is_tor"] is True
    assert "SHARED_IP_CLUSTER_DETECTED" in proxy_cluster.signals


def test_circular_laundering_loop_detection():
    """Detects closed circular multi-hop transaction cycle with amount preservation."""
    fg = FraudGraph(tenant_id="test_tenant")

    # A -> B -> C -> A
    accounts = ["ACCT_A", "ACCT_B", "ACCT_C"]
    for a in accounts:
        fg.add_account(AccountNode(id=a))

    fg.add_transacted_with("ACCT_A", "TXN_AB", "ACCT_B", amount=10000.0)
    fg.add_transacted_with("ACCT_B", "TXN_BC", "ACCT_C", amount=9800.0)
    fg.add_transacted_with("ACCT_C", "TXN_CA", "ACCT_A", amount=9600.0)

    detector = ClusterDetector(fg)
    cycles = detector.detect_circular_laundering_loops(max_depth=6)

    assert len(cycles) >= 1
    c = cycles[0]
    assert c.cluster_type == "cycle_laundering_loop"
    assert c.risk_score >= 0.90
    assert c.metrics["cycle_length"] == 3
    assert c.metrics["amount_preservation_ratio"] >= 0.80
    assert "CIRCULAR_FLOW_CLUSTER_DETECTED" in c.signals


def test_scatter_gather_hub_detection():
    """Detects fan-out (scatter) and fan-in (gather) mule hubs."""
    fg = FraudGraph(tenant_id="test_tenant")

    # 1. Fan-out: HUB_DISPERSE -> 5 targets
    fg.add_account(AccountNode(id="HUB_DISPERSE"))
    for i in range(5):
        target = f"DEST_MULE_{i}"
        fg.add_account(AccountNode(id=target))
        fg.add_transacted_with("HUB_DISPERSE", f"TXN_OUT_{i}", target, amount=2500.0)

    # 2. Fan-in: 5 sources -> HUB_COLLECT
    fg.add_account(AccountNode(id="HUB_COLLECT"))
    for j in range(5):
        src = f"SRC_MULE_{j}"
        fg.add_account(AccountNode(id=src))
        fg.add_transacted_with(src, f"TXN_IN_{j}", "HUB_COLLECT", amount=3000.0)

    detector = ClusterDetector(fg)
    clusters = detector.detect_scatter_gather_hubs(min_degree=4)

    assert len(clusters) == 2
    types = {cl.cluster_type for cl in clusters}
    assert "scatter_gather_fanout" in types
    assert "scatter_gather_fanin" in types


def test_ego_network_and_cytoscape_serialization():
    """Validates ego-subgraph neighborhood extraction and Cytoscape.js export."""
    fg = FraudGraph(tenant_id="test_tenant")
    fg.add_account(AccountNode(id="CENTER_ACCT"))
    fg.add_device(DeviceNode(id="DEV_1"))
    fg.add_account(AccountNode(id="PEER_ACCT"))
    fg.add_uses("CENTER_ACCT", "DEV_1")
    fg.add_uses("PEER_ACCT", "DEV_1")

    # Subgraph centered on DEV_1
    ego = fg.get_ego_subgraph("DEV_1", radius=1)
    assert ego.num_nodes == 3

    # Cytoscape export
    cyto = ego.to_cytoscape_json()
    assert "nodes" in cyto
    assert "edges" in cyto
    assert len(cyto["nodes"]) == 3
    assert len(cyto["edges"]) == 2
    assert "data" in cyto["nodes"][0]
    assert "id" in cyto["nodes"][0]["data"]


def test_langgraph_rule_engine_graph_cluster_integration():
    """Tests rule_engine_node in LangGraph with active graph cluster analysis."""
    from backend.graph import rule_engine_node, AgentState

    # State with history exhibiting device sharing ring
    state: AgentState = {
        "investigation_id": "INV_GRAPH_001",
        "transaction_id": "TXN_TARGET_GRAPH",
        "tenant_id": "default_tenant",
        "tasks": ["rule_evaluation"],
        "customer_evidence": {"name": "Target Customer", "account_type": "CHECKING", "kyc_status": "UNVERIFIED"},
        "transaction_evidence": {
            "txn_id": "TXN_TARGET_GRAPH",
            "account_id": "ACCT_SYNDICATE_0",
            "counterparty": "ACCT_BENEFICIARY_X",
            "amount": 4500.0,
            "currency": "USD",
            "channel": "ACH",
            "timestamp": "2026-01-15T12:00:00+00:00"
        },
        "merchant_evidence": {},
        "device_evidence": {"device_id": "DEV_FARM_01", "os": "Android"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": None,
        "rule_reasons": [],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
        "compliance_alerts": None,
        "has_typology_alert": None,
        "predicted_verdict": None,
        "workflow_status": None,
        "ml_risk_score": None,
        "ml_calibrated_probability": None,
        "ml_top_features": None,
        "ml_model_id": None,
        "graph_cluster_evidence": None,
        # Transaction history showing 3 other accounts sharing the exact same device DEV_FARM_01
        "transaction_history": [
            {"txn_id": "HIST_01", "account_id": "ACCT_SYNDICATE_1", "counterparty": "CP_1", "amount": 3500.0, "device_id": "DEV_FARM_01"},
            {"txn_id": "HIST_02", "account_id": "ACCT_SYNDICATE_2", "counterparty": "CP_2", "amount": 4200.0, "device_id": "DEV_FARM_01"},
            {"txn_id": "HIST_03", "account_id": "ACCT_SYNDICATE_3", "counterparty": "CP_3", "amount": 3900.0, "device_id": "DEV_FARM_01"},
        ]
    }

    # Execute rule_engine_node
    res_state = rule_engine_node(state)

    # Graph cluster evidence must be populated
    assert res_state["graph_cluster_evidence"] is not None
    graph_evidence = res_state["graph_cluster_evidence"]
    assert graph_evidence["cluster_risk_score"] >= 0.85
    assert len(graph_evidence["clusters"]) >= 1

    # Signal collection must include SHARED_DEVICE_RING_DETECTED
    signals = [s["signal"] for s in res_state["risk_signals"]]
    assert "SHARED_DEVICE_RING_DETECTED" in signals

    # Rule score must reflect elevated cluster risk
    assert res_state["rule_score"] >= 0.85
    reasons_str = " ".join(res_state["rule_reasons"])
    assert "Graph Cluster Anomaly" in reasons_str
