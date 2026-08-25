from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import uuid
import datetime
import time
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from database import engine, Base, get_db
import models
from graph import build_graph
import auth
from security import encrypt_data
from metrics import metrics_collector

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FFIRE API Gateway", description="Financial Fraud Investigation Reasoning Engine")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    action: str
    details: Optional[str] = None
    timestamp: datetime.datetime

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

class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            ]
        }
    }

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "investigator"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Smith",
                    "email": "john.smith@example.com",
                    "password": "securePassword123!",
                    "role": "investigator"
                }
            ]
        }
    }

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

# Build the LangGraph app once
graph_app = build_graph()

def run_investigation_task(investigation_id: str, transaction_id: str, db: Optional[Session] = None):
    start_time = time.time()
    should_close_db = False
    if db is None:
        db = next(get_db())
        should_close_db = True
    try:
        initial_state = {
            "investigation_id": investigation_id,
            "transaction_id": transaction_id,
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
        config = {"configurable": {"thread_id": investigation_id}}
        result = graph_app.invoke(initial_state, config=config)

        # Update DB
        investigation = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
        if investigation:
            if result.get("confidence") is not None:
                investigation.confidence = result["confidence"]
                # Import here to avoid circular imports
                from graph import CONFIDENCE_THRESHOLD
                if result["confidence"] < CONFIDENCE_THRESHOLD:
                    investigation.status = "ESCALATED"
                else:
                    investigation.status = "COMPLETED"
            else:
                investigation.status = "COMPLETED"

            if result.get("risk_score") is not None:
                investigation.risk_score = result["risk_score"]

            investigation.report = result.get("report")

            # Save retrieved evidence sources
            evidence_sources = ["customer_evidence", "transaction_evidence", "merchant_evidence", "device_evidence", "location_evidence"]
            for src in evidence_sources:
                if result.get(src):
                    snippet_text = str(result[src])
                    ev = models.Evidence(
                        investigation_id=investigation_id,
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
        if investigation:
            investigation.status = "FAILED"
            investigation.report = f"Internal error: {e}"
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
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        name=user.name, 
        email=user.email, 
        role=user.role, 
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.get_user_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
    elif inv.status == "ESCALATED":
        risk_score = 0.85
    elif inv.status.startswith("CLOSED_REJECT"):
        risk_score = 0.95
    elif inv.status.startswith("CLOSED_APPROVE") or inv.status == "COMPLETED":
        risk_score = 0.15
    else:
        risk_score = 0.50

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
        created_at=inv.created_at
    )

# --- Protected Investigation Routes ---

@app.post("/api/v1/investigations", response_model=InvestigationResponse, status_code=202)
async def submit_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permissions("investigator"))
):
    """
    FO-1: Accept an investigation request for a transaction or customer identifier.

    This endpoint initiates a financial fraud investigation for the specified transaction.
    The investigation process follows the FFIRE (Financial Fraud Investigation Reasoning Engine)
    workflow which includes:

    1. Planning: Decompose investigation into required evidence-gathering tasks
    2. Evidence Retrieval: Parallel collection of customer, transaction, merchant, device, and location evidence
    3. Rule-based Analysis: Apply deterministic fraud detection rules
    4. Knowledge Lookup: Search historical fraud cases for similar patterns
    5. Risk Reasoning: LLM-powered analysis combining rule results, historical patterns, and evidence
    6. Validation: Check for hallucinations and unsupported claims in the reasoning
    7. Report Generation: Create structured investigation report
    8. Human Review: Escalate to human analyst if confidence is low or validation fails after retries

    The investigation runs asynchronously in the background. Use the returned investigation_id
    to poll for results using the GET /api/v1/investigations/{investigation_id} endpoint.

    Args:
        request: InvestigationRequest containing transaction_id and user_id
        background_tasks: FastAPI background task runner
        db: Database session dependency
        current_user: Authenticated user with investigator role

    Returns:
        InvestigationResponse: Initial investigation status with investigation_id

    Raises:
        HTTPException:
            - 400 if email already registered (during user creation)
            - 401 if authentication fails
            - 403 if user lacks investigator role
            - 404 if transaction not found (though mock data will be created)
            - 500 for internal server errors
    """
    # Verify or mock transaction
    txn = db.query(models.Transaction).filter(models.Transaction.txn_id == request.transaction_id).first()
    if not txn:
        # Create full mock relational data for Phase 2 data integration
        cust = models.Customer(
            name="Alex Johnson (Demo)",
            kyc_status="VERIFIED",
            risk_tier="MEDIUM"
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)

        acct = models.Account(customer_id=cust.customer_id, account_type="CHECKING")
        merch = models.Merchant(
            name="HighRisk Electronics",
            category="Electronics",
            risk_score=0.85
        )
        dev = models.Device(
            customer_id=cust.customer_id,
            fingerprint="hash-999-new",
            os="Unknown"
        )
        db.add_all([acct, merch, dev])
        db.commit()
        db.refresh(acct)
        db.refresh(merch)

        txn = models.Transaction(
            txn_id=request.transaction_id,
            account_id=acct.account_id,
            merchant_id=merch.merchant_id,
            amount=4250.00,
            currency="USD",
            status="PENDING"
        )
        db.add(txn)
        db.commit()

        loc = models.Location(
            txn_id=request.transaction_id,
            geo_coord="55.7558, 37.6173",
            country="RU"
        )
        db.add(loc)
        db.commit()

    inv = models.Investigation(
        txn_id=request.transaction_id,
        status="RUNNING"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    audit_log = models.AuditLog(
        investigation_id=inv.investigation_id,
        action="Investigation Started"
    )
    db.add(audit_log)
    db.commit()

    background_tasks.add_task(run_investigation_task, inv.investigation_id, request.transaction_id)

    return build_investigation_response(inv, db)

@app.get("/api/v1/investigations/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get the status and result of a specific investigation.
    """
    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    return build_investigation_response(inv, db)

@app.post("/api/v1/investigations/{investigation_id}/review")
async def review_investigation(
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

    if inv.status not in ["COMPLETED", "ESCALATED", "FAILED", "RUNNING"]:
        raise HTTPException(status_code=400, detail=f"Cannot review investigation in status {inv.status}")

    action_type = review_action.action.upper()
    if action_type not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    inv.status = f"CLOSED_{action_type}"
    if action_type == "APPROVE":
        inv.risk_score = 0.10
    else:
        inv.risk_score = 0.95

    notes_str = f"Analyst Review ({action_type}) by {current_user.name}: {review_action.notes or 'No additional notes provided'}"
    if inv.report:
        inv.report += f"\n\n### Human Analyst Resolution\n**Verdict**: {action_type}\n**Reviewer**: {current_user.name}\n**Notes**: {review_action.notes or 'None'}"
    else:
        inv.report = f"## Investigation Report\n**Status**: CLOSED_{action_type}\n\n### Human Analyst Resolution\n{notes_str}"

    audit_log = models.AuditLog(
        investigation_id=inv.investigation_id,
        action=f"HUMAN_REVIEW: {action_type}",
        details=notes_str
    )
    db.add(audit_log)
    db.commit()
    db.refresh(inv)

    # Record outcome metrics
    metrics_collector.stop_investigation_timer(investigation_id, status="completed" if action_type == "APPROVE" else "failed")

    return {"status": "success", "new_status": inv.status, "investigation": build_investigation_response(inv, db)}

@app.get("/api/v1/investigations", response_model=InvestigationListResponse)
async def list_investigations(
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

@app.post("/api/v1/investigations/{investigation_id}/export")
async def export_investigation_report(
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
        "export_date": datetime.datetime.utcnow().isoformat(),
        "investigation": response_data.model_dump(),
        "audit_trail": audit_trail
    }

    if format == "json":
        return payload
    elif format == "html":
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>FFRE Investigation Report - {inv.investigation_id}</title><style>body{{font-family:sans-serif;margin:40px;color:#1e293b;}} h1{{color:#0f172a;}} table{{border-collapse:collapse;width:100%;margin-top:20px;}} th,td{{border:1px solid #cbd5e1;padding:8px;text-align:left;}} th{{background-color:#f1f5f9;}} .badge{{padding:4px 8px;border-radius:4px;font-weight:bold;background-color:#e2e8f0;}}</style></head>
<body>
<h1>Financial Fraud Investigation Report</h1>
<p><strong>Investigation ID:</strong> {inv.investigation_id} | <strong>Transaction ID:</strong> {inv.txn_id}</p>
<p><strong>Status:</strong> <span class="badge">{inv.status}</span> | <strong>Risk Score:</strong> {inv.risk_score or 'N/A'} | <strong>Confidence:</strong> {inv.confidence or 'N/A'}</p>
<h2>Executive Summary & Findings</h2>
<pre>{inv.report or 'No detailed report available.'}</pre>
<h2>Audit Trail</h2>
<table><tr><th>Timestamp</th><th>Action</th><th>Details</th></tr>
{''.join([f"<tr><td>{log['timestamp']}</td><td>{log['action']}</td><td>{log['details']}</td></tr>" for log in audit_trail])}
</table>
</body>
</html>"""
        return Response(content=html_content, media_type="text/html")
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

@app.patch("/api/v1/investigations/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permissions("investigator"))
):
    """
    Update an investigation.

    Currently supports updating the status field.
    In a full implementation, this could support updating other fields as well.

    Requires investigator role or higher.
    """
    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    # Update fields if provided
    if status is not None:
        # Validate status transition (optional - could be more comprehensive)
        valid_statuses = ["RUNNING", "COMPLETED", "ESCALATED", "FAILED", "CLOSED_APPROVE", "CLOSED_REJECT"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        inv.status = status

        # Add audit log entry for the status change
        audit_log = models.AuditLog(
            investigation_id=inv.investigation_id,
            action=f"STATUS_UPDATED: {status}",
            details=f"Status updated to {status} by {current_user.name}"
        )
        db.add(audit_log)

    db.commit()
    db.refresh(inv)

    # Return updated investigation
    return build_investigation_response(inv, db)

@app.delete("/api/v1/investigations/{investigation_id}")
async def delete_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_permissions("administrator"))
):
    """
    Delete an investigation.

    This operation is restricted to administrators only.
    When an investigation is deleted, all associated evidence and audit logs are also deleted
    due to CASCADE relationships in the database model.

    Returns a success message upon deletion.
    """
    inv = db.query(models.Investigation).filter(models.Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    # Store info for audit log before deletion
    investigation_id_for_log = inv.investigation_id
    txn_id_for_log = inv.txn_id

    # Delete evidence associated with investigation
    db.query(models.Evidence).filter(models.Evidence.investigation_id == investigation_id).delete()

    # Create immutable tombstone audit log before deleting investigation record
    tombstone_log = models.AuditLog(
        investigation_id=None,
        action=f"INVESTIGATION_DELETED: {investigation_id_for_log}",
        details=f"Investigation for transaction {txn_id_for_log} deleted by administrator {current_user.name}"
    )
    db.add(tombstone_log)

    # Delete investigation record
    db.delete(inv)
    db.commit()

    return {"status": "success", "message": f"Investigation {investigation_id} deleted successfully. Audit trail retained permanently."}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint to verify the API is operational.

    Returns a simple JSON response indicating the service is healthy and operational.
    This endpoint can be used by load balancers, monitoring systems, or orchestration
    platforms to check the availability of the service.

    Returns:
        dict: A dictionary containing status and version information
    """
    return {"status": "healthy", "version": "1.0"}

@app.get("/api/v1/metrics")
async def get_metrics():
    """Endpoint to retrieve performance metrics for monitoring."""
    return {
        "investigation_duration_stats": metrics_collector.get_investigation_duration_stats(),
        "retry_count_stats": metrics_collector.get_retry_count_stats(),
        "confidence_score_stats": metrics_collector.get_confidence_score_stats(),
        "risk_score_stats": metrics_collector.get_risk_score_stats(),
        "investment_outcome_counts": metrics_collector.get_investment_outcome_counts()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
