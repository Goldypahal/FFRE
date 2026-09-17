import uuid
import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Numeric, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base
import security

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    _name = Column("name", String(255), nullable=False)
    _email = Column("email", String(255), nullable=False)
    email_hash = Column(String(64), nullable=True, unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="investigator")
    status = Column(String(20), nullable=False, default="active")
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @hybrid_property
    def name(self):
        return security.decrypt_data(self._name) if self._name else None

    @name.setter
    def name(self, value):
        self._name = security.encrypt_data(value) if value else None

    @hybrid_property
    def email(self):
        return security.decrypt_data(self._email) if self._email else None

    @email.setter
    def email(self, value):
        if value:
            self._email = security.encrypt_data(value)
            self.email_hash = security.compute_blind_index(value)
        else:
            self._email = None
            self.email_hash = None

class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    name = Column(String(100), nullable=False)
    kyc_status = Column(String(50), default="UNVERIFIED")
    risk_tier = Column(String(20), default="LOW")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    accounts = relationship("Account", back_populates="customer")
    devices = relationship("Device", back_populates="customer")

class Account(Base):
    __tablename__ = "account"

    account_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    customer_id = Column(String, ForeignKey("customer.customer_id"))
    account_type = Column(String(50), default="CHECKING")
    balance = Column(Numeric(12, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Merchant(Base):
    __tablename__ = "merchant"

    merchant_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="RETAIL")
    risk_score = Column(Numeric(4, 3), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="merchant")

class Transaction(Base):
    __tablename__ = "transaction"

    txn_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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
    _fingerprint = Column("fingerprint", String(255))
    os = Column(String(50))
    ip_address = Column(String(45))

    customer = relationship("Customer", back_populates="devices")

    @hybrid_property
    def fingerprint(self):
        return security.decrypt_data(self._fingerprint) if self._fingerprint else None

    @fingerprint.setter
    def fingerprint(self, value):
        self._fingerprint = security.encrypt_data(value) if value else None

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
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(250), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    previous_hash = Column(String(64), nullable=True, default=None)
    entry_hash = Column(String(64), nullable=True, default=None)

    investigation = relationship("Investigation", back_populates="audit_logs")

    @staticmethod
    def calculate_entry_hash(prev_hash: Optional[str], log_id: str, action: str, timestamp_str: str, details: Optional[str] = "") -> str:
        """
        Calculates SHA-256 tamper-evident entry hash chaining with the previous log record.
        Creates an immutable, verifiable audit trail for NFR-5.
        """
        import hashlib
        payload = f"{prev_hash or 'GENESIS'}|{log_id}|{action}|{timestamp_str}|{details or ''}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_job"

    id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_id = Column(String, nullable=False)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=3, nullable=False)
    failed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class EvidenceVaultItem(Base):
    __tablename__ = "evidence_vault"

    item_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, default="IDENTITY_DOCUMENTS")
    title = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    tag = Column(String(50), nullable=True, default="KYC_VERIFIED")
    file_type = Column(String(50), nullable=False, default="JSON")
    file_size = Column(Integer, default=1024)
    sha256_hash = Column(String(64), nullable=False)
    risk_level = Column(String(20), default="LOW")
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(100), default="Cryptographic Signature")
    description = Column(Text, nullable=True)
    storage_path = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

class ReportRecord(Base):
    __tablename__ = "reports"

    report_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False, default="Investigation Report")
    generated_by = Column(String(100), nullable=False, default="System")
    status = Column(String(50), nullable=False, default="Completed")
    file_format = Column(String(20), nullable=False, default="pdf")
    file_size = Column(Integer, default=2400000)
    description = Column(Text, nullable=True)
    content_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    category = Column(String(50), nullable=False, default="general")
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class SystemIntegration(Base):
    __tablename__ = "system_integrations"

    integration_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="connected")
    last_sync = Column(DateTime, nullable=True)
    config_count = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PromptRecord(Base):
    __tablename__ = "prompt_registry"

    prompt_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False, default="v1.0")
    template_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    variables = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(100), default="System")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)