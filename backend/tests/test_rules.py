from rules import evaluate_rules

def test_evaluate_rules_low_risk():
    """Test rule evaluation for low risk transaction"""
    state = {
        "transaction_evidence": {"amount": 50.0, "currency": "USD", "status": "COMPLETED"},
        "customer_evidence": {"kyc_status": "VERIFIED", "risk_tier": "LOW"},
        "merchant_evidence": {"historical_fraud_rate": 0.01},
        "device_evidence": {"new_device": False},
        "location_evidence": {"country": "US"}
    }

    score, reasons = evaluate_rules(state)

    # Should be low risk
    assert score >= 0.0
    assert score < 0.3  # Low risk threshold
    assert isinstance(reasons, list)

def test_evaluate_rules_high_risk():
    """Test rule evaluation for high risk transaction"""
    state = {
        "transaction_evidence": {"amount": 5000.0, "currency": "USD", "status": "PENDING"},
        "customer_evidence": {"kyc_status": "PENDING", "risk_tier": "HIGH"},
        "merchant_evidence": {"historical_fraud_rate": 0.8},
        "device_evidence": {"new_device": True, "os": "Unknown"},
        "location_evidence": {"country": "RU", "ip": "192.168.1.1"}
    }

    score, reasons = evaluate_rules(state)

    # Should be high risk
    assert score >= 0.7  # High risk threshold
    assert isinstance(reasons, list)
    assert len(reasons) > 0  # Should have triggered some rules

def test_evaluate_rules_medium_risk():
    """Test rule evaluation for medium risk transaction"""
    state = {
        "transaction_evidence": {"amount": 500.0, "currency": "USD", "status": "PENDING"},
        "customer_evidence": {"kyc_status": "VERIFIED", "risk_tier": "MEDIUM"},
        "merchant_evidence": {"historical_fraud_rate": 0.1},
        "device_evidence": {"new_device": False},
        "location_evidence": {"country": "CA"}
    }

    score, reasons = evaluate_rules(state)

    # Should be medium risk
    assert score >= 0.3
    assert score < 0.7
    assert isinstance(reasons, list)

def test_evaluate_rules_empty_state():
    """Test rule evaluation with minimal state"""
    state = {
        "transaction_evidence": {},
        "customer_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {}
    }

    score, reasons = evaluate_rules(state)

    # Should handle empty states gracefully
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(reasons, list)