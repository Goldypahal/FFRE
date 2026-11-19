"""
Unit tests for synthetic scenario generation across all 8 typologies.
"""

from ffire_bench.generators.ffire_gen import FFIREGenerator
from ffire_bench.generators.perturbations import AdversarialPerturbations
from ffire_bench.schema.models import Track, Split


def test_generator_all_8_typologies():
    """Verify that all 8 typologies generate valid cases."""
    gen = FFIREGenerator(seed=123)
    typologies = FFIREGenerator.TYPOLOGIES

    for idx, typ in enumerate(typologies):
        case = gen.generate_case(
            case_idx=idx + 1,
            typology=typ,
            inject_error=True,
            track=Track.T1,
            split=Split.DEV
        )
        assert case.typology == typ
        assert len(case.evidence) >= 1
        assert len(case.claims) >= 1
        assert case.case_id.startswith("FB-T1-")
        assert case.cluster_id.startswith("C-")
        assert not case.case_label.safe_to_file  # Error was injected


def test_deterministic_generation_reproducibility():
    """Verify that identical seed produces identical cases."""
    gen1 = FFIREGenerator(seed=999)
    gen2 = FFIREGenerator(seed=999)

    case1 = gen1.generate_case(1, typology="structuring")
    case2 = gen2.generate_case(1, typology="structuring")

    assert case1.narrative == case2.narrative
    assert len(case1.claims) == len(case2.claims)
    assert case1.claims[0].span == case2.claims[0].span


def test_adversarial_perturbations():
    """Verify perturbation injections."""
    gen = FFIREGenerator(seed=42)
    case = gen.generate_case(1, typology="structuring")

    # Prompt injection
    perturbed_pi = AdversarialPerturbations.inject_prompt_injection(case)
    assert len(perturbed_pi.evidence) == len(case.evidence) + 1
    assert any("SYSTEM OVERRIDE" in str(ev.content) for ev in perturbed_pi.evidence)

    # Distractor evidence
    perturbed_dist = AdversarialPerturbations.insert_distractor_evidence(case)
    assert len(perturbed_dist.evidence) == len(case.evidence) + 1
    assert any("Subway Sandwiches" in str(ev.content) for ev in perturbed_dist.evidence)
