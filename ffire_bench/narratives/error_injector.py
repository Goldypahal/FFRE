"""
Controlled error injection engine for FFIRE-Bench.
Injects taxonomy-compliant errors (E1–E12) into clean narratives while
tracking exact character-level start and end spans, refuting evidence IDs,
and regulatory severity tiers.
"""

from typing import List, Dict, Any, Tuple, Optional
from ffire_bench.schema.models import Claim, ClaimLabel, ErrorCode, Severity


class ErrorInjector:
    """
    Applies deterministic mutations to narrative text, returning the mutated narrative
    and the corresponding annotated Claims with exact [start, end] character spans.
    """

    @staticmethod
    def inject_mutation(
        base_narrative: str,
        target_phrase: str,
        replacement_phrase: str,
        error_code: ErrorCode,
        severity: Severity,
        label: ClaimLabel,
        gold_evidence_ids: List[str],
        claim_id: str
    ) -> Tuple[str, Claim]:
        """
        Replaces target_phrase in base_narrative with replacement_phrase and returns
        the new narrative and a Claim object with the exact character span.
        """
        idx = base_narrative.find(target_phrase)
        if idx == -1:
            # Fallback: append replacement phrase if target not found
            idx = len(base_narrative)
            mutated = base_narrative + "\n" + replacement_phrase
        else:
            mutated = (
                base_narrative[:idx] +
                replacement_phrase +
                base_narrative[idx + len(target_phrase):]
            )

        start_span = idx
        end_span = idx + len(replacement_phrase)

        claim = Claim(
            claim_id=claim_id,
            span=[start_span, end_span],
            text=replacement_phrase,
            label=label,
            error_code=error_code,
            severity=severity,
            gold_evidence_ids=gold_evidence_ids
        )

        return mutated, claim

    @staticmethod
    def create_supported_claim(
        narrative: str,
        exact_phrase: str,
        claim_id: str,
        gold_evidence_ids: List[str]
    ) -> Claim:
        """Locates an exact supported phrase in narrative and generates a Claim object."""
        idx = narrative.find(exact_phrase)
        if idx == -1:
            raise ValueError(f"Phrase '{exact_phrase}' not found in narrative.")

        return Claim(
            claim_id=claim_id,
            span=[idx, idx + len(exact_phrase)],
            text=exact_phrase,
            label=ClaimLabel.SUPPORTED,
            error_code=None,
            severity=None,
            gold_evidence_ids=gold_evidence_ids
        )
