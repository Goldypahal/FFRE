"""
Heterogeneous Fraud Graph Engine (Phase 4).

Wraps NetworkX MultiDiGraph to model complex multi-entity financial networks:
Customer, Account, Transaction, Device, IP, Merchant, Location.
Supports derived infrastructure-sharing edges (SHARES_DEVICE, SHARES_IP)
and sub-network ego-graph extraction.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import itertools
import networkx as nx

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
)


class FraudGraph:
    """
    Heterogeneous Multi-DiGraph representing financial crime entities and flows.
    """

    def __init__(self, tenant_id: str = "default_tenant"):
        self.tenant_id = tenant_id
        self.g = nx.MultiDiGraph()

    @property
    def num_nodes(self) -> int:
        return self.g.number_of_nodes()

    @property
    def num_edges(self) -> int:
        return self.g.number_of_edges()

    # --- Node Adders ---

    def add_customer(self, cust: CustomerNode):
        self.g.add_node(cust.id, **cust.to_dict())

    def add_account(self, acct: AccountNode):
        self.g.add_node(acct.id, **acct.to_dict())

    def add_transaction(self, txn: TransactionNode):
        self.g.add_node(txn.id, **txn.to_dict())

    def add_device(self, dev: DeviceNode):
        self.g.add_node(dev.id, **dev.to_dict())

    def add_ip(self, ip: IPNode):
        self.g.add_node(ip.id, **ip.to_dict())

    def add_merchant(self, merch: MerchantNode):
        self.g.add_node(merch.id, **merch.to_dict())

    def add_location(self, loc: LocationNode):
        self.g.add_node(loc.id, **loc.to_dict())

    # --- Relationship Adders ---

    def add_owns(self, customer_id: str, account_id: str):
        """Customer OWNS Account."""
        self.g.add_edge(customer_id, account_id, rel=EdgeType.OWNS.value)

    def add_uses(self, entity_id: str, target_id: str, infrastructure_type: str = "device"):
        """Account or Customer USES Device or IP."""
        self.g.add_edge(entity_id, target_id, rel=EdgeType.USES.value, infrastructure_type=infrastructure_type)

    def add_transacted_with(
        self,
        src_account_id: str,
        txn_id: str,
        dest_id: str,
        amount: float,
        timestamp: str = "",
        channel: str = "ACH"
    ):
        """
        Account -> Transaction -> Destination (Account or Merchant).
        Maintains bipartite transaction node for multi-attribute flow modeling.
        """
        # Edge 1: Originator -> Transaction
        self.g.add_edge(
            src_account_id,
            txn_id,
            rel=EdgeType.TRANSACTED_WITH.value,
            direction="outbound",
            amount=amount,
            timestamp=timestamp,
            channel=channel
        )
        # Edge 2: Transaction -> Beneficiary
        self.g.add_edge(
            txn_id,
            dest_id,
            rel=EdgeType.TRANSACTED_WITH.value,
            direction="inbound",
            amount=amount,
            timestamp=timestamp,
            channel=channel
        )

    def add_located_at(self, entity_id: str, location_id: str):
        """Entity (Transaction, Customer, IP) LOCATED_AT Location."""
        self.g.add_edge(entity_id, location_id, rel=EdgeType.LOCATED_AT.value)

    def add_shares_device(self, acct_a: str, acct_b: str, device_id: str):
        """Derived edge: two accounts share the same physical device."""
        self.g.add_edge(acct_a, acct_b, rel=EdgeType.SHARES_DEVICE.value, device_id=device_id)
        self.g.add_edge(acct_b, acct_a, rel=EdgeType.SHARES_DEVICE.value, device_id=device_id)

    def add_shares_ip(self, acct_a: str, acct_b: str, ip_address: str):
        """Derived edge: two accounts share the same network IP address."""
        self.g.add_edge(acct_a, acct_b, rel=EdgeType.SHARES_IP.value, ip_address=ip_address)
        self.g.add_edge(acct_b, acct_a, rel=EdgeType.SHARES_IP.value, ip_address=ip_address)

    # --- Derived Synthetic Edges ---

    def derive_shared_infrastructure_edges(self) -> Tuple[int, int]:
        """
        Inspects all Device and IP nodes. If multiple accounts or customers
        connect to the same device/IP via USES edges, derives SHARES_DEVICE
        and SHARES_IP relationships between all pairs.
        Returns (derived_device_edges, derived_ip_edges).
        """
        dev_edges_count = 0
        ip_edges_count = 0

        # 1. Device sharing
        device_nodes = [n for n, d in self.g.nodes(data=True) if d.get("node_type") == NodeType.DEVICE.value]
        for dev in device_nodes:
            # Find in-neighbors (accounts or customers using this device)
            users = [u for u in self.g.predecessors(dev) if self.g.nodes[u].get("node_type") in [NodeType.ACCOUNT.value, NodeType.CUSTOMER.value]]
            if len(users) > 1:
                for u1, u2 in itertools.combinations(users, 2):
                    self.add_shares_device(u1, u2, dev)
                    dev_edges_count += 2

        # 2. IP sharing
        ip_nodes = [n for n, d in self.g.nodes(data=True) if d.get("node_type") == NodeType.IP.value]
        for ip in ip_nodes:
            users = [u for u in self.g.predecessors(ip) if self.g.nodes[u].get("node_type") in [NodeType.ACCOUNT.value, NodeType.CUSTOMER.value]]
            if len(users) > 1:
                for u1, u2 in itertools.combinations(users, 2):
                    self.add_shares_ip(u1, u2, ip)
                    ip_edges_count += 2

        return dev_edges_count, ip_edges_count

    # --- Ego-Graph Extraction & Serialization ---

    def get_ego_subgraph(self, center_node_id: str, radius: int = 2) -> "FraudGraph":
        """Extracts localized k-hop neighborhood graph centered around target entity."""
        if center_node_id not in self.g:
            return FraudGraph(tenant_id=self.tenant_id)

        # Convert to undirected view to capture bidirectional reachability
        undirected_view = self.g.to_undirected()
        sub_nodes = nx.single_source_shortest_path_length(undirected_view, center_node_id, cutoff=radius).keys()

        sub_g = FraudGraph(tenant_id=self.tenant_id)
        sub_g.g = self.g.subgraph(sub_nodes).copy()
        return sub_g

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """Serializes graph to Cytoscape.js format for frontend visualization."""
        elements = {"nodes": [], "edges": []}

        for n, data in self.g.nodes(data=True):
            elements["nodes"].append({
                "data": {
                    "id": str(n),
                    "label": str(data.get("name") or str(n)),
                    "node_type": data.get("node_type", "Unknown"),
                    **{k: str(v) for k, v in data.items() if k not in ["name", "node_type"]}
                }
            })

        for u, v, k, data in self.g.edges(data=True, keys=True):
            elements["edges"].append({
                "data": {
                    "id": f"{u}->{v}:{k}",
                    "source": str(u),
                    "target": str(v),
                    "relationship": data.get("rel", "TRANSACTED_WITH"),
                    **{key: str(val) for key, val in data.items() if key != "rel"}
                }
            })

        return elements


_global_fraud_graph: Optional[FraudGraph] = None


def get_fraud_graph(tenant_id: str = "default_tenant") -> FraudGraph:
    global _global_fraud_graph
    if _global_fraud_graph is None or _global_fraud_graph.tenant_id != tenant_id:
        _global_fraud_graph = FraudGraph(tenant_id=tenant_id)
    return _global_fraud_graph
