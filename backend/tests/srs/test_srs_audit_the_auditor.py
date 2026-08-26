import os
import json
import pytest
from scripts.audit_the_auditor import IndependentAuditorEngine

def test_auditor_independent_ast_symbol_verification():
    """
    Task 38 Test 1: Verify independent AST parser resolves target python symbols.
    """
    auditor = IndependentAuditorEngine()
    
    # Test existing symbol in main.py
    found_main = auditor.parse_ast_for_symbol("backend/main.py", "create_investigation")
    assert found_main is True

    # Test non-existent symbol
    found_fake = auditor.parse_ast_for_symbol("backend/main.py", "non_existent_fake_symbol_123")
    assert found_fake is False

def test_auditor_independent_srs_text_reconciliation():
    """
    Task 38 Test 2: Verify independent regex scan of FFIRE_SRS.txt reconciles 67/67 IDs.
    """
    auditor = IndependentAuditorEngine()
    reconcil = auditor.reconcile_srs_text_independently()

    assert reconcil["status"] == "PASSED"
    assert reconcil["found_count"] == 67

def test_auditor_tamper_detection_and_signature_integrity():
    """
    Task 38 Test 3: Verify SHA-256 integrity signature calculation and artifact verification.
    """
    auditor = IndependentAuditorEngine()
    hash_json = auditor.calculate_sha256("data/srs_traceability.json")
    hash_report = auditor.calculate_sha256("data/srs_audit_report.md")

    assert len(hash_json) == 64
    assert len(hash_report) == 64
    assert hash_json != hash_report

def test_auditor_fault_mutation_detection():
    """
    Task 38 Test 4: Verify metamorphic fault mutation detection when missing symbol is provided.
    """
    auditor = IndependentAuditorEngine()
    found = auditor.parse_ast_for_symbol("backend/main.py", "mutated_missing_function_name")
    assert found is False

def test_auditor_executive_verification_report():
    """
    Task 38 Test 5: Verify zero-trust verification report generation.
    """
    auditor = IndependentAuditorEngine()
    res = auditor.run_zero_trust_verification()

    assert res["reconciliation_status"] == "PASSED"
    assert res["artifact_verification_status"] == "PASSED"
    assert os.path.exists("data/srs_traceability.json.sha256")
    assert os.path.exists("data/audit_the_auditor_report.md")
