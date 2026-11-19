"""
Unit tests for baseline runners and model adapters.
"""

from ffire_bench.generators.ffire_gen import FFIREGenerator
from ffire_bench.runners import (
    MajorityBaselineRunner,
    RandomBaselineRunner,
    HeuristicRuleRunner,
    LLMPromptRunner,
    FFIREVerifierRunner
)
from ffire_bench.schema.models import ClaimLabel


def test_baseline_runners_execution():
    """Verify that all baseline runners produce valid PredictionBundles."""
    gen = FFIREGenerator(seed=42)
    cases = [gen.generate_case(i) for i in range(1, 4)]

    runners = [
        MajorityBaselineRunner(),
        RandomBaselineRunner(seed=42),
        HeuristicRuleRunner(),
        LLMPromptRunner(),
        FFIREVerifierRunner()
    ]

    for runner in runners:
        bundle = runner.run_benchmark(cases)
        assert bundle.model_name == runner.name
        assert len(bundle.predictions) == 3
        for pred in bundle.predictions:
            assert pred.case_id.startswith("FB-T1-")
            assert len(pred.claims) >= 1


def test_majority_baseline_predicts_all_supported():
    """Verify that majority baseline labels all claims as SUPPORTED."""
    gen = FFIREGenerator(seed=42)
    case = gen.generate_case(1, inject_error=True)
    runner = MajorityBaselineRunner()
    pred = runner.predict_case(case)

    for cl in pred.claims:
        assert cl.predicted_label == ClaimLabel.SUPPORTED
    assert pred.predicted_safe_to_file is True
