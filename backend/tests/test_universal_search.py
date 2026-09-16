import pytest
import datetime
from fastapi.testclient import TestClient
import models
from auth import get_current_user
from main import app

def test_universal_search_basic(client, db_session):
    """Verify universal search finds investigations, evidence, and reports by query."""
    # Seed investigation
    inv = models.Investigation(
        investigation_id="INV-SEARCH-101",
        txn_id="TXN-QUERY-999",
        status="COMPLETED",
        risk_score=0.82,
        report="Critical suspicious transaction detected for shell company.",
        tenant_id="default_tenant"
    )
    # Seed evidence vault item
    ev = models.EvidenceVaultItem(
        item_id="ev-search-1",
        title="Passport Scan Alpha",
        category="IDENTITY_DOCUMENTS",
        source="KYC_PORTAL",
        tag="PASSPORT_VALIDATED",
        risk_level="LOW",
        file_type="PDF",
        file_size=2048,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_verified=True,
        tenant_id="default_tenant"
    )
    # Seed report
    rep = models.ReportRecord(
        report_id="rep-search-1",
        title="Quarterly AML Risk Dossier",
        report_type="FINCEN_SAR",
        status="FINALIZED",
        generated_by="Automated Engine",
        file_format="pdf",
        description="Comprehensive quarterly risk filing report.",
        tenant_id="default_tenant"
    )
    db_session.add_all([inv, ev, rep])
    db_session.commit()

    # 1. Search for investigation by case id
    res_inv = client.get("/api/v1/search/universal?q=INV-SEARCH-101")
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["total"] >= 1
    types = [r["type"] for r in data_inv["results"]]
    assert "investigation" in types

    # 2. Search for evidence by tag
    res_ev = client.get("/api/v1/search/universal?q=PASSPORT_VALIDATED")
    assert res_ev.status_code == 200
    data_ev = res_ev.json()
    assert data_ev["total"] >= 1
    assert data_ev["results"][0]["type"] == "evidence"

    # 3. Search for report by title keyword
    res_rep = client.get("/api/v1/search/universal?q=Quarterly")
    assert res_rep.status_code == 200
    data_rep = res_rep.json()
    assert data_rep["total"] >= 1
    assert data_rep["results"][0]["type"] == "report"

def test_universal_search_category_filter(client, db_session):
    """Verify category query parameter filters results."""
    inv = models.Investigation(
        investigation_id="INV-CAT-1",
        txn_id="TXN-CAT-1",
        status="QUEUED",
        report="Category filtering test case",
        tenant_id="default_tenant"
    )
    ev = models.EvidenceVaultItem(
        item_id="ev-cat-1",
        title="Category Filter Evidence Doc",
        category="CONTRACTS",
        source="LEGAL_DEPT",
        tag="CONTRACT_AUDIT",
        risk_level="MEDIUM",
        file_type="PDF",
        file_size=1024,
        sha256_hash="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        is_verified=True,
        tenant_id="default_tenant"
    )
    db_session.add_all([inv, ev])
    db_session.commit()

    # Query with category=evidence should only return evidence
    res = client.get("/api/v1/search/universal?q=Category&category=evidence")
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) >= 1
    for r in results:
        assert r["type"] == "evidence"

def test_universal_search_multitenant_isolation(client, db_session):
    """Verify cross-tenant resources are not returned in universal search."""
    inv_other = models.Investigation(
        investigation_id="INV-SECRET-OTHER-TENANT",
        txn_id="TXN-SECRET-99",
        status="COMPLETED",
        report="Sensitive confidential data from tenant B",
        tenant_id="tenant_foreign_corp"
    )
    db_session.add(inv_other)
    db_session.commit()

    # Current user is in default_tenant, searching for SECRET should yield 0 results
    res = client.get("/api/v1/search/universal?q=SECRET")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
