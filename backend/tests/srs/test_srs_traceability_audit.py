import os
import sys
import json
import pytest
from pathlib import Path

repo_root = str(Path(__file__).resolve().parents[3])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from scripts.srs_audit_engine import SRSEvidenceAuditEngine

def test_srs_audit_engine_execution_and_artifacts():
    """Task 26 Test: Verify SRSEvidenceAuditEngine executes cleanly and produces evidence-backed JSON and Markdown reports."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary is not None
    assert summary["total_requirements"] == 67
    assert summary["implementation_coverage_pct"] == 100.0
    assert summary["evidence_mapping_coverage_pct"] == 100.0
    assert summary["verification_coverage_pct"] == 100.0
    assert summary["production_readiness_coverage_pct"] > 80.0

    # Task 28: Source-of-Truth SRS Document Reconciliation verification
    reconciliation = summary.get("srs_reconciliation", {})
    assert reconciliation.get("status") == "PASSED"
    assert reconciliation.get("srs_requirements_found_in_text") == 67
    assert reconciliation.get("audit_catalog_requirements") == 67
    assert reconciliation.get("exact_id_matches") == 67
    assert reconciliation.get("missing_from_audit_count") == 0
    assert reconciliation.get("extra_in_audit_count") == 0
    assert reconciliation.get("duplicates_count") == 0

    # Verify JSON artifact
    json_path = "data/srs_traceability.json"
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "metadata" in data
    assert "reconciliation" in data["metadata"]
    assert data["metadata"]["reconciliation"]["status"] == "PASSED"
    assert "requirements" in data
    assert len(data["requirements"]) == 67

    # Verify Markdown artifact
    md_path = "data/srs_audit_report.md"
    assert os.path.exists(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "# FFIRE SRS Evidence-Driven Audit Scorecard" in md_content
    assert "SRS DOCUMENT (FFIRE_SRS.txt) RECONCILIATION SUMMARY" in md_content
    assert "Reconciliation Status:             🟢 PASSED (100% Exact Match)" in md_content

def test_task29_semantic_evidence_verification_matrix():
    """Task 29 Test: Verify 100% semantic requirement evidence verification (target symbol & dedicated test matching)."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["semantic_verification_coverage_pct"] == 100.0
    assert summary["implementation_coverage_pct"] == 100.0
    assert summary["verification_coverage_pct"] == 100.0

    for req_res in engine.results:
        assert req_res["symbol_found"] is True, f"Symbol {req_res['target_symbol']} missing for {req_res['req_id']}"
        assert req_res["test_found"] is True, f"Test {req_res['target_test']} missing for {req_res['req_id']}"
        assert req_res["verification_status"] == "VERIFIED"

def test_task30_runtime_behavioral_acceptance_suite():
    """Task 30 Test: Verify 100% runtime acceptance evidence coverage across positive and negative testing suites."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

    for req_res in engine.results:
        assert req_res["positive_status"] == "PASS", f"Positive status failed for {req_res['req_id']}"
        assert req_res["negative_status"] == "PASS", f"Negative status failed for {req_res['req_id']}"
        assert req_res["runtime_behavior_verdict"] == "VERIFIED"

def test_task31_failure_injection_and_chaos_resilience_suite():
    """Task 31 Test: Verify 100% chaos resilience coverage across 20 operational failure modes."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task32_security_penetration_and_abuse_suite():
    """Task 32 Test: Verify 100% security penetration coverage across 30 defined security controls."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task33_ha_kubernetes_deployment_suite():
    """Task 33 Test: Verify 100% HA deployment coverage across multi-pod gateway & DB sync controls."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task35_observability_and_alerting_suite():
    """Task 35 Test: Verify 100% observability & Prometheus alerting coverage."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["observability_alerting_coverage_pct"] == 100.0
    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task36_production_deployment_suite():
    """Task 36 Test: Verify 100% production deployment & environment diagnostic coverage and 100% Production Readiness score."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["production_deployment_coverage_pct"] == 100.0
    assert summary["production_readiness_coverage_pct"] == 100.0
    assert summary["observability_alerting_coverage_pct"] == 100.0
    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task37_final_compliance_suite():
    """Task 37 Test: Verify 100% final 67/67 SRS compliance coverage."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["final_compliance_audit_coverage_pct"] == 100.0
    assert summary["production_deployment_coverage_pct"] == 100.0
    assert summary["production_readiness_coverage_pct"] == 100.0
    assert summary["observability_alerting_coverage_pct"] == 100.0
    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task38_audit_the_auditor_suite():
    """Task 38 Test: Verify 100% audit-the-auditor zero-trust coverage."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["audit_the_auditor_coverage_pct"] == 100.0
    assert summary["final_compliance_audit_coverage_pct"] == 100.0
    assert summary["production_deployment_coverage_pct"] == 100.0
    assert summary["production_readiness_coverage_pct"] == 100.0
    assert summary["observability_alerting_coverage_pct"] == 100.0
    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0

def test_task39_final_evidence_package_suite():
    """Task 39 Test: Final Enterprise Milestone Verdict - Verify 100% reviewer evidence package coverage."""
    engine = SRSEvidenceAuditEngine()
    summary = engine.run_audit()

    assert summary["final_evidence_package_coverage_pct"] == 100.0
    assert summary["audit_the_auditor_coverage_pct"] == 100.0
    assert summary["final_compliance_audit_coverage_pct"] == 100.0
    assert summary["production_deployment_coverage_pct"] == 100.0
    assert summary["production_readiness_coverage_pct"] == 100.0
    assert summary["observability_alerting_coverage_pct"] == 100.0
    assert summary["ha_deployment_coverage_pct"] == 100.0
    assert summary["security_penetration_coverage_pct"] == 100.0
    assert summary["chaos_resilience_coverage_pct"] == 100.0
    assert summary["runtime_acceptance_evidence_coverage_pct"] == 100.0
