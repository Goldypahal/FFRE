"""
Synthetic Data Generator for FFIRE Benchmarks.
Generates schema-compliant, deterministic synthetic financial entities and transactions
with configurable fraud archetypes, random seeds, and export capabilities.
"""

import os
import sys
import csv
import json
import random
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Ensure backend can be imported
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import models

class FraudArchetype(str, Enum):
    BENIGN = "BENIGN"
    HIGH_VELOCITY_BURST = "HIGH_VELOCITY_BURST"
    GEOGRAPHIC_IMPOSSIBILITY = "GEOGRAPHIC_IMPOSSIBILITY"
    AMOUNT_ANOMALY = "AMOUNT_ANOMALY"
    NEW_DEVICE_ATO = "NEW_DEVICE_ATO"
    STRUCTURING_SMURFING = "STRUCTURING_SMURFING"

@dataclass
class GeneratedDataset:
    tenant_id: str
    customers: List[Dict[str, Any]] = field(default_factory=list)
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    merchants: List[Dict[str, Any]] = field(default_factory=list)
    devices: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        archetypes = {}
        for t in self.transactions:
            arch = t.get("archetype", "UNKNOWN")
            archetypes[arch] = archetypes.get(arch, 0) + 1
        return {
            "tenant_id": self.tenant_id,
            "total_customers": len(self.customers),
            "total_accounts": len(self.accounts),
            "total_merchants": len(self.merchants),
            "total_transactions": len(self.transactions),
            "archetype_distribution": archetypes
        }

class SyntheticDataGenerator:
    """Deterministic synthetic data generator for FFIRE open benchmarks."""

    FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", "Isla", "Jack"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    MERCHANT_NAMES = [
        ("Apex Supermarket", "GROCERY", 0.02),
        ("Corner Coffee", "DINING", 0.01),
        ("Metro Transit", "TRANSPORTATION", 0.01),
        ("Global Airlines", "TRAVEL", 0.15),
        ("CyberTech Direct", "ELECTRONICS", 0.35),
        ("Luxury Jewelers", "LUXURY", 0.65),
        ("CryptoExchange X", "CRYPTO", 0.85),
        ("Midnight Casino Online", "GAMBLING", 0.90)
    ]

    def __init__(self, seed: int = 42, tenant_id: str = "benchmark_tenant"):
        self.seed = seed
        self.tenant_id = tenant_id
        self.rng = random.Random(seed)

    def generate_dataset(
        self,
        num_customers: int = 10,
        txns_per_customer: int = 5,
        fraud_ratio: float = 0.25,
        base_timestamp: Optional[datetime.datetime] = None
    ) -> GeneratedDataset:
        """Generates a complete relational graph of synthetic banking entities and transactions."""
        if base_timestamp is None:
            base_timestamp = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

        dataset = GeneratedDataset(tenant_id=self.tenant_id)

        # 1. Generate Merchants
        for idx, (m_name, m_cat, m_risk) in enumerate(self.MERCHANT_NAMES):
            dataset.merchants.append({
                "merchant_id": f"m_bench_{idx+1:03d}",
                "name": m_name,
                "category": m_cat,
                "risk_score": m_risk,
                "tenant_id": self.tenant_id
            })

        # 2. Generate Customers and Accounts
        txn_counter = 1
        for c_idx in range(num_customers):
            c_id = f"c_bench_{c_idx+1:04d}"
            name = f"{self.rng.choice(self.FIRST_NAMES)} {self.rng.choice(self.LAST_NAMES)}"
            kyc_status = "VERIFIED" if self.rng.random() > 0.1 else "PENDING"
            risk_tier = "HIGH" if self.rng.random() < 0.15 else "LOW"

            customer = {
                "customer_id": c_id,
                "name": name,
                "kyc_status": kyc_status,
                "risk_tier": risk_tier,
                "tenant_id": self.tenant_id
            }
            dataset.customers.append(customer)

            a_id = f"a_bench_{c_idx+1:04d}"
            account = {
                "account_id": a_id,
                "customer_id": c_id,
                "tenant_id": self.tenant_id,
                "balance": round(self.rng.uniform(1500.0, 45000.0), 2),
                "status": "ACTIVE"
            }
            dataset.accounts.append(account)

            # Known primary device
            d_id = f"dev_bench_{c_idx+1:04d}"
            dataset.devices.append({
                "device_id": d_id,
                "customer_id": c_id,
                "os": "iOS" if self.rng.random() > 0.5 else "Windows",
                "ip_address": f"198.51.100.{c_idx+1}",
                "fingerprint": f"fp_bench_{c_idx+1:04d}",
                "tenant_id": self.tenant_id
            })

            # Home location
            dataset.locations.append({
                "location_id": f"loc_bench_{c_idx+1:04d}",
                "geo_coord": f"{40.7128 + self.rng.uniform(-0.05, 0.05):.4f},{-74.0060 + self.rng.uniform(-0.05, 0.05):.4f}",
                "country": "USA",
                "tenant_id": self.tenant_id
            })

            # 3. Generate Transactions for Customer
            for t_idx in range(txns_per_customer):
                is_fraud = self.rng.random() < fraud_ratio
                t_id = f"TXN_BENCH_{txn_counter:06d}"
                txn_counter += 1

                t_time = base_timestamp + datetime.timedelta(
                    days=self.rng.randint(0, 6),
                    hours=self.rng.randint(0, 23),
                    minutes=self.rng.randint(0, 59)
                )

                if not is_fraud:
                    archetype = FraudArchetype.BENIGN
                    merch = self.rng.choice(dataset.merchants[:4])  # low risk
                    amount = round(self.rng.uniform(12.50, 185.00), 2)
                    ip = f"198.51.100.{c_idx+1}"
                    dev_ref = d_id
                    channel = "POS" if self.rng.random() > 0.5 else "ONLINE"
                else:
                    # Pick an anomalous archetype
                    archetype = self.rng.choice([
                        FraudArchetype.HIGH_VELOCITY_BURST,
                        FraudArchetype.GEOGRAPHIC_IMPOSSIBILITY,
                        FraudArchetype.AMOUNT_ANOMALY,
                        FraudArchetype.NEW_DEVICE_ATO,
                        FraudArchetype.STRUCTURING_SMURFING
                    ])

                    if archetype == FraudArchetype.AMOUNT_ANOMALY:
                        merch = self.rng.choice(dataset.merchants[4:])  # high risk
                        amount = round(self.rng.uniform(4500.0, 18000.0), 2)
                        ip = f"198.51.100.{c_idx+1}"
                        dev_ref = d_id
                        channel = "ONLINE"
                    elif archetype == FraudArchetype.NEW_DEVICE_ATO:
                        merch = self.rng.choice(dataset.merchants[4:])
                        amount = round(self.rng.uniform(2200.0, 7500.0), 2)
                        ip = f"203.0.113.{self.rng.randint(10, 250)}"  # Foreign unknown IP
                        dev_ref = f"dev_foreign_{txn_counter}"
                        channel = "ONLINE"
                    elif archetype == FraudArchetype.STRUCTURING_SMURFING:
                        merch = self.rng.choice(dataset.merchants[:4])
                        amount = round(self.rng.uniform(9700.0, 9950.0), 2)
                        ip = f"198.51.100.{c_idx+1}"
                        dev_ref = d_id
                        channel = "BRANCH"
                    elif archetype == FraudArchetype.GEOGRAPHIC_IMPOSSIBILITY:
                        merch = self.rng.choice(dataset.merchants[3:6])
                        amount = round(self.rng.uniform(450.0, 1900.0), 2)
                        ip = f"185.220.101.{self.rng.randint(1, 200)}"
                        dev_ref = f"dev_travel_{txn_counter}"
                        channel = "ATM"
                    else:  # HIGH_VELOCITY_BURST
                        merch = self.rng.choice(dataset.merchants[4:7])
                        amount = round(self.rng.uniform(300.0, 950.0), 2)
                        ip = f"198.51.100.{c_idx+1}"
                        dev_ref = d_id
                        channel = "ONLINE"

                dataset.transactions.append({
                    "txn_id": t_id,
                    "account_id": a_id,
                    "merchant_id": merch["merchant_id"],
                    "amount": amount,
                    "currency": "USD",
                    "channel": channel,
                    "ip_address": ip,
                    "device_ref": dev_ref,
                    "counterparty": merch["name"],
                    "timestamp": t_time.isoformat(),
                    "tenant_id": self.tenant_id,
                    "archetype": archetype.value,
                    "status": "PENDING"
                })

        return dataset

    @staticmethod
    def export_csv(dataset: GeneratedDataset, output_path: str):
        """Exports transactions to standard RFC-4180 CSV format."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        headers = ["txn_id", "account_id", "merchant_id", "amount", "currency", "channel", "ip_address", "device_ref", "counterparty", "timestamp"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for t in dataset.transactions:
                writer.writerow(t)

    @staticmethod
    def export_json(dataset: GeneratedDataset, output_path: str):
        """Exports dataset to formatted JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": dataset.summary(),
                "customers": dataset.customers,
                "accounts": dataset.accounts,
                "merchants": dataset.merchants,
                "devices": dataset.devices,
                "locations": dataset.locations,
                "transactions": dataset.transactions
            }, f, indent=2)

    @staticmethod
    def seed_to_db(dataset: GeneratedDataset, db_session) -> Dict[str, int]:
        """Seeds generated dataset directly into database session with idempotency."""
        inserted = {"customers": 0, "accounts": 0, "merchants": 0, "transactions": 0, "devices": 0, "locations": 0}

        # Merchants
        for m_data in dataset.merchants:
            existing = db_session.query(models.Merchant).filter(models.Merchant.merchant_id == m_data["merchant_id"]).first()
            if not existing:
                clean_m = {k: v for k, v in m_data.items() if hasattr(models.Merchant, k)}
                db_session.add(models.Merchant(**clean_m))
                inserted["merchants"] += 1

        # Customers
        for c_data in dataset.customers:
            existing = db_session.query(models.Customer).filter(models.Customer.customer_id == c_data["customer_id"]).first()
            if not existing:
                clean_c = {k: v for k, v in c_data.items() if hasattr(models.Customer, k)}
                db_session.add(models.Customer(**clean_c))
                inserted["customers"] += 1

        # Accounts
        for a_data in dataset.accounts:
            existing = db_session.query(models.Account).filter(models.Account.account_id == a_data["account_id"]).first()
            if not existing:
                clean_a = {k: v for k, v in a_data.items() if hasattr(models.Account, k)}
                db_session.add(models.Account(**clean_a))
                inserted["accounts"] += 1

        # Devices
        for d_data in dataset.devices:
            existing = db_session.query(models.Device).filter(models.Device.device_id == d_data["device_id"]).first()
            if not existing:
                clean_d = {k: v for k, v in d_data.items() if hasattr(models.Device, k)}
                db_session.add(models.Device(**clean_d))
                inserted["devices"] += 1

        # Locations
        for l_data in dataset.locations:
            existing = db_session.query(models.Location).filter(models.Location.location_id == l_data["location_id"]).first()
            if not existing:
                clean_l = {k: v for k, v in l_data.items() if hasattr(models.Location, k)}
                db_session.add(models.Location(**clean_l))
                inserted["locations"] += 1

        # Transactions
        for t_data in dataset.transactions:
            existing = db_session.query(models.Transaction).filter(models.Transaction.txn_id == t_data["txn_id"]).first()
            if not existing:
                clean_t = {k: v for k, v in t_data.items() if hasattr(models.Transaction, k)}
                if "timestamp" in clean_t and isinstance(clean_t["timestamp"], str):
                    clean_t["timestamp"] = datetime.datetime.fromisoformat(clean_t["timestamp"])
                db_session.add(models.Transaction(**clean_t))
                inserted["transactions"] += 1

        db_session.commit()
        return inserted
