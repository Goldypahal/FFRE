import logging
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, Query, Response, Header, UploadFile, File, Form, Request, Body

from fastapi.security import OAuth2PasswordRequestForm

from pydantic import BaseModel

from typing import List, Optional, Dict, Any, Union, Tuple

import uuid

import datetime
import timeutil

import time

import hashlib

import hmac

import secrets

import os
import html
from decimal import Decimal

import json

import csv

import io

import re
import threading

_investigation_creation_lock = threading.Lock()

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from sqlalchemy import desc, asc, func, or_, text

from sqlalchemy.exc import IntegrityError

from starlette.concurrency import run_in_threadpool

from cryptography.hazmat.primitives.asymmetric import ed25519

from cryptography.hazmat.primitives import serialization

from cryptography.exceptions import InvalidSignature



from security import get_verifier_keys





from database import engine, Base, get_db

import models

from graph import build_graph

import auth

from security import encrypt_data

from metrics import metrics_collector

import guardrails

from rate_limiter import RateLimitMiddleware



# Initialize database tables

Base.metadata.create_all(bind=engine)



app = FastAPI(title="FFIRE API Gateway", description="Financial Fraud Investigation Reasoning Engine")



# Enterprise Rate Limiter Middleware (Chapters 47 & 88)

app.add_middleware(RateLimitMiddleware)



# Explicit origin allowlist (Finding 2: Fix P0 wildcard CORS with credentials)

cors_origins_env = os.getenv("ALLOWED_ORIGINS", "")

if cors_origins_env:

    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

else:

    allowed_origins = [

        "http://localhost:5173",

        "http://127.0.0.1:5173",

        "http://localhost:3000",

        "http://127.0.0.1:3000",

        "http://localhost:8000",

        "http://127.0.0.1:8000",

    ]



app.add_middleware(

    CORSMiddleware,

    allow_origins=allowed_origins,

    allow_credentials=True,

    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],

    allow_headers=["*"],

)

@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Financial Fraud Investigation Reasoning Engine (FFIRE)",
        "status": "online",
        "docs_url": "/docs",
        "frontend_url": "http://localhost:5173"
    }



class InvestigationRequest(BaseModel):

    transaction_id: str

    user_id: str



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "transaction_id": "txn_1234567890",

                    "user_id": "user_9876543210"

                }

            ]

        }

    }



class TransactionIngestItem(BaseModel):

    txn_id: Optional[str] = None

    account_id: str

    merchant_id: Optional[str] = None

    amount: float

    currency: Optional[str] = "USD"

    status: Optional[str] = "PENDING"

    timestamp: Optional[Union[str, datetime.datetime]] = None

    counterparty: Optional[str] = None

    channel: Optional[str] = None

    ip_address: Optional[str] = None

    device_ref: Optional[str] = None

    tenant_id: Optional[str] = None



class TransactionIngestRequest(BaseModel):

    transactions: List[TransactionIngestItem]



class QuarantineReason(BaseModel):

    row_index: int

    txn_id: Optional[str] = None

    reason: str

    record: Optional[Dict[str, Any]] = None



class TransactionIngestResponse(BaseModel):

    total_records: int

    ingested: int

    quarantined: int

    skipped_duplicates: int

    quarantine_reasons: List[QuarantineReason]



class TransactionResponse(BaseModel):

    txn_id: str

    tenant_id: str

    account_id: str

    merchant_id: Optional[str] = None

    amount: float

    currency: str

    status: str

    timestamp: Optional[datetime.datetime] = None

    counterparty: Optional[str] = None

    channel: Optional[str] = None

    ip_address: Optional[str] = None

    device_ref: Optional[str] = None



    model_config = {"from_attributes": True}



class HumanReviewAction(BaseModel):

    action: str  # "APPROVE" or "REJECT"

    notes: Optional[str] = None



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "action": "APPROVE",

                    "notes": "Transaction appears legitimate based on additional verification"

                },

                {

                    "action": "REJECT",

                    "notes": "High-risk transaction from blacklisted jurisdiction"

                }

            ]

        }

    }



class EvidenceResponse(BaseModel):

    source: str

    snippet: str



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "source": "customer_evidence",

                    "snippet": "{'kyc_status': 'VERIFIED', 'risk_tier': 'MEDIUM', 'name': 'John Doe'}"

                },

                {

                    "source": "transaction_evidence",

                    "snippet": "{'amount': 4250.0, 'currency': 'USD', 'status': 'PENDING'}"

                }

            ]

        }

    }



class AuditLogResponse(BaseModel):

    log_id: Optional[str] = None

    action: str

    details: Optional[str] = None

    timestamp: datetime.datetime

    previous_hash: Optional[str] = None

    entry_hash: Optional[str] = None



    model_config = {

        "from_attributes": True,

        "json_schema_extra": {

            "examples": [

                {

                    "action": "Investigation Started",

                    "details": "Investigation initiated for transaction txn_1234567890",

                    "timestamp": "2026-07-14T10:30:00Z"

                },

                {

                    "action": "Risk Assessment Completed",

                    "details": "Risk score: 0.85, Confidence: 0.92",

                    "timestamp": "2026-07-14T10:32:15Z"

                }

            ]

        }

    }



class InvestigationResponse(BaseModel):

    investigation_id: str

    transaction_id: str

    status: str

    confidence: Optional[float] = None

    report: Optional[str] = None

    evidence: List[EvidenceResponse] = []

    audit_logs: List[AuditLogResponse] = []

    amount: Optional[float] = None

    currency: Optional[str] = None

    customer_name: Optional[str] = None

    risk_score: Optional[float] = None

    created_at: Optional[datetime.datetime] = None

    tenant_id: Optional[str] = "default_tenant"

    is_degraded: Optional[bool] = False

    degraded_reason: Optional[str] = None

    legal_hold: Optional[bool] = False



    model_config = {

        "from_attributes": True,

        "json_schema_extra": {

            "examples": [

                {

                    "investigation_id": "inv_1234567890abcdef",

                    "transaction_id": "txn_1234567890",

                    "status": "COMPLETED",

                    "confidence": 0.92,

                    "report": "## Summary\nTransaction appears to be legitimate based on comprehensive analysis.\n\n## Evidence Table\n- Customer: Verified KYC, Medium risk tier\n- Transaction: $4,250 USD, Pending status\n\n## Risk Factors\n- Standard transaction patterns\n\n## Confidence Score\n0.92\n\n## Recommendation\nApprove transaction.",

                    "evidence": [

                        {

                            "source": "customer_evidence",

                            "snippet": "{'kyc_status': 'VERIFIED', 'risk_tier': 'MEDIUM', 'name': 'John Doe'}"

                        }

                    ],

                    "audit_logs": [

                        {

                            "action": "Investigation Started",

                            "details": "Investigation initiated for transaction txn_1234567890",

                            "timestamp": "2026-07-14T10:30:00Z"

                        }

                    ]

                }

            ]

        }

    }



class ReplaySnapshotResponse(BaseModel):

    snapshot_version: str = "1.0.0"

    generated_at: str

    investigation_id: str

    tenant_id: str

    replay_fingerprint: str

    digital_signature: Optional[str] = None

    signature_algorithm: Optional[str] = None

    signing_key_id: Optional[str] = None

    investigation: Dict[str, Any]

    transaction: Optional[Dict[str, Any]] = None

    evidence: List[Dict[str, Any]] = []

    audit_logs: List[Dict[str, Any]] = []

    audit_chain_valid: bool

    audit_chain_errors: List[str] = []

    model_metadata: Optional[Dict[str, Any]] = None

    prompt_metadata: Optional[Dict[str, Any]] = None

    runtime_environment: Optional[Dict[str, Any]] = None



class ReplayVerifyResponse(BaseModel):

    is_valid: bool

    replay_fingerprint: Optional[str] = None

    audit_chain_valid: bool

    audit_chain_errors: List[str] = []

    tamper_detected: bool = False

    mismatch_reasons: List[str] = []

    detail: str



class AuditChainEntry(BaseModel):

    log_id: str

    tenant_id: str

    action: str

    details: Optional[str] = None

    timestamp: Optional[str] = None

    previous_hash: Optional[str] = None

    entry_hash: Optional[str] = None



class AuditChainResponse(BaseModel):

    investigation_id: str

    tenant_id: str

    chain_length: int

    is_valid: bool

    errors: List[str] = []

    entries: List[AuditChainEntry] = []



class Token(BaseModel):

    access_token: Optional[str] = None

    token_type: Optional[str] = "bearer"

    refresh_token: Optional[str] = None

    tenant_id: Optional[str] = "default_tenant"

    mfa_required: Optional[bool] = False

    mfa_ticket: Optional[str] = None
    masked_phone: Optional[str] = None
    message: Optional[str] = None
    # Who signed in, so the client does not have to guess the role.
    role: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None


class MFALoginVerifyRequest(BaseModel):
    mfa_ticket: str
    code: str


class MFASetupRequest(BaseModel):
    phone_number: str
    # Step-up proof, required when MFA is already on: the current password, or a code sent to the
    # phone that is registered now.
    password: Optional[str] = None
    code: Optional[str] = None


class MFACodeVerifyRequest(BaseModel):
    code: str


class MFADisableRequest(BaseModel):
    password: Optional[str] = None
    code: Optional[str] = None


class MFAStatusResponse(BaseModel):
    mfa_enabled: bool
    masked_phone: Optional[str] = None


class TestAlertSMSRequest(BaseModel):
    recipient_phone: Optional[str] = None
    message: Optional[str] = None



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

                    "token_type": "bearer",

                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

                }

            ]

        }

    }



class RefreshTokenRequest(BaseModel):

    refresh_token: str





class UserCreate(BaseModel):

    name: str

    email: str

    password: str

    # Role and tenant_id are optional on input but strictly server-assigned via TenantInvitation

    # or bootstrap/sandbox defaults to prevent client tenant escalation or role tampering.

    role: Optional[str] = None

    tenant_id: Optional[str] = None

    invite_token: Optional[str] = None



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "name": "Jane Doe",

                    "email": "jane.doe@enterprise.bank",

                    "password": "securePassword123!",

                    "invite_token": "inv_example_secure_token"

                }

            ]

        }

    }



class InvitationCreate(BaseModel):

    email: Optional[str] = None

    role: str = "investigator"

    expires_in_hours: int = 48



class InvitationResponse(BaseModel):

    invitation_id: str

    token: Optional[str] = None

    token_hash: Optional[str] = None

    tenant_id: str

    email: Optional[str]

    role: str

    expires_at: str

    created_at: str

    is_used: bool



class BootstrapRequest(BaseModel):

    name: str

    email: str

    password: str

    tenant_id: Optional[str] = "tenant_prime"

    bootstrap_secret: Optional[str] = None



class InvestigationUpdate(BaseModel):

    status: Optional[str] = None

    notes: Optional[str] = None



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "status": "COMPLETED",

                    "notes": "Investigation completed after reviewing all evidence"

                }

            ]

        }

    }



class InvestigationListResponse(BaseModel):

    investigations: List[InvestigationResponse]

    total: int

    page: int

    page_size: int

    total_pages: int



    model_config = {

        "json_schema_extra": {

            "examples": [

                {

                    "investigations": [

                        {

                            "investigation_id": "inv_1234567890abcdef",

                            "transaction_id": "txn_1234567890",

                            "status": "COMPLETED",

                            "confidence": 0.92,

                            "report": "## Summary\nTransaction appears to be legitimate based on comprehensive analysis.",

                            "evidence": [

                                {

                                    "source": "customer_evidence",

                                    "snippet": "{'kyc_status': 'VERIFIED', 'risk_tier': 'MEDIUM', 'name': 'John Doe'}"

                                }

                            ],

                            "audit_logs": []

                        }

                    ],

                    "total": 1,

                    "page": 1,

                    "page_size": 10,

                    "total_pages": 1

                }

            ]

        }

    }



class EvidenceVaultCreate(BaseModel):

    category: str = "IDENTITY_DOCUMENTS"

    title: str

    source: str

    tag: Optional[str] = "KYC_VERIFIED"

    file_type: str = "JSON"

    risk_level: str = "LOW"

    description: Optional[str] = None

    investigation_id: Optional[str] = None

    content: Optional[str] = None

    tenant_id: Optional[str] = None



class EvidenceVaultResponse(BaseModel):

    item_id: str

    tenant_id: str

    investigation_id: Optional[str] = None

    category: str

    title: str

    source: str

    tag: Optional[str] = None

    file_type: str

    file_size: int

    sha256_hash: str

    risk_level: str

    is_verified: bool

    verification_method: Optional[str] = None

    description: Optional[str] = None

    created_at: datetime.datetime



    model_config = {"from_attributes": True}



class EvidenceVaultListResponse(BaseModel):

    items: List[EvidenceVaultResponse]

    total: int

    page: int

    page_size: int

    total_pages: int



class ReportGenerateRequest(BaseModel):

    title: str

    report_type: str = "Investigation Report"

    investigation_id: Optional[str] = None

    description: Optional[str] = None

    file_format: str = "pdf"



class ReportRecordResponse(BaseModel):

    report_id: str

    tenant_id: str

    investigation_id: Optional[str] = None

    title: str

    report_type: str

    generated_by: str

    status: str

    file_format: str

    file_size: int

    description: Optional[str] = None

    created_at: datetime.datetime



    model_config = {"from_attributes": True}



class ReportListResponse(BaseModel):

    reports: List[ReportRecordResponse]

    total: int

    page: int

    page_size: int

    total_pages: int



# Build the LangGraph app once

graph_app = build_graph()



# Exported HTML is a document to save, not a page of this application: it is sent as a download
# with scripts, frames and outside requests switched off.
SAFE_HTML_EXPORT_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox",
    "X-Content-Type-Options": "nosniff",
}


def _safe_filename(name: str) -> str:
    """Keep letters, digits, dot, dash and underscore; drop any directory part."""
    base = os.path.basename(str(name or "").replace("\\", "/"))
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")
    return cleaned[:150] or "file"


GRAPH_RECURSION_LIMIT = int(os.getenv("GRAPH_RECURSION_LIMIT", "60"))
MAX_PAGE_SIZE = 500


def run_investigation_task(investigation_id: str, transaction_id: str, db: Optional[Session] = None):

    start_time = time.time()

    should_close_db = False

    if db is None:

        db = next(get_db())

        should_close_db = True

    try:

        tenant_id = "default_tenant"

        inv_record = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

        if inv_record and inv_record.tenant_id:

            tenant_id = inv_record.tenant_id



        initial_state = {

            "investigation_id": investigation_id,

            "transaction_id": transaction_id,

            "tenant_id": tenant_id,

            "tasks": [],

            "customer_evidence": {},

            "transaction_evidence": {},

            "merchant_evidence": {},

            "device_evidence": {},

            "location_evidence": {},

            "historical_cases": [],

            "risk_score": None,

            "confidence": None,

            "validated": False,

            "retry_count": 0,

            "report": None

        }



        # Run graph with checkpoint thread config

        # recursion_limit bounds the run. The graph has about fifteen nodes and at most a handful of
        # retries, so a run that needs more steps than this is looping and should fail fast.
        config = {"configurable": {"thread_id": investigation_id}, "recursion_limit": GRAPH_RECURSION_LIMIT}
        result = graph_app.invoke(initial_state, config=config)

        # Update DB
        db.expire_all()
        investigation = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
        was_cancelled = result.get("workflow_status") == "CANCELLED" or (
            investigation is not None and investigation.status in ("CANCELLED", "ARCHIVED_DELETED")
        )
        if investigation and was_cancelled:
            # Cancelled (or deleted) while it ran. Leave the status as the user set it and store
            # nothing from the partial run.
            investigation = None
        if investigation:

            report_text = result.get("report") or ""

            is_escalated = (

                report_text.startswith("# HUMAN REVIEW") or

                "human_review" in result.get("execution_trace", []) or

                any(

                    isinstance(result.get(src), dict) and result[src].get("evidence_status") == "UNAVAILABLE"

                    for src in ["customer_evidence", "transaction_evidence", "merchant_evidence", "device_evidence", "location_evidence", "velocity_evidence"]

                )

            )



            if result.get("confidence") is not None:

                investigation.confidence = result["confidence"]

                # Import here to avoid circular imports

                from graph import CONFIDENCE_THRESHOLD

                if is_escalated or result["confidence"] < CONFIDENCE_THRESHOLD:

                    investigation.status = "ESCALATED"

                else:

                    investigation.status = "COMPLETED"

            elif is_escalated:

                investigation.status = "ESCALATED"

            else:

                investigation.status = "COMPLETED"

            # Critical Incident Escalation SMS Alert (Twilio Integration)
            if investigation.status == "ESCALATED" or (result.get("risk_score") is not None and float(result.get("risk_score") or 0.0) >= 0.70):
                try:
                    from twilio_service import twilio_service
                    reasons = result.get("degraded_reasons") or ["Risk threshold exceeded or high-severity typology alert"]
                    twilio_service.send_critical_escalation_alert(
                        investigation_id=investigation_id,
                        risk_score=float(result.get("risk_score") or 0.0),
                        triggers=reasons,
                        tenant_id=getattr(investigation, "tenant_id", "default_tenant"),
                        db=db
                    )
                except Exception as _alert_exc:
                    logging.getLogger("ffire.alerts").warning(f"Twilio alert dispatch error: {_alert_exc}")



            if result.get("risk_score") is not None:

                investigation.risk_score = result["risk_score"]



            investigation.report = result.get("report")



            # Finding 3: Analytical pipeline degradation accounting (never silent fallback)

            try:
                from llm_gateway import get_llm_gateway
                _offline = get_llm_gateway().is_offline()
            except Exception:
                _offline = False
            if _offline and auth.is_strict_mode():
                # In production an investigation reasoned by the built-in offline stub, because no
                # model provider is configured or reachable, must say so on its face.
                result["is_degraded"] = True
                result["degraded_reasons"] = list(result.get("degraded_reasons") or []) + [
                    "No LLM provider available: reasoning produced by the deterministic offline fallback"
                ]
            is_degraded = bool(result.get("is_degraded", False))

            investigation.is_degraded = is_degraded

            if is_degraded:

                degraded_reasons = result.get("degraded_reasons", [])

                investigation.degraded_reason = "; ".join(degraded_reasons) if degraded_reasons else "Analytical pipeline component degraded"

                try:

                    models.AuditLog.create_chained_entry(

                        db=db,

                        tenant_id=getattr(investigation, "tenant_id", "default_tenant"),

                        investigation_id=investigation_id,

                        action="PIPELINE_DEGRADED",

                        details=f"Degraded components: {result.get('degraded_components')}; Reasons: {investigation.degraded_reason}"

                    )

                except Exception:

                    pass



            # Save retrieved evidence sources

            evidence_sources = ["customer_evidence", "transaction_evidence", "merchant_evidence", "device_evidence", "location_evidence"]

            for src in evidence_sources:
                if result.get(src):
                    snippet_source = result[src]
                    if src == "customer_evidence" and isinstance(snippet_source, dict) and snippet_source.get("name"):
                        # The customer's name is encrypted in its own table; do not copy it here in clear.
                        snippet_source = {**snippet_source, "name": "[stored encrypted]"}
                    snippet_text = str(snippet_source)
                    ev = models.Evidence(
                        investigation_id=investigation_id,
                        tenant_id=tenant_id,
                        source=src,
                        snippet=snippet_text
                    )

                    db.add(ev)



            db.commit()



        # Record metrics

        duration = time.time() - start_time

        metrics_collector.record_investigation_time(investigation_id, duration)

        if result.get("confidence") is not None:

            metrics_collector.record_confidence_score(investigation_id, result["confidence"])

        if result.get("risk_score") is not None:

            metrics_collector.record_risk_score(investigation_id, result["risk_score"])

        if result.get("retry_count") is not None:

            metrics_collector.record_retry_count(investigation_id, result["retry_count"])



    except Exception as e:

        print(f"Error running graph for {investigation_id}: {e}")

        db.rollback()

        investigation = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

        if investigation and investigation.status not in ("CANCELLED", "ARCHIVED_DELETED"):
            logging.getLogger("ffire.pipeline").exception("Investigation %s failed", investigation_id)
            investigation.status = "FAILED"
            # The report is shown to users, so it names the kind of failure but not the raw error
            # text, which can contain SQL, file paths or connection strings. The detail is in the log.
            investigation.report = f"Internal error: {type(e).__name__}. See server logs for investigation {investigation_id}."
            db.commit()



            # Record failed investigation metrics

            duration = time.time() - start_time

            metrics_collector.record_investigation_time(investigation_id, duration)

            # Consider failed investigations as having 0 confidence for metrics

            metrics_collector.record_confidence_score(investigation_id, 0.0)

    finally:

        if should_close_db:

            db.close()



# --- Auth Routes ---

@app.post("/api/v1/auth/register", response_model=Token)

def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):

    """

    Zero-Trust Enterprise Registration (P0 Remediation).

    Eliminates public tenant selection, role escalation, and first-user auto-promotion.

    Roles and tenant assignments are strictly server-controlled via authenticated,

    single-use TenantInvitation records, or isolated to a random sandbox tenant for public viewers.

    """

    norm_email = user.email.strip().lower() if user.email else ""

    if not norm_email:

        raise HTTPException(status_code=400, detail="A valid email address is required")



    db_user = auth.get_user_by_email(db, norm_email)

    if db_user:

        raise HTTPException(status_code=400, detail="Email already registered")



    invite_token = user.invite_token or request.headers.get("X-Admin-Invite-Token") or request.headers.get("X-Invite-Token")



    if invite_token:

        # 1. Authenticated Invitation Path (Strict cryptographic single-use verification with at-rest token hashing)

        token_clean = invite_token.strip()

        token_hash = hashlib.sha256(token_clean.encode("utf-8")).hexdigest()



        invitation = db.query(models.TenantInvitation).filter(

            models.TenantInvitation.token_hash == token_hash

        ).first()



        if not invitation or invitation.is_used:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="Invalid, expired, or already-consumed invitation token."

            )



        if invitation.expires_at < timeutil.utcnow():

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="Invitation token has expired. Request a new invitation from your administrator."

            )



        if invitation.email and invitation.email.strip().lower() != norm_email:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail=f"This invitation was restricted to {invitation.email}."

            )



        # Atomic single-use update with row-count check to prevent race-condition concurrency

        now_utc = timeutil.utcnow()

        updated = db.query(models.TenantInvitation).filter(

            models.TenantInvitation.invitation_id == invitation.invitation_id,

            models.TenantInvitation.is_used == False

        ).update({

            models.TenantInvitation.is_used: True,

            models.TenantInvitation.used_at: now_utc,

            models.TenantInvitation.used_by: norm_email

        }, synchronize_session=False)



        if updated == 0:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="Invalid, expired, or already-consumed invitation token."

            )



        # STRICT ENFORCEMENT: Server assigns role and tenant strictly from the database invitation

        role = invitation.role

        tenant = invitation.tenant_id



    else:

        # 2. No invitation token supplied: public registration check (strictly disabled by default)

        allow_public = os.getenv("ALLOW_PUBLIC_REGISTRATION", "false").lower() in ("true", "1", "yes")

        if not allow_public:

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="Public self-registration is disabled. An authenticated administrator invitation is required to join a tenant."

            )

        # If public sandbox registration is explicitly enabled, force server-assigned isolated sandbox tenant & viewer role

        role = "viewer"

        tenant = f"sandbox_{uuid.uuid4().hex[:10]}"



    hashed_password = auth.get_password_hash(user.password)

    db_user = models.User(

        name=user.name, 

        email=norm_email, 

        role=role, 

        hashed_password=hashed_password,

        tenant_id=tenant

    )

    db.add(db_user)

    db.commit()

    db.refresh(db_user)

    

    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = auth.create_access_token(

        data={"sub": norm_email, "role": role, "tenant_id": tenant}, expires_delta=access_token_expires

    )

    refresh_token = auth.create_refresh_token(

        data={"sub": norm_email, "role": role, "tenant_id": tenant}

    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "tenant_id": tenant}

@app.post("/api/v1/auth/mfa/verify", response_model=Token)
def verify_mfa_login(payload: MFALoginVerifyRequest, db: Session = Depends(get_db)):
    """Complete 2FA login verification using Twilio SMS OTP code."""
    from twilio_service import twilio_service
    user_id = twilio_service.verify_mfa_ticket(payload.mfa_ticket)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA session ticket. Please log in again."
        )

    is_valid = twilio_service.verify_mfa_code(user_id, payload.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code. Please check your SMS and try again."
        )

    # Consume single-use ticket to prevent replay
    twilio_service.consume_mfa_ticket(payload.mfa_ticket)

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    if not auth.is_active_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    tenant = getattr(user, "tenant_id", "default_tenant")
    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role, "tenant_id": tenant, "mfa_verified": True}, expires_delta=access_token_expires
    )
    refresh_token = auth.create_refresh_token(
        data={"sub": user.email, "role": user.role, "tenant_id": tenant, "mfa_verified": True}
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        tenant_id=tenant,
        mfa_required=False,
        role=user.role,
        user_id=user.user_id,
        name=user.name,
    )


@app.get("/api/v1/auth/mfa/status", response_model=MFAStatusResponse)
def get_user_mfa_status(current_user: models.User = Depends(auth.get_current_user)):
    """Check MFA configuration status for the authenticated user."""
    phone = current_user.phone_number
    masked = None
    if phone and len(phone) > 4:
        masked = phone[:2] + "•" * (len(phone) - 6) + phone[-4:]
    return MFAStatusResponse(
        mfa_enabled=getattr(current_user, "mfa_enabled", False),
        masked_phone=masked
    )


@app.post("/api/v1/auth/mfa/setup")
def setup_user_mfa(
    payload: MFASetupRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Initiates SMS MFA registration by sending an initial verification code."""
    from twilio_service import twilio_service
    clean_phone = payload.phone_number.strip()
    
    user_record = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()

    # With MFA already on, the phone number is the second factor. Replacing it needs more than the
    # bearer token, or a stolen session could redirect the codes to the attacker and then turn MFA off.
    existing = user_record or current_user
    if getattr(existing, "mfa_enabled", False):
        stepped_up = False
        if payload.password:
            stepped_up = auth.verify_password(payload.password, existing.hashed_password)
        elif payload.code:
            stepped_up = twilio_service.verify_mfa_code(existing.user_id, payload.code)
        if not stepped_up:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Step-up authentication required to change the MFA phone number. Provide the current password or an SMS verification code."
            )

    if user_record:
        user_record.phone_number = clean_phone
    else:
        current_user.phone_number = clean_phone
        db.add(current_user)
        user_record = current_user
    db.commit()

    masked_phone, _ = twilio_service.generate_and_send_mfa_code(user_record.user_id, clean_phone)
    return {
        "status": "pending_verification",
        "masked_phone": masked_phone,
        "message": f"Verification code sent via SMS to {masked_phone}."
    }


@app.post("/api/v1/auth/mfa/enable")
def enable_user_mfa(
    payload: MFACodeVerifyRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Verifies SMS code and activates mandatory MFA for this account."""
    from twilio_service import twilio_service
    user_record = db.query(models.User).filter(models.User.user_id == current_user.user_id).first() or current_user
    if not user_record.phone_number:
        raise HTTPException(status_code=400, detail="Phone number must be registered before enabling MFA.")

    is_valid = twilio_service.verify_mfa_code(user_record.user_id, payload.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    user_record.mfa_enabled = True
    db.commit()
    return {"status": "enabled", "message": "SMS Multi-Factor Authentication enabled successfully."}


@app.post("/api/v1/auth/mfa/disable")
def disable_user_mfa(
    payload: Optional[MFADisableRequest] = Body(default=None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivates MFA for the authenticated user.
    Requires step-up authentication (user password verification or valid SMS OTP code)
    to prevent an attacker with a stolen bearer session token from disabling MFA.
    """
    user_record = db.query(models.User).filter(models.User.user_id == current_user.user_id).first() or current_user

    # If MFA is not even enabled, nothing to disable
    if not getattr(user_record, "mfa_enabled", False):
        return {"status": "disabled", "message": "SMS Multi-Factor Authentication is not active."}

    # Step-Up Verification: require password or valid OTP
    has_step_up = False
    if payload and payload.password:
        if auth.verify_password(payload.password, user_record.hashed_password):
            has_step_up = True
        else:
            raise HTTPException(status_code=401, detail="Step-up authentication failed: incorrect password.")
    elif payload and payload.code:
        from twilio_service import twilio_service
        if twilio_service.verify_mfa_code(user_record.user_id, payload.code):
            has_step_up = True
        else:
            raise HTTPException(status_code=401, detail="Step-up authentication failed: invalid verification code.")

    if not has_step_up:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Step-up authentication required to disable MFA. Please provide current password or SMS verification code."
        )

    user_record.mfa_enabled = False
    db.commit()
    return {"status": "disabled", "message": "SMS Multi-Factor Authentication disabled successfully."}


@app.post("/api/v1/admin/alerts/test-sms")
def test_twilio_sms_alert(
    payload: TestAlertSMSRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Test administrative dispatch of Twilio SMS notifications."""
    if getattr(current_user, "role", "") not in auth.ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Administrative privileges required.")

    from twilio_service import twilio_service
    target = payload.recipient_phone or twilio_service.alert_phone or "+15005550006"
    msg = payload.message or "[FFIRE TEST ALERT] Verification of Twilio SMS alerting connectivity."
    res = twilio_service.send_sms(target, msg)
    # Report delivery only; the message text is not echoed back.
    return {"status": "success", "result": {k: v for k, v in res.items() if k != "body"}}




@app.post("/api/v1/auth/bootstrap", response_model=Token)

def bootstrap_initial_admin(

    payload: BootstrapRequest,

    request: Request,

    db: Session = Depends(get_db)

):

    """

    Initial instance bootstrap endpoint (P0 Remediation).

    Only permitted when no users exist in the database and a valid BOOTSTRAP_SECRET_KEY is provided.

    Creates the first administrator account with server-assigned 'admin' role.

    """

    expected_secret = os.getenv("BOOTSTRAP_SECRET_KEY")

    if not expected_secret:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Bootstrap initialization is disabled: BOOTSTRAP_SECRET_KEY is not configured in server environment."

        )



    provided_secret = (

        request.headers.get("X-Bootstrap-Secret")

        or payload.bootstrap_secret

    )

    if not provided_secret or not hmac.compare_digest(provided_secret.strip(), expected_secret.strip()):

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Invalid or missing bootstrap secret key."

        )



    if db.query(models.User).count() > 0:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Bootstrap initialization is disabled: System already contains registered users."

        )



    norm_email = payload.email.strip().lower()

    existing_user = auth.get_user_by_email(db, norm_email)

    if existing_user:

        raise HTTPException(status_code=400, detail="Email already registered.")



    tenant = payload.tenant_id.strip() if payload.tenant_id else "tenant_prime"

    # The first account is the installation's operator: the one role that may cross tenant
    # boundaries. Administrators invited afterwards are confined to their own tenant.
    bootstrap_role = auth.PLATFORM_ADMIN_ROLE

    admin_user = models.User(

        name=payload.name,

        email=norm_email,

        role=bootstrap_role,

        hashed_password=auth.get_password_hash(payload.password),

        tenant_id=tenant

    )

    db.add(admin_user)

    db.commit()

    db.refresh(admin_user)



    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = auth.create_access_token(

        data={"sub": norm_email, "role": bootstrap_role, "tenant_id": tenant},

        expires_delta=access_token_expires

    )

    refresh_token = auth.create_refresh_token(

        data={"sub": norm_email, "role": bootstrap_role, "tenant_id": tenant}

    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "tenant_id": tenant}



@app.post("/api/v1/admin/invitations", response_model=InvitationResponse)

def create_tenant_invitation(

    payload: InvitationCreate,

    current_user: models.User = Depends(auth.get_current_user),

    db: Session = Depends(get_db)

):

    """

    Issue a single-use cryptographically secure invitation token for the administrator's tenant.

    Only users with 'admin' or 'administrator' role can issue invitations.

    """

    user_role = getattr(current_user, "role", "")

    if user_role not in auth.ADMIN_ROLES:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Administrative privileges required to issue tenant invitations."

        )



    target_role = (payload.role or "investigator").lower().strip()

    if target_role not in auth.VALID_ROLES:

        raise HTTPException(

            status_code=400,

            detail=f"Invalid invitation role '{target_role}'. Permitted roles: {', '.join(sorted(auth.VALID_ROLES))}"

        )



    token = f"inv_{secrets.token_urlsafe(32)}"

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    expires_at = timeutil.utcnow() + datetime.timedelta(hours=max(1, min(payload.expires_in_hours, 720)))

    tenant_id = getattr(current_user, "tenant_id", "default_tenant")



    inv = models.TenantInvitation(

        token=None,

        token_hash=token_hash,

        tenant_id=tenant_id,

        email=payload.email.strip().lower() if payload.email else None,

        role=target_role,

        created_by=current_user.email or "admin",

        created_at=timeutil.utcnow(),

        expires_at=expires_at,

        is_used=False

    )

    db.add(inv)

    db.commit()

    db.refresh(inv)



    return InvitationResponse(

        invitation_id=inv.invitation_id,

        token=token,

        token_hash=token_hash,

        tenant_id=inv.tenant_id,

        email=inv.email,

        role=inv.role,

        expires_at=inv.expires_at.isoformat(),

        created_at=inv.created_at.isoformat(),

        is_used=inv.is_used

    )



@app.get("/api/v1/admin/invitations", response_model=List[InvitationResponse])

def list_tenant_invitations(

    current_user: models.User = Depends(auth.get_current_user),

    db: Session = Depends(get_db)

):

    """List all invitations for the administrator's tenant."""

    user_role = getattr(current_user, "role", "")

    if user_role not in auth.ADMIN_ROLES:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Administrative privileges required to view tenant invitations."

        )

    tenant_id = getattr(current_user, "tenant_id", "default_tenant")

    invitations = db.query(models.TenantInvitation).filter(

        models.TenantInvitation.tenant_id == tenant_id

    ).order_by(models.TenantInvitation.created_at.desc()).all()



    return [

        InvitationResponse(

            invitation_id=inv.invitation_id,

            token=None,

            token_hash=inv.token_hash,

            tenant_id=inv.tenant_id,

            email=inv.email,

            role=inv.role,

            expires_at=inv.expires_at.isoformat(),

            created_at=inv.created_at.isoformat(),

            is_used=inv.is_used

        )

        for inv in invitations

    ]



@app.delete("/api/v1/admin/invitations/{invitation_id}")

def revoke_tenant_invitation(

    invitation_id: str,

    current_user: models.User = Depends(auth.get_current_user),

    db: Session = Depends(get_db)

):

    """Revoke a pending tenant invitation."""

    user_role = getattr(current_user, "role", "")

    if user_role not in auth.ADMIN_ROLES:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Administrative privileges required to revoke tenant invitations."

        )

    tenant_id = getattr(current_user, "tenant_id", "default_tenant")

    inv = db.query(models.TenantInvitation).filter(

        models.TenantInvitation.invitation_id == invitation_id,

        models.TenantInvitation.tenant_id == tenant_id

    ).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Invitation not found.")



    db.delete(inv)

    db.commit()

    return {"status": "success", "message": f"Invitation {invitation_id} revoked."}



@app.post("/api/v1/auth/logout")

def logout_user(token: str = Depends(auth.oauth2_scheme), current_user: models.User = Depends(auth.get_current_user)):

    """
    End the session: revoke this access token and every token issued to the user up to now,
    refresh tokens included. Revoking the access token alone left the refresh token able to mint
    new ones, so logging out did not log anyone out.
    """
    auth.revoke_token(token)
    auth.revoke_user_sessions(current_user.email)
    return {"status": "success", "message": "Successfully logged out. Access and refresh tokens revoked."}



@app.post("/api/v1/auth/login", response_model=Token)

def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = auth.get_user_by_email(db, form_data.username)

    if not user or not auth.verify_password(form_data.password, user.hashed_password):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Incorrect username or password",

            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.is_active_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    tenant = getattr(user, "tenant_id", "default_tenant")
    # SMS Multi-Factor Authentication check (Strict Fail-Closed Enforcement)
    if getattr(user, "mfa_enabled", False):
        if not getattr(user, "phone_number", None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA is enabled for this account but no verified phone number is registered. Please contact an administrator."
            )
        try:
            from twilio_service import twilio_service
            masked_phone, mfa_ticket = twilio_service.generate_and_send_mfa_code(user.user_id, user.phone_number)
            return Token(
                mfa_required=True,
                mfa_ticket=mfa_ticket,
                masked_phone=masked_phone,
                message=f"Two-factor authentication code sent via SMS to {masked_phone}."
            )
        except HTTPException:
            raise
        except Exception as exc:
            logging.getLogger("ffire.auth").error(f"Failed to initiate SMS MFA challenge: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MFA verification service is temporarily unavailable. Access denied."
            )
    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = auth.create_access_token(

        data={"sub": user.email, "role": user.role, "tenant_id": tenant}, expires_delta=access_token_expires

    )

    refresh_token = auth.create_refresh_token(

        data={"sub": user.email, "role": user.role, "tenant_id": tenant}

    )

    return {
        "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "tenant_id": tenant,
        "role": user.role, "user_id": user.user_id, "name": user.name,
    }


@app.post("/api/v1/auth/refresh", response_model=Token)

def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):

    """Exchange a valid refresh token for a fresh access token and rotated refresh token (Chapter 47)."""

    token_data = auth.decode_refresh_token(payload.refresh_token)

    email = token_data.get("sub")

    if not email:

        raise HTTPException(status_code=401, detail="Invalid refresh token payload")



    user = auth.get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=401, detail="User associated with refresh token no longer exists")
    if not auth.is_active_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")




    # Enforce MFA requirement if enabled for user
    mfa_verified = token_data.get("mfa_verified", False)
    if getattr(user, "mfa_enabled", False) and not mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification required to refresh session tokens."
        )

    tenant = getattr(user, "tenant_id", "default_tenant")
    new_access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role, "tenant_id": tenant, "mfa_verified": mfa_verified},
        expires_delta=datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = auth.create_refresh_token(
        data={"sub": user.email, "role": user.role, "tenant_id": tenant, "mfa_verified": mfa_verified}
    )
    # Rotation: the token just used is spent. Without this an old refresh token stayed valid for
    # its full seven days after being exchanged.
    try:
        auth.revoke_token(payload.refresh_token, ttl_seconds=auth.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Token revocation registry unavailable")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "tenant_id": tenant,
        "role": user.role,
        "user_id": user.user_id,
        "name": user.name,
    }





def build_investigation_response(inv: models.Investigation, db: Session) -> InvestigationResponse:

    evidence_list = [EvidenceResponse(source=ev.source, snippet=ev.snippet) for ev in inv.evidence]

    audit_log_list = [AuditLogResponse.model_validate(al) for al in inv.audit_logs]



    amount = None

    currency = None

    customer_name = None

    risk_score = None

    if inv.transaction:

        amount = float(inv.transaction.amount)

        currency = inv.transaction.currency

        acct = db.query(models.Account).filter(models.Account.account_id == inv.transaction.account_id).first()

        if acct:

            cust = db.query(models.Customer).filter(models.Customer.customer_id == acct.customer_id).first()

            if cust:

                customer_name = cust.name

                

    if inv.risk_score is not None:

        risk_score = float(inv.risk_score)

    else:

        risk_score = None



    return InvestigationResponse(

        investigation_id=inv.investigation_id,

        transaction_id=inv.txn_id,

        status=inv.status,

        confidence=inv.confidence,

        report=inv.report,

        evidence=evidence_list,

        audit_logs=audit_log_list,

        amount=amount,

        currency=currency,

        customer_name=customer_name,

        risk_score=risk_score,

        created_at=inv.created_at,

        tenant_id=getattr(inv, "tenant_id", "default_tenant")

    )



def enforce_tenant_isolation(current_user: models.User, inv: models.Investigation):

    """

    Mandatory tenant isolation enforcement:

    Admin users can access all records. Non-admin users can ONLY access records matching their tenant_id.

    Fails closed (403) if tenant_id is missing, null, or mismatched on either the user or the investigation.

    """

    if auth.is_platform_admin(current_user):

        return

    user_tenant = getattr(current_user, "tenant_id", None)

    inv_tenant = getattr(inv, "tenant_id", None)

    if not user_tenant or not inv_tenant:

        raise HTTPException(

            status_code=403,

            detail="Access denied: Missing tenant context (fail-closed)"

        )

    if inv_tenant != user_tenant:

        raise HTTPException(

            status_code=403,

            detail="Access denied: Resource belongs to another tenant"

        )



def investigation_execution_mode() -> str:
    """
    "worker": a separate worker process takes jobs from the Redis queue and runs them.
    "inline": this API process runs each investigation as a background task.

    Exactly one of the two runs a given investigation. Doing both (as the code once did) ran every
    investigation twice whenever a worker was deployed. INVESTIGATION_EXECUTION sets the mode;
    left unset it is "worker" when a Redis broker is connected and "inline" otherwise. Set it to
    "inline" if you run Redis but no worker.
    """
    configured = os.getenv("INVESTIGATION_EXECUTION", "").strip().lower()
    if configured in ("worker", "inline"):
        return configured
    from worker import worker_queue
    return "inline" if worker_queue.get_broker_backend() == "in_memory" else "worker"


def _dispatch_investigation(investigation_id: str, transaction_id: str, background_tasks: BackgroundTasks) -> None:
    from worker import worker_queue
    if investigation_execution_mode() == "worker":
        worker_queue.enqueue(investigation_id, transaction_id)
    else:
        worker_queue.transition_job_state(investigation_id, "QUEUED")
        background_tasks.add_task(run_investigation_task, investigation_id, transaction_id)


EVIDENCE_MAX_BYTES = int(os.getenv("EVIDENCE_MAX_BYTES", str(25 * 1024 * 1024)))


def demo_seeding_enabled() -> bool:
    """Sample evidence, reports and audit entries are created only when FFRE_DEMO_SEED is switched on."""
    return os.getenv("FFRE_DEMO_SEED", "").strip().lower() in ("1", "true", "yes", "on")


def _require_same_tenant(current_user: models.User, record_tenant: Optional[str], what: str = "Record") -> None:
    """403 unless the record is in the caller's tenant. A caller with no tenant is refused, not waved through."""
    if auth.is_platform_admin(current_user):
        return
    user_tenant = getattr(current_user, "tenant_id", None)
    if not user_tenant or record_tenant != user_tenant:
        raise HTTPException(status_code=403, detail=f"Access denied: {what} belongs to another tenant")


# Roles that work cases (administrators are always allowed as well).
CASE_WORKER_ROLES = ("investigator", "analyst", "compliance_officer")
CANCELLABLE_STATUSES = {"QUEUED", "RUNNING", "RETRYING", "WAITING_HUMAN", "ESCALATED", "FAILED"}
REVIEWABLE_STATUSES = {"COMPLETED", "ESCALATED", "WAITING_HUMAN", "FAILED"}


# --- Protected Investigation Routes ---



@app.post("/api/v1/investigations", response_model=InvestigationResponse, status_code=202)

def create_investigation(

    request: InvestigationRequest,

    background_tasks: BackgroundTasks,

    response: Response,

    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("investigator"))

):

    """

    FO-1: Accept an investigation request for a transaction or customer identifier.

    """

    # Task 15: Explicit Header or Payload-derived Idempotency Key Handling

    # Prompt injection guardrail defense (Chapters 47 & 88)

    is_inj, matches, _ = guardrails.detect_prompt_injection(f"{request.transaction_id} {request.user_id}")

    if is_inj:

        raise HTTPException(

            status_code=400,

            detail=f"Security Alert: Adversarial prompt injection detected in payload: {', '.join(matches)}"

        )



    user_tenant = getattr(current_user, "tenant_id", "default_tenant")

    payload_fp = hashlib.sha256(f"{request.transaction_id}:{request.user_id}".encode("utf-8")).hexdigest()



    if idempotency_key_header:

        idemp_key = f"idemp_{idempotency_key_header.strip()}"

    else:

        raw_key = f"{user_tenant}:{request.transaction_id}:{request.user_id}"

        idemp_key = f"idemp_{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    with _investigation_creation_lock:
        existing_inv = db.query(models.Investigation).filter(
            models.Investigation.idempotency_key == idemp_key,
            models.Investigation.tenant_id == user_tenant,
            models.Investigation.status.in_(["RUNNING", "QUEUED", "COMPLETED", "WAITING_HUMAN", "ESCALATED", "FAILED"])
        ).first()

        if existing_inv:
            if (existing_inv.request_fingerprint and existing_inv.request_fingerprint != payload_fp) or existing_inv.txn_id != request.transaction_id:
                raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
            if existing_inv.status == "FAILED":
                # A failed run is not a result worth caching: asking again retries it. Returning the
                # failure as a cache hit made the transaction impossible to investigate ever again.
                existing_inv.status = "QUEUED"
                existing_inv.report = None
                existing_inv.updated_at = timeutil.utcnow()
                db.add(models.AuditLog(
                    investigation_id=existing_inv.investigation_id,
                    action="Investigation Retried",
                    details="Previous run failed; re-queued on a repeated request.",
                    tenant_id=user_tenant,
                ))
                db.commit()
                _dispatch_investigation(existing_inv.investigation_id, request.transaction_id, background_tasks)
                response.headers["X-Cache-Hit"] = "false"
                return build_investigation_response(existing_inv, db)
            response.headers["X-Cache-Hit"] = "true"
            return build_investigation_response(existing_inv, db)
        # Verify transaction exists under caller's tenant (Task T0.2 / Finding V1)
        txn = db.query(models.Transaction).filter(
            models.Transaction.txn_id == request.transaction_id,
            models.Transaction.tenant_id == user_tenant
        ).first()
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")

        inv = models.Investigation(
            txn_id=request.transaction_id,
            status="QUEUED",
            idempotency_key=idemp_key,
            request_fingerprint=payload_fp,
            tenant_id=user_tenant
        )
        db.add(inv)
        try:
            db.commit()
            db.refresh(inv)
        except IntegrityError:
            db.rollback()
            existing_inv = db.query(models.Investigation).filter(
                models.Investigation.idempotency_key == idemp_key,
                models.Investigation.tenant_id == user_tenant
            ).first()
            if existing_inv:
                if (existing_inv.request_fingerprint and existing_inv.request_fingerprint != payload_fp) or existing_inv.txn_id != request.transaction_id:
                    raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
                response.headers["X-Cache-Hit"] = "true"
                return build_investigation_response(existing_inv, db)
            raise

    audit_log = models.AuditLog(
        investigation_id=inv.investigation_id,

        action="Investigation Started",

        tenant_id=user_tenant

    )

    db.add(audit_log)

    db.commit()



    _dispatch_investigation(inv.investigation_id, request.transaction_id, background_tasks)
    response.headers["X-Cache-Hit"] = "false"

    return build_investigation_response(inv, db)



# --- Transaction Ingestion Connector (Task T1.2 / Finding V8) ---



@app.post("/api/v1/transactions/ingest", response_model=TransactionIngestResponse)

async def ingest_transactions(

    request: Request,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("investigator"))

):

    """

    Task T1.2 / Finding V8: Batch Transaction Ingestion Connector & CSV Import.

    Supports JSON batch arrays or CSV text/multipart payloads.

    Enforces tenant scoping, validation, quarantine accounting, and idempotency skipping.

    """

    user_tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    content_type = request.headers.get("content-type", "").lower()



    raw_records: List[Dict[str, Any]] = []



    # 1. Parse payload based on content-type

    if "multipart/form-data" in content_type:

        form = await request.form()

        file_obj = form.get("file")

        if not file_obj or not hasattr(file_obj, "read"):
            raise HTTPException(status_code=400, detail="Missing file in multipart/form-data upload")
        content_bytes = await file_obj.read()

        text = content_bytes.decode("utf-8", errors="replace")

        reader = csv.DictReader(io.StringIO(text))

        for row in reader:

            raw_records.append(dict(row))

    elif "text/csv" in content_type:

        body = await request.body()

        text = body.decode("utf-8", errors="replace")

        reader = csv.DictReader(io.StringIO(text))

        for row in reader:

            raw_records.append(dict(row))

    else:

        # Default JSON parsing

        try:

            body_json = await request.json()

        except Exception as e:

            raise HTTPException(status_code=400, detail=f"Malformed JSON: {str(e)}")

        if isinstance(body_json, list):

            raw_records = body_json

        elif isinstance(body_json, dict) and "transactions" in body_json:

            raw_records = body_json["transactions"]

        elif isinstance(body_json, dict):

            raw_records = [body_json]

        else:

            raise HTTPException(status_code=400, detail="JSON payload must be an array or object with 'transactions' key")



    if not isinstance(raw_records, list):
        raise HTTPException(status_code=400, detail="'transactions' must be an array of records")
    if len(raw_records) > INGEST_MAX_ROWS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large: {len(raw_records)} records. Send at most {INGEST_MAX_ROWS} per request."
        )
    return await run_in_threadpool(_sync_process_transactions, db, raw_records, user_tenant, current_user.role)



MAX_TRANSACTION_AMOUNT = Decimal("10000000000")  # NUMERIC(12, 2) holds values below 10^10
INGEST_MAX_ROWS = int(os.getenv("INGEST_MAX_ROWS", "10000"))


def _sync_process_transactions(db: Session, raw_records: List[Dict[str, Any]], user_tenant: str, caller_role: str) -> TransactionIngestResponse:

    total_records = len(raw_records)

    ingested = 0

    quarantined = 0

    skipped_duplicates = 0

    quarantine_reasons = []



    ALLOWED_CHANNELS = {"web", "mobile", "pos", "atm", "api", "wire", "ach", "branch", "other"}



    for idx, row in enumerate(raw_records, start=1):
        if not isinstance(row, dict):
            # A batch entry that is not an object (a bare string or number) has no fields to read.
            quarantined += 1
            quarantine_reasons.append(QuarantineReason(
                row_index=idx,
                txn_id=None,
                reason="Malformed record: each entry must be a JSON object",
                record={"raw": str(row)[:200]}
            ))
            continue
        txn_id = row.get("txn_id")

        if txn_id and isinstance(txn_id, str):

            txn_id = txn_id.strip() or None

        else:

            txn_id = None



        # Tenant isolation check

        row_tenant = row.get("tenant_id")

        effective_tenant = user_tenant

        if row_tenant and str(row_tenant).strip():

            row_tenant_str = str(row_tenant).strip()

            if caller_role != auth.PLATFORM_ADMIN_ROLE and row_tenant_str != user_tenant:

                quarantined += 1

                quarantine_reasons.append(QuarantineReason(

                    row_index=idx,

                    txn_id=txn_id,

                    reason=f"Cross-tenant violation: Caller ({user_tenant}) cannot ingest on behalf of tenant '{row_tenant_str}'",

                    record=row

                ))

                continue

            effective_tenant = row_tenant_str



        # Account validation

        account_id = row.get("account_id")

        if not account_id:

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason="Missing required field: account_id",

                record=row

            ))

            continue

        account_id = str(account_id).strip()



        acct = db.query(models.Account).filter(models.Account.account_id == account_id).first()

        if not acct:

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason=f"Referenced account '{account_id}' does not exist",

                record=row

            ))

            continue



        acct_tenant = getattr(acct, "tenant_id", "default_tenant")

        if caller_role != auth.PLATFORM_ADMIN_ROLE and acct_tenant != effective_tenant:

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason=f"Cross-tenant violation: Account '{account_id}' belongs to tenant '{acct_tenant}'",

                record=row

            ))

            continue



        # Amount validation

        raw_amt = row.get("amount")

        if raw_amt is None or raw_amt == "":

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason="Missing required field: amount",

                record=row

            ))

            continue

        try:
            # Decimal, not float: the column is NUMERIC(12, 2), and float() happily parses "nan"
            # and "inf", which pass a "<= 0" test and then poison every sum they take part in.
            amount_val = Decimal(str(raw_amt).strip())
            if not amount_val.is_finite():
                raise ValueError("non-finite amount")
        except (ValueError, TypeError, ArithmeticError):

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason=f"Invalid numeric amount '{raw_amt}'",

                record=row

            ))

            continue



        if amount_val <= 0:

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=txn_id,

                reason=f"Invalid amount {amount_val}: amount must be strictly positive",
                record=row
            ))
            continue
        if amount_val >= MAX_TRANSACTION_AMOUNT:
            quarantined += 1
            quarantine_reasons.append(QuarantineReason(
                row_index=idx,
                txn_id=txn_id,
                reason=f"Invalid amount {amount_val}: exceeds the supported maximum of {MAX_TRANSACTION_AMOUNT}",
                record=row
            ))
            continue
        amount_val = amount_val.quantize(Decimal("0.01"))



        # Channel validation

        channel_val = row.get("channel")

        if channel_val and isinstance(channel_val, str) and channel_val.strip():

            channel_val = channel_val.strip().lower()

            if channel_val not in ALLOWED_CHANNELS:

                quarantined += 1

                quarantine_reasons.append(QuarantineReason(

                    row_index=idx,

                    txn_id=txn_id,

                    reason=f"Invalid channel '{channel_val}': must be one of {sorted(ALLOWED_CHANNELS)}",

                    record=row

                ))

                continue

        else:

            channel_val = None



        # Currency validation

        currency_val = row.get("currency")

        if currency_val and isinstance(currency_val, str) and currency_val.strip():

            currency_val = currency_val.strip().upper()

            if len(currency_val) != 3 or not currency_val.isalpha():

                quarantined += 1

                quarantine_reasons.append(QuarantineReason(

                    row_index=idx,

                    txn_id=txn_id,

                    reason=f"Invalid currency code '{currency_val}': must be 3-letter ISO-4217 code",

                    record=row

                ))

                continue

        else:

            currency_val = "USD"



        # Timestamp validation

        timestamp_val = timeutil.utcnow()

        raw_ts = row.get("timestamp")

        if raw_ts and isinstance(raw_ts, str) and raw_ts.strip():

            raw_ts = raw_ts.strip()

            try:

                ts_clean = raw_ts.replace("Z", "+00:00")

                timestamp_val = datetime.datetime.fromisoformat(ts_clean)

            except Exception:

                quarantined += 1

                quarantine_reasons.append(QuarantineReason(

                    row_index=idx,

                    txn_id=txn_id,

                    reason=f"Malformed timestamp '{raw_ts}': must be valid ISO-8601 format",

                    record=row

                ))

                continue

        elif isinstance(raw_ts, datetime.datetime):
            timestamp_val = raw_ts
        # Stored timestamps are naive UTC. Convert an offset-aware value instead of dropping its
        # offset, which would record 10:00+05:30 as 10:00 UTC.
        if timestamp_val.tzinfo is not None:
            timestamp_val = timestamp_val.astimezone(datetime.timezone.utc).replace(tzinfo=None)



        # Idempotency / Duplicate check

        if txn_id:

            existing = db.query(models.Transaction).filter(

                models.Transaction.tenant_id == effective_tenant,

                models.Transaction.txn_id == txn_id

            ).first()

            if existing:

                skipped_duplicates += 1

                continue



        # Create Transaction

        assigned_txn_id = txn_id or f"txn_{uuid.uuid4().hex[:12]}"

        new_txn = models.Transaction(

            txn_id=assigned_txn_id,

            tenant_id=effective_tenant,

            account_id=account_id,

            merchant_id=row.get("merchant_id") or None,

            amount=amount_val,

            currency=currency_val,

            status=row.get("status") or "PENDING",

            timestamp=timestamp_val,

            counterparty=row.get("counterparty") or None,

            channel=channel_val,

            ip_address=row.get("ip_address") or None,

            device_ref=row.get("device_ref") or None,

        )

        db.add(new_txn)

        try:

            db.commit()

            ingested += 1

        except Exception as e:

            db.rollback()

            quarantined += 1

            quarantine_reasons.append(QuarantineReason(

                row_index=idx,

                txn_id=assigned_txn_id,

                reason="Database rejected the record (for example a duplicate transaction id or an unknown merchant)",

                record=row

            ))



    return TransactionIngestResponse(

        total_records=total_records,

        ingested=ingested,

        quarantined=quarantined,

        skipped_duplicates=skipped_duplicates,

        quarantine_reasons=quarantine_reasons

    )



@app.get("/api/v1/transactions", response_model=List[TransactionResponse])

def list_transactions(

    limit: int = 50,

    offset: int = 0,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """List transactions scoped to the caller's tenant."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    offset = max(0, offset)
    user_tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    query = db.query(models.Transaction)

    if not auth.is_platform_admin(current_user):

        query = query.filter(models.Transaction.tenant_id == user_tenant)

    return query.order_by(desc(models.Transaction.timestamp)).offset(offset).limit(limit).all()



@app.get("/api/v1/transactions/{txn_id}", response_model=TransactionResponse)

def get_transaction_by_id(

    txn_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Get single transaction by ID scoped to the caller's tenant."""

    txn = db.query(models.Transaction).filter(models.Transaction.txn_id == txn_id).first()

    if not txn:

        raise HTTPException(status_code=404, detail="Transaction not found")

    user_tenant = getattr(current_user, "tenant_id", "default_tenant")

    if not auth.is_platform_admin(current_user) and getattr(txn, "tenant_id", None) != user_tenant:

        raise HTTPException(status_code=403, detail="Access denied: Resource belongs to another tenant")

    return txn



@app.get("/api/v1/investigations/{investigation_id}", response_model=InvestigationResponse)

def get_investigation(

    investigation_id: str, 

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Get the status and result of a specific investigation.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv or getattr(inv, "is_deleted", False):

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)

        

    return build_investigation_response(inv, db)



# --- Chapter 30: LangGraph Execution Monitor API ---



@app.get("/api/v1/graph/{investigation_id}")

def get_investigation_graph(

    investigation_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Chapter 30: LangGraph Execution Monitor API returning interactive DAG topology, node states, and metrics."""

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    is_completed = inv.status in ("COMPLETED", "ESCALATED", "CLOSED_APPROVE", "CLOSED_REJECT")

    is_running = inv.status in ("RUNNING", "QUEUED", "RETRYING")



    raw_evidence = {ev.source: ev.snippet for ev in inv.evidence}



    nodes = [

        {

            "id": "planner",

            "name": "Planner & Strategy",

            "category": "planning",

            "status": "completed" if (is_completed or is_running) else "pending",

            "duration_ms": 145,

            "tokens": 420,

            "prompt_version": "v2.1-prod",

            "dependencies": [],

            "description": "Decomposes investigation into concurrent retrieval and assessment sub-tasks.",

            "inputs": {"transaction_id": inv.txn_id, "investigation_id": inv.investigation_id},

            "outputs": {"tasks": ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location"]}

        },

        {

            "id": "retrieve_customer",

            "name": "Customer Retriever",

            "category": "retrieval",

            "status": "completed" if is_completed else ("running" if is_running else "pending"),

            "duration_ms": 120,

            "tokens": 280,

            "prompt_version": "v1.8-prod",

            "dependencies": ["planner"],

            "description": "Fetches customer profile, historical baseline, and KYC verification status.",

            "inputs": {"customer_id": "cust-profile"},

            "outputs": {"customer_evidence": raw_evidence.get("customer_evidence", "KYC verified")}

        },

        {

            "id": "retrieve_transaction",

            "name": "Transaction Retriever",

            "category": "retrieval",

            "status": "completed" if is_completed else ("running" if is_running else "pending"),

            "duration_ms": 95,

            "tokens": 310,

            "prompt_version": "v1.4-prod",

            "dependencies": ["planner"],

            "description": "Queries historical velocity, transaction clustering, and counterparty graphs.",

            "inputs": {"transaction_id": inv.txn_id},

            "outputs": {"transaction_evidence": raw_evidence.get("transaction_evidence", "Anomaly score 0.82")}

        },

        {

            "id": "retrieve_merchant",

            "name": "Merchant Retriever",

            "category": "retrieval",

            "status": "completed" if is_completed else ("running" if is_running else "pending"),

            "duration_ms": 110,

            "tokens": 195,

            "prompt_version": "v1.2-prod",

            "dependencies": ["planner"],

            "description": "Checks merchant risk profile, chargeback ratios, and high-risk categorization.",

            "inputs": {"merchant_id": "merch-profile"},

            "outputs": {"merchant_evidence": raw_evidence.get("merchant_evidence", "High-risk category")}

        },

        {

            "id": "retrieve_device",

            "name": "Device Intelligence",

            "category": "retrieval",

            "status": "completed" if is_completed else ("running" if is_running else "pending"),

            "duration_ms": 85,

            "tokens": 240,

            "prompt_version": "v2.0-prod",

            "dependencies": ["planner"],

            "description": "Analyzes hardware fingerprint, browser telemetry, and emulator detection.",

            "inputs": {"fingerprint": "dev-hash"},

            "outputs": {"device_evidence": raw_evidence.get("device_evidence", "Unrecognized device fingerprint")}

        },

        {

            "id": "retrieve_location",

            "name": "Location & Travel",

            "category": "retrieval",

            "status": "completed" if is_completed else ("running" if is_running else "pending"),

            "duration_ms": 130,

            "tokens": 260,

            "prompt_version": "v1.5-prod",

            "dependencies": ["planner"],

            "description": "Evaluates IP geolocation, VPN/proxy exit nodes, and impossible travel physics.",

            "inputs": {"ip": "client-ip", "geo": "coordinates"},

            "outputs": {"location_evidence": raw_evidence.get("location_evidence", "Distance mismatch: 3400 miles")}

        },

        {

            "id": "evidence_aggregator",

            "name": "Evidence Aggregator",

            "category": "synthesis",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 65,

            "tokens": 180,

            "prompt_version": "v2.2-prod",

            "dependencies": ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location"],

            "description": "Fuses heterogeneous signal vectors into unified investigation state.",

            "inputs": {"evidence_sources": 5},

            "outputs": {"aggregated_signals": len(raw_evidence)}

        },

        {

            "id": "evidence_validator",

            "name": "Evidence Validator",

            "category": "validation",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 140,

            "tokens": 390,

            "prompt_version": "v1.9-prod",

            "dependencies": ["evidence_aggregator"],

            "description": "Performs cross-signal corroboration and flags evidential contradictions.",

            "inputs": {"signals": len(raw_evidence)},

            "outputs": {"corroborated": True, "contradictions": 0}

        },

        {

            "id": "reasoner",

            "name": "Multi-Agent Reasoner",

            "category": "reasoning",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 420,

            "tokens": 1250,

            "prompt_version": "v3.0-prod",

            "dependencies": ["evidence_validator"],

            "description": "Executes chain-of-thought financial crime pattern deduction.",

            "inputs": {"validated_signals": True},

            "outputs": {"preliminary_verdict": "FRAUD_SUSPECTED", "risk_score": float(inv.risk_score) if inv.risk_score is not None else None}

        },

        {

            "id": "critic",

            "name": "Critic & Reflection",

            "category": "reasoning",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 280,

            "tokens": 640,

            "prompt_version": "v2.4-prod",

            "dependencies": ["reasoner"],

            "description": "Adversarially evaluates reasoning logic to detect hallucinations or weak inferences.",

            "inputs": {"reasoning_chain": "ATO deduction"},

            "outputs": {"critique_passed": True, "confidence_adjustment": "+0.05"}

        },

        {

            "id": "confidence_calculator",

            "name": "Confidence Calculator",

            "category": "scoring",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 75,

            "tokens": 120,

            "prompt_version": "v1.0-prod",

            "dependencies": ["critic"],

            "description": "Computes final weighted Bayesian confidence score across all domain vectors.",

            "inputs": {"critique": "PASSED"},

            "outputs": {"final_confidence": float(inv.confidence or 0.92)}

        },

        {

            "id": "reporter",

            "name": "Executive Reporter",

            "category": "reporting",

            "status": "completed" if is_completed else "pending",

            "duration_ms": 310,

            "tokens": 890,

            "prompt_version": "v2.5-prod",

            "dependencies": ["confidence_calculator"],

            "description": "Synthesizes regulatory narrative, explainable dossier, and SAR-ready summaries.",

            "inputs": {"status": inv.status},

            "outputs": {"report_generated": bool(inv.report)}

        }

    ]



    # Replace the placeholder figures above with what was actually recorded. The pipeline writes one
    # audit entry per node run ("NODE_EXECUTION: <node>", "... in <n>ms"), so timings and completion
    # come from there. Token counts are not recorded per node, so they are reported as unmeasured
    # (zero, with "measured": false) instead of an invented number.
    display_to_pipeline = {
        "evidence_aggregator": ["evidence_verifier", "velocity_check", "rule_engine", "knowledge_lookup"],
        "evidence_validator": ["validator"],
        "reasoner": ["risk_reasoning"],
        "confidence_calculator": ["validator"],
        "reporter": ["report_generator", "human_review"],
    }
    recorded_ms: Dict[str, int] = {}
    for entry in inv.audit_logs:
        action = entry.action or ""
        if not action.startswith("NODE_EXECUTION: "):
            continue
        timing = re.search(r" in (\d+)ms", entry.details or "")
        if timing:
            node_key = action.split(": ", 1)[1].strip()
            recorded_ms[node_key] = recorded_ms.get(node_key, 0) + int(timing.group(1))
    for node in nodes:
        sources = display_to_pipeline.get(node["id"], [node["id"]])
        ran = [s for s in sources if s in recorded_ms]
        node["measured"] = bool(ran)
        node["duration_ms"] = sum(recorded_ms[s] for s in ran)
        node["tokens"] = 0
        node["prompt_version"] = None
        if ran:
            node["status"] = "completed"
        elif is_completed:
            node["status"] = "skipped"
        elif node["status"] == "completed":
            node["status"] = "running" if is_running else "pending"
        outputs = node.get("outputs") or {}
        if outputs.get("transaction_evidence") == "Anomaly score 0.82":
            outputs["transaction_evidence"] = None
        outputs.pop("contradictions", None)
        outputs.pop("corroborated", None)
        if "preliminary_verdict" in outputs:
            outputs["preliminary_verdict"] = None
        if "final_confidence" in outputs:
            outputs["final_confidence"] = float(inv.confidence) if inv.confidence is not None else None

    total_duration = sum(n["duration_ms"] for n in nodes if n["status"] == "completed")
    usage = metrics_collector.get_investigation_token_usage(investigation_id) if hasattr(metrics_collector, "get_investigation_token_usage") else None
    return {
        "investigation_id": inv.investigation_id,
        "status": inv.status,
        "graph_version": "v2.4.0-langgraph",
        "nodes": nodes,
        "metrics": {
            "total_runtime_ms": total_duration,
            "average_node_runtime_ms": round(total_duration / max(1, sum(1 for n in nodes if n["status"] == "completed")), 1),
            "total_tokens": (usage or {}).get("total_tokens", 0),
            "prompt_tokens": (usage or {}).get("prompt_tokens", 0),
            "completion_tokens": (usage or {}).get("completion_tokens", 0),
            "estimated_cost_usd": (usage or {}).get("cost_usd", 0.0),
            "tokens_measured": usage is not None,
            "completed_nodes": sum(1 for n in nodes if n["status"] == "completed"),
            "total_nodes": len(nodes)
        }
    }



@app.post("/api/v1/investigations/{investigation_id}/cancel", response_model=InvestigationResponse)

def cancel_investigation(

    investigation_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Task 14: Cancel a running investigation protocol."""

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)
    auth.require_role(current_user, *CASE_WORKER_ROLES)
    # Only work that is still open can be cancelled. A finished or human-closed case must not be
    # flipped to CANCELLED, which would erase its outcome.
    if inv.is_deleted or inv.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Cannot cancel investigation in status {inv.status}")
    inv.status = "CANCELLED"
    audit_log = models.AuditLog(
        investigation_id=inv.investigation_id,
        tenant_id=getattr(inv, "tenant_id", None) or "default_tenant",
        action="INVESTIGATION_CANCELLED",
        details=f"Cancelled by user {getattr(current_user, 'email', current_user.user_id)}"
    )

    db.add(audit_log)

    db.commit()

    db.refresh(inv)



    from worker import worker_queue

    worker_queue.cancel(investigation_id)

    return build_investigation_response(inv, db)



@app.post("/api/v1/investigations/{investigation_id}/review")

def review_investigation(

    investigation_id: str,

    review_action: HumanReviewAction,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Handle human review action (APPROVE or REJECT) for an investigation.

    Updates status, records risk adjustment, appends analyst resolution to report, and logs audit trail.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)
    auth.require_role(current_user, *CASE_WORKER_ROLES)
    # A case is reviewed once the pipeline has finished with it. Reviewing one that is still running
    # let the pipeline overwrite the analyst's decision when it completed.
    if inv.is_deleted or inv.status not in REVIEWABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Cannot review investigation in status {inv.status}")



    action_type = review_action.action.upper()

    if action_type not in ["APPROVE", "REJECT"]:

        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")



    # The analyst's decision is recorded in the status, the report and the audit log. The model's
    # risk score is left as computed: overwriting it with 0.10 or 0.95 destroyed the very number
    # the decision was made against.
    inv.status = f"CLOSED_{action_type}"
    notes_str = f"Analyst Review ({action_type}) by {current_user.name}: {review_action.notes or 'No additional notes provided'}"

    if inv.report:

        inv.report += f"\n\n### Human Analyst Resolution\n**Verdict**: {action_type}\n**Reviewer**: {current_user.name}\n**Notes**: {review_action.notes or 'None'}"

    else:

        inv.report = f"## Investigation Report\n**Status**: CLOSED_{action_type}\n\n### Human Analyst Resolution\n{notes_str}"



    audit_log = models.AuditLog(

        investigation_id=inv.investigation_id,

        action=f"HUMAN_REVIEW: {action_type}",

        details=notes_str,

        tenant_id=getattr(inv, "tenant_id", "default_tenant")

    )

    db.add(audit_log)

    db.commit()

    db.refresh(inv)



    # Record outcome metrics

    metrics_collector.stop_investigation_timer(investigation_id, status="completed" if action_type == "APPROVE" else "failed")



    return {"status": "success", "new_status": inv.status, "investigation": build_investigation_response(inv, db)}



@app.get("/api/v1/investigations", response_model=InvestigationListResponse)

def list_investigations(

    page: int = Query(1, ge=1, description="Page number"),

    page_size: int = Query(10, ge=1, le=100, description="Items per page"),

    status: Optional[str] = Query(None, description="Filter by investigation status"),

    txn_id: Optional[str] = Query(None, description="Filter by transaction ID or search term"),

    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),

    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),

    sort_by: str = Query("created_at", description="Field to sort by (created_at, investigation_id, status, confidence)"),

    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Get a list of investigations with pagination, filtering, and sorting.



    This endpoint supports:

    - Pagination via page and page_size parameters

    - Filtering by status, transaction ID search, and date range (start_date, end_date)

    - Sorting by various fields (default: created_at)



    Returns a paginated list of investigations suitable for display in a dashboard or queue view.

    """

    # Build the base query

    query = db.query(models.Investigation)

    if not auth.is_platform_admin(current_user):

        user_tenant = getattr(current_user, "tenant_id", None)

        if not user_tenant:

            raise HTTPException(status_code=403, detail="Access denied: Non-admin user missing tenant context")

        query = query.filter(models.Investigation.tenant_id == user_tenant)



    # Deleted investigations are hidden unless they are asked for by status.
    if status != "ARCHIVED_DELETED":
        query = query.filter(models.Investigation.is_deleted.is_(False))

    # Apply filters
    if status:
        query = query.filter(models.Investigation.status == status)

    if txn_id:

        search_pattern = f"%{txn_id}%"

        query = query.filter(

            (models.Investigation.txn_id.ilike(search_pattern)) |

            (models.Investigation.investigation_id.ilike(search_pattern))

        )

    if start_date:

        try:

            start_date_dt = datetime.datetime.fromisoformat(start_date)

            query = query.filter(models.Investigation.created_at >= start_date_dt)

        except ValueError:

            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

    if end_date:

        try:

            end_date_dt = datetime.datetime.fromisoformat(end_date)

            query = query.filter(models.Investigation.created_at <= end_date_dt)

        except ValueError:

            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")



    # Apply sorting

    if sort_by == "created_at":

        # Handle null values in created_at by treating them as far past for sorting purposes

        if sort_order == "desc":

            query = query.order_by(desc(func.coalesce(models.Investigation.created_at, datetime.datetime.min)))

        else:

            query = query.order_by(asc(func.coalesce(models.Investigation.created_at, datetime.datetime.min)))

    elif sort_by == "status":

        if sort_order == "desc":

            query = query.order_by(desc(models.Investigation.status))

        else:

            query = query.order_by(asc(models.Investigation.status))

    elif sort_by == "confidence":

        # Handle null values in confidence by treating them as 0 for sorting purposes

        if sort_order == "desc":

            query = query.order_by(desc(func.coalesce(models.Investigation.confidence, 0.0)))

        else:

            query = query.order_by(asc(func.coalesce(models.Investigation.confidence, 0.0)))

    else:

        # Default to sorting by investigation_id (UUID-based, roughly chronological)

        if sort_order == "desc":

            query = query.order_by(desc(models.Investigation.investigation_id))

        else:

            query = query.order_by(asc(models.Investigation.investigation_id))



    # Get total count for pagination

    total = query.count()



    # Apply pagination

    offset = (page - 1) * page_size

    investigations = query.offset(offset).limit(page_size).all()



    # Calculate total pages

    total_pages = (total + page_size - 1) // page_size



    # Convert to response models

    investigation_responses = [build_investigation_response(inv, db) for inv in investigations]



    return InvestigationListResponse(

        investigations=investigation_responses,

        total=total,

        page=page,

        page_size=page_size,

        total_pages=total_pages

    )



@app.get("/api/v1/investigations/{investigation_id}/export")

@app.post("/api/v1/investigations/{investigation_id}/export")

def export_investigation_report(

    investigation_id: str,

    format: str = Query("json", pattern="^(json|pdf|html)$"),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Export full investigation report in JSON, HTML, or PDF format with evidence and audit history.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    response_data = build_investigation_response(inv, db)

    audit_logs = db.query(models.AuditLog).filter(models.AuditLog.investigation_id == investigation_id).order_by(models.AuditLog.timestamp).all()



    audit_trail = [

        {

            "timestamp": log.timestamp.isoformat(),

            "action": log.action,

            "details": log.details

        }

        for log in audit_logs

    ]



    payload = {

        "export_date": timeutil.utcnow().isoformat(),

        "investigation": response_data.model_dump(),

        "audit_trail": audit_trail

    }



    if format == "json":

        return payload

    elif format == "html":

        # Every value below comes from the database: report text, analyst notes, audit details.
        # All of it is escaped, so none of it can run as script in the reader's browser.
        def esc(value) -> str:
            return html.escape("" if value is None else str(value))

        html_content = f"""<!DOCTYPE html>

<html>

<head><title>FFRE Investigation Report - {esc(inv.investigation_id)}</title><style>body{{font-family:sans-serif;margin:40px;color:#1e293b;}} h1{{color:#0f172a;}} table{{border-collapse:collapse;width:100%;margin-top:20px;}} th,td{{border:1px solid #cbd5e1;padding:8px;text-align:left;}} th{{background-color:#f1f5f9;}} .badge{{padding:4px 8px;border-radius:4px;font-weight:bold;background-color:#e2e8f0;}}</style></head>

<body>

<h1>Financial Fraud Investigation Report</h1>

<p><strong>Investigation ID:</strong> {esc(inv.investigation_id)} | <strong>Transaction ID:</strong> {esc(inv.txn_id)}</p>

<p><strong>Status:</strong> <span class="badge">{esc(inv.status)}</span> | <strong>Risk Score:</strong> {inv.risk_score or 'N/A'} | <strong>Confidence:</strong> {inv.confidence or 'N/A'}</p>

<h2>Executive Summary & Findings</h2>

<pre>{esc(inv.report or 'No detailed report available.')}</pre>

<h2>Audit Trail</h2>

<table><tr><th>Timestamp</th><th>Action</th><th>Details</th></tr>

{''.join([f"<tr><td>{esc(log['timestamp'])}</td><td>{esc(log['action'])}</td><td>{esc(log['details'])}</td></tr>" for log in audit_trail])}

</table>

</body>

</html>"""

        return Response(
            content=html_content,
            media_type="text/html",
            headers=SAFE_HTML_EXPORT_HEADERS | {"Content-Disposition": f'attachment; filename="report_{_safe_filename(investigation_id)}.html"'},
        )

    else:

        try:

            from reportlab.lib.pagesizes import letter

            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            from reportlab.lib import colors

            import io



            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

            styles = getSampleStyleSheet()



            title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))

            heading_style = ParagraphStyle('DocHeading', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#1e293b"), spaceBefore=12)

            body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#334155"))



            elements = []

            elements.append(Paragraph("Financial Fraud Investigation Report (FFRE)", title_style))

            elements.append(Spacer(1, 10))



            meta_text = f"<b>Investigation ID:</b> {inv.investigation_id} | <b>Transaction ID:</b> {inv.txn_id}<br/><b>Status:</b> {inv.status} | <b>Risk Score:</b> {inv.risk_score or 'N/A'} | <b>Confidence:</b> {inv.confidence or 'N/A'}<br/><b>Generated Date:</b> {payload['export_date']}"

            elements.append(Paragraph(meta_text, body_style))

            elements.append(Spacer(1, 15))



            import html as html_lib

            elements.append(Paragraph("Executive Summary & Findings", heading_style))

            report_text = html_lib.escape(inv.report or "No report available.").replace('\n', '<br/>')

            elements.append(Paragraph(report_text, body_style))

            elements.append(Spacer(1, 15))



            elements.append(Paragraph(f"Audit Trail ({len(audit_trail)} Entries)", heading_style))



            table_data = [["Timestamp", "Action", "Details"]]

            for log in audit_trail[:30]:

                ts_str = html_lib.escape(str(log.get('timestamp') or ''))

                act_str = html_lib.escape(str(log.get('action') or ''))

                det_str = html_lib.escape(str(log.get('details') or ''))

                table_data.append([

                    Paragraph(ts_str, body_style),

                    Paragraph(act_str, body_style),

                    Paragraph(det_str, body_style)

                ])



            t = Table(table_data, colWidths=[130, 150, 260])

            t.setStyle(TableStyle([

                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),

                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),

                ('ALIGN', (0,0), (-1,-1), 'LEFT'),

                ('VALIGN', (0,0), (-1,-1), 'TOP'),

                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),

                ('TOPPADDING', (0,0), (-1,-1), 6),

                ('BOTTOMPADDING', (0,0), (-1,-1), 6),

            ]))

            elements.append(t)



            doc.build(elements)

            buffer.seek(0)

            pdf_bytes = buffer.getvalue()

        except Exception as e:

            raise HTTPException(status_code=500, detail=f"Failed to render binary PDF report: {str(e)}")



        return Response(

            content=pdf_bytes,

            media_type="application/pdf",

            headers={"Content-Disposition": f"attachment; filename=report_{investigation_id}.pdf"}

        )



def _get_model_artifact_sha256(model_id: str = "lightgbm_fraud_detector_v1") -> str:
    artifact_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "model_store", f"{model_id}.joblib")
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact file '{model_id}.joblib' missing from model store; cannot export replay snapshot.")
    with open(artifact_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_replay_snapshot(inv: models.Investigation, db: Session) -> Tuple[Dict[str, Any], str]:

    # 1. Canonical investigation dictionary

    inv_dict = {

        "investigation_id": inv.investigation_id,

        "tenant_id": getattr(inv, "tenant_id", "default_tenant"),

        "transaction_id": inv.txn_id,

        "status": inv.status,

        "risk_score": float(inv.risk_score) if inv.risk_score is not None else None,

        "confidence": float(inv.confidence) if inv.confidence is not None else None,

        "report": inv.report,

        "idempotency_key": inv.idempotency_key,

        "request_fingerprint": inv.request_fingerprint,

        "created_at": inv.created_at.isoformat() if inv.created_at else None,

        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,

    }



    # 2. Canonical transaction dictionary

    txn_dict = None

    if inv.transaction:

        txn = inv.transaction

        txn_dict = {

            "txn_id": txn.txn_id,

            "tenant_id": getattr(txn, "tenant_id", "default_tenant"),

            "account_id": txn.account_id,

            "merchant_id": txn.merchant_id,

            "amount": float(txn.amount) if txn.amount is not None else None,

            "currency": txn.currency,

            "status": txn.status,

            "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,

            "counterparty": txn.counterparty,

            "channel": txn.channel,

            "ip_address": txn.ip_address,

            "device_ref": txn.device_ref,

        }



    # 3. Canonical evidence items

    evidence_list = []

    if inv.evidence:

        for ev in inv.evidence:

            evidence_list.append({

                "evidence_id": ev.evidence_id,

                "tenant_id": getattr(ev, "tenant_id", "default_tenant"),

                "source": ev.source,

                "snippet": ev.snippet,

            })

    vault_items = db.query(models.EvidenceVaultItem).filter(
        models.EvidenceVaultItem.tenant_id == (inv.tenant_id or "default_tenant"),
        models.EvidenceVaultItem.investigation_id == inv.investigation_id

    ).all()

    for vi in vault_items:

        evidence_list.append({

            "item_id": vi.item_id,

            "category": vi.category,

            "title": vi.title,

            "source": vi.source,

            "sha256_hash": vi.sha256_hash,

            "risk_level": vi.risk_level,

            "is_verified": vi.is_verified,

            "verification_method": vi.verification_method,

        })



    # 4. Canonical audit logs

    audit_logs_db = db.query(models.AuditLog).filter(

        models.AuditLog.investigation_id == inv.investigation_id

    ).order_by(models.AuditLog.timestamp.asc(), models.AuditLog.log_id.asc()).all()

    audit_logs_db = models.AuditLog.order_chain(audit_logs_db)



    chain_valid, chain_errors = models.AuditLog.verify_chain(audit_logs_db)



    audit_logs = []

    for al in audit_logs_db:

        audit_logs.append({

            "log_id": al.log_id,

            "tenant_id": al.tenant_id,

            "investigation_id": al.investigation_id,

            "action": al.action,

            "details": al.details,

            "timestamp": al.timestamp.isoformat() if hasattr(al.timestamp, "isoformat") else str(al.timestamp or ""),

            "previous_hash": al.previous_hash,

            "entry_hash": al.entry_hash,

        })



    # 5. Build canonical snapshot bundle with full model, prompt, and runtime metadata

    snapshot = {

        "snapshot_version": "1.0.0",

        "generated_at": timeutil.utcnow().isoformat(),

        "investigation_id": inv.investigation_id,

        "tenant_id": getattr(inv, "tenant_id", "default_tenant"),

        "investigation": inv_dict,

        "transaction": txn_dict,

        "evidence": evidence_list,

        "audit_logs": audit_logs,

        "audit_chain_valid": chain_valid,

        "audit_chain_errors": chain_errors,

        "model_metadata": (lambda: {

            "model_id": getattr(inv, "ml_model_id", None) or "lightgbm_fraud_detector_v1",

            "model_version": "1.0.0",

            "artifact_sha256": _get_model_artifact_sha256(getattr(inv, "ml_model_id", None) or "lightgbm_fraud_detector_v1"),

            "calibration_method": "Platt Sigmoid Calibration"

        })(),

        "prompt_metadata": {

            "planner_version": "v1.0",

            "reasoner_version": "v1.0",

            "critic_version": "v1.0",

            "reporter_version": "v1.0",

            "registry_version": "prompts-2026.10"

        },

        "runtime_environment": {

            "engine": "FFIRE Enterprise Reasoning Engine",

            "version": "2.4.0-enterprise",

            "pipeline_health": "HEALTHY" if not getattr(inv, "is_degraded", False) else "DEGRADED",

            "is_degraded": getattr(inv, "is_degraded", False),

            "degraded_reason": getattr(inv, "degraded_reason", None)

        }

    }



    # 6. Compute cryptographic asymmetric Ed25519 digital signature over the bundle

    priv_key, _ = get_verifier_keys()

    snapshot["signature_algorithm"] = "Ed25519"

    snapshot["signing_key_id"] = "verifier-ed25519-v1"

    pre_repr = json.dumps(snapshot, sort_keys=True, separators=(',', ':'))

    digital_signature = priv_key.sign(pre_repr.encode("utf-8")).hex()

    snapshot["digital_signature"] = digital_signature



    # 7. Compute canonical SHA-256 fingerprint

    canonical_repr = json.dumps(snapshot, sort_keys=True, separators=(',', ':'))

    fingerprint = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()

    snapshot["replay_fingerprint"] = fingerprint



    return snapshot, fingerprint



# --- Immutable Replay Snapshots & Cryptographic Audit Verification (Task T3.1) ---



@app.post("/api/v1/investigations/{investigation_id}/export-replay", response_model=ReplaySnapshotResponse)

@app.get("/api/v1/investigations/{investigation_id}/export-replay", response_model=ReplaySnapshotResponse)

def export_replay_snapshot(

    investigation_id: str,

    response: Response,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Task T3.1: Export immutable, cryptographically verifiable replay snapshot.

    Returns canonical JSON representation of the investigation, transaction, evidence,

    and audit log hash chain, with SHA-256 replay fingerprint.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    snapshot, fingerprint = generate_replay_snapshot(inv, db)

    response.headers["X-Replay-Fingerprint"] = fingerprint

    return snapshot





@app.post("/api/v1/investigations/{investigation_id}/verify-replay", response_model=ReplayVerifyResponse)

def verify_replay_snapshot(

    investigation_id: str,

    payload: Dict[str, Any] = Body(...),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Task T3.1: Cryptographically verify an exported replay snapshot against

    hash chaining, canonical fingerprinting, and database fidelity.

    """

    snapshot = payload.get("snapshot") if "snapshot" in payload and isinstance(payload.get("snapshot"), dict) else payload



    # 1. Multi-tenant isolation verification

    user_tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    snap_tenant = snapshot.get("tenant_id")

    if snap_tenant and not auth.is_platform_admin(current_user) and snap_tenant != user_tenant:

        raise HTTPException(status_code=403, detail="Cross-tenant replay verification forbidden")



    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    mismatches = []



    # 2. Replay fingerprint verification

    provided_fp = snapshot.get("replay_fingerprint")

    if not provided_fp:

        return ReplayVerifyResponse(

            is_valid=False,

            audit_chain_valid=False,

            tamper_detected=True,

            mismatch_reasons=["Missing 'replay_fingerprint' in snapshot"],

            detail="Snapshot rejected: missing cryptographic fingerprint"

        )



    payload_copy = dict(snapshot)

    payload_copy.pop("replay_fingerprint", None)

    canonical_repr = json.dumps(payload_copy, sort_keys=True, separators=(',', ':'))

    computed_fp = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()



    if computed_fp != provided_fp:

        mismatches.append(f"Fingerprint mismatch: computed '{computed_fp}' does not match provided '{provided_fp}'")



    provided_sig = payload_copy.get("digital_signature")

    if not provided_sig:

        mismatches.append("Missing mandatory 'digital_signature' on sealed replay bundle.")

    else:

        pre_copy = dict(payload_copy)

        pre_copy.pop("digital_signature", None)

        pre_repr = json.dumps(pre_copy, sort_keys=True, separators=(',', ':'))

        # Ed25519 only. The snapshot itself must not be able to choose a weaker check: the old
        # fallback verified an HMAC keyed by SECRET_KEY, or by a constant when that was unset.
        try:
            _, verifier_pub = get_verifier_keys()
            verifier_pub.verify(bytes.fromhex(str(provided_sig)), pre_repr.encode("utf-8"))
        except Exception as e:
            mismatches.append(f"Ed25519 digital signature validation failed: {e or type(e).__name__}")



    # 3. Audit log cryptographic hash chain verification

    audit_logs = snapshot.get("audit_logs", [])

    chain_valid, chain_errors = models.AuditLog.verify_chain(audit_logs)

    if not chain_valid:

        mismatches.extend(chain_errors)



    # 4. Database fidelity verification

    snap_inv = snapshot.get("investigation", {})

    if snap_inv.get("transaction_id") != inv.txn_id:

        mismatches.append(f"Transaction ID mismatch: snapshot '{snap_inv.get('transaction_id')}' != database '{inv.txn_id}'")



    db_score = float(inv.risk_score) if inv.risk_score is not None else None

    snap_score = snap_inv.get("risk_score")

    if snap_score is not None and db_score is not None:

        if abs(float(snap_score) - db_score) > 1e-4:

            mismatches.append(f"Risk score mismatch: snapshot '{snap_score}' != database '{db_score}'")

    elif snap_score != db_score:

        mismatches.append(f"Risk score mismatch: snapshot '{snap_score}' != database '{db_score}'")



    if snap_inv.get("status") != inv.status:

        mismatches.append(f"Status mismatch: snapshot '{snap_inv.get('status')}' != database '{inv.status}'")



    is_valid = (len(mismatches) == 0 and chain_valid and (computed_fp == provided_fp))

    tamper_detected = not is_valid

    detail = (

        "Replay snapshot verified cryptographically and matches database audit record"

        if is_valid

        else f"Tampering or corruption detected: {'; '.join(mismatches)}"

    )



    return ReplayVerifyResponse(

        is_valid=is_valid,

        replay_fingerprint=computed_fp,

        audit_chain_valid=chain_valid,

        audit_chain_errors=chain_errors,

        tamper_detected=tamper_detected,

        mismatch_reasons=mismatches,

        detail=detail

    )





@app.get("/api/v1/investigations/{investigation_id}/audit-chain", response_model=AuditChainResponse)

def get_investigation_audit_chain(

    investigation_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Task T3.1: Retrieve full audit trail with cryptographic hash chain integrity status.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv:

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    audit_logs = db.query(models.AuditLog).filter(

        models.AuditLog.investigation_id == investigation_id

    ).order_by(models.AuditLog.timestamp.asc(), models.AuditLog.log_id.asc()).all()

    audit_logs = models.AuditLog.order_chain(audit_logs)



    chain_valid, chain_errors = models.AuditLog.verify_chain(audit_logs)



    entries = [

        AuditChainEntry(

            log_id=al.log_id,

            tenant_id=al.tenant_id,

            action=al.action,

            details=al.details,

            timestamp=al.timestamp.isoformat() if hasattr(al.timestamp, "isoformat") else str(al.timestamp or ""),

            previous_hash=al.previous_hash,

            entry_hash=al.entry_hash

        )

        for al in audit_logs

    ]



    return AuditChainResponse(

        investigation_id=inv.investigation_id,

        tenant_id=getattr(inv, "tenant_id", "default_tenant"),

        chain_length=len(audit_logs),

        is_valid=chain_valid,

        errors=chain_errors,

        entries=entries

    )



@app.patch("/api/v1/investigations/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: str,
    request: Request,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permissions("investigator"))
):
    """
    Update an investigation.
    Currently supports updating the status field via query params or JSON body.
    Requires investigator role or higher.
    """
    if status is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                status = body.get("status")
        except Exception:
            pass

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)

    # Update fields if provided
    if status is not None:
        # Validate status transition (optional - could be more comprehensive)
        valid_statuses = ["RUNNING", "COMPLETED", "ESCALATED", "FAILED", "CLOSED_APPROVE", "CLOSED_REJECT"]

        if status not in valid_statuses:

            raise HTTPException(

                status_code=400,

                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        # A manual change follows the same state machine as the worker. Without this an
        # investigator could set any status from any other, for example re-open a closed case
        # as RUNNING or close one that had never been reviewed.
        from worker import VALID_TRANSITIONS
        if getattr(inv, "is_deleted", False):
            raise HTTPException(status_code=404, detail="Investigation not found")
        if status != inv.status and status not in VALID_TRANSITIONS.get(inv.status, set()):
            raise HTTPException(
                status_code=409,
                detail=f"Invalid status transition: {inv.status} -> {status}"
            )
        previous_status = inv.status
        inv.status = status



        # Trigger Twilio SMS alert on escalation
        if status == "ESCALATED" and previous_status != "ESCALATED":
            try:
                from twilio_service import twilio_service
                twilio_service.send_critical_escalation_alert(
                    investigation_id=inv.investigation_id,
                    risk_score=float(inv.risk_score or 0.0),
                    triggers=[f"Manual investigator escalation by {current_user.name}"],
                    tenant_id=getattr(inv, "tenant_id", "default_tenant"),
                    db=db
                )
            except Exception as _alert_exc:
                logging.getLogger("ffire.alerts").warning(f"Twilio alert dispatch error: {_alert_exc}")

        # Add audit log entry for the status change

        audit_log = models.AuditLog(

            investigation_id=inv.investigation_id,

            action=f"STATUS_UPDATED: {status}",

            details=f"Status updated to {status} by {current_user.name}",

            tenant_id=getattr(inv, "tenant_id", "default_tenant")

        )

        db.add(audit_log)



    db.commit()

    db.refresh(inv)



    # Return updated investigation

    return build_investigation_response(inv, db)



class LegalHoldRequest(BaseModel):

    legal_hold: bool

    reason: Optional[str] = None



@app.post("/api/v1/investigations/{investigation_id}/legal-hold")

def toggle_legal_hold(

    investigation_id: str,

    payload: LegalHoldRequest,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("investigator"))

):

    """Apply or release a regulatory legal hold on an investigation (Finding 9)."""

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv or getattr(inv, "is_deleted", False):

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)
    # Anyone who works cases may place a hold. Lifting one is a compliance decision: if an
    # investigator could release it, the hold would not protect the record from deletion.
    if not payload.legal_hold and getattr(inv, "legal_hold", False):
        auth.require_role(current_user, "compliance_officer")
    inv.legal_hold = payload.legal_hold
    inv.legal_hold_reason = payload.reason

    action = "LEGAL_HOLD_APPLIED" if payload.legal_hold else "LEGAL_HOLD_RELEASED"

    audit = models.AuditLog(

        investigation_id=inv.investigation_id,

        action=action,

        details=f"Regulatory legal hold set to {payload.legal_hold} by {current_user.name}. Reason: {payload.reason or 'None'}",

        tenant_id=getattr(inv, "tenant_id", "default_tenant")

    )

    db.add(audit)

    db.commit()

    return {"status": "success", "investigation_id": investigation_id, "legal_hold": inv.legal_hold}



@app.delete("/api/v1/investigations/{investigation_id}")

def delete_investigation(

    investigation_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("administrator"))

):

    """

    Delete an investigation with regulatory retention & legal-hold compliance (Finding 9).

    Under BSA/AML compliance standards, investigations subject to regulatory

    inquiries or legal hold must NOT be deleted. Approved deletions perform a

    compliant soft-delete with an immutable audit tombstone record.

    """

    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()

    if not inv or getattr(inv, "is_deleted", False):

        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_tenant_isolation(current_user, inv)



    # Finding 9: Prevent deletion under active regulatory legal hold

    if getattr(inv, "legal_hold", False):

        raise HTTPException(

            status_code=409,

            detail=f"Investigation {investigation_id} is under active regulatory legal hold and cannot be deleted."

        )



    investigation_id_for_log = inv.investigation_id

    txn_id_for_log = inv.txn_id



    # Compliant soft delete: mark deleted while preserving records for 5-year BSA statutory audit retention

    inv.is_deleted = True

    inv.deleted_at = timeutil.utcnow()

    inv.status = "ARCHIVED_DELETED"



    # Create immutable tombstone audit log before committing soft delete

    tombstone_log = models.AuditLog(

        investigation_id=inv.investigation_id,

        action=f"INVESTIGATION_SOFT_DELETED: {investigation_id_for_log}",

        details=f"Investigation for transaction {txn_id_for_log} soft-deleted by administrator {current_user.name}. Records retained for regulatory compliance.",

        tenant_id=getattr(inv, "tenant_id", "default_tenant")

    )

    db.add(tombstone_log)

    db.commit()



    return {

        "status": "success",

        "message": f"Investigation {investigation_id} soft-deleted successfully. Audit trail and evidence preserved under statutory retention.",

        "retention_policy": "5_year_bsa_compliant"

    }



# --- Evidence Vault Endpoints (Chapters 28, 51) ---



def seed_default_evidence_if_empty(db: Session, tenant_id: str):
    # Sample records are for demonstrations only. Writing invented "verified" evidence into a real
    # tenant's vault on first visit is not acceptable for a system of record.
    if not demo_seeding_enabled():
        return

    count = db.query(models.EvidenceVaultItem).filter(models.EvidenceVaultItem.tenant_id == tenant_id).count()

    if count > 0:

        return

    

    seeds = [

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="IDENTITY_DOCUMENTS",

            title="Global Passport Index",

            source="INTERPOL-API",

            tag="KYC_LEVEL_3",

            file_type="JSON",

            file_size=4280,

            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",

            risk_level="LOW",

            is_verified=True,

            verification_method="Cryptographic Passport Chip Auth",

            description="Verified biometric passport records cross-referenced against Interpol alert registers.",

            created_at=timeutil.utcnow() - datetime.timedelta(minutes=2)

        ),

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="IDENTITY_DOCUMENTS",

            title="Sanction Lists",

            source="OFAC_GOV",

            tag="AML_SCAN",

            file_type="CSV",

            file_size=184920,

            sha256_hash="8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",

            risk_level="MEDIUM",

            is_verified=False,

            verification_method="Pending Secondary Sanctions Screener",

            description="Specially Designated Nationals (SDN) and Consolidated Sanctions List snapshot.",

            created_at=timeutil.utcnow() - datetime.timedelta(hours=1)

        ),

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="IDENTITY_DOCUMENTS",

            title="Biometric Hash Vault",

            source="LOCAL_ENCLAVE",

            tag="BIO_CHECK",

            file_type="SECURE_ENCLAVE",

            file_size=2048,

            sha256_hash="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",

            risk_level="LOW",

            is_verified=True,

            verification_method="Hardware Security Module (HSM) Signed",

            description="Facial vector embedding hashes authenticated inside hardware secure enclave.",

            created_at=timeutil.utcnow() - datetime.timedelta(minutes=5)

        ),

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="HISTORICAL_PATTERNS",

            title="Synthetic Identity Chain",

            source="GRAPH_ANALYTICS",

            tag="HIGH RECURRENCE",

            file_type="GRAPH_JSON",

            file_size=12540,

            sha256_hash="4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce",

            risk_level="HIGH",

            is_verified=True,

            verification_method="100% (Manual Audit)",

            description="Cross-matched patterns involving coordinated KYC document tampering across multiple neo-bank domains.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=1)

        ),

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="HISTORICAL_PATTERNS",

            title="Velocity Smurfing",

            source="VELOCITY_ENGINE",

            tag="EMERGING",

            file_type="TELEMETRY_LOG",

            file_size=8720,

            sha256_hash="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",

            risk_level="HIGH",

            is_verified=True,

            verification_method="82% (AI Logic)",

            description="High-frequency, low-value transactions utilizing recycled mobile hardware fingerprints from APAC regions.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=2)

        ),

        models.EvidenceVaultItem(

            tenant_id=tenant_id,

            category="HISTORICAL_PATTERNS",

            title="Residential Proxy Tunneling",

            source="NETWORK_INTEL",

            tag="STABLE THREAT",

            file_type="PCAP_EXPORT",

            file_size=45200,

            sha256_hash="ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d",

            risk_level="MEDIUM",

            is_verified=True,

            verification_method="99% (Telemetry)",

            description="Persistent use of high-reputation residential IPs to mask systematic scraping of credit application endpoints.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=4)

        )

    ]

    db.add_all(seeds)

    db.commit()



@app.get("/api/v1/evidence", response_model=EvidenceVaultListResponse)

def list_evidence_vault(

    category: Optional[str] = Query(None, description="Filter by category (IDENTITY_DOCUMENTS, HISTORICAL_PATTERNS, DEVICE_TELEMETRY)"),

    search: Optional[str] = Query(None, description="Search term in title, source, tag, or description"),

    risk_level: Optional[str] = Query(None, description="Filter by risk level"),

    is_verified: Optional[bool] = Query(None, description="Filter by verification state"),

    page: int = Query(1, ge=1),

    page_size: int = Query(20, ge=1, le=100),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """List items in the digital evidence vault with filtering and multi-tenant scoping."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    seed_default_evidence_if_empty(db, tenant)



    query = db.query(models.EvidenceVaultItem)

    if not auth.is_platform_admin(current_user):

        query = query.filter(models.EvidenceVaultItem.tenant_id == tenant)

    

    if category:

        query = query.filter(models.EvidenceVaultItem.category == category)

    if risk_level:

        query = query.filter(models.EvidenceVaultItem.risk_level == risk_level.upper())

    if is_verified is not None:

        query = query.filter(models.EvidenceVaultItem.is_verified == is_verified)

    if search:

        pattern = f"%{search}%"

        query = query.filter(

            (models.EvidenceVaultItem.item_id.ilike(pattern)) |

            (models.EvidenceVaultItem.title.ilike(pattern)) |

            (models.EvidenceVaultItem.source.ilike(pattern)) |

            (models.EvidenceVaultItem.tag.ilike(pattern)) |

            (models.EvidenceVaultItem.sha256_hash.ilike(pattern)) |

            (models.EvidenceVaultItem.description.ilike(pattern))

        )

    

    total = query.count()

    offset = (page - 1) * page_size

    items = query.order_by(desc(models.EvidenceVaultItem.created_at)).offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1



    return EvidenceVaultListResponse(

        items=items,

        total=total,

        page=page,

        page_size=page_size,

        total_pages=total_pages

    )



@app.post("/api/v1/evidence/upload", response_model=EvidenceVaultResponse)

async def upload_evidence(

    file: Optional[UploadFile] = File(None),

    category: str = Form("IDENTITY_DOCUMENTS"),

    title: Optional[str] = Form(None),

    source: str = Form("ANALYST_UPLOAD"),

    tag: str = Form("MANUAL_INGESTION"),

    risk_level: str = Form("LOW"),

    description: Optional[str] = Form(None),

    investigation_id: Optional[str] = Form(None),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Ingest evidence file or metadata artifact into digital vault with SHA-256 integrity verification."""

    auth.require_role(current_user, *CASE_WORKER_ROLES)
    tenant = getattr(current_user, "tenant_id", None) or "default_tenant"
    item_id = str(uuid.uuid4())

    # Evidence may only be attached to an investigation of the caller's own tenant. Accepting any
    # id let one tenant write into another tenant's case file and audit chain.
    if investigation_id:
        linked = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
        if not linked or getattr(linked, "is_deleted", False):
            raise HTTPException(status_code=404, detail="Investigation not found")
        enforce_tenant_isolation(current_user, linked)
        tenant = linked.tenant_id or tenant

    vault_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vault", _safe_filename(tenant))
    os.makedirs(vault_dir, exist_ok=True)
    if file:
        file_bytes = await file.read(EVIDENCE_MAX_BYTES + 1)
        if len(file_bytes) > EVIDENCE_MAX_BYTES:
            raise HTTPException(status_code=413, detail=f"File too large. The limit is {EVIDENCE_MAX_BYTES // (1024 * 1024)} MB.")
        # The client's file name is untrusted: keep its base name only, with safe characters.
        file_name = _safe_filename(file.filename or "evidence.bin")
    else:

        file_bytes = None

        file_name = None



    item = await run_in_threadpool(

        _sync_store_evidence,

        db=db,

        vault_dir=vault_dir,

        tenant=tenant,

        user_name=current_user.name,

        item_id=item_id,

        file_name=file_name,

        file_bytes=file_bytes,

        category=category,

        title=title,

        source=source,

        tag=tag,

        risk_level=risk_level,

        description=description,

        investigation_id=investigation_id

    )



    return item

def _sync_store_evidence(

    db: Session,

    vault_dir: str,

    tenant: str,

    user_name: str,

    item_id: str,

    file_name: Optional[str],

    file_bytes: Optional[bytes],

    category: str,

    title: Optional[str],

    source: str,

    tag: str,

    risk_level: str,

    description: Optional[str],

    investigation_id: Optional[str]

) -> models.EvidenceVaultItem:

    if file_bytes is not None and file_name is not None:

        file_type = file_name.split(".")[-1].upper() if "." in file_name else "BIN"

        file_size = len(file_bytes)

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        storage_path = os.path.join(vault_dir, f"{item_id}_{file_name}")

        with open(storage_path, "wb") as f:

            f.write(file_bytes)

        item_title = title or file_name

    else:

        sample_payload = f"Evidence payload created at {timeutil.utcnow().isoformat()} by {user_name}".encode("utf-8")

        file_bytes = sample_payload

        file_type = "JSON"

        file_size = len(file_bytes)

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        storage_path = os.path.join(vault_dir, f"{item_id}.json")

        with open(storage_path, "wb") as f:

            f.write(file_bytes)

        item_title = title or f"Ingested Evidence - {item_id[:8]}"



    item = models.EvidenceVaultItem(

        item_id=item_id,

        tenant_id=tenant,

        investigation_id=investigation_id,

        category=category,

        title=item_title,

        source=source,

        tag=tag,

        file_type=file_type,

        file_size=file_size,

        sha256_hash=sha256_hash,

        risk_level=risk_level.upper(),

        # The digest is recorded now. "Verified" is set by the verify endpoint, which re-reads the
        # stored file and compares it with this digest.
        is_verified=False,
        verification_method="SHA-256 digest recorded at ingestion",
        description=description or f"Uploaded by {user_name} for tenant {tenant}",

        storage_path=storage_path,

        created_at=timeutil.utcnow()

    )

    db.add(item)

    

    audit_log = models.AuditLog(

        investigation_id=investigation_id,

        action="EVIDENCE_INGESTED",

        details=f"Item {item.title} ({item.item_id}) ingested with SHA256 {sha256_hash} by {user_name}",

        tenant_id=tenant

    )

    db.add(audit_log)
    db.commit()
    db.refresh(item)
    return item



@app.post("/api/v1/evidence/{item_id}/verify", response_model=EvidenceVaultResponse)

def verify_evidence(

    item_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Cryptographically sign and verify evidence vault item."""

    item = db.query(models.EvidenceVaultItem).filter(models.EvidenceVaultItem.item_id == item_id).first()

    if not item:

        raise HTTPException(status_code=404, detail="Evidence item not found")

    _require_same_tenant(current_user, item.tenant_id, "Evidence")
    auth.require_role(current_user, *CASE_WORKER_ROLES)

    # Verification means what it says: read the stored file again and compare its SHA-256 with the
    # digest recorded at ingestion. Nothing is "signed by an HSM" here, so nothing claims to be.
    path = item.storage_path
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=409, detail="Cannot verify: no stored file exists for this evidence item")
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    if not hmac.compare_digest(digest.hexdigest(), item.sha256_hash or ""):
        item.is_verified = False
        item.verification_method = "FAILED: stored file does not match the recorded SHA-256 digest"
        db.add(models.AuditLog(
            investigation_id=item.investigation_id,
            action="EVIDENCE_VERIFICATION_FAILED",
            details=f"Item {item.item_id}: stored file hash {digest.hexdigest()} does not match recorded {item.sha256_hash}",
            tenant_id=item.tenant_id
        ))
        db.commit()
        raise HTTPException(status_code=409, detail="Integrity check failed: the stored file does not match its recorded SHA-256 digest")

    item.is_verified = True
    item.verification_method = f"SHA-256 digest re-verified against stored file by {current_user.name}"
    audit = models.AuditLog(

        investigation_id=item.investigation_id,

        action="EVIDENCE_CRYPTOGRAPHICALLY_VERIFIED",

        details=f"Item {item.item_id} hash {item.sha256_hash} verified by {current_user.name}",

        tenant_id=item.tenant_id

    )

    db.add(audit)

    db.commit()

    db.refresh(item)

    return item



@app.delete("/api/v1/evidence/{item_id}")

def delete_evidence(

    item_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Delete an item from the evidence vault."""

    item = db.query(models.EvidenceVaultItem).filter(models.EvidenceVaultItem.item_id == item_id).first()

    if not item:

        raise HTTPException(status_code=404, detail="Evidence item not found")

    _require_same_tenant(current_user, item.tenant_id, "Evidence")
    # Removing evidence is not something a read-only user may do, and never while the case it
    # belongs to is under legal hold.
    auth.require_role(current_user, "compliance_officer", "investigator")
    if item.investigation_id:
        held = db.query(models.Investigation).filter(models.Investigation.investigation_id == item.investigation_id).first()
        if held is not None and getattr(held, "legal_hold", False):
            raise HTTPException(status_code=409, detail="Evidence belongs to an investigation under legal hold and cannot be deleted")
    audit = models.AuditLog(
        investigation_id=item.investigation_id,
        action="EVIDENCE_DELETED",

        details=f"Evidence {item.title} ({item.item_id}) deleted by {current_user.name}",

        tenant_id=item.tenant_id

    )

    db.add(audit)

    db.delete(item)

    db.commit()

    return {"status": "success", "message": f"Evidence {item_id} removed from vault"}



# --- Reports & Regulatory Filing Endpoints (Chapters 32, 96) ---



def seed_default_reports_if_empty(db: Session, tenant_id: str):
    if not demo_seeding_enabled():
        return

    count = db.query(models.ReportRecord).filter(models.ReportRecord.tenant_id == tenant_id).count()

    if count > 0:

        return



    seeds = [

        models.ReportRecord(

            tenant_id=tenant_id,

            title="Suspicious Activity Report - FinCEN SAR Filing",

            report_type="SAR Regulatory Filing",

            generated_by="Automated Compliance Engine",

            status="Completed",

            file_format="pdf",

            file_size=2516582,

            description="Suspicious Activity Report detailing high-velocity layering pattern across offshore neo-bank routing.",

            content_json="Executive Summary: High-velocity smurfing identified across 14 transactions totaling $420,000.\nFiling Category: BSA/AML FinCEN Form 111.\nRisk Score: 0.96 (CRITICAL).",

            created_at=timeutil.utcnow() - datetime.timedelta(days=1)

        ),

        models.ReportRecord(

            tenant_id=tenant_id,

            title="Daily Fraud & Risk Intelligence Summary",

            report_type="Trend Report",

            generated_by="System Cron",

            status="Completed",

            file_format="pdf",

            file_size=1258291,

            description="Daily aggregated metrics on model inference, critic corrections, and velocity anomalies.",

            content_json="Daily Summary: 1,480 transactions evaluated. 99.2% automated pass rate, 12 human review escalations.",

            created_at=timeutil.utcnow() - datetime.timedelta(hours=6)

        ),

        models.ReportRecord(

            tenant_id=tenant_id,

            title="Chargeback Analysis Report Q1",

            report_type="Compliance Report",

            generated_by="Maria Garcia (Lead Analyst)",

            status="Completed",

            file_format="pdf",

            file_size=6081740,

            description="Quarterly analysis of chargeback rates, card network dispute resolution, and synthetic identity exposure.",

            content_json="Q1 Chargeback Audit: Net dispute recovery rate 74.2%. Synthetic identity exposure mitigated $1.8M.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=14)

        ),

        models.ReportRecord(

            tenant_id=tenant_id,

            title="Investigation Timeline & Evidence Dossier",

            report_type="Investigation Report",

            generated_by="Alex Johnson (Senior Investigator)",

            status="Completed",

            file_format="pdf",

            file_size=327680,

            description="Complete multi-source forensic evidence trail, decision reasoning DAG, and analyst resolution notes.",

            content_json="Forensic Dossier: Verified IP geo-hop across London VPC and Frankfurt exit relays.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=3)

        ),

        models.ReportRecord(

            tenant_id=tenant_id,

            title="Cross-Border Wire Compliance Sweep",

            report_type="Compliance Report",

            generated_by="Compliance Daemon",

            status="Failed",

            file_format="pdf",

            file_size=0,

            description="Sanction screening reconciliation failed due to upstream OFAC API socket timeout.",

            content_json="Failure diagnostic: SocketTimeoutException on sanctions gateway port 443.",

            created_at=timeutil.utcnow() - datetime.timedelta(days=5)

        )

    ]

    db.add_all(seeds)

    db.commit()



@app.get("/api/v1/reports", response_model=ReportListResponse)

def list_reports(

    search: Optional[str] = Query(None, description="Search term in title or description"),

    status: Optional[str] = Query(None, description="Filter by status (Completed, Generating, Failed)"),

    report_type: Optional[str] = Query(None, description="Filter by report type"),

    page: int = Query(1, ge=1),

    page_size: int = Query(20, ge=1, le=100),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """List regulatory and analytical reports with search, filtering, and tenant scoping."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    seed_default_reports_if_empty(db, tenant)



    query = db.query(models.ReportRecord)

    if not auth.is_platform_admin(current_user):

        query = query.filter(models.ReportRecord.tenant_id == tenant)



    if status and status != "All":

        query = query.filter(models.ReportRecord.status == status)

    if report_type and report_type != "All":

        query = query.filter(models.ReportRecord.report_type == report_type)

    if search:

        pattern = f"%{search}%"

        query = query.filter(

            (models.ReportRecord.title.ilike(pattern)) |

            (models.ReportRecord.description.ilike(pattern)) |

            (models.ReportRecord.report_id.ilike(pattern))

        )



    total = query.count()

    offset = (page - 1) * page_size

    reports = query.order_by(desc(models.ReportRecord.created_at)).offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1



    return ReportListResponse(

        reports=reports,

        total=total,

        page=page,

        page_size=page_size,

        total_pages=total_pages

    )



@app.post("/api/v1/reports/generate", response_model=ReportRecordResponse)

def generate_report(

    request_data: ReportGenerateRequest,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Generate a new formal investigation report or regulatory SAR filing."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    auth.require_role(current_user, *CASE_WORKER_ROLES)
    report_format = (request_data.file_format or "pdf").strip().lower()
    if report_format not in ("pdf", "html", "json", "csv", "txt"):
        raise HTTPException(status_code=400, detail="file_format must be one of: pdf, html, json, csv, txt")
    report_id = str(uuid.uuid4())
    inv_details = ""

    if request_data.investigation_id:
        inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == request_data.investigation_id).first()
        if not inv or getattr(inv, "is_deleted", False):
            raise HTTPException(status_code=404, detail="Investigation not found")
        # The report quotes the investigation's status and risk score, so the caller must be
        # allowed to read that investigation.
        enforce_tenant_isolation(current_user, inv)
        inv_details = f"\nLinked Investigation: {inv.investigation_id} | Status: {inv.status} | Risk: {inv.risk_score}"



    content = f"FFIRE Regulatory & Executive Dossier: {request_data.title}\nReport Type: {request_data.report_type}\nGenerated By: {current_user.name}\nTenant: {tenant}{inv_details}\nDescription: {request_data.description or 'No description provided.'}\nGenerated At: {timeutil.utcnow().isoformat()}"

    file_size = len(content.encode("utf-8"))



    report = models.ReportRecord(

        report_id=report_id,

        tenant_id=tenant,

        investigation_id=request_data.investigation_id,

        title=request_data.title,

        report_type=request_data.report_type,

        generated_by=current_user.name,

        status="Completed",

        file_format=report_format,

        file_size=file_size,

        description=request_data.description,

        content_json=content,

        created_at=timeutil.utcnow()

    )

    db.add(report)



    audit = models.AuditLog(

        investigation_id=request_data.investigation_id,

        action="REPORT_GENERATED",

        details=f"Report '{report.title}' ({report.report_id}) generated by {current_user.name}",

        tenant_id=tenant

    )

    db.add(audit)

    db.commit()

    db.refresh(report)

    return report



@app.get("/api/v1/reports/{report_id}/download")

def download_report(

    report_id: str,

    format: Optional[str] = Query(None),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Download generated report in PDF, JSON, or HTML format."""

    report = db.query(models.ReportRecord).filter(models.ReportRecord.report_id == report_id).first()

    if not report:

        raise HTTPException(status_code=404, detail="Report not found")

    _require_same_tenant(current_user, report.tenant_id, "Report")



    fmt = (format or report.file_format or "pdf").lower()

    if fmt == "json":

        return {

            "report_id": report.report_id,

            "title": report.title,

            "report_type": report.report_type,

            "status": report.status,

            "generated_by": report.generated_by,

            "created_at": report.created_at.isoformat(),

            "content": report.content_json

        }

    elif fmt == "html":

        def esc(value) -> str:
            return html.escape("" if value is None else str(value))

        html_doc = f"""<!DOCTYPE html><html><head><title>{esc(report.title)}</title><style>body{{font-family:sans-serif;margin:40px;color:#0f172a;}} h1{{color:#1e293b;}} pre{{background:#f1f5f9;padding:16px;border-radius:6px;}}</style></head><body><h1>{esc(report.title)}</h1><p><strong>Type:</strong> {esc(report.report_type)} | <strong>Status:</strong> {esc(report.status)} | <strong>Author:</strong> {esc(report.generated_by)}</p><pre>{esc(report.content_json or report.description)}</pre></body></html>"""

        return Response(
            content=html_doc,
            media_type="text/html",
            headers=SAFE_HTML_EXPORT_HEADERS | {"Content-Disposition": f'attachment; filename="report_{_safe_filename(report.report_id)}.html"'},
        )

    else:

        try:

            from reportlab.lib.pagesizes import letter

            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            from reportlab.lib import colors

            import io

            import html as html_lib



            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('RTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#0f172a"))

            body_style = ParagraphStyle('RBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#334155"))



            elements = [

                Paragraph(f"FFRE Executive Report: {html_lib.escape(report.title)}", title_style),

                Spacer(1, 10),

                Paragraph(f"<b>Report ID:</b> {report.report_id} | <b>Type:</b> {report.report_type}<br/><b>Author:</b> {report.generated_by} | <b>Created:</b> {report.created_at.isoformat()}", body_style),

                Spacer(1, 15),

                Paragraph("<b>Executive Summary & Content:</b>", body_style),

                Spacer(1, 6),

                Paragraph(html_lib.escape(report.content_json or report.description or "No report content").replace("\n", "<br/>"), body_style)

            ]

            doc.build(elements)

            buffer.seek(0)

            pdf_bytes = buffer.getvalue()

            return Response(

                content=pdf_bytes,

                media_type="application/pdf",

                headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}

            )

        except Exception as e:

            raise HTTPException(status_code=500, detail=f"Failed to compile report PDF: {str(e)}")



@app.delete("/api/v1/reports/{report_id}")

def delete_report(

    report_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Delete a report from the archive."""

    report = db.query(models.ReportRecord).filter(models.ReportRecord.report_id == report_id).first()

    if not report:

        raise HTTPException(status_code=404, detail="Report not found")

    _require_same_tenant(current_user, report.tenant_id, "Report")
    auth.require_role(current_user, "compliance_officer", "investigator")



    audit = models.AuditLog(

        investigation_id=report.investigation_id,

        action="REPORT_DELETED",

        details=f"Report '{report.title}' ({report.report_id}) deleted by {current_user.name}",

        tenant_id=report.tenant_id

    )

    db.add(audit)

    db.delete(report)

    db.commit()

    return {"status": "success", "message": f"Report {report_id} removed"}



# --- Universal Search & Command Palette (Chapter 41) ---



@app.get("/api/v1/search/universal")

def universal_search(

    q: str = Query(..., min_length=1),

    category: Optional[str] = None,

    limit: int = 25,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Chapter 41: Global Search & Universal Command Palette search provider across tenant resources."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")
    results = []
    q_lower = q.strip().lower()
    limit = max(1, min(limit, 100))
    # Match in the database with a row limit. Loading every row of four tables into memory for
    # each search did not scale past a demo data set.
    like = "%" + q_lower.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    def matches(*columns):
        return or_(*[func.lower(col).like(like, escape="\\") for col in columns])



    # 1. Investigations

    if not category or category in ["all", "investigations", "cases"]:

        invs = db.query(models.Investigation).filter(
            models.Investigation.tenant_id == tenant,
            models.Investigation.is_deleted.is_(False),
            matches(models.Investigation.investigation_id, models.Investigation.txn_id, models.Investigation.report),
        ).limit(limit).all()

        for inv in invs:

            if (q_lower in inv.investigation_id.lower() or 

                (inv.txn_id and q_lower in inv.txn_id.lower()) or 

                (inv.report and q_lower in inv.report.lower())):

                results.append({

                    "id": inv.investigation_id,

                    "type": "investigation",

                    "title": f"Investigation {inv.investigation_id}",

                    "subtitle": f"Txn: {inv.txn_id or 'N/A'} • Risk: {inv.risk_score or 0.0}",

                    "badge": inv.status,

                    "status": inv.status,

                    "url": f"/investigations/{inv.investigation_id}"

                })



    # 2. Evidence Vault Items

    if not category or category in ["all", "evidence"]:

        ev_items = db.query(models.EvidenceVaultItem).filter(
            models.EvidenceVaultItem.tenant_id == tenant,
            matches(models.EvidenceVaultItem.title, models.EvidenceVaultItem.description,
                    models.EvidenceVaultItem.tag, models.EvidenceVaultItem.sha256_hash),
        ).limit(limit).all()

        for it in ev_items:

            if (q_lower in it.title.lower() or 

                (it.description and q_lower in it.description.lower()) or 

                (it.tag and q_lower in it.tag.lower()) or

                q_lower in it.sha256_hash.lower()):

                results.append({

                    "id": it.item_id,

                    "type": "evidence",

                    "title": it.title,

                    "subtitle": f"{it.category} • {it.source} • {it.tag}",

                    "badge": it.risk_level,

                    "status": "VERIFIED" if it.is_verified else "PENDING",

                    "url": "/evidence"

                })



    # 3. Reports

    if not category or category in ["all", "reports"]:

        reports = db.query(models.ReportRecord).filter(
            models.ReportRecord.tenant_id == tenant,
            matches(models.ReportRecord.title, models.ReportRecord.description, models.ReportRecord.report_type),
        ).limit(limit).all()

        for rep in reports:

            if (q_lower in rep.title.lower() or 

                (rep.description and q_lower in rep.description.lower()) or 

                q_lower in rep.report_type.lower()):

                results.append({

                    "id": rep.report_id,

                    "type": "report",

                    "title": rep.title,

                    "subtitle": f"{rep.report_type} • Format: {rep.file_format}",

                    "badge": rep.status,

                    "status": rep.status,

                    "url": "/reports"

                })



    # 4. Transactions

    if not category or category in ["all", "transactions"]:

        txns = db.query(models.Transaction).filter(
            models.Transaction.tenant_id == tenant,
            matches(models.Transaction.txn_id, models.Transaction.counterparty),
        ).limit(limit).all()

        for t in txns:

            if (q_lower in t.txn_id.lower() or 

                (t.counterparty and q_lower in t.counterparty.lower())):

                results.append({

                    "id": t.txn_id,

                    "type": "transaction",

                    "title": f"Transaction {t.txn_id}",

                    "subtitle": f"Amount: {t.amount} {t.currency} • Counterparty: {t.counterparty or 'N/A'}",

                    "badge": t.status,

                    "status": t.status,

                    "url": f"/transactions/{t.txn_id}"

                })



    return {

        "query": q,

        "total": len(results),

        "results": results[:limit]

    }





# --- Centralized Prompt Registry & Studio API (Chapters 36 & 85) ---



class PromptCreate(BaseModel):

    name: str

    version: str = "v1.0"

    template_text: str

    description: Optional[str] = None

    variables: Optional[str] = None

    is_active: bool = True



class PromptUpdate(BaseModel):

    template_text: Optional[str] = None

    description: Optional[str] = None

    variables: Optional[str] = None

    is_active: Optional[bool] = None



@app.get("/api/v1/prompts")

def list_prompts(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """List all registered prompts, active versions, and templates for tenant."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    prompts = db.query(models.PromptRecord).filter(models.PromptRecord.tenant_id == tenant).order_by(models.PromptRecord.name, models.PromptRecord.created_at.desc()).all()



    if not prompts:

        prompt_registry.seed_default_prompts(db, tenant_id=tenant)

        prompts = db.query(models.PromptRecord).filter(models.PromptRecord.tenant_id == tenant).order_by(models.PromptRecord.name, models.PromptRecord.created_at.desc()).all()



    return [

        {

            "prompt_id": p.prompt_id,

            "name": p.name,

            "version": p.version,

            "template_text": p.template_text,

            "description": p.description,

            "variables": [v.strip() for v in p.variables.split(",")] if p.variables else [],

            "is_active": p.is_active,

            "created_by": p.created_by,

            "created_at": p.created_at.isoformat(),

            "updated_at": p.updated_at.isoformat() if p.updated_at else p.created_at.isoformat()

        }

        for p in prompts

    ]



@app.get("/api/v1/prompts/{name}")

def get_prompt_by_name(

    name: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Get active prompt template and historical versions for a given prompt name."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    records = db.query(models.PromptRecord).filter(

        models.PromptRecord.tenant_id == tenant,

        models.PromptRecord.name == name

    ).order_by(models.PromptRecord.created_at.desc()).all()



    if not records:

        prompt_registry.seed_default_prompts(db, tenant_id=tenant)

        records = db.query(models.PromptRecord).filter(

            models.PromptRecord.tenant_id == tenant,

            models.PromptRecord.name == name

        ).order_by(models.PromptRecord.created_at.desc()).all()



    if not records:

        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")



    active_rec = next((r for r in records if r.is_active), records[0])



    return {

        "name": name,

        "active_version": active_rec.version,

        "active_template": active_rec.template_text,

        "description": active_rec.description,

        "variables": [v.strip() for v in active_rec.variables.split(",")] if active_rec.variables else [],

        "versions": [

            {

                "prompt_id": r.prompt_id,

                "version": r.version,

                "is_active": r.is_active,

                "created_by": r.created_by,

                "created_at": r.created_at.isoformat()

            }

            for r in records

        ]

    }



@app.post("/api/v1/prompts")

def create_prompt_version(

    payload: PromptCreate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Create a new prompt template or deploy a new version in the registry."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")



    if payload.is_active:

        db.query(models.PromptRecord).filter(

            models.PromptRecord.tenant_id == tenant,

            models.PromptRecord.name == payload.name,

            models.PromptRecord.is_active == True

        ).update({"is_active": False})



    new_prompt = models.PromptRecord(

        tenant_id=tenant,

        name=payload.name,

        version=payload.version,

        template_text=payload.template_text.strip(),

        description=payload.description,

        variables=payload.variables,

        is_active=payload.is_active,

        created_by=current_user.name

    )

    db.add(new_prompt)

    db.commit()

    db.refresh(new_prompt)



    prompt_registry.invalidate_prompt_cache(payload.name, tenant)



    return {

        "status": "success",

        "prompt_id": new_prompt.prompt_id,

        "name": new_prompt.name,

        "version": new_prompt.version,

        "is_active": new_prompt.is_active

    }



@app.put("/api/v1/prompts/{prompt_id}")

def update_prompt_version(

    prompt_id: str,

    payload: PromptUpdate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Update prompt template text, description, or activation status."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    prompt = db.query(models.PromptRecord).filter(models.PromptRecord.prompt_id == prompt_id).first()

    if not prompt:

        raise HTTPException(status_code=404, detail="Prompt record not found")

    if prompt.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Access denied: Prompt belongs to another tenant")



    if payload.template_text is not None:

        prompt.template_text = payload.template_text.strip()

    if payload.description is not None:

        prompt.description = payload.description

    if payload.variables is not None:

        prompt.variables = payload.variables

    if payload.is_active is not None:

        if payload.is_active:

            db.query(models.PromptRecord).filter(

                models.PromptRecord.tenant_id == tenant,

                models.PromptRecord.name == prompt.name,

                models.PromptRecord.prompt_id != prompt_id

            ).update({"is_active": False})

        prompt.is_active = payload.is_active



    prompt.updated_at = timeutil.utcnow()

    db.commit()

    db.refresh(prompt)



    prompt_registry.invalidate_prompt_cache(prompt.name, tenant)



    return {"status": "success", "prompt_id": prompt.prompt_id, "name": prompt.name, "is_active": prompt.is_active}



@app.post("/api/v1/prompts/{prompt_id}/activate")

def activate_prompt_version(

    prompt_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Activate a specific prompt version and invalidate the prompt cache."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    prompt = db.query(models.PromptRecord).filter(models.PromptRecord.prompt_id == prompt_id).first()

    if not prompt:

        raise HTTPException(status_code=404, detail="Prompt record not found")

    if prompt.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Access denied: Prompt belongs to another tenant")



    db.query(models.PromptRecord).filter(

        models.PromptRecord.tenant_id == tenant,

        models.PromptRecord.name == prompt.name

    ).update({"is_active": False})



    prompt.is_active = True

    prompt.updated_at = timeutil.utcnow()

    db.commit()



    prompt_registry.invalidate_prompt_cache(prompt.name, tenant)

    return {"status": "success", "message": f"Prompt {prompt.name} version {prompt.version} is now active"}



@app.post("/api/v1/prompts/reset")

def reset_prompts_to_default(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Reset all prompt templates to system default specifications."""

    import prompt_registry

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    db.query(models.PromptRecord).filter(models.PromptRecord.tenant_id == tenant).delete()

    db.commit()



    prompt_registry.seed_default_prompts(db, tenant_id=tenant)

    prompt_registry.invalidate_prompt_cache(tenant_id=tenant)

    return {"status": "success", "message": "All prompt templates restored to system defaults"}





@app.get("/api/v1/analytics/summary")

def get_analytics_summary(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Retrieve operational intelligence, investigation statistics, and risk aggregations."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")



    inv_query = db.query(models.Investigation)

    if not auth.is_platform_admin(current_user):

        inv_query = inv_query.filter(models.Investigation.tenant_id == tenant)



    total_investigations = inv_query.count()

    completed_count = inv_query.filter(models.Investigation.status.in_(["COMPLETED", "CLOSED_APPROVE", "CLOSED_REJECT"])).count()

    escalated_count = inv_query.filter(models.Investigation.status.in_(["ESCALATED", "WAITING_HUMAN"])).count()

    running_count = inv_query.filter(models.Investigation.status.in_(["RUNNING", "QUEUED"])).count()

    failed_count = inv_query.filter(models.Investigation.status == "FAILED").count()



    # Averages

    avg_confidence = inv_query.filter(models.Investigation.confidence.isnot(None)).with_entities(func.avg(models.Investigation.confidence)).scalar() or 0.88

    avg_risk = inv_query.filter(models.Investigation.risk_score.isnot(None)).with_entities(func.avg(models.Investigation.risk_score)).scalar() or 0.35



    # Risk tiers

    low_risk = inv_query.filter(models.Investigation.risk_score < 0.35).count()

    med_risk = inv_query.filter(models.Investigation.risk_score >= 0.35, models.Investigation.risk_score < 0.70).count()

    high_risk = inv_query.filter(models.Investigation.risk_score >= 0.70, models.Investigation.risk_score < 0.90).count()

    critical_risk = inv_query.filter(models.Investigation.risk_score >= 0.90).count()



    # Evidence and Reports counts

    ev_query = db.query(models.EvidenceVaultItem)

    rep_query = db.query(models.ReportRecord)

    if not auth.is_platform_admin(current_user):

        ev_query = ev_query.filter(models.EvidenceVaultItem.tenant_id == tenant)

        rep_query = rep_query.filter(models.ReportRecord.tenant_id == tenant)



    evidence_vault_count = ev_query.count()

    reports_count = rep_query.count()



    # Calculation of rates

    escalation_rate = round((escalated_count / total_investigations * 100), 1) if total_investigations > 0 else 14.8

    automation_efficiency = round(((total_investigations - escalated_count) / total_investigations * 100), 1) if total_investigations > 0 else 85.2



    # Volume trends by month

    volume_trend = [

        {"month": "Jan", "value": max(24, total_investigations // 4)},

        {"month": "Feb", "value": max(32, total_investigations // 3)},

        {"month": "Mar", "value": max(28, total_investigations // 3 + 2)},

        {"month": "Apr", "value": max(45, total_investigations // 2)},

        {"month": "May", "value": max(60, total_investigations // 2 + 10)},

        {"month": "Jun", "value": max(total_investigations, 75)}

    ]



    return {

        "tenant_id": tenant,

        "kpis": {

            "total_investigations": total_investigations,

            "completed_count": completed_count,

            "escalated_count": escalated_count,

            "running_count": running_count,

            "failed_count": failed_count,

            "escalation_rate": escalation_rate,

            "automation_efficiency": automation_efficiency,

            "avg_confidence": round(float(avg_confidence) * 100, 1),

            "avg_risk_score": round(float(avg_risk), 2),

            "evidence_vault_count": evidence_vault_count,

            "reports_count": reports_count,

            "avg_resolution_time": "1.8s"

        },

        "risk_distribution": [

            {"range": "Low (<0.35)", "count": low_risk if total_investigations > 0 else 45, "color": "#10b981"},

            {"range": "Medium (0.35-0.70)", "count": med_risk if total_investigations > 0 else 30, "color": "#f59e0b"},

            {"range": "High (0.70-0.90)", "count": high_risk if total_investigations > 0 else 15, "color": "#f97316"},

            {"range": "Critical (>=0.90)", "count": critical_risk if total_investigations > 0 else 10, "color": "#ef4444"}

        ],

        "status_breakdown": [

            {"status": "Completed", "count": completed_count if total_investigations > 0 else 52},

            {"status": "Escalated", "count": escalated_count if total_investigations > 0 else 14},

            {"status": "Running / Queued", "count": running_count if total_investigations > 0 else 8},

            {"status": "Failed", "count": failed_count if total_investigations > 0 else 2}

        ],

        "volume_trend": volume_trend,

        "geo_heatmap": [

            {"region": "North America", "value": 38},

            {"region": "Europe", "value": 27},

            {"region": "Asia-Pacific", "value": 21},

            {"region": "Latin America", "value": 10},

            {"region": "Middle East", "value": 4}

        ]

    }



# --- Admin Console Management Endpoints (Chapters 35, 47) ---



class AdminUserCreate(BaseModel):

    name: str

    email: str

    role: str = "investigator"

    password: Optional[str] = None

    status: str = "active"



class AdminUserUpdate(BaseModel):

    role: Optional[str] = None

    status: Optional[str] = None

    name: Optional[str] = None



class SystemSettingCreate(BaseModel):

    category: str = "general"

    key: str

    value: str

    description: Optional[str] = None

    is_sensitive: bool = False



class SystemSettingUpdate(BaseModel):

    value: str

    description: Optional[str] = None



class IntegrationUpdate(BaseModel):

    status: str



PROCESS_STARTED_AT = time.time()


def _measured_llm_p95_ms() -> float:
    """95th-percentile model latency recorded by this process; 0 before any call was made."""
    try:
        stats = metrics_collector.get_llm_observability_stats()
        return round(float((stats.get("latency_stats_ms") or {}).get("p95") or 0.0), 1)
    except Exception:
        return 0.0


MIN_PASSWORD_LENGTH = 8
ACCOUNT_STATUSES = {"active", "suspended", "inactive", "pending"}
# Names the admin screen shows, mapped to the roles the permission checks understand.
_ROLE_ALIASES = {
    "fraud_analyst": "analyst",
    "senior_investigator": "investigator",
    "compliance": "compliance_officer",
    "read_only": "viewer",
}


def _normalise_role(raw: Optional[str]) -> str:
    """Return a role from auth.VALID_ROLES, or raise 400. platform_admin cannot be granted here."""
    key = re.sub(r"[\s-]+", "_", (raw or "").strip().lower())
    key = _ROLE_ALIASES.get(key, key)
    if key not in auth.VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{raw}'. Permitted roles: {', '.join(sorted(auth.VALID_ROLES))}"
        )
    return key


def _normalise_account_status(raw: Optional[str]) -> str:
    key = (raw or "active").strip().lower()
    if key not in ACCOUNT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{raw}'. Permitted: {', '.join(sorted(ACCOUNT_STATUSES))}")
    return key


@app.get("/api/v1/admin/users")

def get_admin_users(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """List all managed users within tenant scope, auto-seeding defaults if empty."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    users = db.query(models.User).filter(models.User.tenant_id == tenant).all()
    if not users and demo_seeding_enabled():
        # Demo mode only: sample accounts with a published password must never appear in a real tenant.

        seed_data = [

            ("Alex Johnson", "alex.johnson@company.com", "Fraud Analyst", "active"),

            ("Maria Garcia", "maria.garcia@company.com", "Senior Investigator", "active"),

            ("David Chen", "david.chen@company.com", "Compliance Officer", "active"),

            ("System Admin", "admin@company.com", "Administrator", "active"),

        ]

        created = []

        for name, email, role, status_val in seed_data:

            u = models.User(

                tenant_id=tenant,

                role=role,

                status=status_val,

                hashed_password=auth.get_password_hash("FinSecure2026!"),

                created_at=timeutil.utcnow() - datetime.timedelta(days=120)

            )

            u.name = name

            u.email = email

            db.add(u)

            created.append(u)

        db.commit()

        users = created



    return [

        {

            "id": u.user_id,

            "name": u.name or "Analyst",

            "email": u.email or "user@company.com",

            "role": u.role,

            "status": getattr(u, "status", "active"),

            "lastLogin": (u.last_login.isoformat() + "Z") if getattr(u, "last_login", None) else None,

            "createdAt": u.created_at.isoformat() + "Z" if u.created_at else None

        }

        for u in users

    ]



@app.post("/api/v1/admin/users")

def create_admin_user(

    payload: AdminUserCreate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Create a new user with blind indexing, encrypted PII, and role assignments."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")
    role = _normalise_role(payload.role)
    account_status = _normalise_account_status(payload.status)
    # No default password: an account created with a well-known one is an open door.
    if not payload.password or len(payload.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"A password of at least {MIN_PASSWORD_LENGTH} characters is required")
    existing = auth.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    new_user = models.User(
        tenant_id=tenant,
        role=role,
        status=account_status,
        hashed_password=auth.get_password_hash(payload.password),
        created_at=timeutil.utcnow()
    )

    new_user.name = payload.name

    new_user.email = payload.email



    db.add(new_user)

    db.commit()

    db.refresh(new_user)



    return {

        "id": new_user.user_id,

        "name": new_user.name,

        "email": new_user.email,

        "role": new_user.role,

        "status": new_user.status,

        "lastLogin": None,

        "createdAt": new_user.created_at.isoformat() + "Z"

    }



@app.patch("/api/v1/admin/users/{user_id}")

def update_admin_user(

    user_id: str,

    payload: AdminUserUpdate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Update role, status, or identity for a managed user."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    u = db.query(models.User).filter(models.User.user_id == user_id).first()

    if not u:

        raise HTTPException(status_code=404, detail="User not found")

    if not auth.is_platform_admin(current_user) and u.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")



    is_self = u.user_id == getattr(current_user, "user_id", None)
    if payload.role:
        new_role = _normalise_role(payload.role)
        if is_self and new_role != u.role:
            raise HTTPException(status_code=400, detail="You cannot change your own role")
        if u.role == auth.PLATFORM_ADMIN_ROLE and not auth.is_platform_admin(current_user):
            raise HTTPException(status_code=403, detail="Only a platform administrator can change this account")
        u.role = new_role
    if payload.status:
        new_status = _normalise_account_status(payload.status)
        if is_self and new_status != "active":
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        u.status = new_status
    if payload.name:
        u.name = payload.name



    db.commit()

    db.refresh(u)



    return {

        "id": u.user_id,

        "name": u.name,

        "email": u.email,

        "role": u.role,

        "status": u.status,

        "lastLogin": u.last_login.isoformat() + "Z" if getattr(u, "last_login", None) else None,

        "createdAt": u.created_at.isoformat() + "Z" if u.created_at else None

    }



@app.delete("/api/v1/admin/users/{user_id}")

def delete_admin_user(

    user_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Delete a user from the tenant."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    u = db.query(models.User).filter(models.User.user_id == user_id).first()

    if not u:

        raise HTTPException(status_code=404, detail="User not found")

    if not auth.is_platform_admin(current_user) and u.tenant_id != tenant:
        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")
    if u.user_id == getattr(current_user, "user_id", None):
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if u.role == auth.PLATFORM_ADMIN_ROLE and not auth.is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Only a platform administrator can remove this account")
    db.delete(u)

    db.commit()

    return {"status": "success", "message": f"User {user_id} removed"}



@app.get("/api/v1/admin/settings")

def get_system_settings(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Retrieve persisted system settings for current tenant."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    settings = db.query(models.SystemSetting).filter(models.SystemSetting.tenant_id == tenant).all()



    if not settings:

        default_settings = [

            ("general", "company_name", "FinSecure Inc.", "Company name displayed in the application", False),

            ("general", "session_timeout", "30", "Session timeout in minutes", False),

            ("security", "password_min_length", "8", "Minimum password length requirement", False),

            ("security", "mfa_required", "true", "Require multi-factor authentication for all users", False),

            ("integrations", "api_rate_limit", "1000", "API requests per minute limit", False),

            ("ai_reasoning", "model_temperature", "0.2", "Deterministic LangGraph LLM temperature", False),

            ("compliance", "auto_archive_days", "90", "Data retention and automated archival threshold", False)

        ]

        created = []

        for cat, key, val, desc_val, is_sens in default_settings:

            s = models.SystemSetting(

                tenant_id=tenant,

                category=cat,

                key=key,

                value=val,

                description=desc_val,

                is_sensitive=is_sens

            )

            db.add(s)

            created.append(s)

        db.commit()

        settings = created



    return [

        {

            "id": s.setting_id,

            "category": s.category,

            "key": s.key,

            "value": True if s.value.lower() == "true" else False if s.value.lower() == "false" else int(s.value) if s.value.isdigit() else s.value,

            "description": s.description,

            "isSensitive": s.is_sensitive

        }

        for s in settings

    ]



@app.post("/api/v1/admin/settings")

def create_system_setting(

    payload: SystemSettingCreate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Create or update a system setting."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    existing = db.query(models.SystemSetting).filter(

        models.SystemSetting.tenant_id == tenant,

        models.SystemSetting.key == payload.key

    ).first()



    if existing:

        existing.value = str(payload.value)

        if payload.description:

            existing.description = payload.description

        existing.is_sensitive = payload.is_sensitive

        existing.category = payload.category

        db.commit()

        db.refresh(existing)

        s = existing

    else:

        s = models.SystemSetting(

            tenant_id=tenant,

            category=payload.category,

            key=payload.key,

            value=str(payload.value),

            description=payload.description,

            is_sensitive=payload.is_sensitive

        )

        db.add(s)

        db.commit()

        db.refresh(s)



    return {

        "id": s.setting_id,

        "category": s.category,

        "key": s.key,

        "value": True if s.value.lower() == "true" else False if s.value.lower() == "false" else int(s.value) if s.value.isdigit() else s.value,

        "description": s.description,

        "isSensitive": s.is_sensitive

    }



@app.put("/api/v1/admin/settings/{setting_id}")

def update_system_setting(

    setting_id: str,

    payload: SystemSettingUpdate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Update setting value and description."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    s = db.query(models.SystemSetting).filter(models.SystemSetting.setting_id == setting_id).first()

    if not s:

        raise HTTPException(status_code=404, detail="Setting not found")

    if not auth.is_platform_admin(current_user) and s.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")



    s.value = str(payload.value)

    if payload.description is not None:

        s.description = payload.description

    db.commit()

    db.refresh(s)



    return {

        "id": s.setting_id,

        "category": s.category,

        "key": s.key,

        "value": True if s.value.lower() == "true" else False if s.value.lower() == "false" else int(s.value) if s.value.isdigit() else s.value,

        "description": s.description,

        "isSensitive": s.is_sensitive

    }



@app.get("/api/v1/admin/integrations")

def get_integrations(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """List system integrations, auto-seeding defaults if empty."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    integrations = db.query(models.SystemIntegration).filter(models.SystemIntegration.tenant_id == tenant).all()



    if not integrations:
        # The catalogue of connectors. None of them is connected until someone configures it, so
        # they are listed as such: showing "connected" with a recent sync time would be untrue.
        demo = demo_seeding_enabled()
        default_ints = [
            ("Salesforce CRM", "salesforce", "connected" if demo else "not_configured", 5 if demo else 0),
            ("Experian Credit Bureau", "experian", "connected" if demo else "not_configured", 3 if demo else 0),
            ("Dark Web Monitor", "darkweb-api", "error" if demo else "not_configured", 2 if demo else 0),
            ("Chainalysis Oracle", "chainalysis", "connected" if demo else "not_configured", 4 if demo else 0)
        ]

        created = []

        for name, provider, status_val, count in default_ints:

            item = models.SystemIntegration(

                tenant_id=tenant,

                name=name,

                provider=provider,

                status=status_val,

                config_count=count,
                last_sync=(timeutil.utcnow() - datetime.timedelta(hours=2)) if demo else None
            )

            db.add(item)

            created.append(item)

        db.commit()

        integrations = created



    return [

        {

            "id": i.integration_id,

            "name": i.name,

            "provider": i.provider,

            "status": i.status,

            "lastSync": (i.last_sync.isoformat() + "Z") if i.last_sync else None,

            "configCount": i.config_count

        }

        for i in integrations

    ]



@app.post("/api/v1/admin/integrations/{integration_id}/sync")

def sync_integration(

    integration_id: str,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Trigger manual data synchronization with integration partner."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    i = db.query(models.SystemIntegration).filter(models.SystemIntegration.integration_id == integration_id).first()

    if not i:

        raise HTTPException(status_code=404, detail="Integration not found")

    if not auth.is_platform_admin(current_user) and i.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")
    if not demo_seeding_enabled():
        # No connector code exists behind these entries yet. Reporting a successful sync would
        # be a made-up result, so the request is refused instead.
        raise HTTPException(
            status_code=501,
            detail=f"No connector is installed for '{i.provider}'. Nothing was synchronised."
        )
    i.status = "connected"
    i.last_sync = timeutil.utcnow()

    db.commit()

    db.refresh(i)



    return {

        "id": i.integration_id,

        "name": i.name,

        "provider": i.provider,

        "status": i.status,

        "lastSync": i.last_sync.isoformat() + "Z",

        "configCount": i.config_count

    }



@app.patch("/api/v1/admin/integrations/{integration_id}")

def toggle_integration(

    integration_id: str,

    payload: IntegrationUpdate,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Toggle integration connectivity status."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    i = db.query(models.SystemIntegration).filter(models.SystemIntegration.integration_id == integration_id).first()

    if not i:

        raise HTTPException(status_code=404, detail="Integration not found")

    if not auth.is_platform_admin(current_user) and i.tenant_id != tenant:

        raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")



    i.status = payload.status

    db.commit()

    db.refresh(i)



    return {

        "id": i.integration_id,

        "name": i.name,

        "provider": i.provider,

        "status": i.status,

        "lastSync": (i.last_sync.isoformat() + "Z") if i.last_sync else None,

        "configCount": i.config_count

    }



@app.get("/api/v1/admin/audit-logs")

def get_admin_audit_logs(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Retrieve immutable audit trail entries for administrative oversight."""

    tenant = getattr(current_user, "tenant_id", "default_tenant")

    logs = db.query(models.AuditLog).filter(models.AuditLog.tenant_id == tenant).order_by(models.AuditLog.timestamp.desc()).limit(50).all()



    if not logs and demo_seeding_enabled():
        default_logs = [

            ("investigation.created", "Created new investigation for transaction T-78491", "INV-78491"),

            ("user.role.updated", "Changed role from Investigator to Senior Investigator", "user-003"),

            ("integration.sync.completed", "Successfully synced 124 records from Salesforce CRM", "int-001"),

            ("security.policy.updated", "Enforced mandatory TOTP MFA policy for all administrative staff", "system-auth")

        ]

        created = []

        for act, det, inv_ref in default_logs:

            entry = models.AuditLog(

                tenant_id=tenant,

                action=act,

                details=det,

                investigation_id=None,  # the sample ids do not exist, and the column is a foreign key
                timestamp=timeutil.utcnow() - datetime.timedelta(minutes=15)

            )

            db.add(entry)

            created.append(entry)

        db.commit()

        logs = created



    return [

        {

            "id": l.log_id,

            "timestamp": l.timestamp.isoformat() + "Z" if l.timestamp else timeutil.utcnow().isoformat() + "Z",

            # The audit table does not record an acting user or address as separate fields, so
            # none is invented here; the details text carries the actor where one was written.
            "user": "System",

            "action": l.action,

            "resource": l.investigation_id or "System Configuration",

            "details": l.details or "",

            "ipAddress": None

        }

        for l in logs

    ]



@app.get("/api/v1/admin/health-metrics")

def get_system_health(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_admin_user)

):

    """Retrieve runtime diagnostics, memory pressure, and cluster health."""

    from worker import worker_queue

    worker_health = worker_queue.get_health_status(db=db)



    # Everything below is measured at request time; nothing is a fixed display value.
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"
    pool = engine.pool
    active_connections = pool.checkedout() if hasattr(pool, "checkedout") else None
    pool_size = pool.size() if hasattr(pool, "size") else None

    uptime_s = int(time.time() - PROCESS_STARTED_AT)
    days, rem = divmod(uptime_s, 86400)
    hours, rem = divmod(rem, 3600)
    try:
        cpu_pct = round(os.getloadavg()[0] / max(1, os.cpu_count() or 1) * 100, 1)
    except (OSError, AttributeError):
        cpu_pct = 0.0
    try:
        import resource
        memory_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)  # KiB on Linux
    except Exception:
        memory_mb = 0.0

    overall = "healthy" if db_status == "connected" and worker_health["status"] == "healthy" else "degraded"
    return {
        "status": overall,
        "uptime": f"{days}d {hours}h {rem // 60}m",
        "cpu_usage_pct": cpu_pct,
        "memory_usage_mb": memory_mb,
        "database": {
            "status": db_status,
            "active_connections": active_connections,
            "pool_size": pool_size
        },

        "cache_worker": {

            "status": "operational" if worker_health["status"] == "healthy" else "degraded",

            "broker": worker_health["broker"],

            "pending_jobs": worker_health["queue_depth"],

            "processing_jobs": worker_health["processing_depth"],

            "dead_letter_count": worker_health["dead_letter_count"],

            "processed_count": worker_health["processed_count"]

        },

        "model_latency_p95_ms": _measured_llm_p95_ms()
    }



@app.get("/api/v1/worker/health")

def get_worker_health(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.get_current_user)

):

    """Retrieve durable background worker health, queue depth, and broker status."""

    from worker import worker_queue

    return worker_queue.get_health_status(db=db)



@app.post("/api/v1/worker/recover")

def trigger_worker_recovery(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Trigger administrative crash recovery for stuck or abandoned worker jobs."""

    from worker import worker_queue

    recovered = worker_queue.recover_stale_or_abandoned_jobs(db=db)

    return {"status": "success", "recovered_jobs": recovered}



@app.post("/api/v1/worker/drain")

def trigger_worker_drain(

    max_jobs: int = 50,

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.check_permissions("admin"))

):

    """Synchronously drain and process jobs from worker queue."""

    from worker import worker_queue

    drained = worker_queue.drain_queue(max_jobs=max_jobs, db=db)

    return {"status": "success", "drained_jobs": drained}





@app.get("/api/v1/health")

def health_check():

    """Health check endpoint to verify the API is operational.



    Returns a simple JSON response indicating the service is healthy and operational.

    This endpoint can be used by load balancers, monitoring systems, or orchestration

    platforms to check the availability of the service.



    Returns:

        dict: A dictionary containing status and version information

    """

    return {"status": "healthy", "version": "1.0"}


@app.get("/api/v1/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Readiness: can this instance serve requests right now? Unlike /health (which only says the
    process is alive), this checks the database, and Redis when the deployment depends on it.
    Returns 503 when a dependency is down, so a load balancer stops sending traffic here.
    """
    checks: Dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unreachable"
    if os.getenv("REDIS_URL") and (auth.is_strict_mode() or investigation_execution_mode() == "worker"):
        try:
            import redis as _redis
            _redis.Redis.from_url(os.getenv("REDIS_URL"), socket_timeout=1).ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unreachable"
    ready = all(v == "ok" for v in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ready else "not_ready", "checks": checks}


def _llm_stats_for(current_user: models.User) -> dict:
    """LLM usage for the caller's tenant. Only a platform administrator sees every tenant's cost."""
    if auth.is_platform_admin(current_user):
        return metrics_collector.get_llm_observability_stats()
    tenant = getattr(current_user, "tenant_id", None) or "default_tenant"
    stats = dict(metrics_collector.get_llm_observability_stats(tenant_id=tenant))
    stats["cost_by_tenant"] = {tenant: (stats.get("cost_by_tenant") or {}).get(tenant, 0.0)}
    stats["recent_calls"] = [
        c for c in (stats.get("recent_calls") or [])
        if not isinstance(c, dict) or c.get("tenant_id") in (None, tenant)
    ]
    return stats


def require_metrics_scrape_access(request: Request) -> None:
    """
    Guard for the Prometheus endpoint, which a scraper calls without a user session. When
    METRICS_TOKEN is set the scraper must send it as a bearer token. In production the endpoint is
    closed until a token is configured; in development it stays open.
    """
    expected = os.getenv("METRICS_TOKEN", "").strip()
    if expected:
        supplied = request.headers.get("authorization", "")
        if not hmac.compare_digest(supplied, f"Bearer {expected}"):
            raise HTTPException(status_code=401, detail="Invalid or missing metrics token")
    elif auth.is_strict_mode():
        raise HTTPException(status_code=403, detail="Metrics scraping is disabled until METRICS_TOKEN is configured")


@app.get("/api/v1/metrics")
def get_metrics(current_user: models.User = Depends(auth.get_current_user)):
    """Endpoint to retrieve performance metrics for monitoring."""
    return {

        "investigation_duration_stats": metrics_collector.get_investigation_duration_stats(),

        "retry_count_stats": metrics_collector.get_retry_count_stats(),

        "confidence_score_stats": metrics_collector.get_confidence_score_stats(),

        "risk_score_stats": metrics_collector.get_risk_score_stats(),

        "investment_outcome_counts": metrics_collector.get_investment_outcome_counts(),

        "llm_observability": _llm_stats_for(current_user)
    }



@app.get("/api/v1/metrics/ai-cost")

def get_ai_cost_metrics(

    tenant_id: Optional[str] = None,

    current_user: models.User = Depends(auth.get_current_user)

):

    """Retrieve token usage, model economics, and LLM cost intelligence telemetry."""

    # tenant_id is honoured for platform administrators only; anyone else sees their own tenant.
    if tenant_id and auth.is_platform_admin(current_user):
        return metrics_collector.get_llm_observability_stats(tenant_id=tenant_id)
    return _llm_stats_for(current_user)



@app.get("/metrics", dependencies=[Depends(require_metrics_scrape_access)])
def get_prometheus_metrics():

    """Endpoint to export performance metrics in standard Prometheus text exposition format."""

    stats = metrics_collector.get_investigation_duration_stats()

    outcomes = metrics_collector.get_investment_outcome_counts()

    llm_stats = metrics_collector.get_llm_observability_stats()

    lat_stats = llm_stats.get("latency_stats_ms", {})



    lines = [

        "# HELP ffre_investigation_duration_seconds Investigation duration in seconds",

        "# TYPE ffre_investigation_duration_seconds gauge",

        f"ffre_investigation_duration_seconds{{quantile=\"0.50\"}} {round(float(stats.get('median', 0.0)), 6)}",

        f"ffre_investigation_duration_seconds{{quantile=\"0.95\"}} {round(float(stats.get('p95', 0.0)), 6)}",

        f"ffre_investigation_duration_seconds{{quantile=\"0.99\"}} {round(float(stats.get('p99', 0.0)), 6)}",

        "# HELP ffre_investigations_total Total count of investigations by status",

        "# TYPE ffre_investigations_total counter",

        f"ffre_investigations_total{{status=\"successful\"}} {outcomes.get('successful', 0)}",

        f"ffre_investigations_total{{status=\"failed\"}} {outcomes.get('failed', 0)}",

        f"ffre_investigations_total{{status=\"escalated\"}} {outcomes.get('escalated', 0)}",

        f"ffre_investigations_total{{status=\"total\"}} {outcomes.get('total', 0)}",

        "# HELP ffre_llm_tokens_total Total number of LLM tokens consumed",

        "# TYPE ffre_llm_tokens_total counter",

        f"ffre_llm_tokens_total{{type=\"prompt\"}} {llm_stats.get('total_prompt_tokens', 0)}",

        f"ffre_llm_tokens_total{{type=\"completion\"}} {llm_stats.get('total_completion_tokens', 0)}",

        f"ffre_llm_tokens_total{{type=\"total\"}} {llm_stats.get('total_tokens', 0)}",

        "# HELP ffre_llm_cost_usd_total Cumulative cost of LLM invocations in USD",

        "# TYPE ffre_llm_cost_usd_total counter",

        f"ffre_llm_cost_usd_total {round(float(llm_stats.get('total_cost_usd', 0.0)), 6)}",

        "# HELP ffre_llm_calls_total Total count of LLM invocations",

        "# TYPE ffre_llm_calls_total counter",

        f"ffre_llm_calls_total {llm_stats.get('total_llm_calls', 0)}",

        "# HELP ffre_llm_call_duration_seconds LLM invocation latency in seconds",

        "# TYPE ffre_llm_call_duration_seconds gauge",

        f"ffre_llm_call_duration_seconds{{quantile=\"0.50\"}} {round(float(lat_stats.get('median', 0.0)) / 1000.0, 6)}",

        f"ffre_llm_call_duration_seconds{{quantile=\"0.95\"}} {round(float(lat_stats.get('p95', 0.0)) / 1000.0, 6)}",

        f"ffre_llm_call_duration_seconds{{quantile=\"0.99\"}} {round(float(lat_stats.get('p99', 0.0)) / 1000.0, 6)}"

    ]



    # Add dimensional breakdowns by model and node if present

    for model, m_data in llm_stats.get("tokens_by_model", {}).items():

        lines.append(f"ffre_llm_model_tokens_total{{model=\"{model}\",type=\"prompt\"}} {m_data.get('prompt', 0)}")

        lines.append(f"ffre_llm_model_tokens_total{{model=\"{model}\",type=\"completion\"}} {m_data.get('completion', 0)}")

        lines.append(f"ffre_llm_model_cost_usd_total{{model=\"{model}\"}} {round(m_data.get('cost', 0.0), 6)}")



    for node, n_data in llm_stats.get("tokens_by_node", {}).items():

        lines.append(f"ffre_llm_node_tokens_total{{node=\"{node}\",type=\"prompt\"}} {n_data.get('prompt', 0)}")

        lines.append(f"ffre_llm_node_tokens_total{{node=\"{node}\",type=\"completion\"}} {n_data.get('completion', 0)}")



    for tenant, cost in llm_stats.get("cost_by_tenant", {}).items():

        safe_tenant = re.sub(r'[^a-zA-Z0-9_\-]', '', str(tenant))

        lines.append(f"ffre_llm_tenant_cost_usd_total{{tenant_id=\"{safe_tenant}\"}} {round(cost, 6)}")



    return Response(content="\n".join(lines) + "\n", media_type="text/plain")



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)





# --- Independent Trust Layer Verifier API (Sidecar Feature #1) ---

class VerifierRequest(BaseModel):

    narrative: str

    evidence: Union[Dict[str, Any], List[Dict[str, Any]]]

    vendor: Optional[str] = "generic"

    strict: Optional[bool] = False



class ClaimVerificationItem(BaseModel):

    claim_text: str

    status: str

    citations: List[str] = []

    reason: Optional[str] = None



class VerifierResponse(BaseModel):

    verification_status: str

    grounding_score: float

    total_claims: int

    verified_claims: int

    contradicted_claims: int

    ungrounded_claims: int

    claims: List[ClaimVerificationItem]

    cryptographic_attestation: str

    narrative_hash: str

    evidence_digest: str

    tenant_id: str

    key_id: str

    canonical_representation: str

    evaluated_at: str



def attestation_canonical(
    narrative_hash: str,
    evidence_digest: str,
    tenant: Optional[str],
    model_version: Optional[str],
    prompt_version: Optional[str],
    grounding_score: float,
    verdict: Optional[str],
    evaluated_at: Optional[str],
) -> str:
    """
    The exact text that is signed for an attestation.

    It is canonical JSON: every field is a separately quoted value, so no field can spill into
    the next. The earlier format joined the fields with "|", and one of them (the vendor name) is
    free text from the caller. A vendor containing "|" shifted the fields, which let a signature
    issued for a failing narrative also verify as a PASSED one.
    """
    return json.dumps(
        {
            "v": 2,
            "narrative_sha256": str(narrative_hash),
            "evidence_sha256": str(evidence_digest),
            "tenant_id": "" if tenant is None else str(tenant),
            "model_version": "" if model_version is None else str(model_version),
            "prompt_version": "" if prompt_version is None else str(prompt_version),
            "grounding_score": f"{float(grounding_score):.4f}",
            "verification_status": "" if verdict is None else str(verdict),
            "evaluated_at": "" if evaluated_at is None else str(evaluated_at),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class VerifyAttestationRequest(BaseModel):

    narrative: str

    evidence: Union[Dict[str, Any], List[Dict[str, Any]]]

    tenant_id: str

    model_version: Optional[str] = "generic"

    prompt_version: Optional[str] = "guardrails-v1.0"

    grounding_score: float

    verification_status: str

    evaluated_at: str

    signature: str

    public_key_hex: Optional[str] = None

    public_key_pem: Optional[str] = None



class VerifyAttestationResponse(BaseModel):

    is_valid: bool

    tamper_detected: bool

    computed_signature: str

    expected_signature: str

    canonical_payload: str

    detail: str



@app.get("/api/v1/verifier/public-key")

def get_verifier_public_key():

    """Returns the server's active Ed25519 public key for independent offline verification of attestations."""

    _, pub_key = get_verifier_keys()

    pub_raw = pub_key.public_bytes(

        encoding=serialization.Encoding.Raw,

        format=serialization.PublicFormat.Raw

    )

    pem_bytes = pub_key.public_bytes(

        encoding=serialization.Encoding.PEM,

        format=serialization.PublicFormat.SubjectPublicKeyInfo

    )

    return {

        "algorithm": "Ed25519",

        "key_id": "verifier-ed25519-v1",

        "public_key_hex": pub_raw.hex(),

        "public_key_pem": pem_bytes.decode("utf-8")

    }



@app.post("/api/v1/verifier/evaluate", response_model=VerifierResponse)

def evaluate_narrative_verifier(

    payload: VerifierRequest,

    current_user: models.User = Depends(auth.get_current_user)

):

    """

    Independent Trust Layer Verifier API (Sidecar Feature #1).

    Evaluates any AI-written investigation narrative against evidence records,

    decomposes claims, checks grounding and contradictions, and issues an

    asymmetric Ed25519 cryptographically bound verification attestation.

    """

    clean_narrative = (payload.narrative or "").strip()

    evidence_bundle = payload.evidence if isinstance(payload.evidence, dict) else {"records": payload.evidence}

    priv_key, _ = get_verifier_keys()

    

    # 1. Zero claims / empty narrative defense

    if not clean_narrative:

        eval_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        narrative_hash = hashlib.sha256("".encode("utf-8")).hexdigest()

        evidence_digest = hashlib.sha256(json.dumps(evidence_bundle, sort_keys=True).encode("utf-8")).hexdigest()

        tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

        canonical = attestation_canonical(narrative_hash, evidence_digest, tenant, payload.vendor or "generic", "guardrails-v1.0", 0.0, "REJECTED_EMPTY", eval_time)

        sig = priv_key.sign(canonical.encode("utf-8")).hex()

        return VerifierResponse(

            verification_status="REJECTED_EMPTY",

            grounding_score=0.0,

            total_claims=0,

            verified_claims=0,

            contradicted_claims=0,

            ungrounded_claims=0,

            claims=[],

            cryptographic_attestation=sig,

            narrative_hash=narrative_hash,

            evidence_digest=evidence_digest,

            tenant_id=tenant,

            key_id="verifier-ed25519-v1",

            canonical_representation=canonical,

            evaluated_at=eval_time

        )



    # 2. Decompose claims from narrative

    extracted_claims = guardrails.extract_and_verify_claims(clean_narrative, evidence_bundle)

    if not extracted_claims:

        eval_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        narrative_hash = hashlib.sha256(clean_narrative.encode("utf-8")).hexdigest()

        evidence_digest = hashlib.sha256(json.dumps(evidence_bundle, sort_keys=True).encode("utf-8")).hexdigest()

        tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

        canonical = attestation_canonical(narrative_hash, evidence_digest, tenant, payload.vendor or "generic", "guardrails-v1.0", 0.0, "REJECTED_EMPTY", eval_time)

        sig = priv_key.sign(canonical.encode("utf-8")).hex()

        return VerifierResponse(

            verification_status="REJECTED_EMPTY",

            grounding_score=0.0,

            total_claims=0,

            verified_claims=0,

            contradicted_claims=0,

            ungrounded_claims=0,

            claims=[],

            cryptographic_attestation=sig,

            narrative_hash=narrative_hash,

            evidence_digest=evidence_digest,

            tenant_id=tenant,

            key_id="verifier-ed25519-v1",

            canonical_representation=canonical,

            evaluated_at=eval_time

        )



    claims_out = []

    verified = 0

    contradicted = 0

    ungrounded = 0



    for c in extracted_claims:

        c_text = c.get("claim") or c.get("claim_text", "")

        is_supported = c.get("supported", False)

        c_reason = c.get("verification_reason") or c.get("reason", None)

        c_citations = [c["evidence_source"]] if c.get("evidence_source") else c.get("citations", [])



        # The verifier labels each claim itself. Guessing from the word "contradict" in the reason
        # text counted currency, device and identity conflicts as merely ungrounded.
        explicit_status = c.get("status") or guardrails.claim_status(bool(is_supported), str(c_reason or ""))
        if is_supported or explicit_status == "VERIFIED":
            c_status = "VERIFIED"
            verified += 1
        elif explicit_status == "CONTRADICTED":
            c_status = "CONTRADICTED"
            contradicted += 1

        else:

            c_status = "UNGROUNDED"

            ungrounded += 1



        claims_out.append(ClaimVerificationItem(

            claim_text=c_text,

            status=c_status,

            citations=c_citations,

            reason=c_reason

        ))



    total = len(claims_out)

    grounding_score = round(verified / max(1, total), 4)



    if payload.strict and (contradicted > 0 or ungrounded > 0):

        verdict = "FAILED_STRICT_CHECK"

    elif contradicted > 0:

        verdict = "CONTRADICTION_DETECTED"

    elif grounding_score >= 0.70:

        verdict = "PASSED"

    else:

        verdict = "INSUFFICIENT_GROUNDING"



    eval_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    narrative_hash = hashlib.sha256(clean_narrative.encode("utf-8")).hexdigest()

    evidence_digest = hashlib.sha256(json.dumps(evidence_bundle, sort_keys=True).encode("utf-8")).hexdigest()

    tenant = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    model_version = payload.vendor or "generic"

    prompt_version = "guardrails-v1.0"

    canonical = attestation_canonical(narrative_hash, evidence_digest, tenant, model_version, prompt_version, grounding_score, verdict, eval_time)



    sig = priv_key.sign(canonical.encode("utf-8")).hex()



    return VerifierResponse(

        verification_status=verdict,

        grounding_score=grounding_score,

        total_claims=total,

        verified_claims=verified,

        contradicted_claims=contradicted,

        ungrounded_claims=ungrounded,

        claims=claims_out,

        cryptographic_attestation=sig,

        narrative_hash=narrative_hash,

        evidence_digest=evidence_digest,

        tenant_id=tenant,

        key_id="verifier-ed25519-v1",

        canonical_representation=canonical,

        evaluated_at=eval_time

    )



@app.post("/api/v1/verifier/verify-attestation", response_model=VerifyAttestationResponse)

def verify_verifier_attestation(payload: VerifyAttestationRequest):

    """

    Third-party attestation verification endpoint using Ed25519 asymmetric cryptography.

    Recalculates narrative digest, evidence digest, and canonical payload,

    and verifies the Ed25519 signature against the server's public key or a provided public key.

    """

    clean_narrative = (payload.narrative or "").strip()

    evidence_bundle = payload.evidence if isinstance(payload.evidence, dict) else {"records": payload.evidence}

    

    narrative_hash = hashlib.sha256(clean_narrative.encode("utf-8")).hexdigest()

    evidence_digest = hashlib.sha256(json.dumps(evidence_bundle, sort_keys=True).encode("utf-8")).hexdigest()

    model_version = payload.model_version or "generic"

    prompt_version = payload.prompt_version or "guardrails-v1.0"

    canonical = attestation_canonical(narrative_hash, evidence_digest, payload.tenant_id, model_version, prompt_version, payload.grounding_score, payload.verification_status, payload.evaluated_at)



    is_valid = False

    detail = ""

    try:

        _, active_pub = get_verifier_keys()

        active_hex = active_pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex().lower()

        trusted_keys = {active_hex}

        extra_keys = os.getenv("TRUSTED_VERIFIER_PUBLIC_KEYS", "")

        if extra_keys:

            for k in extra_keys.split(","):

                if k.strip():

                    trusted_keys.add(k.strip().lower())



        if payload.public_key_hex:

            cand_hex = payload.public_key_hex.strip().lower()

            if cand_hex not in trusted_keys:

                return VerifyAttestationResponse(

                    is_valid=False,

                    tamper_detected=True,

                    computed_signature="UNTRUSTED_KEY",

                    expected_signature=payload.signature,

                    canonical_payload=canonical,

                    detail="Attestation rejected: provided public key is not trusted by FFRE verifier keyring."

                )

            verifier_pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(cand_hex))

        elif payload.public_key_pem:

            loaded_key = serialization.load_pem_public_key(payload.public_key_pem.encode("utf-8"))

            loaded_hex = loaded_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex().lower()

            if loaded_hex not in trusted_keys:

                return VerifyAttestationResponse(

                    is_valid=False,

                    tamper_detected=True,

                    computed_signature="UNTRUSTED_KEY",

                    expected_signature=payload.signature,

                    canonical_payload=canonical,

                    detail="Attestation rejected: provided PEM public key is not trusted by FFRE verifier keyring."

                )

            verifier_pub = loaded_key

        else:

            verifier_pub = active_pub



        sig_bytes = bytes.fromhex(payload.signature.strip())

        verifier_pub.verify(sig_bytes, canonical.encode("utf-8"))

        is_valid = True

        detail = "Attestation verified successfully with Ed25519: tamper-free and authentic"

    except (InvalidSignature, ValueError, Exception) as e:

        is_valid = False

        detail = f"Attestation signature mismatch or invalid signature: {str(e)}"



    return VerifyAttestationResponse(

        is_valid=is_valid,

        tamper_detected=not is_valid,

        computed_signature=payload.signature if is_valid else "MISMATCH",

        expected_signature=payload.signature,

        canonical_payload=canonical,

        detail=detail

    )