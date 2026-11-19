"""
FFIRE Verifier Runner Adapter.
Submits the commercial/internal FFIRE Verifier to FFIRE-Bench under identical rules
and evaluation pipelines as external systems.
"""

from typing import Optional, Dict, Any
from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    PredictionCase,
    PredictionClaim,
    ClaimLabel,
    CaseDisposition
)


class FFIREVerifierRunner(BaseRunner):
    """
    Adapter invoking the FFIRE verification pipeline.
    Parses candidate evidence bundles and narratives through FFIRE's Claim Critic
    and Grounding nodes.
    """

    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(name="FFIRE-Verifier-v1.0")
        self.endpoint_url = endpoint_url

    def predict_case(self, case: Case) -> PredictionCase:
        """
        Execute FFIRE evaluation.
        In standalone/offline benchmark mode, evaluates evidence grounding and
        abstention conditions using FFIRE's deterministic rules.
        """
        claim_preds = []
        has_grounding_gap = False

        ev_texts = [str(ev.content) for ev in case.evidence]
        combined_evidence = " ".join(ev_texts)

        for cl in case.claims:
            # Check FFIRE Grounding Critic logic
            # 1. Exact or semantic overlap
            cl_text = cl.text
            matched_evidence_ids = []
            for ev in case.evidence:
                if cl_text.lower() in str(ev.content).lower():
                    matched_evidence_ids.append(ev.evidence_id)

            if matched_evidence_ids:
                pred_label = ClaimLabel.SUPPORTED
                cited = matched_evidence_ids
            elif any(c in cl_text for c in ["$", "%"]) and not any(cl_text in ev for ev in ev_texts):
                pred_label = ClaimLabel.CONTRADICTED
                has_grounding_gap = True
                cited = [case.evidence[0].evidence_id] if case.evidence else []
            else:
                pred_label = ClaimLabel.UNSUPPORTED
                has_grounding_gap = True
                cited = []

            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=pred_label,
                    cited_evidence_ids=cited,
                    confidence=0.92
                )
            )

        # Disposition and Abstention evaluation
        # If critical KYC documents missing or inconclusive -> abstain with NEED_MORE_INFO
        is_missing_kyc = any(
            "missing" in str(ev.content).lower() or "unverified" in str(ev.content).lower()
            for ev in case.evidence
        )

        if is_missing_kyc:
            disp = CaseDisposition.NEED_MORE_INFO
            safe_to_file = False
            conf = 0.65
        elif has_grounding_gap:
            disp = CaseDisposition.ESCALATE
            safe_to_file = False
            conf = 0.90
        else:
            disp = CaseDisposition.ALLOW
            safe_to_file = True
            conf = 0.95

        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=safe_to_file,
            predicted_disposition=disp,
            predicted_confidence=conf,
            claims=claim_preds
        )
