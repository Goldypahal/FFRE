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

def test_check_graph_cycle_detected():
    """Verify directed circular transaction flow is flagged."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0},
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 12000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.50
    assert "Circular flow detected" in reason
    assert "ACC_A -> ACC_B -> ACC_C -> ACC_A" in reason

def test_check_graph_cycle_no_cycle():
    """Verify non-cyclic linear flow is not flagged as cycle."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 1000.0},
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 900.0},
    ]
    curr_txn = {"account_id": "ACC_C", "counterparty": "ACC_D", "amount": 800.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score == 0.0
    assert reason == ""

def test_check_scatter_gather_detected():
    """Verify rapid intermediate pass-through mule is flagged."""
    from rules import check_scatter_gather
    history = [
        {"account_id": "ACC_SRC", "counterparty": "ACC_MULE", "amount": 15000.0},
    ]
    curr_txn = {"account_id": "ACC_MULE", "counterparty": "ACC_DST", "amount": 14500.0}
    score, reason = check_scatter_gather(history, curr_txn)
    assert score >= 0.40
    assert "Scatter-gather intermediate pass-through detected" in reason

def test_evaluate_rules_with_graph_cycle():
    """Verify evaluate_rules incorporates graph cycle into overall score."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_A",
            "counterparty": "ACC_B",
            "amount": 12000.0,
            "currency": "USD",
            "recent_transactions": [
                {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0},
                {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0},
            ]
        },
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "device_evidence": {"new_device": False},
        "location_evidence": {"country": "US"}
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.50
    assert any("Circular flow detected" in r for r in reasons)

def test_evaluate_rules_structuring_threshold():
    """Verify structuring threshold rule flags transactions between $8,000 and $9,999."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_STRUCT_1",
            "amount": 9500.0,
            "currency": "USD",
        }
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.65
    assert any("Structuring threshold pattern detected" in r for r in reasons)

def test_evaluate_rules_high_value_anomaly():
    """Verify transactions exceeding $20,000 trigger high-value anomaly."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_LARGE_1",
            "amount": 45000.0,
            "currency": "USD",
        }
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.85
    assert any("High-value transaction anomaly" in r for r in reasons)


def test_check_graph_cycle_cross_tenant_isolation():
    """Verify cross-tenant edges are strictly isolated and do not create false cycles."""
    from rules import check_graph_cycle
    # Tenant 1 has ACC_A -> ACC_B
    # Tenant 2 has ACC_B -> ACC_C and ACC_C -> ACC_A
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0, "tenant_id": "TENANT_2"},
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0, "tenant_id": "TENANT_2"},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 12000.0, "tenant_id": "TENANT_1"}
    score, reason = check_graph_cycle(history, curr_txn)
    # Because edges belong to TENANT_2, TENANT_1 should see no cycle
    assert score == 0.0
    assert reason == ""


def test_check_graph_cycle_bilateral_refund():
    """Verify ordinary bilateral flow (A -> B -> A) under $10,000 is treated as benign refund."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_MERCHANT", "counterparty": "ACC_BUYER", "amount": 750.0},
    ]
    # Current transaction: BUYER had paid MERCHANT earlier, now MERCHANT returns 750 (or vice versa)
    curr_txn = {"account_id": "ACC_BUYER", "counterparty": "ACC_MERCHANT", "amount": 750.0}
    score, reason = check_graph_cycle(history, curr_txn)
    # Should not trigger circular laundering cycle
    assert score == 0.0
    assert reason == ""


def test_check_graph_cycle_bilateral_large_roundtrip():
    """Verify large bilateral round-trip (>= $10,000 each way) is flagged as high-value round trip."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_A", "amount": 25000.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 25000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.40
    assert "High-value bilateral round-trip flow detected" in reason


def test_check_graph_cycle_split_transfer():
    """Verify split transfer paths converging to close a cycle are detected."""
    from rules import check_graph_cycle
    history = [
        # Split: A sends to B1 and B2
        {"account_id": "ACC_A", "counterparty": "ACC_B1", "amount": 6000.0},
        {"account_id": "ACC_A", "counterparty": "ACC_B2", "amount": 6000.0},
        # B1 and B2 aggregate to C
        {"account_id": "ACC_B1", "counterparty": "ACC_C", "amount": 5900.0},
        {"account_id": "ACC_B2", "counterparty": "ACC_C", "amount": 5900.0},
        # C sends back to A
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11500.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B1", "amount": 6000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.50
    assert "Circular flow detected" in reason


def test_check_graph_cycle_depth_limit():
    """Verify cycle exceeding max_depth (e.g. 6 hops when max_depth=5) is not traversed beyond limit."""
    from rules import check_graph_cycle
    # 6-hop path: A -> B -> C -> D -> E -> F -> A
    history = [
        {"account_id": "B", "counterparty": "C", "amount": 5000.0},
        {"account_id": "C", "counterparty": "D", "amount": 5000.0},
        {"account_id": "D", "counterparty": "E", "amount": 5000.0},
        {"account_id": "E", "counterparty": "F", "amount": 5000.0},
        {"account_id": "F", "counterparty": "A", "amount": 5000.0},
    ]
    curr_txn = {"account_id": "A", "counterparty": "B", "amount": 5000.0}
    # With max_depth=4, the path [B, C, D, E] cannot reach F -> A
    score_shallow, _ = check_graph_cycle(history, curr_txn, max_depth=4)
    assert score_shallow == 0.0

    # With max_depth=5, path [B, C, D, E, F] finds F -> A
    score_deep, reason_deep = check_graph_cycle(history, curr_txn, max_depth=5)
    assert score_deep >= 0.50
    assert "Circular flow detected" in reason_deep




def test_check_graph_cycle_detected():
    """Verify directed circular transaction flow is flagged."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0},
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 12000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.50
    assert "Circular flow detected" in reason
    assert "ACC_A -> ACC_B -> ACC_C -> ACC_A" in reason

def test_check_graph_cycle_no_cycle():
    """Verify non-cyclic linear flow is not flagged as cycle."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 1000.0},
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 900.0},
    ]
    curr_txn = {"account_id": "ACC_C", "counterparty": "ACC_D", "amount": 800.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score == 0.0
    assert reason == ""

def test_check_scatter_gather_detected():
    """Verify rapid intermediate pass-through mule is flagged."""
    from rules import check_scatter_gather
    history = [
        {"account_id": "ACC_SRC", "counterparty": "ACC_MULE", "amount": 15000.0},
    ]
    curr_txn = {"account_id": "ACC_MULE", "counterparty": "ACC_DST", "amount": 14500.0}
    score, reason = check_scatter_gather(history, curr_txn)
    assert score >= 0.40
    assert "Scatter-gather intermediate pass-through detected" in reason

def test_evaluate_rules_with_graph_cycle():
    """Verify evaluate_rules incorporates graph cycle into overall score."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_A",
            "counterparty": "ACC_B",
            "amount": 12000.0,
            "currency": "USD",
            "recent_transactions": [
                {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0},
                {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0},
            ]
        },
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "device_evidence": {"new_device": False},
        "location_evidence": {"country": "US"}
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.50
    assert any("Circular flow detected" in r for r in reasons)

def test_evaluate_rules_structuring_threshold():
    """Verify structuring threshold rule flags transactions between $8,000 and $9,999."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_STRUCT_1",
            "amount": 9500.0,
            "currency": "USD",
        }
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.65
    assert any("Structuring threshold pattern detected" in r for r in reasons)

def test_evaluate_rules_high_value_anomaly():
    """Verify transactions exceeding $20,000 trigger high-value anomaly."""
    state = {
        "transaction_evidence": {
            "account_id": "ACC_LARGE_1",
            "amount": 45000.0,
            "currency": "USD",
        }
    }
    score, reasons = evaluate_rules(state)
    assert score >= 0.85
    assert any("High-value transaction anomaly" in r for r in reasons)


def test_check_graph_cycle_cross_tenant_isolation():
    """Verify cross-tenant edges are strictly isolated and do not create false cycles."""
    from rules import check_graph_cycle
    # Tenant 1 has ACC_A -> ACC_B
    # Tenant 2 has ACC_B -> ACC_C and ACC_C -> ACC_A
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_C", "amount": 12000.0, "tenant_id": "TENANT_2"},
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11800.0, "tenant_id": "TENANT_2"},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 12000.0, "tenant_id": "TENANT_1"}
    score, reason = check_graph_cycle(history, curr_txn)
    # Because edges belong to TENANT_2, TENANT_1 should see no cycle
    assert score == 0.0
    assert reason == ""


def test_check_graph_cycle_bilateral_refund():
    """Verify ordinary bilateral flow (A -> B -> A) under $10,000 is treated as benign refund."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_MERCHANT", "counterparty": "ACC_BUYER", "amount": 750.0},
    ]
    # Current transaction: BUYER had paid MERCHANT earlier, now MERCHANT returns 750 (or vice versa)
    curr_txn = {"account_id": "ACC_BUYER", "counterparty": "ACC_MERCHANT", "amount": 750.0}
    score, reason = check_graph_cycle(history, curr_txn)
    # Should not trigger circular laundering cycle
    assert score == 0.0
    assert reason == ""


def test_check_graph_cycle_bilateral_large_roundtrip():
    """Verify large bilateral round-trip (>= $10,000 each way) is flagged as high-value round trip."""
    from rules import check_graph_cycle
    history = [
        {"account_id": "ACC_B", "counterparty": "ACC_A", "amount": 25000.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B", "amount": 25000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.40
    assert "High-value bilateral round-trip flow detected" in reason


def test_check_graph_cycle_split_transfer():
    """Verify split transfer paths converging to close a cycle are detected."""
    from rules import check_graph_cycle
    history = [
        # Split: A sends to B1 and B2
        {"account_id": "ACC_A", "counterparty": "ACC_B1", "amount": 6000.0},
        {"account_id": "ACC_A", "counterparty": "ACC_B2", "amount": 6000.0},
        # B1 and B2 aggregate to C
        {"account_id": "ACC_B1", "counterparty": "ACC_C", "amount": 5900.0},
        {"account_id": "ACC_B2", "counterparty": "ACC_C", "amount": 5900.0},
        # C sends back to A
        {"account_id": "ACC_C", "counterparty": "ACC_A", "amount": 11500.0},
    ]
    curr_txn = {"account_id": "ACC_A", "counterparty": "ACC_B1", "amount": 6000.0}
    score, reason = check_graph_cycle(history, curr_txn)
    assert score >= 0.50
    assert "Circular flow detected" in reason


def test_check_graph_cycle_depth_limit():
    """Verify cycle exceeding max_depth (e.g. 6 hops when max_depth=5) is not traversed beyond limit."""
    from rules import check_graph_cycle
    # 6-hop path: A -> B -> C -> D -> E -> F -> A
    history = [
        {"account_id": "B", "counterparty": "C", "amount": 5000.0},
        {"account_id": "C", "counterparty": "D", "amount": 5000.0},
        {"account_id": "D", "counterparty": "E", "amount": 5000.0},
        {"account_id": "E", "counterparty": "F", "amount": 5000.0},
        {"account_id": "F", "counterparty": "A", "amount": 5000.0},
    ]
    curr_txn = {"account_id": "A", "counterparty": "B", "amount": 5000.0}
    # With max_depth=4, the path [B, C, D, E] cannot reach F -> A
    score_shallow, _ = check_graph_cycle(history, curr_txn, max_depth=4)
    assert score_shallow == 0.0

    # With max_depth=5, path [B, C, D, E, F] finds F -> A
    score_deep, reason_deep = check_graph_cycle(history, curr_txn, max_depth=5)
    assert score_deep >= 0.50
    assert "Circular flow detected" in reason_deep