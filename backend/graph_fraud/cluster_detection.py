"""
Suspicious Graph Cluster & Financial Crime Syndicate Detection Engine (Phase 4).

Detects:
1. Device-sharing syndicate rings (multiple distinct accounts on single device).
2. IP-sharing proxy clusters (VPN/Tor and multi-account concentration).
3. Circular directed laundering loops (A -> B -> C -> A with amount preservation).
4. Scatter-gather mule dispersion and collection hubs (fan-out / fan-in).
5. Transaction-level ego-network risk evaluation.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import datetime
import itertools
import networkx as nx

from backend.graph_fraud.schema import (
    NodeType,
    EdgeType,
    SuspiciousCluster,
)
from backend.graph_fraud.graph_engine import FraudGraph


class ClusterDetector:
    """
    Graph algorithms for detecting illicit financial crime networks,
    mule syndicates, and infrastructure sharing anomalies.
    """

    def __init__(self, graph: FraudGraph):
        self.fg = graph
        self.g = graph.g

    def detect_device_sharing_rings(self, min_accounts: int = 2) -> List[SuspiciousCluster]:
        """
        Detects syndicate rings where a single physical device is utilized
        by multiple distinct customer accounts.
        """
        clusters: List[SuspiciousCluster] = []
        device_nodes = [n for n, d in self.g.nodes(data=True) if d.get("node_type") == NodeType.DEVICE.value]

        for dev_id in device_nodes:
            dev_data = self.g.nodes[dev_id]
            # Find users (accounts or customers)
            users = [u for u in self.g.predecessors(dev_id) if self.g.nodes[u].get("node_type") in [NodeType.ACCOUNT.value, NodeType.CUSTOMER.value]]
            distinct_users = list(set(users))

            if len(distinct_users) >= min_accounts:
                unverified_count = 0
                for u in distinct_users:
                    u_data = self.g.nodes[u]
                    kyc = u_data.get("kyc_status")
                    if not kyc and u_data.get("node_type") == NodeType.ACCOUNT.value:
                        for owner in self.g.predecessors(u):
                            if self.g.nodes[owner].get("node_type") == NodeType.CUSTOMER.value:
                                kyc = self.g.nodes[owner].get("kyc_status")
                                break
                    if kyc in ["UNVERIFIED", "FAILED", "PENDING"]:
                        unverified_count += 1

                # Risk score formulation
                base_risk = 0.60
                if len(distinct_users) >= 4:
                    base_risk = 0.85
                if len(distinct_users) >= 6:
                    base_risk = 0.96
                if unverified_count > 0:
                    base_risk = min(1.0, base_risk + (unverified_count * 0.05))

                cid = f"CLUSTER_DEV_{dev_id}"
                explanation = (
                    f"Device-Sharing Syndicate Ring: Device '{dev_id}' (OS: {dev_data.get('os', 'Unknown')}) "
                    f"is shared across {len(distinct_users)} distinct customer accounts "
                    f"({unverified_count} unverified KYC). Indicates coordinated credential sharing or mule ring."
                )

                clusters.append(SuspiciousCluster(
                    cluster_id=cid,
                    cluster_type="device_sharing_ring",
                    risk_score=round(base_risk, 4),
                    node_ids=[dev_id] + distinct_users,
                    edge_types=[EdgeType.USES.value, EdgeType.SHARES_DEVICE.value],
                    metrics={
                        "shared_device": dev_id,
                        "accounts_count": len(distinct_users),
                        "unverified_kyc_count": unverified_count,
                        "device_os": dev_data.get("os", "Unknown")
                    },
                    signals=["SHARED_DEVICE_RING_DETECTED"],
                    explanation=explanation
                ))

        return clusters

    def detect_ip_sharing_syndicates(self, min_accounts: int = 3) -> List[SuspiciousCluster]:
        """
        Detects proxy or network clusters where multiple accounts concentrate on a single IP,
        especially when involving VPN or Tor anonymity networks.
        """
        clusters: List[SuspiciousCluster] = []
        ip_nodes = [n for n, d in self.g.nodes(data=True) if d.get("node_type") == NodeType.IP.value]

        for ip_id in ip_nodes:
            ip_data = self.g.nodes[ip_id]
            is_vpn = bool(ip_data.get("is_vpn"))
            is_tor = bool(ip_data.get("is_tor"))

            users = [u for u in self.g.predecessors(ip_id) if self.g.nodes[u].get("node_type") in [NodeType.ACCOUNT.value, NodeType.CUSTOMER.value]]
            distinct_users = list(set(users))

            threshold = 2 if (is_vpn or is_tor) else min_accounts
            if len(distinct_users) >= threshold:
                base_risk = 0.65
                if is_tor:
                    base_risk = 0.95
                elif is_vpn:
                    base_risk = 0.85
                elif len(distinct_users) >= 5:
                    base_risk = 0.88

                cid = f"CLUSTER_IP_{ip_id}"
                anonymity_tag = "Tor" if is_tor else ("VPN" if is_vpn else "Standard")
                explanation = (
                    f"IP-Sharing Syndicate: IP address '{ip_data.get('ip_address', ip_id)}' ({anonymity_tag}) "
                    f"is actively shared by {len(distinct_users)} distinct customer accounts. "
                    f"Suggests proxy routing or botnet-driven transaction automation."
                )

                clusters.append(SuspiciousCluster(
                    cluster_id=cid,
                    cluster_type="ip_syndicate",
                    risk_score=round(base_risk, 4),
                    node_ids=[ip_id] + distinct_users,
                    edge_types=[EdgeType.USES.value, EdgeType.SHARES_IP.value],
                    metrics={
                        "ip_address": ip_data.get("ip_address", ip_id),
                        "accounts_count": len(distinct_users),
                        "is_vpn": is_vpn,
                        "is_tor": is_tor
                    },
                    signals=["SHARED_IP_CLUSTER_DETECTED", "ANONYMOUS_PROXY_NETWORK" if (is_vpn or is_tor) else "IP_CONCENTRATION"],
                    explanation=explanation
                ))

        return clusters

    def detect_circular_laundering_loops(self, max_depth: int = 6) -> List[SuspiciousCluster]:
        """
        Detects closed circular directed loops where money originates from Account A,
        passes through intermediaries B and C, and returns to A.
        """
        clusters: List[SuspiciousCluster] = []

        # Build account-to-account directed projection
        acct_di = nx.DiGraph()
        for u, v, data in self.g.edges(data=True):
            if data.get("rel") == EdgeType.TRANSACTED_WITH.value and data.get("direction") == "outbound":
                # u is Account, v is Transaction
                txn_node = v
                for _, beneficiary, b_data in self.g.out_edges(txn_node, data=True):
                    if b_data.get("rel") == EdgeType.TRANSACTED_WITH.value and b_data.get("direction") == "inbound":
                        amt = float(data.get("amount") or 0.0)
                        acct_di.add_edge(u, beneficiary, amount=amt, txn_id=txn_node)

        # Detect simple cycles
        try:
            cycles = list(nx.simple_cycles(acct_di))
        except Exception:
            cycles = []

        for cycle in cycles:
            if 3 <= len(cycle) <= max_depth:
                # Check cycle amount preservation
                amounts = []
                for idx in range(len(cycle)):
                    src = cycle[idx]
                    dst = cycle[(idx + 1) % len(cycle)]
                    if acct_di.has_edge(src, dst):
                        amounts.append(acct_di[src][dst].get("amount", 0.0))

                mean_amt = sum(amounts) / len(amounts) if amounts else 0.0
                max_dev = max(abs(a - mean_amt) for a in amounts) if amounts else 0.0
                preservation_ratio = 1.0 - (max_dev / mean_amt) if mean_amt > 0 else 0.0

                risk_score = 0.95 if preservation_ratio >= 0.70 else 0.85
                cid = f"CLUSTER_CYCLE_{'_'.join(cycle[:3])}"

                explanation = (
                    f"Directed Circular Laundering Loop: Detected {len(cycle)}-hop circular flow "
                    f"({' -> '.join(cycle)} -> {cycle[0]}). "
                    f"Average transfer volume: ${mean_amt:,.2f} with {preservation_ratio*100:.1f}% amount preservation. "
                    f"Characteristic of layering to disguise illicit source."
                )

                clusters.append(SuspiciousCluster(
                    cluster_id=cid,
                    cluster_type="cycle_laundering_loop",
                    risk_score=round(risk_score, 4),
                    node_ids=list(cycle),
                    edge_types=[EdgeType.TRANSACTED_WITH.value],
                    metrics={
                        "cycle_length": len(cycle),
                        "mean_amount": round(mean_amt, 2),
                        "amount_preservation_ratio": round(preservation_ratio, 2)
                    },
                    signals=["CIRCULAR_FLOW_CLUSTER_DETECTED", "MULTI_HOP_LAYERING_NETWORK"],
                    explanation=explanation
                ))

        return clusters

    def detect_scatter_gather_hubs(self, min_degree: int = 4) -> List[SuspiciousCluster]:
        """
        Detects smurfing and money mule hubs:
        1. Fan-out (Scatter): single source dispersing to >= min_degree destinations.
        2. Fan-in (Gather): single destination gathering from >= min_degree sources.
        """
        clusters: List[SuspiciousCluster] = []

        # Account-to-account projection
        out_counts: Dict[str, List[Tuple[str, float]]] = {}
        in_counts: Dict[str, List[Tuple[str, float]]] = {}

        for u, v, data in self.g.edges(data=True):
            if data.get("rel") == EdgeType.TRANSACTED_WITH.value and data.get("direction") == "outbound":
                txn_node = v
                amt = float(data.get("amount") or 0.0)
                for _, dest, _ in self.g.out_edges(txn_node, data=True):
                    out_counts.setdefault(u, []).append((dest, amt))
                    in_counts.setdefault(dest, []).append((u, amt))

        # Check Fan-out
        for hub_acct, targets in out_counts.items():
            distinct_targets = list({t for t, _ in targets})
            if len(distinct_targets) >= min_degree:
                total_scattered = sum(a for _, a in targets)
                cid = f"CLUSTER_SCATTER_{hub_acct}"
                explanation = (
                    f"Scatter Dispersion (Fan-Out) Hub: Account '{hub_acct}' rapidly scattered "
                    f"${total_scattered:,.2f} across {len(distinct_targets)} distinct destination accounts. "
                    f"Classic layering/smurfing disbursement behavior."
                )
                clusters.append(SuspiciousCluster(
                    cluster_id=cid,
                    cluster_type="scatter_gather_fanout",
                    risk_score=0.88,
                    node_ids=[hub_acct] + distinct_targets,
                    edge_types=[EdgeType.TRANSACTED_WITH.value],
                    metrics={
                        "hub_account": hub_acct,
                        "dispersion_degree": len(distinct_targets),
                        "total_volume": round(total_scattered, 2)
                    },
                    signals=["SCATTER_GATHER_FANOUT_DETECTED"],
                    explanation=explanation
                ))

        # Check Fan-in
        for gather_acct, sources in in_counts.items():
            distinct_sources = list({s for s, _ in sources})
            if len(distinct_sources) >= min_degree:
                total_gathered = sum(a for _, a in sources)
                cid = f"CLUSTER_GATHER_{gather_acct}"
                explanation = (
                    f"Gather Collection (Fan-In) Mule: Account '{gather_acct}' collected "
                    f"${total_gathered:,.2f} from {len(distinct_sources)} distinct source accounts. "
                    f"Classic mule aggregation behavior."
                )
                clusters.append(SuspiciousCluster(
                    cluster_id=cid,
                    cluster_type="scatter_gather_fanin",
                    risk_score=0.88,
                    node_ids=[gather_acct] + distinct_sources,
                    edge_types=[EdgeType.TRANSACTED_WITH.value],
                    metrics={
                        "accumulator_account": gather_acct,
                        "aggregation_degree": len(distinct_sources),
                        "total_volume": round(total_gathered, 2)
                    },
                    signals=["SCATTER_GATHER_FANIN_DETECTED"],
                    explanation=explanation
                ))

        return clusters

    def detect_all_clusters(self) -> List[SuspiciousCluster]:
        """Runs all cluster detection algorithms and returns unified anomalous clusters."""
        self.fg.derive_shared_infrastructure_edges()

        all_clusters: List[SuspiciousCluster] = []
        all_clusters.extend(self.detect_device_sharing_rings())
        all_clusters.extend(self.detect_ip_sharing_syndicates())
        all_clusters.extend(self.detect_circular_laundering_loops())
        all_clusters.extend(self.detect_scatter_gather_hubs())

        all_clusters.sort(key=lambda c: c.risk_score, reverse=True)
        return all_clusters

    def evaluate_transaction_cluster_risk(
        self,
        txn_id: str,
        radius: int = 2
    ) -> Tuple[float, List[SuspiciousCluster], List[Dict[str, Any]]]:
        """
        Extracts localized ego-network for a transaction, runs cluster detection,
        and returns (cluster_risk_score, overlapping_clusters, risk_signals).
        """
        if txn_id not in self.g:
            return 0.0, [], []

        ego_fg = self.fg.get_ego_subgraph(txn_id, radius=radius)
        ego_detector = ClusterDetector(ego_fg)
        overlapping_clusters = ego_detector.detect_all_clusters()

        if not overlapping_clusters:
            return 0.0, [], []

        max_risk = max(c.risk_score for c in overlapping_clusters)
        risk_signals = []
        for c in overlapping_clusters:
            for s in c.signals:
                risk_signals.append({
                    "signal": s,
                    "severity": c.risk_score,
                    "source": "graph_cluster_detector",
                    "evidence": {
                        "cluster_id": c.cluster_id,
                        "cluster_type": c.cluster_type,
                        "explanation": c.explanation,
                        "metrics": c.metrics
                    }
                })

        return round(max_risk, 4), overlapping_clusters, risk_signals
