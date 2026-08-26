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

    # Verify JSON artifact
    json_path = "data/srs_traceability.json"
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "metadata" in data
    assert "requirements" in data
    assert len(data["requirements"]) == 67

    # Verify Markdown artifact
    md_path = "data/srs_audit_report.md"
    assert os.path.exists(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "# FFIRE SRS Evidence-Driven Audit Scorecard" in md_content
    assert "NFR-1 Performance Benchmark" in md_content
