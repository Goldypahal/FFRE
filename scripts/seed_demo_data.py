"""
FFIRE Synthetic Demo Data Seeder (Task T0.2)
Generates clearly synthetic, non-PII records under an explicit tenant.
Used by tests, benchmark harnesses, and local development.
"""

import os
import sys
import argparse
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import models
from database import SessionLocal, init_db


def seed_transaction(
    db: Session,
    txn_id: str,
    tenant_id: str = "default_tenant",
    amount: float = 1250.00,
    currency: str = "USD",
    customer_id: Optional[str] = None,
    customer_name: str = "Synthetic Test Customer",
    merchant_id: Optional[str] = None,
    merchant_name: str = "Synthetic Retail Store",
    merchant_category: str = "RETAIL",
    merchant_risk: float = 0.05,
    device_id: Optional[str] = None,
    device_fingerprint: str = "synthetic-device-fp-001",
    os_name: str = "SyntheticOS-1.0",
    country: str = "US",
    geo_coord: str = "37.7749, -122.4194",
    include_device: bool = True,
    include_location: bool = True
) -> models.Transaction:
    """
    Creates a complete, clearly synthetic relational transaction fixture
    (Customer, Account, Merchant, Transaction, Device, Location) under the specified tenant.
    """
    cid = customer_id or f"c_syn_{txn_id}"
    cust = db.query(models.Customer).filter(
        models.Customer.customer_id == cid,
        models.Customer.tenant_id == tenant_id
    ).first()
    if not cust:
        cust = models.Customer(
            customer_id=cid,
            tenant_id=tenant_id,
            name=customer_name,
            kyc_status="VERIFIED",
            risk_tier="LOW"
        )
        db.add(cust)
        db.flush()

    aid = f"a_syn_{txn_id}"
    acct = db.query(models.Account).filter(
        models.Account.account_id == aid,
        models.Account.tenant_id == tenant_id
    ).first()
    if not acct:
        acct = models.Account(
            account_id=aid,
            tenant_id=tenant_id,
            customer_id=cust.customer_id,
            account_type="CHECKING",
            balance=10000.00
        )
        db.add(acct)
        db.flush()

    mid = merchant_id or f"m_syn_{txn_id}"
    merch = db.query(models.Merchant).filter(
        models.Merchant.merchant_id == mid,
        models.Merchant.tenant_id == tenant_id
    ).first()
    if not merch:
        merch = models.Merchant(
            merchant_id=mid,
            tenant_id=tenant_id,
            name=merchant_name,
            category=merchant_category,
            risk_score=merchant_risk
        )
        db.add(merch)
        db.flush()

    # Pre-create or fetch transaction
    txn = db.query(models.Transaction).filter(
        models.Transaction.txn_id == txn_id,
        models.Transaction.tenant_id == tenant_id
    ).first()
    if not txn:
        txn = models.Transaction(
            txn_id=txn_id,
            tenant_id=tenant_id,
            account_id=acct.account_id,
            merchant_id=merch.merchant_id,
            amount=amount,
            currency=currency,
            status="PENDING"
        )
        db.add(txn)
        db.flush()

    # Device
    if include_device:
        did = device_id or f"dev_syn_{txn_id}"
        dev = db.query(models.Device).filter(
            models.Device.device_id == did,
            models.Device.tenant_id == tenant_id
        ).first()
        if not dev:
            dev = models.Device(
                device_id=did,
                tenant_id=tenant_id,
                customer_id=cust.customer_id,
                os=os_name,
                ip_address="192.0.2.1"
            )
            dev.fingerprint = device_fingerprint
            db.add(dev)
            db.flush()

    # Location
    if include_location:
        loc_id = f"loc_syn_{txn_id}"
        loc = db.query(models.Location).filter(
            models.Location.location_id == loc_id,
            models.Location.tenant_id == tenant_id
        ).first()
        if not loc:
            loc = models.Location(
                location_id=loc_id,
                tenant_id=tenant_id,
                txn_id=txn.txn_id,
                geo_coord=geo_coord,
                country=country
            )
            db.add(loc)
            db.flush()

    db.commit()
    db.refresh(txn)
    return txn


def seed_demo_suite(tenant_id: str = "demo_tenant", count: int = 5):
    """CLI seed function to populate sample synthetic records."""
    init_db()
    db = SessionLocal()
    try:
        print(f"Seeding {count} synthetic transactions for tenant '{tenant_id}'...")
        for i in range(1, count + 1):
            txn_id = f"TXN_SYN_DEMO_{i:04d}"
            seed_transaction(
                db,
                txn_id=txn_id,
                tenant_id=tenant_id,
                amount=100.0 * i,
                customer_name=f"Synthetic Demo User {i}",
                merchant_name=f"Synthetic Demo Merchant {i}"
            )
            print(f"  [+] Created synthetic transaction: {txn_id} (Tenant: {tenant_id})")
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic FFIRE demo transactions.")
    parser.add_argument("--tenant", default="demo_tenant", help="Tenant ID for synthetic records")
    parser.add_argument("--count", type=int, default=5, help="Number of records to generate")
    args = parser.parse_args()
    seed_demo_suite(tenant_id=args.tenant, count=args.count)