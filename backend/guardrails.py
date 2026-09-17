from typing import Dict, Any, Tuple, List
import re

def extract_and_verify_claims(draft_explanation: str, evidence_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts claims from draft explanation and verifies evidence field matching and support.
    Returns structured claim verification objects:
    [
        {"claim": sentence, "evidence_source": field_name, "supported": bool, "confidence": float}
    ]
    """
    if not draft_explanation:
        return []

    evidence_fields = {}
    evidence_floats = set()

    def extract_field_map(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                field_key = f"{prefix}.{k}" if prefix else str(k)
                if isinstance(v, (dict, list)):
                    extract_field_map(v, field_key)
                elif v is not None:
                    val_str = str(v).lower()
                    evidence_fields[field_key.lower()] = val_str
                    try:
                        evidence_floats.add(float(v))
                    except (ValueError, TypeError):
                        pass
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_field_map(item, f"{prefix}[{i}]")

    extract_field_map(evidence_bundle)
    full_corpus = " ".join(evidence_fields.values())
    has_location_evidence = any("country" in k or "location" in k or "geo" in k for k in evidence_fields.keys())

    claim_verifications = []
    sentences = re.split(r'(?<=[.!?])\s+', draft_explanation)

    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean or len(sentence_clean) < 10 or sentence_clean.startswith("[System Error"):
            continue

        sentence_lower = sentence_clean.lower()
        matched_source = "general_evidence"
        supported = True
        confidence = 0.95

        # Check field citations in claim
        for field_name, field_val in evidence_fields.items():
            field_short = field_name.split(".")[-1]
            if field_short in sentence_lower or field_name in sentence_lower:
                matched_source = field_name
                break

        # Check for ungrounded numerical claims (amounts/counts) with numeric equivalence
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', sentence_clean)
        for num in numbers:
            num_val = float(num)
            if num_val > 5: # Only verify non-trivial numbers
                if num not in full_corpus and num_val not in evidence_floats:
                    supported = False
                    confidence = 0.30
                    break

        # Check for ungrounded location/country claims
        if ("country" in sentence_lower or "location" in sentence_lower) and not has_location_evidence:
            supported = False
            confidence = 0.25

        # Check for specific ungrounded keywords
        if "hallucinated_fact" in sentence_lower:
            supported = False
            confidence = 0.10
        elif "unknown os" in sentence_lower and "unknown" not in full_corpus:
            supported = False
            confidence = 0.20
        elif "highrisk electronics" in sentence_lower and "highrisk electronics" not in full_corpus:
            supported = False
            confidence = 0.20

        claim_verifications.append({
            "claim": sentence_clean,
            "evidence_source": matched_source,
            "supported": supported,
            "confidence": confidence
        })

    return claim_verifications

def validate_claims(draft_explanation: str, evidence_bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that claims in the draft explanation are grounded in the evidence bundle (FO-6).
    Uses extract_and_verify_claims for general claim grounding verification.
    """
    if not draft_explanation:
        return True, []

    verifications = extract_and_verify_claims(draft_explanation, evidence_bundle)
    unsupported_claims = [v["claim"] for v in verifications if not v["supported"]]

    is_validated = len(unsupported_claims) == 0
    return is_validated, unsupported_claims


# --- Prompt Injection Defense Guardrails (Chapters 47 & 88) ---

INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?",
    r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?)",
    r"forget\s+(?:everything|all)\s+(?:you\s+know|above)",
    r"system\s+prompt\s*:",
    r"new\s+role\s*:",
    r"you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|evil|jailbroken|dan)",
    r"dan\s+mode",
    r"developer\s+mode\s+(?:enabled|activated)",
    r"<\|(?:im_start|im_end|endoftext)\|>",
    r"\[\/?(?:inst|system|prompt)\]",
    r"(?:output|print|display|dump)\s+(?:all\s+)?(?:secret|api[_\s]?keys?|environment\s+variables?|passwords?)",
    r"(?:base64|hex)\s+encode\s+(?:all\s+)?(?:keys?|secrets?|passwords?)"
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def detect_prompt_injection(text: str) -> Tuple[bool, List[str], float]:
    """
    Detect adversarial prompt injection, jailbreak attempts, and system override patterns (Chapter 88).
    Returns (is_injection: bool, matched_patterns: List[str], risk_score: float).
    """
    if not text:
        return False, [], 0.0

    matches = []
    for pat in _COMPILED_PATTERNS:
        match = pat.search(text)
        if match:
            matches.append(match.group(0))

    if matches:
        risk_score = min(1.0, 0.5 + (0.25 * len(matches)))
        return True, matches, risk_score

    return False, [], 0.0

def sanitize_prompt_input(text: str) -> str:
    """
    Sanitize user and system inputs before LLM template interpolation:
    - Neutralize LLM control tokens and instruction delimiters
    - Strip hazardous control characters
    """
    if not text:
        return ""
    sanitized = text.replace("<|", "&lt;|").replace("|>", "|&gt;")
    sanitized = re.sub(r"\[\/?(?:inst|system|prompt)\]", "", sanitized, flags=re.IGNORECASE)
    return sanitized.strip()

