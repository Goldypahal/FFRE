"""
Zero-shot LLM runner for FFIRE-Bench.

This runner always calls a real model through an ``api_caller`` (see
``ffire_bench.runners.llm_clients``). There is deliberately no offline
fallback: an earlier version silently fell back to string matching while
reporting itself under an LLM's name, which made leaderboard rows misleading.
"""

import json
from typing import Any, Callable, Dict, Optional

from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    CaseDisposition,
    ClaimLabel,
    PredictionCase,
    PredictionClaim,
)


ZERO_SHOT_VERIFIER_SYSTEM_PROMPT = """You are a senior Financial Crime Compliance QA Auditor.
Your task is to verify an AI-written financial crime investigation narrative against the raw evidence bundle.

For each listed claim, classify it as:
- SUPPORTED: Fully verified by the evidence.
- CONTRADICTED: Directly conflicts with the evidence.
- UNSUPPORTED: Facts or conclusions not present anywhere in the evidence.
- NOT_CHECKABLE: Subjective or unfalsifiable conjecture.

Cite the evidence IDs (e.g. "EV-1") you relied on for each claim.
Return ONLY valid JSON matching this schema:
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

PROMPT_VERSION = "zero-shot-v1"


def _clamp01(value: Any, default: float) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return default


class LLMPromptRunner(BaseRunner):
    """Runs one zero-shot prompt per case against a real LLM."""

    def __init__(self, model_name: str, api_caller: Optional[Callable[..., Dict[str, Any]]] = None):
        if api_caller is None:
            raise ValueError(
                "LLMPromptRunner needs a real model: pass api_caller "
                "(see ffire_bench.runners.llm_clients.make_caller)."
            )
        super().__init__(name=model_name)
        self.api_caller = api_caller
        self.parse_failures = 0

    def build_prompt(self, case: Case) -> str:
        ev_text = "\n\n".join(
            f"[{ev.evidence_id}] ({ev.type.value}): {ev.title}\n"
            f"{json.dumps(ev.content, indent=2) if isinstance(ev.content, (dict, list)) else ev.content}"
            for ev in case.evidence
        )
        claims_text = "\n".join(f'- Claim ID: {cl.claim_id} | Text: "{cl.text}"' for cl in case.claims)
        return (
            f"=== EVIDENCE BUNDLE ===\n{ev_text}\n\n"
            f"=== CANDIDATE NARRATIVE ===\n{case.narrative}\n\n"
            f"=== CLAIMS TO VERIFY ===\n{claims_text}\n"
        )

    def predict_case(self, case: Case) -> PredictionCase:
        try:
            response = self.api_caller(system=ZERO_SHOT_VERIFIER_SYSTEM_PROMPT, user=self.build_prompt(case))
        except ValueError:
            # Unparseable reply: score it as a wrong answer instead of crashing the run.
            response = {}
            self.parse_failures += 1

        by_id = {}
        for item in response.get("claims", []) or []:
            if isinstance(item, dict) and item.get("claim_id"):
                by_id[str(item["claim_id"])] = item

        claim_preds = []
        for cl in case.claims:
            item = by_id.get(cl.claim_id, {})
            try:
                label = ClaimLabel(str(item.get("label", "")).upper())
            except ValueError:
                # Missing or invalid label counts as an abstention, which is scored as wrong
                # unless the gold label is NOT_CHECKABLE.
                label = ClaimLabel.NOT_CHECKABLE
            claim_preds.append(
                PredictionClaim(
                    claim_id=cl.claim_id,
                    predicted_label=label,
                    cited_evidence_ids=[str(e) for e in item.get("cited_evidence_ids", []) or []],
                    confidence=_clamp01(item.get("confidence"), 0.5),
                )
            )

        try:
            disposition = CaseDisposition(str(response.get("disposition", "")).upper())
        except ValueError:
            disposition = CaseDisposition.NEED_MORE_INFO

        safe = response.get("safe_to_file")
        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=bool(safe) if isinstance(safe, bool) else False,
            predicted_disposition=disposition,
            predicted_confidence=_clamp01(response.get("confidence"), 0.5),
            claims=claim_preds,
        )
