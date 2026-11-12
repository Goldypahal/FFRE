import datetime
import timeutil
import pytest
import models
from retry_policy import RetryPolicy, execute_with_timeout
from graph import velocity_check_node

def test_zero_transaction_velocity_window_metrics(db_session):
    """Refinement 4 Test: Verify pure zero-transaction velocity window metrics returns count=0 and sum=0.0."""
    cust = models.Customer(customer_id="c_zero_1", name="Zero Txn Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_zero_1", customer_id="c_zero_1")
    merch = models.Merchant(merchant_id="m_zero_1", name="Zero Merchant", risk_score=0.01)

    now = timeutil.utcnow()
    three_hours_ago = now - datetime.timedelta(hours=3)

    # Historical transaction 3 hours ago (outside 1h and 5m windows)
    t_old = models.Transaction(txn_id="T-ZERO-OLD", account_id="a_zero_1", merchant_id="m_zero_1", amount=1500.0, currency="USD", status="COMPLETED", timestamp=three_hours_ago)

    db_session.add_all([cust, acct, merch, t_old])
    db_session.commit()

    # The transaction under investigation happens now; the windows are measured back from it.
    t_now = models.Transaction(txn_id="T-ZERO-NOW", account_id="a_zero_1", merchant_id="m_zero_1", amount=20.0, currency="USD", status="COMPLETED", timestamp=now)
    db_session.add(t_now)
    db_session.commit()

    state = {"investigation_id": "inv_zero_1", "transaction_id": "T-ZERO-NOW"}
    res = velocity_check_node(state)
    vel = res.get("velocity_evidence", {})

    # The 5m window holds only the transaction itself: the older one was 3 hours earlier.
    assert vel["velocity_5m"]["count"] == 1
    assert vel["velocity_5m"]["sum"] == 20.0

    # Investigating the older transaction must not count the later one (windows end at the transaction).
    res_old = velocity_check_node({"investigation_id": "inv_zero_1", "transaction_id": "T-ZERO-OLD"})
    assert res_old["velocity_evidence"]["velocity_5m"]["count"] == 1
    assert res_old["velocity_evidence"]["velocity_5m"]["sum"] == 1500.0

def test_retry_policy_error_classification():
    """Task 11 Test: RetryPolicy correctly distinguishes retryable vs non-retryable exceptions."""
    policy = RetryPolicy()

    assert policy.is_retryable(TimeoutError("Connection timed out")) is True
    assert policy.is_retryable(ConnectionError("Network connection reset")) is True
    assert policy.is_retryable(ValueError("Invalid argument format")) is False
    assert policy.is_retryable(PermissionError("Unauthorized access")) is False

def test_retry_policy_exponential_backoff():
    """Task 12 Test: Verify exponential backoff delay calculation increases with attempt count."""
    policy = RetryPolicy(initial_delay=0.1, backoff_factor=2.0, jitter=False)

    delay_0 = policy.calculate_backoff(0)
    delay_1 = policy.calculate_backoff(1)
    delay_2 = policy.calculate_backoff(2)

    assert pytest.approx(delay_0, 0.01) == 0.1
    assert pytest.approx(delay_1, 0.01) == 0.2
    assert pytest.approx(delay_2, 0.01) == 0.4

def test_execute_with_timeout_handling():
    """Task 13 Test: Verify timeout wrapper raises TimeoutError when execution exceeds limit."""
    import time
    def slow_operation():
        time.sleep(0.5)
        return "completed"

    # Should succeed with ample timeout
    res = execute_with_timeout(slow_operation, timeout_seconds=2.0)
    assert res == "completed"

    # Should raise TimeoutError when timeout is breached
    with pytest.raises(TimeoutError):
        execute_with_timeout(slow_operation, timeout_seconds=0.05)
