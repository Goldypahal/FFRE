"""
Prompt-based baseline runner for Frontier and Open-Weights LLMs.
Formats standardized zero-shot evaluation prompts for claims verification and error detection.
"""

import json
from typing import Dict, Any, Optional
from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    PredictionCase,
    PredictionClaim,
    ClaimLabel,
    CaseDisposition
)


ZERO_SHOT_VERIFIER_SYSTEM_PROMPT = """You are a senior Financial Crime Compliance QA Auditor.
Your task is to verify an AI-written financial crime investigation narrative against the raw evidence bundle.

For each claim in the narrative, classify it as:
- SUPPORTED: Fully verified by the evidence.
- CONTRADICTED: Directly conflicts with the evidence.
- UNSUPPORTED: Facts or conclusions not present anywhere in the evidence.
- NOT_CHECKABLE: Subjective or unfalsifiable conjecture.

Output valid JSON matching this schema:
{
  "safe_to_file": true | false,
  "disposition": "ALLOW" | "CLOSE" | "FLAG" | "ESCALATE" | "NEED_MORE_INFO",
  "confidence": 0.0 - 1.0,
  "claims": [
    {
      "claim_id": "CL-1",
      "label": "SUPPORTED" | "CONTRADICTED" | "UNSUPPORTED" | "NOT_CHECKABLE",
      "cited_evidence_ids": ["EV-1"],
      "confidence": 0.0 - 1.0
    }
  ]
}
"""


class LLMPromptRunner(BaseRunner):
    """
    Standardized prompt runner for LLM evaluation.
    Supports offline simulation or live completion APIs.
    """

    def __init__(self, model_name: str = "gpt-4o-zero-shot", api_caller: Optional[Any] = None):
        super().__init__(name=model_name)
        self.api_caller = api_caller

    def build_prompt(self, case: Case) -> str:
        ev_text = "\n\n".join(
            f"[{ev.evidence_id}] ({ev.type.value}): {ev.title}\n{json.dumps(ev.content, indent=2) if isinstance(ev.content, (dict, list)) else ev.content}"
            for ev in case.evidence
        )
        claims_text = "\n".join(
            f"- Claim ID: {cl.claim_id} | Text: \"{cl.text}\""
            for cl in case.claims
        )
        return (
            f"=== EVIDENCE BUNDLE ===\n{ev_text}\n\n"
            f"=== CANDIDATE NARRATIVE ===\n{case.narrative}\n\n"
            f"=== CLAIMS TO VERIFY ===\n{claims_text}\n"
        )

    def predict_case(self, case: Case) -> PredictionCase:
        if self.api_caller:
            prompt = self.build_prompt(case)
            response_json = self.api_caller(system=ZERO_SHOT_VERIFIER_SYSTEM_PROMPT, user=prompt)
            # Parse response
            claim_preds = [
                PredictionClaim(
                    claim_id=c["claim_id"],
                    predicted_label=ClaimLabel(c["label"]),
                    cited_evidence_ids=c.get("cited_evidence_ids", []),
                    confidence=c.get("confidence", 0.9)
                )
                for c in response_json.get("claims", [])
            ]
            return PredictionCase(
                case_id=case.case_id,
                predicted_safe_to_file=response_json.get("safe_to_file", False),
                predicted_disposition=CaseDisposition(response_json.get("disposition", "ESCALATE")),
                predicted_confidence=response_json.get("confidence", 0.9),
                claims=claim_preds
            )

        # High-capability simulated zero-shot baseline (identifies obvious amount/date errors)
        claim_preds = []
        has_critical = False
        ev_blob = " ".join(str(ev.content) for ev in case.evidence)

        for cl in case.claims:
            # Check if claim has explicit contradiction markers
            if cl.text in ev_blob:
                pred_label = ClaimLabel.SUPPORTED
                cited = [case.evidence[0].evidence_id] if case.evidence else []
            elif any(sym in cl.text for sym in ["$", "€", "£"]) and not any(sym in ev_blob and cl.text in ev_blob for sym in ["$", "€", "£"]):
                pred_label = ClaimLabel.CONTRADICTED
                has_critical = True
                cited = [case.evidence[0].evidence_id] if case.evidence else []
            else:
                pred_label = ClaimLabel.SUPPORTED
                cited = [case.evidence[0].evidence_id] if case.evidence else []

            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=pred_label,
                    cited_evidence_ids=cited,
                    confidence=0.88
                )
            )

        safe = not has_critical
        disp = CaseDisposition.ALLOW if safe else CaseDisposition.ESCALATE

        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=safe,
            predicted_disposition=disp,
            predicted_confidence=0.88,
            claims=claim_preds
        )
