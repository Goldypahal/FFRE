from guardrails import validate_claims

def test_validate_claims_valid():
    """Test validation of properly grounded claims"""
    explanation = "The transaction amount is 100.00 USD and the customer KYC status is VERIFIED."
    evidence_bundle = {
        "customer": {"kyc_status": "VERIFIED"},
        "transaction": {"amount": 100.0, "currency": "USD"}
    }

    is_valid, unsupported_claims = validate_claims(explanation, evidence_bundle)

    # Both claims should be supported
    assert is_valid == True
    assert len(unsupported_claims) == 0

def test_validate_claims_invalid():
    """Test validation of unsupported claims"""
    explanation = "The transaction amount is 100.00 USD and the customer is from a high-risk country."
    evidence_bundle = {
        "customer": {"kyc_status": "VERIFIED"},
        "transaction": {"amount": 100.0, "currency": "USD"}
        # No country information in evidence
    }

    is_valid, unsupported_claims = validate_claims(explanation, evidence_bundle)

    # One claim should be unsupported (about country)
    assert is_valid == False
    assert len(unsupported_claims) > 0
    # Check that the unsupported claim mentions the country
    assert any("country" in claim.lower() for claim in unsupported_claims)

def test_validate_claims_empty():
    """Test validation with empty explanation"""
    explanation = ""
    evidence_bundle = {}

    is_valid, unsupported_claims = validate_claims(explanation, evidence_bundle)

    # Empty explanation should be valid (no claims to validate)
    assert is_valid == True
    assert len(unsupported_claims) == 0

def test_validate_claims_complex():
    """Test validation with complex explanation"""
    explanation = """
    The transaction involves a high amount of 5000.00 USD.
    The customer has been KYC verified and is in the LOW risk tier.
    The merchant is Electronics Store which has a historical fraud rate of 0.05.
    The transaction occurred in the US which matches the customer's home country.
    """
    evidence_bundle = {
        "customer": {"kyc_status": "VERIFIED", "risk_tier": "LOW"},
        "transaction": {"amount": 5000.0, "currency": "USD"},
        "merchant": {"name": "Electronics Store", "historical_fraud_rate": 0.05},
        "location": {"country": "US"}
    }

    is_valid, unsupported_claims = validate_claims(explanation, evidence_bundle)

    # All claims should be supported
    assert is_valid == True
    assert len(unsupported_claims) == 0