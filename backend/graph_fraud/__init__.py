"""
Heterogeneous Graph Fraud Detection & Suspicious Cluster Analysis Subsystem (Phase 4).

Features:
- Heterogeneous Graph Data Model (7 Node Types, 6 Relationship Types)
- FraudGraph Engine built on NetworkX MultiDiGraph
- Suspicious Cluster Detection (Device-sharing rings, IP syndicates, Cycles, Scatter-Gather hubs)
- LangGraph graph_cluster_analysis_node integration
"""

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
from backend.graph_fraud.graph_engine import FraudGraph, get_fraud_graph
from backend.graph_fraud.cluster_detection import ClusterDetector

__all__ = [
    "NodeType",
    "EdgeType",
    "CustomerNode",
    "AccountNode",
    "TransactionNode",
    "DeviceNode",
    "IPNode",
    "MerchantNode",
    "LocationNode",
    "SuspiciousCluster",
    "FraudGraph",
    "get_fraud_graph",
    "ClusterDetector",
]
