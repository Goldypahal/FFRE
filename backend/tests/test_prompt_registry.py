import pytest
from fastapi.testclient import TestClient
import models
import prompt_registry
from auth import get_current_user
from main import app
from graph import get_planner_prompt, get_reasoner_prompt

def override_admin_user():
    return models.User(
        user_id="admin_1",
        name="Admin User",
        email="admin@example.com",
        role="admin",
        tenant_id="default_tenant"
    )

@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_user] = override_admin_user
    with TestClient(app) as c:
        yield c
    # Restored in clean_db

def test_list_prompts_seeds_defaults(client, db_session):
    """Verify listing prompts auto-seeds standard enterprise prompts if empty."""
    prompt_registry.invalidate_prompt_cache()
    res = client.get("/api/v1/prompts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5

    names = {p["name"] for p in data}
    assert {"planner", "reasoner", "critic", "validator", "reporter"}.issubset(names)

    # Check structure
    planner = next(p for p in data if p["name"] == "planner")
    assert planner["version"] == "v1.0"
    assert planner["is_active"] is True
    assert "transaction_summary" in planner["variables"]

def test_get_prompt_by_name(client, db_session):
    """Verify retrieval of specific prompt and its versions."""
    res = client.get("/api/v1/prompts/reasoner")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "reasoner"
    assert data["active_version"] == "v1.0"
    assert "fraud investigation reasoning engine" in data["active_template"]
    assert len(data["versions"]) >= 1

def test_create_and_activate_new_version(admin_client, db_session):
    """Verify creating a new version of a prompt and activating it."""
    prompt_registry.invalidate_prompt_cache()
    # Seed defaults first
    admin_client.get("/api/v1/prompts")

    # Create v2.0 for planner
    payload = {
        "name": "planner",
        "version": "v2.0",
        "template_text": "Custom V2 Planner: Investigate {transaction_summary} strictly with deep forensics.",
        "description": "V2 high-security enterprise planning prompt.",
        "variables": "transaction_summary,forensic_mode",
        "is_active": True
    }
    res = admin_client.post("/api/v1/prompts", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["version"] == "v2.0"
    assert res_data["is_active"] is True

    # Check graph dynamic resolution
    loaded_template = get_planner_prompt(tenant_id="default_tenant")
    assert "Custom V2 Planner" in loaded_template

    # Check previous v1.0 is now deactivated
    get_res = admin_client.get("/api/v1/prompts/planner")
    p_data = get_res.json()
    assert p_data["active_version"] == "v2.0"
    v1_rec = next(v for v in p_data["versions"] if v["version"] == "v1.0")
    assert v1_rec["is_active"] is False

    # Reactivate v1.0
    v1_id = v1_rec["prompt_id"]
    act_res = admin_client.post(f"/api/v1/prompts/{v1_id}/activate")
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "success"

    # Verify graph resolution switched back
    restored_template = get_planner_prompt(tenant_id="default_tenant")
    assert "You are a financial fraud investigation planner" in restored_template

def test_update_prompt_version(admin_client, db_session):
    """Verify updating template text and variables of a prompt record."""
    # Fetch existing planner
    res = admin_client.get("/api/v1/prompts/planner")
    p_id = res.json()["versions"][0]["prompt_id"]

    update_payload = {
        "description": "Updated prompt description for testing."
    }
    up_res = admin_client.put(f"/api/v1/prompts/{p_id}", json=update_payload)
    assert up_res.status_code == 200
    assert up_res.json()["status"] == "success"

def test_prompt_multitenant_isolation(client, db_session):
    """Verify tenant A cannot overwrite or view tenant B's customized prompt templates."""
    prompt_registry.invalidate_prompt_cache()
    # Seed prompt for tenant_b
    prompt_b = models.PromptRecord(
        tenant_id="tenant_b",
        name="planner",
        version="v_custom_b",
        template_text="Tenant B Custom Planner: {transaction_summary}",
        description="Tenant B custom prompt",
        variables="transaction_summary",
        is_active=True,
        created_by="Admin B"
    )
    db_session.add(prompt_b)
    db_session.commit()

    # User in default_tenant calls GET /api/v1/prompts
    res = client.get("/api/v1/prompts/planner")
    assert res.status_code == 200
    data = res.json()
    # Should only see default_tenant versions, NOT v_custom_b
    versions = [v["version"] for v in data["versions"]]
    assert "v_custom_b" not in versions

    # Verify dynamic loader respects tenant_id
    prompt_b_text = get_planner_prompt(tenant_id="tenant_b")
    assert "Tenant B Custom Planner" in prompt_b_text
    prompt_default_text = get_planner_prompt(tenant_id="default_tenant")
    assert "Tenant B Custom Planner" not in prompt_default_text

def test_reset_prompts_to_default(admin_client, db_session):
    """Verify admin can reset all prompts to factory default templates."""
    reset_res = admin_client.post("/api/v1/prompts/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"

    # Verify defaults are present
    list_res = admin_client.get("/api/v1/prompts")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 5
