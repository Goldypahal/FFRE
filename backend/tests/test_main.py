from fastapi.testclient import TestClient
from main import app
import json

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0"}

def test_create_investigation(client):
    """Test creating a new investigation"""
    response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "T-12345",
            "user_id": "user_1"
        }
    )
    assert response.status_code == 202
    data = response.json()
    assert "investigation_id" in data
    assert data["transaction_id"] == "T-12345"
    assert data["status"] in ["QUEUED", "RUNNING"]

def test_get_investigation_not_found(client):
    """Test getting a non-existent investigation"""
    response = client.get("/api/v1/investigations/non-existent-id")
    assert response.status_code == 404

def test_get_investigation_after_creation(client):
    """Test getting an investigation after creation"""
    # Create an investigation
    create_response = client.post(
        "/api/v1/investigations",
        json={
            "transaction_id": "T-67890",
            "user_id": "user_2"
        }
    )
    assert create_response.status_code == 202
    investigation_id = create_response.json()["investigation_id"]

    # Get the investigation
    get_response = client.get(f"/api/v1/investigations/{investigation_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["investigation_id"] == investigation_id
    assert data["transaction_id"] == "T-67890"
    # Status might be QUEUED, RUNNING, or COMPLETED depending on async processing
    assert data["status"] in ["QUEUED", "RUNNING", "COMPLETED", "WAITING_HUMAN", "ESCALATED"]

def test_export_investigation_pdf_format(client):
    """Test exporting investigation report in genuine binary PDF format"""
    create_response = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "T-PDF-TEST", "user_id": "user_pdf"}
    )
    assert create_response.status_code == 202
    inv_id = create_response.json()["investigation_id"]

    export_response = client.post(f"/api/v1/investigations/{inv_id}/export?format=pdf")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/pdf"
    assert export_response.content.startswith(b"%PDF")

def test_multitenancy_isolation(client):
    """Test that users from different tenants cannot access or manipulate each other's investigations"""
    import models
    from auth import get_current_user

    # Create investigation as tenant_alpha
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    create_resp = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "T-ALPHA-01", "user_id": "user_alpha"}
    )
    assert create_resp.status_code == 202
    inv_id = create_resp.json()["investigation_id"]

    # Verify tenant_alpha can get the investigation
    get_alpha_resp = client.get(f"/api/v1/investigations/{inv_id}")
    assert get_alpha_resp.status_code == 200
    assert get_alpha_resp.json()["tenant_id"] == "tenant_alpha"

    # Switch user to tenant_beta
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )

    # Attempt cross-tenant GET: should fail with 403 Forbidden
    get_beta_resp = client.get(f"/api/v1/investigations/{inv_id}")
    assert get_beta_resp.status_code == 403
    assert "Access denied" in get_beta_resp.json()["detail"]

    # Attempt cross-tenant EXPORT: should fail with 403 Forbidden
    export_beta_resp = client.post(f"/api/v1/investigations/{inv_id}/export?format=json")
    assert export_beta_resp.status_code == 403

    # Attempt cross-tenant CANCEL: should fail with 403 Forbidden
    cancel_beta_resp = client.post(f"/api/v1/investigations/{inv_id}/cancel")
    assert cancel_beta_resp.status_code == 403

    # Attempt cross-tenant REVIEW: should fail with 403 Forbidden
    review_beta_resp = client.post(
        f"/api/v1/investigations/{inv_id}/review",
        json={"action": "APPROVE", "notes": "Cross tenant breach attempt"}
    )
    assert review_beta_resp.status_code == 403

    # Switch to admin user: can access cross-tenant
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_admin",
        name="Admin User",
        email="admin@example.com",
        role="admin",
        tenant_id="admin_tenant"
    )
    admin_get_resp = client.get(f"/api/v1/investigations/{inv_id}")
    assert admin_get_resp.status_code == 200

    # Reset dependency override to default
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_1",
        name="Test User",
        email="test@example.com",
        role="investigator",
        tenant_id="default_tenant"
    )