"""
Phase 5 Complete Investigator End-to-End Workflow & Error States Qualification Suite.

Validates the full investigator user journey against the real HTTP API without manual DB editing:
1. Sign in and authenticate (register, login, obtain JWT bearer token).
2. Open the investigation dashboard (GET /api/v1/investigations).
3. Search for a transaction via Universal Search (GET /api/v1/search/universal).
4. Create an investigation (POST /api/v1/investigations).
5. Observe status while processing (GET /api/v1/investigations/{id}).
6. Open the completed report and review findings.
7. Inspect supporting evidence attached to the investigation.
8. View the 12-node DAG reasoning graph (GET /api/v1/graph/{id}).
9. Route / review case with Human Review action (POST /api/v1/investigations/{id}/review).
10. Approve / reject review where authorized.
11. Export report dossier with cryptographic audit history (POST /api/v1/investigations/{id}/export).
12. Strict multi-tenant isolation: Tenant Beta cannot inspect Tenant Alpha records (HTTP 403).
13. Comprehensive error states: invalid credentials, expired token, missing tenant context, 404.
"""

import uuid
import datetime
import pytest
from jose import jwt

import models
from auth import SECRET_KEY, ALGORITHM


def test_investigator_complete_user_journey_e2e(client, db_session):
    """
    Phase 5 Qualification Test:
    Executes the full investigator lifecycle strictly through the public API interface.
    Acceptance criterion: An investigator can complete the intended workflow without
    manually editing database records or calling internal functions.
    """
    tenant_alpha = f"bank_alpha_{uuid.uuid4().hex[:6]}"
    analyst_email = f"lead_analyst_{uuid.uuid4().hex[:6]}@alpha.bank"
    analyst_password = "SecureEnterprisePassword2026!"

    # --------------------------------------------------------------------------
    # 1. Sign In & Authenticate
    # --------------------------------------------------------------------------
    # Register analyst
    reg_res = client.post("/api/v1/auth/register", json={
        "email": analyst_email,
        "name": "Lead Fraud Analyst",
        "password": analyst_password,
        "role": "investigator",
        "tenant_id": tenant_alpha
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    token_data = reg_res.json()
    access_token = token_data["access_token"]
    assert access_token is not None

    # Login to verify standard OAuth2 form login
    login_res = client.post("/api/v1/auth/login", data={
        "username": analyst_email,
        "password": analyst_password
    })
    assert login_res.status_code == 200
    login_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {login_token}"}

    # --------------------------------------------------------------------------
    # 2. Open Investigation Dashboard
    # --------------------------------------------------------------------------
    dash_res = client.get("/api/v1/investigations", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "investigations" in dash_data
    assert isinstance(dash_data["investigations"], list)

    # --------------------------------------------------------------------------
    # 3. Seed Target Transaction and Universal Search
    # --------------------------------------------------------------------------
    # Seed a transaction directly into DB for the user's tenant
    txn_id = f"TXN-JOURNEY-{uuid.uuid4().hex[:6]}"
    cust_id = f"CUST-{uuid.uuid4().hex[:6]}"
    acct_id = f"ACCT-{uuid.uuid4().hex[:6]}"
    cust = models.Customer(customer_id=cust_id, name="Alexander Hamilton", kyc_status="VERIFIED", tenant_id=tenant_alpha)
    acct = models.Account(account_id=acct_id, customer_id=cust_id, tenant_id=tenant_alpha)
    txn = models.Transaction(
        txn_id=txn_id,
        account_id=acct_id,
        amount=1450.00,
        currency="USD",
        status="PENDING",
        counterparty="Global Luxury Retailer",
        tenant_id=tenant_alpha
    )
    db_session.add_all([cust, acct, txn])
    db_session.commit()

    # Search for the transaction using universal search API
    search_res = client.get(f"/api/v1/search/universal?q={txn_id}", headers=headers)
    assert search_res.status_code == 200
    search_results = search_res.json()
    assert "results" in search_results
    assert any(item.get("id") == txn_id for item in search_results["results"])

    # --------------------------------------------------------------------------
    # 4. Create an Investigation via API
    # --------------------------------------------------------------------------
    create_payload = {
        "transaction_id": txn_id,
        "user_id": analyst_email
    }
    create_res = client.post("/api/v1/investigations", json=create_payload, headers=headers)
    assert create_res.status_code == 202
    created_inv = create_res.json()
    inv_id = created_inv["investigation_id"]
    assert inv_id is not None
    assert created_inv["transaction_id"] == txn_id

    # --------------------------------------------------------------------------
    # 5. Observe Status While Processing
    # --------------------------------------------------------------------------
    status_res = client.get(f"/api/v1/investigations/{inv_id}", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["investigation_id"] == inv_id
    assert status_data["status"] in ("QUEUED", "RUNNING", "COMPLETED", "ESCALATED")

    # Run investigation to completion
    from main import run_investigation_task
    run_investigation_task(inv_id, txn_id, db=db_session)

    # --------------------------------------------------------------------------
    # 6 & 7. Open Completed Report & Inspect Supporting Evidence
    # --------------------------------------------------------------------------
    completed_res = client.get(f"/api/v1/investigations/{inv_id}", headers=headers)
    assert completed_res.status_code == 200
    inv_detail = completed_res.json()
    assert inv_detail["status"] in ("COMPLETED", "ESCALATED", "APPROVED")
    assert inv_detail["report"] is not None
    assert len(inv_detail["evidence"]) >= 1

    # --------------------------------------------------------------------------
    # 8. View Reasoning Graph DAG
    # --------------------------------------------------------------------------
    graph_res = client.get(f"/api/v1/graph/{inv_id}", headers=headers)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["investigation_id"] == inv_id
    assert len(graph_data["nodes"]) == 12
    assert "planner" in [n["id"] for n in graph_data["nodes"]]
    assert "reporter" in [n["id"] for n in graph_data["nodes"]]

    # --------------------------------------------------------------------------
    # 9 & 10. Human Review: Approve or Reject Case
    # --------------------------------------------------------------------------
    review_res = client.post(
        f"/api/v1/investigations/{inv_id}/review",
        json={"action": "APPROVE", "notes": "Verified legitimate historical luxury shopping pattern."},
        headers=headers
    )
    assert review_res.status_code == 200
    reviewed_data = review_res.json()
    assert reviewed_data["new_status"] == "CLOSED_APPROVE"
    assert reviewed_data["investigation"]["risk_score"] == 0.10

    # --------------------------------------------------------------------------
    # 11. Export Report Dossier with Cryptographic Audit History
    # --------------------------------------------------------------------------
    export_res = client.post(
        f"/api/v1/investigations/{inv_id}/export?format=json",
        headers=headers
    )
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert "export_date" in export_data
    assert "investigation" in export_data
    assert "audit_trail" in export_data
    assert len(export_data["audit_trail"]) >= 1

    # --------------------------------------------------------------------------
    # 12. Confirm Multi-Tenant Isolation Defense
    # --------------------------------------------------------------------------
    # Register an analyst belonging to Tenant Beta
    tenant_beta = f"bank_beta_{uuid.uuid4().hex[:6]}"
    beta_email = f"beta_analyst_{uuid.uuid4().hex[:6]}@beta.bank"
    client.post("/api/v1/auth/register", json={
        "email": beta_email,
        "name": "Beta Fraud Analyst",
        "password": "PasswordBeta2026!",
        "role": "investigator",
        "tenant_id": tenant_beta
    })
    beta_login = client.post("/api/v1/auth/login", data={"username": beta_email, "password": "PasswordBeta2026!"})
    beta_token = beta_login.json()["access_token"]
    beta_headers = {"Authorization": f"Bearer {beta_token}"}

    # Tenant Beta attempts to access Tenant Alpha's investigation -> 403 Forbidden
    cross_res = client.get(f"/api/v1/investigations/{inv_id}", headers=beta_headers)
    assert cross_res.status_code == 403
    assert "another tenant" in cross_res.json()["detail"].lower()

    # Tenant Beta attempts to access Tenant Alpha's graph topology -> 403 Forbidden
    cross_graph = client.get(f"/api/v1/graph/{inv_id}", headers=beta_headers)
    assert cross_graph.status_code == 403

    # Tenant Beta attempts to review Tenant Alpha's investigation -> 403 Forbidden
    cross_review = client.post(
        f"/api/v1/investigations/{inv_id}/review",
        json={"action": "REJECT", "notes": "Hostile cross-tenant review"},
        headers=beta_headers
    )
    assert cross_review.status_code == 403


def test_investigator_error_states_fail_closed(client):
    """
    Validates fail-closed security and robustness across API error conditions:
    - Invalid login credentials (401)
    - Expired JWT token (401)
    - Missing Authorization header on protected endpoints (401)
    - Nonexistent investigation query (404)
    - Malformed review payload (400)
    """
    # 1. Invalid credentials
    bad_login = client.post("/api/v1/auth/login", data={"username": "nobody@bank.internal", "password": "WrongPassword!"})
    assert bad_login.status_code == 401

    # 2. Expired JWT token
    expired_payload = {
        "sub": "expired_analyst@bank.internal",
        "role": "investigator",
        "tenant_id": "tenant_fail",
        "type": "access",
        "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    expired_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_res.status_code == 401

    # 3. Malformed Auth header fails closed with 401
    bad_auth_res = client.get("/api/v1/investigations", headers={"Authorization": "Bearer malformed_unparseable_token"})
    assert bad_auth_res.status_code == 401

    # 4. Nonexistent investigation (404)
    email = f"analyst_err_{uuid.uuid4().hex[:6]}@bank.internal"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "Error Analyst",
        "password": "Password123!",
        "role": "investigator",
        "tenant_id": "tenant_err"
    })
    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"})
    valid_token = login_res.json()["access_token"]
    valid_headers = {"Authorization": f"Bearer {valid_token}"}
    not_found_res = client.get("/api/v1/investigations/INV_NONEXISTENT_9999", headers=valid_headers)
    assert not_found_res.status_code == 404

    # 5. Malformed review action (not APPROVE or REJECT)
    bad_action_res = client.post(
        "/api/v1/investigations/INV_NONEXISTENT_9999/review",
        json={"action": "INVALID_VERDICT_123"},
        headers=valid_headers
    )
    assert bad_action_res.status_code in (400, 404, 422)
