"""
Unit tests for baseline runners and model adapters.
"""

import pytest

from ffire_bench.generators.ffire_gen import FFIREGenerator
from ffire_bench.runners import (
    MajorityBaselineRunner,
    RandomBaselineRunner,
    HeuristicRuleRunner,
    LLMPromptRunner,
    FFIREVerifierRunner,
)
from ffire_bench.runners.llm_clients import extract_json_object
from ffire_bench.schema.models import CaseDisposition, ClaimLabel


def _cases(n=3):
    gen = FFIREGenerator(seed=42)
    return [gen.generate_case(i) for i in range(1, n + 1)]


def test_offline_baseline_runners_execution():
    """Offline baselines produce valid PredictionBundles."""
    cases = _cases()
    for runner in [MajorityBaselineRunner(), RandomBaselineRunner(seed=42), HeuristicRuleRunner()]:
        bundle = runner.run_benchmark(cases)
        assert bundle.model_name == runner.name
        assert len(bundle.predictions) == 3
        for pred in bundle.predictions:
            assert pred.case_id.startswith("FB-T1-")
            assert len(pred.claims) >= 1


def test_majority_baseline_predicts_all_supported():
    gen = FFIREGenerator(seed=42)
    case = gen.generate_case(1, inject_error=True)
    pred = MajorityBaselineRunner().predict_case(case)
    for cl in pred.claims:
        assert cl.predicted_label == ClaimLabel.SUPPORTED
    assert pred.predicted_safe_to_file is True


def test_generator_does_not_claim_human_review():
    for case in _cases(8):
        assert case.provenance.human_reviewed is False
        assert case.provenance.reviewer_count == 0
        assert case.provenance.narrative_source.startswith("template:")


# ---------------------------------------------------------------- LLM runner

def test_llm_runner_requires_real_model():
    with pytest.raises(ValueError):
        LLMPromptRunner(model_name="gpt-4o")


def test_llm_runner_uses_model_answer():
    case = _cases(1)[0]
    seen = {}

    def fake_caller(system, user):
        seen["user"] = user
        return {
            "safe_to_file": False,
            "disposition": "ESCALATE",
            "confidence": 0.7,
            "claims": [
                {"claim_id": cl.claim_id, "label": "CONTRADICTED", "cited_evidence_ids": ["EV-1"], "confidence": 0.8}
                for cl in case.claims
            ],
        }

    pred = LLMPromptRunner(model_name="fake:model", api_caller=fake_caller).predict_case(case)
    assert case.claims[0].text in seen["user"]
    assert all(c.predicted_label == ClaimLabel.CONTRADICTED for c in pred.claims)
    assert pred.claims[0].cited_evidence_ids == ["EV-1"]
    assert pred.predicted_disposition == CaseDisposition.ESCALATE
    assert pred.predicted_safe_to_file is False


def test_llm_runner_scores_bad_reply_as_abstention():
    case = _cases(1)[0]

    def broken_caller(system, user):
        raise ValueError("no JSON")

    runner = LLMPromptRunner(model_name="fake:model", api_caller=broken_caller)
    pred = runner.predict_case(case)
    assert runner.parse_failures == 1
    assert all(c.predicted_label == ClaimLabel.NOT_CHECKABLE for c in pred.claims)


def test_extract_json_object_handles_fences_and_prose():
    assert extract_json_object('Sure:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json_object('Answer: {"b": [1, 2]} done') == {"b": [1, 2]}
    with pytest.raises(ValueError):
        extract_json_object("no json here")


# ------------------------------------------------------------- FFIRE adapter

def test_ffire_runner_requires_backend(monkeypatch):
    monkeypatch.delenv("FFIRE_VERIFIER_URL", raising=False)
    with pytest.raises(ValueError):
        FFIREVerifierRunner()


def test_ffire_runner_calls_endpoint_and_maps_claims():
    case = _cases(1)[0]
    calls = []

    def fake_post(url, headers, body):
        calls.append((url, headers, body))
        return {
            "verification_status": "CONTRADICTION_DETECTED",
            "grounding_score": 0.5,
            "claims": [
                {"claim_text": f"The report states {case.claims[0].text} as fact.",
                 "status": "CONTRADICTED", "citations": ["EV-1"]},
            ],
        }

    runner = FFIREVerifierRunner(endpoint_url="http://ffire.test/", api_token="tok", http_post=fake_post)
    pred = runner.predict_case(case)

    url, headers, body = calls[0]
    assert url == "http://ffire.test/api/v1/verifier/evaluate"
    assert headers["Authorization"] == "Bearer tok"
    assert body["narrative"] == case.narrative
    assert [e["evidence_id"] for e in body["evidence"]] == [e.evidence_id for e in case.evidence]

    assert pred.claims[0].predicted_label == ClaimLabel.CONTRADICTED
    assert pred.claims[0].cited_evidence_ids == ["EV-1"]
    assert pred.predicted_safe_to_file is False


def test_ffire_runner_counts_unaligned_claims():
    case = _cases(1)[0]

    def fake_post(url, headers, body):
        return {"verification_status": "PASSED", "grounding_score": 1.0,
                "claims": [{"claim_text": "zzz unrelated", "status": "VERIFIED"}]}

    runner = FFIREVerifierRunner(endpoint_url="http://ffire.test", http_post=fake_post)
    pred = runner.predict_case(case)
    assert runner.unaligned_claims == len(case.claims)
    assert all(c.predicted_label == ClaimLabel.SUPPORTED for c in pred.claims)
    assert pred.predicted_safe_to_file is True
