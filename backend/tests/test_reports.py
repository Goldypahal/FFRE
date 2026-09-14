import pytest
from fastapi.testclient import TestClient
from main import app
import models
from auth import get_current_user

def test_reports_listing_and_seeding(client):
    """Verify reports listing auto-seeds default items and returns paginated list"""
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert data["total"] >= 5
    titles = [r["title"] for r in data["reports"]]
    assert "Suspicious Activity Report - FinCEN SAR Filing" in titles
    assert "Daily Fraud & Risk Intelligence Summary" in titles
    assert "Chargeback Analysis Report Q1" in titles

def test_reports_filtering(client):
    """Verify filtering by status, report_type, and search term"""
    # Filter by report_type
    resp_type = client.get("/api/v1/reports?report_type=SAR Regulatory Filing")
    assert resp_type.status_code == 200
    reports = resp_type.json()["reports"]
    assert len(reports) >= 1
    assert reports[0]["report_type"] == "SAR Regulatory Filing"

    # Filter by status
    resp_status = client.get("/api/v1/reports?status=Failed")
    assert resp_status.status_code == 200
    failed_reports = resp_status.json()["reports"]
    assert len(failed_reports) >= 1
    assert failed_reports[0]["status"] == "Failed"

    # Search filter
    resp_search = client.get("/api/v1/reports?search=FinCEN")
    assert resp_search.status_code == 200
    search_reports = resp_search.json()["reports"]
    assert len(search_reports) >= 1
    assert "FinCEN" in search_reports[0]["title"]

def test_report_generation(client):
    """Verify generating a formal investigation report and SAR filing"""
    gen_resp = client.post(
        "/api/v1/reports/generate",
        json={
            "title": "Automated SAR Filing - High Risk Case",
            "report_type": "SAR Regulatory Filing",
            "description": "Cross-border rapid transfer smurfing detected",
            "file_format": "pdf"
        }
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert data["title"] == "Automated SAR Filing - High Risk Case"
    assert data["status"] == "Completed"
    assert data["file_format"] == "pdf"
    assert data["file_size"] > 0
    report_id = data["report_id"]

    # Verify download in PDF format
    download_pdf = client.get(f"/api/v1/reports/{report_id}/download?format=pdf")
    assert download_pdf.status_code == 200
    assert download_pdf.headers["content-type"] == "application/pdf"
    assert download_pdf.content.startswith(b"%PDF")

    # Verify download in JSON format
    download_json = client.get(f"/api/v1/reports/{report_id}/download?format=json")
    assert download_json.status_code == 200
    json_data = download_json.json()
    assert json_data["report_id"] == report_id
    assert "Automated SAR Filing" in json_data["title"]

def test_reports_multitenant_isolation(client):
    """Verify reports are strictly isolated per tenant"""
    # Generate report under tenant_alpha
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )
    alpha_gen = client.post(
        "/api/v1/reports/generate",
        json={"title": "Alpha Confidential SAR", "report_type": "SAR Regulatory Filing"}
    )
    assert alpha_gen.status_code == 200
    alpha_report_id = alpha_gen.json()["report_id"]

    # Switch to tenant_beta
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )

    # Beta listing should NOT include Alpha's report
    beta_list = client.get("/api/v1/reports")
    assert beta_list.status_code == 200
    beta_ids = [r["report_id"] for r in beta_list.json()["reports"]]
    assert alpha_report_id not in beta_ids

    # Beta trying to download or delete Alpha report gets 403 Forbidden
    download_attempt = client.get(f"/api/v1/reports/{alpha_report_id}/download")
    assert download_attempt.status_code == 403

    delete_attempt = client.delete(f"/api/v1/reports/{alpha_report_id}")
    assert delete_attempt.status_code == 403

    # Reset
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_1",
        name="Test User",
        email="test@example.com",
        role="investigator",
        tenant_id="default_tenant"
    )
