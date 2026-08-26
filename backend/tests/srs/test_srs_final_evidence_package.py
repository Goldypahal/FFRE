import os
import json
import pytest
from pathlib import Path
from scripts.build_final_evidence_package import build_final_evidence_package, calculate_sha256

def test_task39_evidence_package_generation():
    """
    Task 39 Test 1: Verify automated build_final_evidence_package creates dist/ffre_evidence_package/ and 7 deliverables.
    """
    res = build_final_evidence_package()
    assert res["status"] == "SUCCESS"
    assert res["production_readiness_pct"] == 100.0

    dist_dir = Path("dist/ffre_evidence_package")
    assert dist_dir.exists()

    expected_files = [
        "EXECUTIVE_AUDIT_REPORT.md",
        "srs_traceability.json",
        "srs_traceability.json.sha256",
        "audit_the_auditor_report.md",
        "task20_results.json",
        "FFIRE_SRS.txt",
        "CHECKSUMS.sha256"
    ]

    for fname in expected_files:
        fpath = dist_dir / fname
        assert fpath.exists(), f"Missing evidence deliverable: {fname}"
        assert fpath.stat().st_size > 0, f"Empty evidence deliverable: {fname}"

def test_task39_executive_audit_report_completeness():
    """
    Task 39 Test 2: Verify EXECUTIVE_AUDIT_REPORT.md contains executive summary, 67-requirement matrix, and 100% production readiness verdict.
    """
    report_path = Path("dist/ffre_evidence_package/EXECUTIVE_AUDIT_REPORT.md")
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Financial Fraud Investigation Reasoning Engine (FFRE)" in content
    assert "Reviewer-Ready Executive SRS Compliance & Audit Report" in content
    assert "100.0% PRODUCTION READY (67/67 CORE REQUIREMENTS VERIFIED)" in content
    assert "FINAL FFRE EVIDENCE-DRIVEN ENTERPRISE AUDIT SCORECARD" in content
    assert "Cryptographic Tamper-Evidence & Zero-Trust Signatures" in content

def test_task39_package_sha256_cryptographic_verification():
    """
    Task 39 Test 3: Verify CHECKSUMS.sha256 manifest hashes match physical file hashes.
    """
    manifest_path = Path("dist/ffre_evidence_package/CHECKSUMS.sha256")
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 6

    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2:
            expected_hash, fname = parts[0], parts[1]
            file_path = Path("dist/ffre_evidence_package") / fname
            assert file_path.exists()
            computed_hash = calculate_sha256(str(file_path))
            assert computed_hash == expected_hash, f"Hash mismatch for {fname}"

def test_task39_reviewer_ready_deliverable_validation():
    """
    Task 39 Test 4: Confirm evidence package is self-contained and reviewer-ready.
    """
    srs_path = Path("dist/ffre_evidence_package/FFIRE_SRS.txt")
    json_path = Path("dist/ffre_evidence_package/srs_traceability.json")

    assert srs_path.exists()
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["requirements"]) == 67
    assert data["metadata"]["scorecard"]["total_requirements"] == 67

def test_task39_100_percent_final_milestone_completion():
    """
    Task 39 Test 5: Final Enterprise Milestone Verdict - Assert 100% Production Readiness across all 67 requirements.
    """
    json_path = Path("dist/ffre_evidence_package/srs_traceability.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scorecard = data["metadata"]["scorecard"]

    assert scorecard["total_requirements"] == 67
    assert scorecard["implementation_coverage_pct"] == 100.0
    assert scorecard["semantic_verification_coverage_pct"] == 100.0
    assert scorecard["runtime_acceptance_evidence_coverage_pct"] == 100.0
    assert scorecard["chaos_resilience_coverage_pct"] == 100.0
    assert scorecard["security_penetration_coverage_pct"] == 100.0
    assert scorecard["ha_deployment_coverage_pct"] == 100.0
    assert scorecard["observability_alerting_coverage_pct"] == 100.0
    assert scorecard["production_deployment_coverage_pct"] == 100.0
    assert scorecard["final_compliance_audit_coverage_pct"] == 100.0
    assert scorecard["audit_the_auditor_coverage_pct"] == 100.0
    assert scorecard["production_readiness_coverage_pct"] == 100.0
    assert scorecard["nfr1_target_met"] is True
