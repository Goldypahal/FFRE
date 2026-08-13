from typing import Dict, Any, Tuple, List

def validate_claims(draft_explanation: str, evidence_bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the claims in the draft explanation are grounded in the evidence.
    This simulates a secondary LLM call acting as a strict guardrail (FO-6).
    """
    if not draft_explanation:
        return True, []

    unsupported_claims = []
    draft_lower = draft_explanation.lower()

    # Flatten evidence values for a simplistic mock groundedness check
    evidence_strings = []
    for key, value in evidence_bundle.items():
        if isinstance(value, dict):
            for k, v in value.items():
                evidence_strings.append(str(v).lower())
        elif isinstance(value, list):
            for item in value:
                evidence_strings.append(str(item).lower())
        else:
            evidence_strings.append(str(value).lower())

    # Mock heuristic: If the draft contains specific high-risk keywords, 
    # ensure those concepts exist in the evidence.
    if "unknown os" in draft_lower and "unknown" not in evidence_strings:
        unsupported_claims.append("Claim about 'unknown OS' is not found in device evidence.")
    
    if "highrisk electronics" in draft_lower and "highrisk electronics" not in evidence_strings:
        unsupported_claims.append("Claim about merchant name 'HighRisk Electronics' is not supported.")
        
    if "country" in draft_lower:
        # Check if country exists in the evidence bundle
        has_country = False
        for key, val in evidence_bundle.items():
            if isinstance(val, dict) and ("country" in val or "country" in [k.lower() for k in val.keys()]):
                has_country = True
            elif key.lower() == "country":
                has_country = True
        if not has_country:
            unsupported_claims.append("Claim about country is not supported by evidence.")

    # Introduce a deterministic hallucination check for testing
    if "hallucinated_fact" in draft_lower:
        unsupported_claims.append("Detected hallucinated fact not present in evidence.")

    is_validated = len(unsupported_claims) == 0
    return is_validated, unsupported_claims
