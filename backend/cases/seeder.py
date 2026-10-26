"""
Historical Case Database Seeder (Phase 3).

Populates the HistoricalCaseStore with 120+ structured precedent cases
encompassing regulatory compliance mandates, illicit laundering typologies,
and routine commercial/retail operations.
"""

import os
import sys
import datetime
from typing import List, Dict, Any
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.cases.schema import (
    TransactionFeatures,
    CustomerFeatures,
    MerchantFeatures,
    DeviceFeatures,
    LocationFeatures,
    BehaviorFeatures,
    CaseOutcome,
    HistoricalCase,
)
from backend.cases.database import HistoricalCaseStore, get_case_store


def seed_large_case_database(
    store: HistoricalCaseStore,
    tenant_id: str = "default_tenant",
    clear_existing: bool = False
) -> int:
    """
    Seeds 120+ complete historical cases spanning all mandatory dimensions:
    transaction + customer + merchant + device + location + behavior + outcome.
    """
    if clear_existing:
        store.clear(tenant_id=tenant_id)

    cases: List[HistoricalCase] = []
    base_t = datetime.datetime(2026, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # ---------------------------------------------------------
    # 1. Statutory CTR & High-Value Benign Commercial Cases (25 cases)
    # ---------------------------------------------------------
    commercial_sectors = [
        ("Industrial Steel Corp", "COMMERCIAL", 650000.0, "Global Minerals LLC", 85000.0, "Supplier invoice settlement for raw steel coils"),
        ("Horizon Title & Escrow", "ESCROW", 1250000.0, "First National Realty", 115000.0, "Commercial real estate escrow earnest deposit"),
        ("TechFlow Systems Inc", "PAYROLL", 450000.0, "ADP Payroll Trust", 92000.0, "Bi-weekly corporate executive payroll disbursement"),
        ("Metro Logistics Hub", "COMMERCIAL", 780000.0, "FreightRail Transport", 54000.0, "Intermodal container freight shipping fees"),
        ("Apex Cloud Services", "COMMERCIAL", 920000.0, "DataCenter Infrastructure", 76000.0, "Colocation facility expansion quarterly billing"),
    ]

    for idx, (c_name, acct_type, bal, cp_name, amt, narr) in enumerate(commercial_sectors):
        for sub_i in range(5):
            c_id = f"CASE_CTR_{idx}_{sub_i:02d}"
            case_amt = amt + (sub_i * 3500.0)
            offset_days = (idx * 5) + sub_i
            ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

            case = HistoricalCase(
                case_id=c_id,
                tenant_id=tenant_id,
                transaction=TransactionFeatures(
                    amount=case_amt,
                    currency="USD",
                    channel="WIRE",
                    timestamp=ts,
                    counterparty=cp_name,
                    is_round_hundred=True,
                    is_round_thousand=True,
                    is_statutory_threshold=True,
                    is_structuring_heuristic=False
                ),
                customer=CustomerFeatures(
                    customer_id=f"CUST_CORP_{idx}_{sub_i}",
                    name=c_name,
                    account_type=acct_type,
                    balance=bal,
                    kyc_status="VERIFIED",
                    risk_tier="LOW",
                    country="US",
                    tenure_months=36
                ),
                merchant=MerchantFeatures(
                    name=cp_name,
                    category="SERVICES",
                    historical_fraud_rate=0.001
                ),
                device=DeviceFeatures(
                    os="Linux",
                    browser="Chrome Enterprise",
                    is_vpn=False,
                    is_new_device=False
                ),
                location=LocationFeatures(
                    country="US",
                    city="New York",
                    ip_country="US",
                    is_high_risk_jurisdiction=False
                ),
                behavior=BehaviorFeatures(
                    velocity_1h_count=1,
                    velocity_sum_1h=case_amt,
                    velocity_24h_count=1,
                    velocity_sum_24h=case_amt,
                    amount_to_avg_ratio=1.05,
                    is_high_velocity_burst=False,
                    cycle_score=0.0,
                    has_cycle=False,
                    scatter_gather_score=0.0,
                    has_scatter_gather=False,
                    counterparties_count=3
                ),
                outcome=CaseOutcome(
                    disposition="CLEARED_CTR",
                    typology="benign_commercial_payroll",
                    narrative=f"Legitimate commercial wire of ${case_amt:,.2f}. {narr}. Verified corporate customer, standard counterparty, zero velocity anomalies. Statutory CTR filed under 31 CFR § 1010.311 and adjudicated BENIGN.",
                    ground_truth_score=0.02,
                    adjudicated_at=ts,
                    audit_notes="Mandatory CTR audit log created; laundering risk ruled out."
                ),
                tags=["commercial", "statutory_ctr", "benign", "wire"]
            )
            cases.append(case)

    # ---------------------------------------------------------
    # 2. Structuring & Smurfing Avoidance Patterns (25 cases)
    # ---------------------------------------------------------
    for i in range(25):
        c_id = f"CASE_STRUCT_{i:03d}"
        amt = float(round(8600.0 + (i * 50.0), 2))
        offset_days = i * 2
        ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

        case = HistoricalCase(
            case_id=c_id,
            tenant_id=tenant_id,
            transaction=TransactionFeatures(
                amount=amt,
                currency="USD",
                channel="ACH",
                timestamp=ts,
                counterparty=f"MULE_DEST_{i}",
                is_round_hundred=False,
                is_round_thousand=False,
                is_statutory_threshold=False,
                is_structuring_heuristic=True
            ),
            customer=CustomerFeatures(
                customer_id=f"CUST_STR_{i}",
                name=f"Individual Retail Customer {i}",
                account_type="CHECKING",
                balance=14500.0,
                kyc_status="UNVERIFIED" if i % 2 == 0 else "MEDIUM",
                risk_tier="HIGH",
                country="US",
                tenure_months=3
            ),
            merchant=MerchantFeatures(
                name="QuickTransfer Remit",
                category="MONEY_TRANSFER",
                historical_fraud_rate=0.045
            ),
            device=DeviceFeatures(
                os="Android",
                browser="Mobile Safari",
                is_vpn=True,
                is_new_device=True
            ),
            location=LocationFeatures(
                country="US",
                city="Miami",
                ip_country="US",
                is_high_risk_jurisdiction=False
            ),
            behavior=BehaviorFeatures(
                velocity_1h_count=2,
                velocity_sum_1h=amt * 2,
                velocity_24h_count=4,
                velocity_sum_24h=amt * 4,
                amount_to_avg_ratio=4.8,
                is_high_velocity_burst=True,
                cycle_score=0.0,
                has_cycle=False,
                scatter_gather_score=0.0,
                has_scatter_gather=False,
                counterparties_count=2
            ),
            outcome=CaseOutcome(
                disposition="CONFIRMED_FRAUD",
                typology="structuring_smurfing",
                narrative=f"Intentional structuring heuristic detected. Transaction of ${amt:,.2f} purposefully positioned below the $10,000 statutory CTR recordkeeping threshold. Account exhibited 4 rapid transfers totaling over ${amt*4:,.2f} in 24 hours. SAR filed under 31 U.S.C. § 5324.",
                ground_truth_score=0.92,
                adjudicated_at=ts,
                audit_notes="SAR narrative submitted to FinCEN."
            ),
            tags=["structuring", "smurfing", "fraud", "sar_filed"]
        )
        cases.append(case)

    # ---------------------------------------------------------
    # 3. Directed Cycle Laundering Topologies (20 cases)
    # ---------------------------------------------------------
    for i in range(20):
        c_id = f"CASE_CYCLE_{i:03d}"
        amt = float(round(15000.0 + (i * 1200.0), 2))
        c_score = float(round(0.55 + (i % 5) * 0.08, 2))
        offset_days = i * 3
        ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

        case = HistoricalCase(
            case_id=c_id,
            tenant_id=tenant_id,
            transaction=TransactionFeatures(
                amount=amt,
                currency="USD",
                channel="WIRE",
                timestamp=ts,
                counterparty=f"SHELL_CO_{i}",
                is_round_hundred=True,
                is_round_thousand=True,
                is_statutory_threshold=True,
                is_structuring_heuristic=False
            ),
            customer=CustomerFeatures(
                customer_id=f"CUST_CYC_{i}",
                name=f"Trade Holdings Entity {i}",
                account_type="CHECKING",
                balance=42000.0,
                kyc_status="UNVERIFIED",
                risk_tier="HIGH",
                country="US",
                tenure_months=2
            ),
            merchant=MerchantFeatures(
                name="Offshore Trade Services",
                category="FINANCIAL",
                historical_fraud_rate=0.065
            ),
            device=DeviceFeatures(
                os="Unknown OS",
                browser="Unknown",
                is_vpn=True,
                is_new_device=True
            ),
            location=LocationFeatures(
                country="US",
                ip_country="PA",
                is_high_risk_jurisdiction=True
            ),
            behavior=BehaviorFeatures(
                velocity_1h_count=2,
                velocity_sum_1h=amt * 2,
                velocity_24h_count=3,
                velocity_sum_24h=amt * 3,
                amount_to_avg_ratio=5.2,
                is_high_velocity_burst=True,
                cycle_score=c_score,
                has_cycle=True,
                scatter_gather_score=0.0,
                has_scatter_gather=False,
                counterparties_count=3
            ),
            outcome=CaseOutcome(
                disposition="CONFIRMED_FRAUD",
                typology="cycle_laundering",
                narrative=f"Directed circular laundering network detected. Transfer of ${amt:,.2f} participates in a closed multi-hop circular flow (cycle score {c_score:.2f}) routing funds back to the originating entity across 3 intermediate shell accounts. Immediate SAR escalation.",
                ground_truth_score=0.96,
                adjudicated_at=ts,
                audit_notes="Graph cycle confirmed by multi-hop graph analysis."
            ),
            tags=["cycle", "laundering", "graph", "shell_company"]
        )
        cases.append(case)

    # ---------------------------------------------------------
    # 4. Scatter-Gather / Mule Dispersion Topologies (20 cases)
    # ---------------------------------------------------------
    for i in range(20):
        c_id = f"CASE_SG_{i:03d}"
        amt = float(round(12000.0 + (i * 900.0), 2))
        sg_score = float(round(0.50 + (i % 4) * 0.10, 2))
        offset_days = i * 2
        ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

        case = HistoricalCase(
            case_id=c_id,
            tenant_id=tenant_id,
            transaction=TransactionFeatures(
                amount=amt,
                currency="USD",
                channel="WIRE",
                timestamp=ts,
                counterparty=f"MULE_HUB_{i}",
                is_round_hundred=False,
                is_round_thousand=False,
                is_statutory_threshold=True,
                is_structuring_heuristic=False
            ),
            customer=CustomerFeatures(
                customer_id=f"CUST_SG_{i}",
                name=f"Intermediary Logistics Account {i}",
                account_type="CHECKING",
                balance=28000.0,
                kyc_status="UNVERIFIED",
                risk_tier="HIGH",
                country="US",
                tenure_months=1
            ),
            merchant=MerchantFeatures(
                name="P2P Remittance Gateway",
                category="PAYMENTS",
                historical_fraud_rate=0.05
            ),
            device=DeviceFeatures(
                os="Linux",
                browser="Chrome",
                is_vpn=True,
                is_new_device=True
            ),
            location=LocationFeatures(
                country="US",
                ip_country="CY",
                is_high_risk_jurisdiction=False
            ),
            behavior=BehaviorFeatures(
                velocity_1h_count=3,
                velocity_sum_1h=amt * 3,
                velocity_24h_count=6,
                velocity_sum_24h=amt * 5,
                amount_to_avg_ratio=6.0,
                is_high_velocity_burst=True,
                cycle_score=0.0,
                has_cycle=False,
                scatter_gather_score=sg_score,
                has_scatter_gather=True,
                counterparties_count=6
            ),
            outcome=CaseOutcome(
                disposition="CONFIRMED_FRAUD",
                typology="scatter_gather",
                narrative=f"Rapid pass-through and mule dispersion detected. Incoming lump sum split and scattered across 6 disparate mule accounts within 45 minutes (scatter-gather score {sg_score:.2f}). Total layered amount exceeds ${amt*3:,.2f}.",
                ground_truth_score=0.94,
                adjudicated_at=ts,
                audit_notes="Confirmed money mule network; accounts frozen."
            ),
            tags=["scatter_gather", "mule", "layering", "p2p"]
        )
        cases.append(case)

    # ---------------------------------------------------------
    # 5. Account Takeover (ATO) & Geolocation Jump (15 cases)
    # ---------------------------------------------------------
    for i in range(15):
        c_id = f"CASE_ATO_{i:03d}"
        amt = float(round(4200.0 + (i * 350.0), 2))
        offset_days = i * 4
        ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

        case = HistoricalCase(
            case_id=c_id,
            tenant_id=tenant_id,
            transaction=TransactionFeatures(
                amount=amt,
                currency="USD",
                channel="ACH",
                timestamp=ts,
                counterparty=f"CRYPTO_OFFSHORE_{i}",
                is_round_hundred=True,
                is_round_thousand=False,
                is_statutory_threshold=False,
                is_structuring_heuristic=False
            ),
            customer=CustomerFeatures(
                customer_id=f"CUST_ATO_{i}",
                name=f"Compromised Account Holder {i}",
                account_type="CHECKING",
                balance=18000.0,
                kyc_status="VERIFIED",
                risk_tier="LOW",
                country="US",
                tenure_months=48
            ),
            merchant=MerchantFeatures(
                name="Offshore Crypto Exchange",
                category="CRYPTO",
                historical_fraud_rate=0.095
            ),
            device=DeviceFeatures(
                os="Unknown OS",
                browser="Tor Browser",
                is_vpn=True,
                is_new_device=True
            ),
            location=LocationFeatures(
                country="RU",
                city="Moscow",
                ip_country="RU",
                is_high_risk_jurisdiction=True
            ),
            behavior=BehaviorFeatures(
                velocity_1h_count=3,
                velocity_sum_1h=amt * 3,
                velocity_24h_count=4,
                velocity_sum_24h=amt * 4,
                amount_to_avg_ratio=8.5,
                is_high_velocity_burst=True,
                cycle_score=0.0,
                has_cycle=False,
                scatter_gather_score=0.0,
                has_scatter_gather=False,
                counterparties_count=1
            ),
            outcome=CaseOutcome(
                disposition="CONFIRMED_FRAUD",
                typology="account_takeover",
                narrative=f"Account takeover (ATO) fraud. Credential stuffing led to password reset followed by instant ${amt:,.2f} transfer. Device was unknown OS via Tor from high-risk jurisdiction (RU) within 15 minutes of customer active session in US.",
                ground_truth_score=0.98,
                adjudicated_at=ts,
                audit_notes="Account restored to original owner; fraudulent wire blocked."
            ),
            tags=["account_takeover", "ato", "credential_stuffing", "crypto"]
        )
        cases.append(case)

    # ---------------------------------------------------------
    # 6. Retail Expenses & False Positive Spikes (20 cases)
    # ---------------------------------------------------------
    for i in range(20):
        c_id = f"CASE_RETAIL_{i:03d}"
        amt = float(round(45.0 + (i * 22.5), 2))
        offset_days = i
        ts = (base_t - datetime.timedelta(days=offset_days)).isoformat()

        case = HistoricalCase(
            case_id=c_id,
            tenant_id=tenant_id,
            transaction=TransactionFeatures(
                amount=amt,
                currency="USD",
                channel="ACH",
                timestamp=ts,
                counterparty=f"RETAIL_STORE_{i}",
                is_round_hundred=False,
                is_round_thousand=False,
                is_statutory_threshold=False,
                is_structuring_heuristic=False
            ),
            customer=CustomerFeatures(
                customer_id=f"CUST_RET_{i}",
                name=f"Everyday Shopper {i}",
                account_type="CHECKING",
                balance=5200.0,
                kyc_status="VERIFIED",
                risk_tier="LOW",
                country="US",
                tenure_months=24
            ),
            merchant=MerchantFeatures(
                name="Corner Grocery & Pharmacy",
                category="RETAIL",
                historical_fraud_rate=0.002
            ),
            device=DeviceFeatures(
                os="iOS",
                browser="Mobile Safari",
                is_vpn=False,
                is_new_device=False
            ),
            location=LocationFeatures(
                country="US",
                city="Chicago",
                ip_country="US",
                is_high_risk_jurisdiction=False
            ),
            behavior=BehaviorFeatures(
                velocity_1h_count=1,
                velocity_sum_1h=amt,
                velocity_24h_count=2,
                velocity_sum_24h=amt * 1.5,
                amount_to_avg_ratio=1.0,
                is_high_velocity_burst=False,
                cycle_score=0.0,
                has_cycle=False,
                scatter_gather_score=0.0,
                has_scatter_gather=False,
                counterparties_count=2
            ),
            outcome=CaseOutcome(
                disposition="CONFIRMED_BENIGN",
                typology="benign_retail_expense",
                narrative=f"Normal everyday consumer grocery transaction of ${amt:,.2f}. Verified iOS device, matching residential IP address, low risk tier. Adjudicated BENIGN.",
                ground_truth_score=0.01,
                adjudicated_at=ts,
                audit_notes="Routine retail expense."
            ),
            tags=["retail", "grocery", "benign", "consumer"]
        )
        cases.append(case)

    # Batch persist all cases
    count = store.add_cases(cases)
    print(f"Seeded {count} comprehensive historical cases into {store.db_path} (tenant: {tenant_id})")
    return count


if __name__ == "__main__":
    store = get_case_store()
    seed_large_case_database(store, clear_existing=True)
