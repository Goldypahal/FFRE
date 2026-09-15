import pytest
from fastapi.testclient import TestClient
from main import app
import models
from auth import get_current_user

def test_admin_users_crud(client):
    """Verify admin users listing, creation, role update, and deletion."""
    # 1. Listing / Seeding
    res_list = client.get("/api/v1/admin/users")
    assert res_list.status_code == 200
    users = res_list.json()
    assert len(users) >= 4
    emails = [u["email"] for u in users]
    assert "admin@company.com" in emails
    assert "alex.johnson@company.com" in emails

    # 2. Creation
    res_create = client.post(
        "/api/v1/admin/users",
        json={
            "name": "Sarah Connor",
            "email": "sarah.connor@cyberdyne.com",
            "role": "Fraud Investigator",
            "status": "active"
        }
    )
    assert res_create.status_code == 200
    new_user = res_create.json()
    assert new_user["name"] == "Sarah Connor"
    assert new_user["email"] == "sarah.connor@cyberdyne.com"
    user_id = new_user["id"]

    # 3. Update
    res_update = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={
            "role": "Senior Fraud Specialist",
            "status": "inactive"
        }
    )
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["role"] == "Senior Fraud Specialist"
    assert updated["status"] == "inactive"

    # 4. Deletion
    res_del = client.delete(f"/api/v1/admin/users/{user_id}")
    assert res_del.status_code == 200

def test_admin_settings_crud(client):
    """Verify system settings retrieval, creation, and updating."""
    # 1. Listing / Seeding
    res_list = client.get("/api/v1/admin/settings")
    assert res_list.status_code == 200
    settings = res_list.json()
    assert len(settings) >= 5
    keys = [s["key"] for s in settings]
    assert "company_name" in keys
    assert "session_timeout" in keys

    # 2. Create custom setting
    res_create = client.post(
        "/api/v1/admin/settings",
        json={
            "category": "ai_reasoning",
            "key": "critic_max_loops",
            "value": "3",
            "description": "Maximum self-reflection critique iterations",
            "is_sensitive": False
        }
    )
    assert res_create.status_code == 200
    setting_data = res_create.json()
    setting_id = setting_data["id"]
    assert setting_data["key"] == "critic_max_loops"
    assert setting_data["value"] == 3

    # 3. Update setting value
    res_put = client.put(
        f"/api/v1/admin/settings/{setting_id}",
        json={
            "value": "5",
            "description": "Expanded critique iterations for high risk txns"
        }
    )
    assert res_put.status_code == 200
    assert res_put.json()["value"] == 5

def test_admin_integrations_and_sync(client):
    """Verify integration listing, manual sync trigger, and status toggling."""
    # 1. Listing
    res_list = client.get("/api/v1/admin/integrations")
    assert res_list.status_code == 200
    integrations = res_list.json()
    assert len(integrations) >= 4
    first_int = integrations[0]
    int_id = first_int["id"]

    # 2. Sync
    res_sync = client.post(f"/api/v1/admin/integrations/{int_id}/sync")
    assert res_sync.status_code == 200
    assert res_sync.json()["status"] == "connected"
    assert res_sync.json()["lastSync"] is not None

    # 3. Toggle Status
    res_toggle = client.patch(
        f"/api/v1/admin/integrations/{int_id}",
        json={"status": "disconnected"}
    )
    assert res_toggle.status_code == 200
    assert res_toggle.json()["status"] == "disconnected"

def test_admin_audit_logs_and_health(client):
    """Verify audit log retrieval and health telemetry."""
    # Audit logs
    res_logs = client.get("/api/v1/admin/audit-logs")
    assert res_logs.status_code == 200
    logs = res_logs.json()
    assert len(logs) >= 1
    assert "action" in logs[0]
    assert "timestamp" in logs[0]

    # Health telemetry
    res_health = client.get("/api/v1/admin/health-metrics")
    assert res_health.status_code == 200
    health = res_health.json()
    assert health["status"] == "healthy"
    assert "database" in health
    assert health["database"]["status"] == "connected"
