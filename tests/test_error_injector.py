"""
Unit tests for error injection and character-level span tracking.
"""

from ffire_bench.narratives.error_injector import ErrorInjector
from ffire_bench.schema.models import ErrorCode, Severity, ClaimLabel


def test_error_injection_span_precision():
    """Verify that injected mutation exactly matches the character span coordinates."""
    base_text = "The subject received a total deposit of $10,000.00 on Monday."
    target = "$10,000.00"
    replacement = "$14,500.00"

    mutated, claim = ErrorInjector.inject_mutation(
        base_narrative=base_text,
        target_phrase=target,
        replacement_phrase=replacement,
        error_code=ErrorCode.E1,
        severity=Severity.CRITICAL,
        label=ClaimLabel.CONTRADICTED,
        gold_evidence_ids=["EV-1"],
        claim_id="CL-1"
    )

    span = claim.span
    # Slicing the mutated text at [start, end] must exactly yield the replacement phrase!
    assert mutated[span[0]:span[1]] == replacement
    assert claim.error_code == ErrorCode.E1
    assert claim.severity == Severity.CRITICAL
    assert claim.label == ClaimLabel.CONTRADICTED


def test_supported_claim_span_precision():
    """Verify that create_supported_claim extracts exact character span."""
    narrative = "Account was opened in 2021 with verified identity documents."
    phrase = "verified identity documents"

    claim = ErrorInjector.create_supported_claim(
        narrative=narrative,
        exact_phrase=phrase,
        claim_id="CL-2",
        gold_evidence_ids=["EV-KYC"]
    )

    span = claim.span
    assert narrative[span[0]:span[1]] == phrase
    assert claim.label == ClaimLabel.SUPPORTED
    assert claim.error_code is None
