"""
Heterogeneous Graph Fraud Schema (Phase 4).

Defines:
- 7 Node Types: Customer, Account, Transaction, Device, IP, Merchant, Location
- 6 Relationship Types: OWNS, USES, TRANSACTED_WITH, LOCATED_AT, SHARES_DEVICE, SHARES_IP
- SuspiciousCluster data container for graph anomaly investigations
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


class NodeType(str, Enum):
    CUSTOMER = "Customer"
    ACCOUNT = "Account"
    TRANSACTION = "Transaction"
    DEVICE = "Device"
    IP = "IP"
    MERCHANT = "Merchant"
    LOCATION = "Location"


class EdgeType(str, Enum):
    OWNS = "OWNS"                         # Customer -> Account
    USES = "USES"                         # Customer/Account -> Device, Customer/Account -> IP
    TRANSACTED_WITH = "TRANSACTED_WITH"   # Account -> Transaction -> Account / Merchant
    LOCATED_AT = "LOCATED_AT"             # Transaction / Customer / IP -> Location
    SHARES_DEVICE = "SHARES_DEVICE"       # Account <-> Account (shared device infrastructure)
    SHARES_IP = "SHARES_IP"               # Account <-> Account (shared network IP)


@dataclass
class CustomerNode:
    id: str
    name: str
    kyc_status: str = "VERIFIED"          # VERIFIED, UNVERIFIED, PENDING, FAILED
    risk_tier: str = "LOW"                # LOW, MEDIUM, HIGH

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.CUSTOMER.value, **asdict(self)}


@dataclass
class AccountNode:
    id: str
    account_type: str = "CHECKING"        # CHECKING, COMMERCIAL, ESCROW, SAVINGS
    balance: float = 10000.0

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.ACCOUNT.value, **asdict(self)}


@dataclass
class TransactionNode:
    id: str
    amount: float
    currency: str = "USD"
    timestamp: str = ""
    channel: str = "ACH"                  # WIRE, ACH, CARD, RTP

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.TRANSACTION.value, **asdict(self)}


@dataclass
class DeviceNode:
    id: str
    os: str = "Windows"
    fingerprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.DEVICE.value, **asdict(self)}


@dataclass
class IPNode:
    id: str                               # e.g. "IP_192.168.1.1"
    ip_address: str
    is_vpn: bool = False
    is_tor: bool = False
    asn: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.IP.value, **asdict(self)}


@dataclass
class MerchantNode:
    id: str
    name: str
    category: str = "RETAIL"
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.MERCHANT.value, **asdict(self)}


@dataclass
class LocationNode:
    id: str
    country: str = "US"
    city: Optional[str] = None
    is_high_risk: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"node_type": NodeType.LOCATION.value, **asdict(self)}


@dataclass
class SuspiciousCluster:
    cluster_id: str
    cluster_type: str                     # device_sharing_ring, ip_syndicate, cycle_loop, scatter_gather_hub
    risk_score: float                     # 0.0 (benign) to 1.0 (critical fraud ring)
    node_ids: List[str]                   # Member node identifiers
    edge_types: List[str]                 # Relationships tying the cluster together
    metrics: Dict[str, Any]               # Graph metrics (density, shared_devices_count, accounts_count)
    signals: List[str]                    # Triggered risk signal tags
    explanation: str                      # Human-readable investigative synopsis

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_type": self.cluster_type,
            "risk_score": round(self.risk_score, 4),
            "node_ids": list(self.node_ids),
            "edge_types": list(self.edge_types),
            "metrics": self.metrics,
            "signals": list(self.signals),
            "explanation": self.explanation,
        }
