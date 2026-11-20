"""
Heuristic / Rule-based baseline runner.
Applies regex and lexical containment checks between claims and evidence text.
"""

import re
from typing import List, Set
from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    PredictionCase,
    PredictionClaim,
    ClaimLabel,
    CaseDisposition
)


class HeuristicRuleRunner(BaseRunner):
    """
    Checks lexical and numerical overlap between candidate claims and evidence items.
    """

    def __init__(self):
        super().__init__(name="Baseline-HeuristicRules")

    def _evidence_text_blob(self, case: Case) -> str:
        parts = []
        for ev in case.evidence:
            parts.append(str(ev.content))
        return " ".join(parts).lower()

    def predict_case(self, case: Case) -> PredictionCase:
        ev_blob = self._evidence_text_blob(case)
        claim_preds = []
        has_error = False

        for cl in case.claims:
            cl_text = cl.text.lower()
            cited_ids = []

            # Check for currency amounts (e.g. $10,000)
            amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", cl_text)
            amount_mismatch = False
            for amt in amounts:
                clean_amt = amt.replace(",", "").replace("$", "")
                if clean_amt not in ev_blob and amt not in ev_blob:
                    amount_mismatch = True

            # Match evidence IDs where claim words appear
            for ev in case.evidence:
                ev_str = str(ev.content).lower()
                words = [w for w in re.findall(r"\w+", cl_text) if len(w) > 4]
                if any(w in ev_str for w in words):
                    cited_ids.append(ev.evidence_id)

            if amount_mismatch:
                pred_lbl = ClaimLabel.CONTRADICTED
                has_error = True
            elif not cited_ids:
                pred_lbl = ClaimLabel.UNSUPPORTED
                has_error = True
            else:
                pred_lbl = ClaimLabel.SUPPORTED

            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=pred_lbl,
                    cited_evidence_ids=list(set(cited_ids))[:2],
                    confidence=0.75 if pred_lbl == ClaimLabel.SUPPORTED else 0.85
                )
            )

        safe_to_file = not has_error
        disposition = CaseDisposition.ALLOW if safe_to_file else CaseDisposition.ESCALATE

        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=safe_to_file,
            predicted_disposition=disposition,
            predicted_confidence=0.80,
            claims=claim_preds
        )
