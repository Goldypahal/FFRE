from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
import datetime
from database import Base
from security import encrypt_data, decrypt_data

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "user"

    user_id = Column(String, primary_key=True, default=generate_uuid)
    _name = Column("name", String(150), nullable=False)
    role = Column(String(50), nullable=False)
    _email = Column("email", String(150), nullable=False, unique=True)
    hashed_password = Column(String(200), nullable=False, server_default="")

    @hybrid_property
    def name(self):
        return decrypt_data(self._name) if self._name else None

    @name.setter
    def name(self, value):
        self._name = encrypt_data(value) if value else None

    @hybrid_property
    def email(self):
        return decrypt_data(self._email) if self._email else None

    @email.setter
    def email(self, value):
        self._email = encrypt_data(value) if value else None

class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(String, primary_key=True, default=generate_uuid)
    _name = Column("name", String(150), nullable=False)
    kyc_status = Column(String(20), nullable=False)
    risk_tier = Column(String(10), default="LOW")

    @hybrid_property
    def name(self):
        return decrypt_data(self._name) if self._name else None

    @name.setter
    def name(self, value):
        self._name = encrypt_data(value) if value else None

class Account(Base):
    __tablename__ = "account"

    account_id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customer.customer_id"))
    account_type = Column(String(50))

class Transaction(Base):
    __tablename__ = "transaction"

    txn_id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("account.account_id"))
    merchant_id = Column(String, ForeignKey("merchant.merchant_id"), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False)

    investigations = relationship("Investigation", back_populates="transaction")

class Merchant(Base):
    __tablename__ = "merchant"

    merchant_id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    category = Column(String(100))
    risk_score = Column(Numeric(4, 3))

class Device(Base):
    __tablename__ = "device"

    device_id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customer.customer_id"))
    _fingerprint = Column("fingerprint", String(150))
    os = Column(String(50))

    @hybrid_property
    def fingerprint(self):
        return decrypt_data(self._fingerprint) if self._fingerprint else None

    @fingerprint.setter
    def fingerprint(self, value):
        self._fingerprint = encrypt_data(value) if value else None

class Location(Base):
    __tablename__ = "location"

    location_id = Column(String, primary_key=True, default=generate_uuid)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    geo_coord = Column(String(100))
    country = Column(String(50))

class Investigation(Base):
    __tablename__ = "investigation"

    investigation_id = Column(String, primary_key=True, default=generate_uuid)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    confidence = Column(Numeric(4, 3), nullable=True)
    report = Column(String, nullable=True)

    transaction = relationship("Transaction", back_populates="investigations")
    evidence = relationship("Evidence", back_populates="investigation")
    audit_logs = relationship("AuditLog", back_populates="investigation", order_by="AuditLog.timestamp")

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
    investigation_id = Column(String, ForeignKey("investigation.investigation_id"), index=True)
    action = Column(String(250), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="audit_logs")