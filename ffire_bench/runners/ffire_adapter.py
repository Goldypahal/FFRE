"""
FFIRE Verifier adapter for FFIRE-Bench.

Sends each case to a running FFIRE backend (``POST /api/v1/verifier/evaluate``)
and maps the verifier's answer onto benchmark claims, so FFIRE is scored under
the same rules as every other submitter.

An earlier version of this file did not call FFIRE at all: it re-implemented a
string-matching rule and reported the result as "FFIRE-Verifier-v1.0". That
row said nothing about the real system and has been removed from the results.

Configuration (arguments or environment):
- ``FFIRE_VERIFIER_URL``: base URL of the backend, e.g. ``http://localhost:8000``
- ``FFIRE_API_TOKEN``: bearer token of a user allowed to call the verifier

How claims are mapped
---------------------
The verifier extracts its own claims from the narrative, so its claims do not
line up one-to-one with the benchmark's gold claim spans. Each benchmark claim
is matched to the verifier claims that contain it, or that contain at least
``min_token_overlap`` of its words. If several match, the most severe status
wins (CONTRADICTED > UNGROUNDED > VERIFIED). A benchmark claim the verifier
never mentions is scored as SUPPORTED (the verifier raised no objection), and
the number of such claims is reported in ``unaligned_claims`` so readers can
judge how much of the score depends on this rule.
"""

import json
import os
import re
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from ffire_bench.runners.base import BaseRunner
from ffire_bench.schema.models import (
    Case,
    CaseDisposition,
    ClaimLabel,
    PredictionCase,
    PredictionClaim,
)

STATUS_TO_LABEL = {
    "VERIFIED": ClaimLabel.SUPPORTED,
    "CONTRADICTED": ClaimLabel.CONTRADICTED,
    "UNGROUNDED": ClaimLabel.UNSUPPORTED,
}
SEVERITY = {"CONTRADICTED": 3, "UNGROUNDED": 2, "VERIFIED": 1}

HttpPost = Callable[[str, Dict[str, str], Dict[str, Any]], Dict[str, Any]]


def _default_http_post(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class FFIREVerifierRunner(BaseRunner):
    """Calls the real FFIRE verifier endpoint for every case."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        api_token: Optional[str] = None,
        http_post: Optional[HttpPost] = None,
        min_token_overlap: float = 0.6,
        name: str = "FFIRE-Verifier",
    ):
        endpoint_url = endpoint_url or os.environ.get("FFIRE_VERIFIER_URL")
        if not endpoint_url:
            raise ValueError(
                "FFIREVerifierRunner needs a running FFIRE backend: pass endpoint_url "
                "or set FFIRE_VERIFIER_URL (e.g. http://localhost:8000)."
            )
        super().__init__(name=name)
        self.endpoint = endpoint_url.rstrip("/") + "/api/v1/verifier/evaluate"
        self.api_token = api_token if api_token is not None else os.environ.get("FFIRE_API_TOKEN", "")
        self.http_post = http_post or _default_http_post
        self.min_token_overlap = min_token_overlap
        self.unaligned_claims = 0
        self.total_claims = 0

    def _request_body(self, case: Case) -> Dict[str, Any]:
        return {
            "narrative": case.narrative,
            "evidence": [
                {
                    "evidence_id": ev.evidence_id,
                    "type": ev.type.value,
                    "title": ev.title,
                    "content": ev.content,
                }
                for ev in case.evidence
            ],
            "vendor": "ffire-bench",
            "strict": False,
        }

    def _match(self, claim_text: str, verifier_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        needle = " ".join(_tokens(claim_text))
        needle_tokens = set(_tokens(claim_text))
        matches = []
        for vc in verifier_claims:
            vc_text = " ".join(_tokens(vc.get("claim_text", "")))
            if needle and needle in vc_text:
                matches.append(vc)
            elif needle_tokens:
                overlap = len(needle_tokens & set(vc_text.split())) / len(needle_tokens)
                if overlap >= self.min_token_overlap:
                    matches.append(vc)
        return matches

    def predict_case(self, case: Case) -> PredictionCase:
        headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        response = self.http_post(self.endpoint, headers, self._request_body(case))
        verifier_claims = response.get("claims", []) or []

        claim_preds = []
        for cl in case.claims:
            self.total_claims += 1
            matches = self._match(cl.text, verifier_claims)
            if not matches:
                self.unaligned_claims += 1
                label, cited = ClaimLabel.SUPPORTED, []
            else:
                worst = max(matches, key=lambda m: SEVERITY.get(m.get("status", ""), 0))
                label = STATUS_TO_LABEL.get(worst.get("status", ""), ClaimLabel.UNSUPPORTED)
                cited = [str(c) for c in worst.get("citations", []) or []]
            claim_preds.append(
                PredictionClaim(claim_id=cl.claim_id, predicted_label=label, cited_evidence_ids=cited)
            )

        # The verifier judges the narrative, not the case outcome, so the
        # disposition below is only a placeholder; Track 3 scores for this runner
        # are not meaningful.
        verdict = response.get("verification_status", "")
        safe = verdict == "PASSED"
        grounding = float(response.get("grounding_score", 0.0) or 0.0)
        return PredictionCase(
            case_id=case.case_id,
            predicted_safe_to_file=safe,
            predicted_disposition=CaseDisposition.CLOSE if safe else CaseDisposition.ESCALATE,
            predicted_confidence=min(1.0, max(0.0, grounding)),
            claims=claim_preds,
        )
