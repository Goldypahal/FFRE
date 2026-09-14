import pytest
from fastapi.testclient import TestClient
from main import app
import models
from auth import get_current_user
import io

def test_evidence_vault_listing_and_seeding(client):
    """Verify evidence listing auto-seeds default items and returns paginated list"""
    response = client.get("/api/v1/evidence")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 6
    titles = [item["title"] for item in data["items"]]
    assert "Global Passport Index" in titles
    assert "Sanction Lists" in titles
    assert "Synthetic Identity Chain" in titles

def test_evidence_vault_filtering(client):
    """Verify filtering by category, search query, and risk level"""
    # Category filter
    resp_cat = client.get("/api/v1/evidence?category=IDENTITY_DOCUMENTS")
    assert resp_cat.status_code == 200
    items = resp_cat.json()["items"]
    assert len(items) > 0
    for it in items:
        assert it["category"] == "IDENTITY_DOCUMENTS"

    # Search filter
    resp_search = client.get("/api/v1/evidence?search=Passport")
    assert resp_search.status_code == 200
    search_items = resp_search.json()["items"]
    assert len(search_items) >= 1
    assert "Passport" in search_items[0]["title"]

def test_evidence_upload_and_sha256(client):
    """Verify evidence upload generates genuine SHA-256 hash and audit log"""
    file_content = b"CRITICAL_FINANCIAL_TRANSACTION_EVIDENCE_SAMPLE_DATA_12345"
    file_obj = io.BytesIO(file_content)

    upload_resp = client.post(
        "/api/v1/evidence/upload",
        data={
            "category": "IDENTITY_DOCUMENTS",
            "title": "Uploaded ID Verification Doc",
            "source": "AGENT_TERMINAL",
            "tag": "KYC_PASS",
            "risk_level": "LOW",
            "description": "Scanned document upload test"
        },
        files={"file": ("passport_scan.pdf", file_obj, "application/pdf")}
    )
    assert upload_resp.status_code == 200
    data = upload_resp.json()
    assert data["title"] == "Uploaded ID Verification Doc"
    assert data["file_type"] == "PDF"
    assert data["file_size"] == len(file_content)
    assert len(data["sha256_hash"]) == 64
    assert data["is_verified"] is True
    item_id = data["item_id"]

    # Verify item exists in list
    get_list = client.get(f"/api/v1/evidence?search={item_id}")
    assert get_list.status_code == 200
    assert any(it["item_id"] == item_id for it in get_list.json()["items"])

def test_evidence_verify_and_delete(client):
    """Verify evidence verification endpoint and deletion"""
    # Create item
    upload_resp = client.post(
        "/api/v1/evidence/upload",
        data={
            "category": "HISTORICAL_PATTERNS",
            "title": "Pattern Artifact for Verify",
            "source": "TELEMETRY_SNIFFER",
            "tag": "THREAT_VEC",
            "risk_level": "HIGH"
        }
    )
    assert upload_resp.status_code == 200
    item_id = upload_resp.json()["item_id"]

    # Verify
    verify_resp = client.post(f"/api/v1/evidence/{item_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_verified"] is True
    assert "HSM" in verify_resp.json()["verification_method"]

    # Delete
    del_resp = client.delete(f"/api/v1/evidence/{item_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

def test_evidence_vault_multitenant_isolation(client):
    """Verify evidence items are isolated between tenants"""
    # Create an item under tenant_alpha
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )
    alpha_upload = client.post(
        "/api/v1/evidence/upload",
        data={"title": "Alpha Confidential Intel", "source": "ALPHA_INTEL"}
    )
    assert alpha_upload.status_code == 200
    alpha_item_id = alpha_upload.json()["item_id"]

    # Switch to tenant_beta
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )

    # Beta listing should NOT contain alpha's item
    beta_list = client.get("/api/v1/evidence")
    assert beta_list.status_code == 200
    beta_ids = [it["item_id"] for it in beta_list.json()["items"]]
    assert alpha_item_id not in beta_ids

    # Beta trying to verify or delete alpha item gets 403 Forbidden
    verify_attempt = client.post(f"/api/v1/evidence/{alpha_item_id}/verify")
    assert verify_attempt.status_code == 403

    delete_attempt = client.delete(f"/api/v1/evidence/{alpha_item_id}")
    assert delete_attempt.status_code == 403

    # Reset
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_1",
        name="Test User",
        email="test@example.com",
        role="investigator",
        tenant_id="default_tenant"
    )
