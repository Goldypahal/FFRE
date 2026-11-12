import pytest
from fastapi.testclient import TestClient
from main import app
import models
from auth import get_current_user


def _as(role, user_id="user_admin_1"):
    return lambda: models.User(
        user_id=user_id, name="Test Admin", email="admin@example.com", role=role, tenant_id="default_tenant"
    )


@pytest.fixture
def admin_client(client):
    """The shared client, signed in as a tenant administrator for the duration of one test."""
    app.dependency_overrides[get_current_user] = _as("admin")
    try:
        yield client
    finally:
        app.dependency_overrides[get_current_user] = lambda: models.User(
            user_id="user_1", name="Test User", email="test@example.com", role="investigator", tenant_id="default_tenant"
        )


ADMIN_ROUTES = [
    ("get", "/api/v1/admin/users", None),
    ("post", "/api/v1/admin/users", {"name": "X", "email": "x@example.com", "role": "admin", "status": "active", "password": "Password123!"}),
    ("patch", "/api/v1/admin/users/any-id", {"role": "admin"}),
    ("delete", "/api/v1/admin/users/any-id", None),
    ("get", "/api/v1/admin/settings", None),
    ("post", "/api/v1/admin/settings", {"category": "c", "key": "k", "value": "v"}),
    ("get", "/api/v1/admin/integrations", None),
    ("get", "/api/v1/admin/audit-logs", None),
    ("get", "/api/v1/admin/health-metrics", None),
]


@pytest.mark.parametrize("role", ["viewer", "investigator", "analyst", "compliance_officer"])
def test_admin_routes_reject_non_admins(client, role):
    """Being signed in is not enough: every administration route needs an administrator."""
    app.dependency_overrides[get_current_user] = _as(role, user_id="user_plain")
    try:
        for method, path, body in ADMIN_ROUTES:
            res = getattr(client, method)(path, **({"json": body} if body is not None else {}))
            assert res.status_code == 403, f"{role} reached {method.upper()} {path}: {res.status_code}"
    finally:
        app.dependency_overrides[get_current_user] = lambda: models.User(
            user_id="user_1", name="Test User", email="test@example.com", role="investigator", tenant_id="default_tenant"
        )


def test_admin_cannot_change_own_role_or_use_default_password(admin_client, db_session):
    me = models.User(user_id="user_admin_1", role="admin", tenant_id="default_tenant", hashed_password="x")
    me.name = "Test Admin"
    me.email = "self.admin@example.com"
    db_session.add(me)
    db_session.commit()
    assert admin_client.patch("/api/v1/admin/users/user_admin_1", json={"role": "viewer"}).status_code == 400
    assert admin_client.delete("/api/v1/admin/users/user_admin_1").status_code == 400
    # No password supplied: the account must not be created with a built-in one.
    res = admin_client.post("/api/v1/admin/users", json={"name": "No Pw", "email": "nopw@example.com", "role": "viewer", "status": "active"})
    assert res.status_code == 400
    # Roles outside the known set, including the platform role, cannot be granted here.
    for bad in ("platform_admin", "Superuser"):
        res = admin_client.post("/api/v1/admin/users", json={"name": "Bad", "email": "bad@example.com", "role": bad, "status": "active", "password": "Password123!"})
        assert res.status_code == 400


def test_admin_users_crud(admin_client, monkeypatch):
    """Verify admin users listing, creation, role update, and deletion."""
    client = admin_client
    # 1. Listing. Sample accounts appear only in demo mode.
    res_list = client.get("/api/v1/admin/users")
    assert res_list.status_code == 200
    assert "admin@company.com" not in [u["email"] for u in res_list.json()]

    # 2. Creation
    res_create = client.post(
        "/api/v1/admin/users",
        json={
            "name": "Sarah Connor",
            "email": "sarah.connor@cyberdyne.com",
            "role": "Senior Investigator",
            "status": "active",
            "password": "Password123!"
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
            "role": "Compliance Officer",
            "status": "inactive"
        }
    )
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["role"] == "compliance_officer"
    assert updated["status"] == "inactive"

    # 4. Deletion
    res_del = client.delete(f"/api/v1/admin/users/{user_id}")
    assert res_del.status_code == 200

def test_admin_settings_crud(admin_client):
    """Verify system settings retrieval, creation, and updating."""
    client = admin_client
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

def test_admin_integrations_and_sync(admin_client, monkeypatch):
    """Verify integration listing, manual sync trigger, and status toggling."""
    client = admin_client
    # 1. Listing. Nothing is connected until it is configured.
    res_list = client.get("/api/v1/admin/integrations")
    assert res_list.status_code == 200
    integrations = res_list.json()
    assert len(integrations) >= 4
    assert all(i["status"] == "not_configured" and i["lastSync"] is None for i in integrations)
    first_int = integrations[0]
    int_id = first_int["id"]

    # 2. Sync. With no connector installed, the API says so instead of reporting a success.
    res_sync = client.post(f"/api/v1/admin/integrations/{int_id}/sync")
    assert res_sync.status_code == 501

    # In demo mode the sync is simulated.
    monkeypatch.setenv("FFRE_DEMO_SEED", "true")
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

def test_admin_audit_logs_and_health(admin_client, db_session):
    """Verify audit log retrieval and health telemetry."""
    client = admin_client
    db_session.add(models.AuditLog(tenant_id="default_tenant", action="settings.updated", details="Changed session timeout"))
    db_session.commit()
    # Audit logs: real entries only, and no invented user or address.
    res_logs = client.get("/api/v1/admin/audit-logs")
    assert res_logs.status_code == 200
    logs = res_logs.json()
    assert len(logs) >= 1
    assert "action" in logs[0]
    assert "timestamp" in logs[0]
    assert all(l["action"] != "integration.sync.completed" for l in logs)
    assert all(l["ipAddress"] is None for l in logs)

    # Health telemetry
    res_health = client.get("/api/v1/admin/health-metrics")
    assert res_health.status_code == 200
    health = res_health.json()
    assert health["status"] in ("healthy", "degraded")
    assert "database" in health
    assert health["database"]["status"] == "connected"
