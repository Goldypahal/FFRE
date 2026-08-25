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