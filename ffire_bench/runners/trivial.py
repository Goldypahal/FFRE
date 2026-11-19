"""
Trivial and heuristic baseline runners.
Provides lower-bound anchors to verify benchmark difficulty calibration (§2.8).
"""

import random
from typing import List
from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    PredictionCase,
    PredictionClaim,
    ClaimLabel,
    CaseDisposition
)


class MajorityBaselineRunner(BaseRunner):
    """
    Trivial baseline: predicts the majority class for every field.
    Predicts:
      - Claim label: SUPPORTED
      - Case safe_to_file: True
      - Disposition: ALLOW
    A well-calibrated benchmark requires majority baseline accuracy <= 40% (§2.8).
    """

    def __init__(self):
        super().__init__(name="Baseline-Majority")

    def predict_case(self, case: Case) -> PredictionCase:
        claim_preds = []
        for cl in case.claims:
            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=ClaimLabel.SUPPORTED,
                    cited_evidence_ids=["EV-1"] if case.evidence else [],
                    confidence=1.0
                )
            )

        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=True,
            predicted_disposition=CaseDisposition.ALLOW,
            predicted_confidence=1.0,
            claims=claim_preds
        )


class RandomBaselineRunner(BaseRunner):
    """Uniform random predictions across all labels."""

    def __init__(self, seed: int = 42):
        super().__init__(name="Baseline-Random")
        self.rng = random.Random(seed)
        self.labels = [
            ClaimLabel.SUPPORTED,
            ClaimLabel.CONTRADICTED,
            ClaimLabel.UNSUPPORTED,
            ClaimLabel.NOT_CHECKABLE
        ]
        self.dispositions = [
            CaseDisposition.ALLOW,
            CaseDisposition.CLOSE,
            CaseDisposition.FLAG,
            CaseDisposition.ESCALATE,
            CaseDisposition.NEED_MORE_INFO
        ]

    def predict_case(self, case: Case) -> PredictionCase:
        claim_preds = []
        for cl in case.claims:
            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=self.rng.choice(self.labels),
                    cited_evidence_ids=[self.rng.choice(case.evidence).evidence_id] if case.evidence else [],
                    confidence=round(self.rng.uniform(0.1, 0.9), 2)
                )
            )

        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=self.rng.choice([True, False]),
            predicted_disposition=self.rng.choice(self.dispositions),
            predicted_confidence=round(self.rng.uniform(0.1, 0.9), 2),
            claims=claim_preds
        )
