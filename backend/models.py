import uuid
import datetime
from typing import Optional, Sequence, Any, Tuple, List
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Numeric, Integer, Boolean, UniqueConstraint, UniqueConstraint, event, select
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
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), default="PENDING")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    counterparty = Column(String(255), nullable=True)
    channel = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_ref = Column(String(100), nullable=True)

    account = relationship("Account", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    investigations = relationship("Investigation", back_populates="transaction")
    locations = relationship("Location", back_populates="transaction")

class Device(Base):
    __tablename__ = "device"

    device_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    geo_coord = Column(String(100))
    country = Column(String(50))

    transaction = relationship("Transaction", back_populates="locations")

class Investigation(Base):
    __tablename__ = "investigation"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_investigation_tenant_idempotency_key"),
    )

    investigation_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=True, index=True)
    txn_id = Column(String, ForeignKey("transaction.txn_id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    status = Column(String(20), nullable=False, index=True)
    confidence = Column(Numeric(4, 3), nullable=True)
    risk_score = Column(Numeric(4, 3), nullable=True)
    report = Column(String, nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)
    request_fingerprint = Column(String(64), nullable=True, index=True)

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
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
    investigation_id = Column(String, ForeignKey("investigation.investigation_id"))
    verdict = Column(String(50))
    confidence = Column(Numeric(4, 3))

class RiskScore(Base):
    __tablename__ = "risk_score"

    score_id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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

    @classmethod
    def order_chain(cls, logs: Sequence[Any]) -> List[Any]:
        """Orders audit logs topologically following hash chain pointers (prev_hash -> entry_hash)."""
        if not logs or len(logs) <= 1:
            return list(logs)
        by_prev = {}
        genesis = None
        for log in logs:
            prev = log.get("previous_hash") if isinstance(log, dict) else getattr(log, "previous_hash", None)
            if prev in (None, "", "GENESIS"):
                genesis = log
            else:
                by_prev[prev] = log
        if not genesis:
            return list(logs)
        ordered = [genesis]
        curr = genesis
        while len(ordered) < len(logs):
            curr_hash = curr.get("entry_hash") if isinstance(curr, dict) else getattr(curr, "entry_hash", None)
            if curr_hash in by_prev:
                curr = by_prev[curr_hash]
                ordered.append(curr)
            else:
                break
        if len(ordered) == len(logs):
            return ordered
        return list(logs)

    @classmethod
    def verify_chain(cls, logs: Sequence[Any]) -> Tuple[bool, List[str]]:
        """
        Verifies the cryptographic integrity of an AuditLog hash chain.
        Works on SQLAlchemy AuditLog instances, dicts, or objects with appropriate attributes.
        Returns (True, []) if the chain is intact.
        Returns (False, [error_reasons...]) if any tampering or broken link is found.
        """
        if not logs:
            return True, []

        logs = cls.order_chain(logs)
        errors = []
        for i, log in enumerate(logs):
            if isinstance(log, dict):
                log_id = log.get("log_id")
                action = log.get("action")
                details = log.get("details")
                previous_hash = log.get("previous_hash")
                entry_hash = log.get("entry_hash")
                raw_ts = log.get("timestamp")
            else:
                log_id = getattr(log, "log_id", None)
                action = getattr(log, "action", None)
                details = getattr(log, "details", None)
                previous_hash = getattr(log, "previous_hash", None)
                entry_hash = getattr(log, "entry_hash", None)
                raw_ts = getattr(log, "timestamp", None)

            ts_str = raw_ts.isoformat() if hasattr(raw_ts, "isoformat") else str(raw_ts or "")

            # 1. Verify previous_hash linkage
            if i == 0:
                if previous_hash not in (None, "", "GENESIS"):
                    errors.append(
                        f"Genesis log '{log_id}' at index 0 has unexpected previous_hash '{previous_hash}' (expected None or 'GENESIS')"
                    )
            else:
                pred = logs[i - 1]
                pred_entry_hash = pred.get("entry_hash") if isinstance(pred, dict) else getattr(pred, "entry_hash", None)
                if previous_hash != pred_entry_hash:
                    errors.append(
                        f"Broken chain link at index {i} (log '{log_id}'): previous_hash '{previous_hash}' does not match predecessor entry_hash '{pred_entry_hash}'"
                    )

            # 2. Verify entry_hash recalculation
            expected_hash = cls.calculate_entry_hash(
                previous_hash,
                str(log_id or ""),
                str(action or ""),
                ts_str,
                str(details or "")
            )
            if entry_hash != expected_hash:
                errors.append(
                    f"Tampered entry hash at index {i} (log '{log_id}'): stored entry_hash '{entry_hash}' does not match recalculated hash '{expected_hash}'"
                )

        return (len(errors) == 0, errors)

@event.listens_for(AuditLog, 'before_insert')
def _auto_chain_audit_log(mapper, connection, target):
    """
    Automatically links previous_hash and computes entry_hash for new AuditLog records
    if not explicitly populated by the caller. Preserves explicit hashes set by test fixtures.
    """
    if not target.log_id:
        target.log_id = generate_uuid()
    if not target.timestamp:
        target.timestamp = datetime.datetime.utcnow()

    # If entry_hash already explicitly supplied by caller, track and respect it
    if target.entry_hash:
        if target.investigation_id:
            connection.info.setdefault('last_audit_hashes', {})[target.investigation_id] = target.entry_hash
        return

    # Look up previous hash
    prev_hash = target.previous_hash
    if prev_hash is None and target.investigation_id:
        last_hashes = connection.info.setdefault('last_audit_hashes', {})
        if target.investigation_id in last_hashes:
            prev_hash = last_hashes[target.investigation_id]
        else:
            stmt = select(AuditLog.entry_hash).where(
                AuditLog.investigation_id == target.investigation_id
            ).order_by(AuditLog.timestamp.desc(), AuditLog.log_id.desc()).limit(1)
            row = connection.execute(stmt).first()
            if row and row[0]:
                prev_hash = row[0]

    target.previous_hash = prev_hash
    ts_str = target.timestamp.isoformat() if hasattr(target.timestamp, 'isoformat') else str(target.timestamp or "")
    target.entry_hash = AuditLog.calculate_entry_hash(
        target.previous_hash,
        target.log_id,
        target.action,
        ts_str,
        target.details or ""
    )
    if target.investigation_id:
        connection.info.setdefault('last_audit_hashes', {})[target.investigation_id] = target.entry_hash

    @classmethod
    def verify_chain(cls, logs: Sequence[Any]) -> Tuple[bool, List[str]]:
        """
        Verifies the cryptographic integrity of an AuditLog hash chain.
        Works on SQLAlchemy AuditLog instances, dicts, or objects with appropriate attributes.
        Returns (True, []) if the chain is intact.
        Returns (False, [error_reasons...]) if any tampering or broken link is found.
        """
        if not logs:
            return True, []

        errors = []
        for i, log in enumerate(logs):
            if isinstance(log, dict):
                log_id = log.get("log_id")
                action = log.get("action")
                details = log.get("details")
                previous_hash = log.get("previous_hash")
                entry_hash = log.get("entry_hash")
                raw_ts = log.get("timestamp")
            else:
                log_id = getattr(log, "log_id", None)
                action = getattr(log, "action", None)
                details = getattr(log, "details", None)
                previous_hash = getattr(log, "previous_hash", None)
                entry_hash = getattr(log, "entry_hash", None)
                raw_ts = getattr(log, "timestamp", None)

            ts_str = raw_ts.isoformat() if hasattr(raw_ts, "isoformat") else str(raw_ts or "")

            # 1. Verify previous_hash linkage
            if i == 0:
                if previous_hash not in (None, "", "GENESIS"):
                    errors.append(
                        f"Genesis log '{log_id}' at index 0 has unexpected previous_hash '{previous_hash}' (expected None or 'GENESIS')"
                    )
            else:
                pred = logs[i - 1]
                pred_entry_hash = pred.get("entry_hash") if isinstance(pred, dict) else getattr(pred, "entry_hash", None)
                if previous_hash != pred_entry_hash:
                    errors.append(
                        f"Broken chain link at index {i} (log '{log_id}'): previous_hash '{previous_hash}' does not match predecessor entry_hash '{pred_entry_hash}'"
                    )

            # 2. Verify entry_hash recalculation
            expected_hash = cls.calculate_entry_hash(
                previous_hash,
                str(log_id or ""),
                str(action or ""),
                ts_str,
                str(details or "")
            )
            if entry_hash != expected_hash:
                errors.append(
                    f"Tampered entry hash at index {i} (log '{log_id}'): stored entry_hash '{entry_hash}' does not match recalculated hash '{expected_hash}'"
                )

        return (len(errors) == 0, errors)

@event.listens_for(AuditLog, 'before_insert')
def _auto_chain_audit_log(mapper, connection, target):
    """
    Automatically links previous_hash and computes entry_hash for new AuditLog records
    if not explicitly populated by the caller. Preserves explicit hashes set by test fixtures.
    """
    if not target.log_id:
        target.log_id = generate_uuid()
    if not target.timestamp:
        target.timestamp = datetime.datetime.utcnow()

    # If entry_hash already explicitly supplied by caller, track and respect it
    if target.entry_hash:
        if target.investigation_id:
            connection.info.setdefault('last_audit_hashes', {})[target.investigation_id] = target.entry_hash
        return

    # Look up previous hash
    prev_hash = target.previous_hash
    if prev_hash is None and target.investigation_id:
        last_hashes = connection.info.setdefault('last_audit_hashes', {})
        if target.investigation_id in last_hashes:
            prev_hash = last_hashes[target.investigation_id]
        else:
            stmt = select(AuditLog.entry_hash).where(
                AuditLog.investigation_id == target.investigation_id
            ).order_by(AuditLog.timestamp.desc(), AuditLog.log_id.desc()).limit(1)
            row = connection.execute(stmt).first()
            if row and row[0]:
                prev_hash = row[0]

    target.previous_hash = prev_hash
    ts_str = target.timestamp.isoformat() if hasattr(target.timestamp, 'isoformat') else str(target.timestamp or "")
    target.entry_hash = AuditLog.calculate_entry_hash(
        target.previous_hash,
        target.log_id,
        target.action,
        ts_str,
        target.details or ""
    )
    if target.investigation_id:
        connection.info.setdefault('last_audit_hashes', {})[target.investigation_id] = target.entry_hash

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_job"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), nullable=False, default="default_tenant", index=True)
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