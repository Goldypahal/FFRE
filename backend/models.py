import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Numeric, Integer
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="investigator")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    kyc_status = Column(String(50), default="UNVERIFIED")
    risk_tier = Column(String(20), default="LOW")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    accounts = relationship("Account", back_populates="customer")
    devices = relationship("Device", back_populates="customer")

class Account(Base):
    __tablename__ = "account"

    account_id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customer.customer_id"))
    account_type = Column(String(50), default="CHECKING")
    balance = Column(Numeric(12, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Merchant(Base):
    __tablename__ = "merchant"

    merchant_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="RETAIL")
    risk_score = Column(Numeric(4, 3), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="merchant")

class Transaction(Base):
    __tablename__ = "transaction"

    txn_id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("account.account_id"))
    merchant_id = Column(String, ForeignKey("merchant.merchant_id"))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="PENDING")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    account = relationship("Account", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    investigations = relationship("Investigation", back_populates="transaction")
    locations = relationship("Location", back_populates="transaction")

class Device(Base):
    __tablename__ = "device"

    device_id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customer.customer_id"))
    fingerprint = Column(String(255))
    os = Column(String(50))
    ip_address = Column(String(45))

    customer = relationship("Customer", back_populates="devices")

class Location(Base):
    __tablename__ = "location"

    location_id = Column(String, primary_key=True, default=generate_uuid)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    geo_coord = Column(String(100))
    country = Column(String(50))

    transaction = relationship("Transaction", back_populates="locations")

class Investigation(Base):
    __tablename__ = "investigation"

    investigation_id = Column(String, primary_key=True, default=generate_uuid)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    status = Column(String(20), nullable=False, index=True)
    confidence = Column(Numeric(4, 3), nullable=True)
    risk_score = Column(Numeric(4, 3), nullable=True)
    report = Column(String, nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)

    transaction = relationship("Transaction", back_populates="investigations")
    evidence = relationship("Evidence", back_populates="investigation")
    audit_logs = relationship("AuditLog", back_populates="investigation", order_by="AuditLog.timestamp", cascade="save-update, merge")

class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id"))
    source = Column(String(50), nullable=False)
    snippet = Column(Text, nullable=False)

    investigation = relationship("Investigation", back_populates="evidence")

class FraudCase(Base):
    __tablename__ = "fraud_case"

    case_id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id"))
    verdict = Column(String(50))
    confidence = Column(Numeric(4, 3))

class RiskScore(Base):
    __tablename__ = "risk_score"

    score_id = Column(String, primary_key=True, default=generate_uuid)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    model_score = Column(Numeric(4, 3))
    rule_score = Column(Numeric(4, 3))

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(250), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="audit_logs")

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_job"

    id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String, nullable=False)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=3, nullable=False)
    failed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)