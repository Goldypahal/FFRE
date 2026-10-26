"""
Historical Case Schema & Search Data Models (Phase 3).

Defines the 7-part comprehensive historical case data model:
1. Transaction features
2. Customer features
3. Merchant features
4. Device features
5. Location features
6. Behavior features
7. Case outcome

Plus queries and results for the 4-way Hybrid Search Engine.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import datetime


@dataclass
class TransactionFeatures:
    amount: float
    currency: str = "USD"
    channel: str = "ACH"               # WIRE, ACH, CARD, CASH, RTP
    timestamp: str = ""                 # ISO 8601 UTC
    counterparty: Optional[str] = None
    is_round_hundred: bool = False
    is_round_thousand: bool = False
    is_statutory_threshold: bool = False     # >= $10,000 (CTR mandate)
    is_structuring_heuristic: bool = False   # $8,000 - $9,999 (avoidance proxy)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CustomerFeatures:
    customer_id: str
    name: str
    account_type: str = "CHECKING"     # CHECKING, COMMERCIAL, SAVINGS, ESCROW, PAYROLL
    balance: float = 10000.0
    kyc_status: str = "VERIFIED"       # VERIFIED, UNVERIFIED, PENDING, FAILED
    risk_tier: str = "LOW"             # LOW, MEDIUM, HIGH
    country: str = "US"
    tenure_months: int = 12

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MerchantFeatures:
    merchant_id: Optional[str] = None
    name: Optional[str] = None
    mcc: Optional[str] = None
    category: str = "RETAIL"           # RETAIL, TRAVEL, ELECTRONICS, GAMBLING, CRYPTO, UTILITIES, SERVICES
    historical_fraud_rate: float = 0.0
    dispute_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceFeatures:
    device_id: Optional[str] = None
    os: str = "Windows"
    browser: Optional[str] = "Chrome"
    ip_address: Optional[str] = None
    is_vpn: bool = False
    is_new_device: bool = False
    fingerprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LocationFeatures:
    country: str = "US"
    city: Optional[str] = None
    ip_country: Optional[str] = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_high_risk_jurisdiction: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BehaviorFeatures:
    velocity_1h_count: int = 0
    velocity_sum_1h: float = 0.0
    velocity_24h_count: int = 0
    velocity_sum_24h: float = 0.0
    velocity_7d_count: int = 0
    velocity_sum_7d: float = 0.0
    amount_to_avg_ratio: float = 1.0
    is_high_velocity_burst: bool = False
    cycle_score: float = 0.0
    has_cycle: bool = False
    scatter_gather_score: float = 0.0
    has_scatter_gather: bool = False
    counterparties_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CaseOutcome:
    disposition: str                   # CONFIRMED_FRAUD, CONFIRMED_BENIGN, FALSE_POSITIVE, FILED_SAR, CLEARED_CTR
    typology: str                      # structuring_smurfing, cycle_laundering, scatter_gather, account_takeover, etc.
    narrative: str                     # Detailed investigative synopsis of why this case was adjudicated
    ground_truth_score: float          # 0.0 (benign) to 1.0 (fraud)
    adjudicated_at: Optional[str] = None
    audit_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HistoricalCase:
    case_id: str
    tenant_id: str = "default_tenant"
    transaction: TransactionFeatures = field(default_factory=lambda: TransactionFeatures(amount=0.0))
    customer: CustomerFeatures = field(default_factory=lambda: CustomerFeatures(customer_id="C000", name="Unknown"))
    merchant: MerchantFeatures = field(default_factory=lambda: MerchantFeatures())
    device: DeviceFeatures = field(default_factory=lambda: DeviceFeatures())
    location: LocationFeatures = field(default_factory=lambda: LocationFeatures())
    behavior: BehaviorFeatures = field(default_factory=lambda: BehaviorFeatures())
    outcome: CaseOutcome = field(default_factory=lambda: CaseOutcome(disposition="UNKNOWN", typology="none", narrative="", ground_truth_score=0.0))
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "tenant_id": self.tenant_id,
            "transaction": self.transaction.to_dict(),
            "customer": self.customer.to_dict(),
            "merchant": self.merchant.to_dict(),
            "device": self.device.to_dict(),
            "location": self.location.to_dict(),
            "behavior": self.behavior.to_dict(),
            "outcome": self.outcome.to_dict(),
            "created_at": self.created_at,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoricalCase":
        return cls(
            case_id=data["case_id"],
            tenant_id=data.get("tenant_id", "default_tenant"),
            transaction=TransactionFeatures(**data.get("transaction", {"amount": 0.0})),
            customer=CustomerFeatures(**data.get("customer", {"customer_id": "C000", "name": "Unknown"})),
            merchant=MerchantFeatures(**data.get("merchant", {})),
            device=DeviceFeatures(**data.get("device", {})),
            location=LocationFeatures(**data.get("location", {})),
            behavior=BehaviorFeatures(**data.get("behavior", {})),
            outcome=CaseOutcome(**data.get("outcome", {"disposition": "UNKNOWN", "typology": "none", "narrative": "", "ground_truth_score": 0.0})),
            created_at=data.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            tags=data.get("tags", []),
        )

    def generate_search_document(self) -> str:
        """Constructs an information-dense text summary for vector similarity embedding."""
        t = self.transaction
        c = self.customer
        m = self.merchant
        d = self.device
        l = self.location
        b = self.behavior
        o = self.outcome

        doc = (
            f"Case {self.case_id} [{o.disposition} / {o.typology}]. "
            f"Transaction of {t.amount:,.2f} {t.currency} via {t.channel} for customer {c.name} "
            f"({c.account_type}, KYC {c.kyc_status}, Risk Tier {c.risk_tier}). "
            f"Merchant: {m.name or 'N/A'} ({m.category}, Fraud Rate: {m.historical_fraud_rate*100:.1f}%). "
            f"Device: {d.os} (New Device: {d.is_new_device}, VPN: {d.is_vpn}). "
            f"Location: {l.country} (IP Country: {l.ip_country}, High-Risk Juris: {l.is_high_risk_jurisdiction}). "
            f"Behavior: 1h velocity count {b.velocity_1h_count} (sum ${b.velocity_sum_1h:,.2f}), "
            f"24h velocity count {b.velocity_24h_count} (sum ${b.velocity_sum_24h:,.2f}), "
            f"Cycle Score: {b.cycle_score:.2f}, Scatter-Gather Score: {b.scatter_gather_score:.2f}. "
            f"Investigation Narrative: {o.narrative}"
        )
        return doc


@dataclass
class HybridSearchQuery:
    query_text: Optional[str] = None
    transaction_amount: Optional[float] = None
    channel: Optional[str] = None
    currency: Optional[str] = None
    timestamp: Optional[str] = None
    estimated_risk: Optional[float] = None
    tenant_id: str = "default_tenant"
    filter_dispositions: Optional[List[str]] = None
    filter_typologies: Optional[List[str]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    top_k: int = 5
    weight_vector: float = 0.40
    weight_temporal: float = 0.20
    weight_risk: float = 0.40


@dataclass
class HybridSearchResult:
    case_id: str
    tenant_id: str
    case: HistoricalCase
    vector_similarity: float
    temporal_similarity: float
    risk_similarity: float
    hybrid_score: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "tenant_id": self.tenant_id,
            "vector_similarity": round(self.vector_similarity, 4),
            "temporal_similarity": round(self.temporal_similarity, 4),
            "risk_similarity": round(self.risk_similarity, 4),
            "hybrid_score": round(self.hybrid_score, 4),
            "disposition": self.case.outcome.disposition,
            "typology": self.case.outcome.typology,
            "narrative": self.case.outcome.narrative,
            "explanation": self.explanation,
            "case": self.case.to_dict(),
        }
