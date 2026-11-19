"""
Unit tests for FFIRE-Bench schema and Pydantic models.
"""

import pytest
from pydantic import ValidationError
from ffire_bench.schema.models import (
    Case,
    EvidenceItem,
    EvidenceType,
    Claim,
    ClaimLabel,
    CaseLabel,
    CaseDisposition,
    Provenance,
    Difficulty,
    Severity,
    ErrorCode,
    Track,
    Split,
    PredictionBundle,
    PredictionCase,
    PredictionClaim
)


def test_case_model_valid_instantiation():
    """Verify standard valid case creation."""
    ev = EvidenceItem(
        evidence_id="EV-1",
        type=EvidenceType.TRANSACTION_TABLE,
        title="Ledger",
        content={"amount": 9500.0}
    )
    cl = Claim(
        claim_id="CL-1",
        span=[0, 24],
        text="Deposit was $9,500.00.",
        label=ClaimLabel.SUPPORTED,
        gold_evidence_ids=["EV-1"]
    )
    case = Case(
        case_id="FB-T1-000001",
        version="1.0.0",
        track=Track.T1,
        split=Split.DEV,
        provenance=Provenance(
            generator="ffire_gen_v1",
            narrative_source="template",
            human_reviewed=True,
            reviewer_count=2
        ),
        typology="structuring",
        cluster_id="C-0001",
        evidence=[ev],
        narrative="Deposit was $9,500.00.",
        claims=[cl],
        case_label=CaseLabel(
            safe_to_file=True,
            disposition=CaseDisposition.ESCALATE
        ),
        difficulty=Difficulty.MEDIUM
    )

    dumped = case.model_dump()
    assert dumped["case_id"] == "FB-T1-000001"
    assert dumped["claims"][0]["label"] == "SUPPORTED"
    assert "FFIRE-BENCH-CANARY" in dumped["canary"]


def test_schema_validation_error_on_invalid_enum():
    """Verify validation fails if an invalid claim label or disposition is passed."""
    with pytest.raises(ValidationError):
        Claim(
            claim_id="CL-BAD",
            span=[0, 10],
            text="Invalid",
            label="INVALID_LABEL"  # Not in ClaimLabel enum
        )


def test_prediction_bundle_validation():
    """Verify prediction bundle serialization."""
    pred_case = PredictionCase(
        case_id="FB-T1-000001",
        predicted_safe_to_file=True,
        predicted_disposition=CaseDisposition.ALLOW,
        predicted_confidence=0.95,
        claims=[
            PredictionClaim(
                claim_id="CL-1",
                predicted_label=ClaimLabel.SUPPORTED,
                cited_evidence_ids=["EV-1"],
                confidence=0.95
            )
        ]
    )

    bundle = PredictionBundle(
        benchmark_version="0.1.0",
        model_name="test-model",
        track=Track.T1,
        predictions=[pred_case]
    )

    data = bundle.model_dump()
    assert data["model_name"] == "test-model"
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["claims"][0]["predicted_label"] == "SUPPORTED"
