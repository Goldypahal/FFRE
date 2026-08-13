from typing import Dict, Any, Tuple

def check_velocity(transaction_history: list, current_txn: Dict[str, Any]) -> Tuple[float, str]:
    """
    Checks the velocity of transactions. 
    Rule: If more than 3 transactions in the last hour, flag as high risk.
    """
    if len(transaction_history) > 3:
        return 0.3, "High transaction velocity detected (>3 in 1 hour)."
    return 0.0, ""

def check_device(device_evidence: Dict[str, Any]) -> Tuple[float, str]:
    """
    Checks device heuristics.
    Rule: If device is new or OS is unknown, add risk penalty.
    """
    score = 0.0
    reasons = []
    if device_evidence.get("new_device"):
        score += 0.2
        reasons.append("New device detected.")
    if device_evidence.get("os") == "Unknown":
        score += 0.1
        reasons.append("Unknown OS.")
    
    return score, " ".join(reasons)

def check_merchant(merchant_evidence: Dict[str, Any]) -> Tuple[float, str]:
    """
    Checks merchant risk.
    Rule: Direct penalty based on historical fraud rate.
    """
    rate = merchant_evidence.get("historical_fraud_rate", 0.0)
    if rate > 0.1:
        return 0.2, f"Merchant has high historical fraud rate ({rate*100}%)."
    return 0.0, ""

def check_geolocation(location_evidence: Dict[str, Any], customer_home: str) -> Tuple[float, str]:
    """
    Checks for geolocation mismatch.
    Rule: If country does not match customer's home country, add risk.
    """
    txn_country = location_evidence.get("country")
    if txn_country and txn_country != customer_home:
        return 0.3, f"Geolocation mismatch: Txn in {txn_country}, Home in {customer_home}."
    return 0.0, ""

def evaluate_rules(state: Dict[str, Any]) -> Tuple[float, list]:
    """
    Evaluates all rules and returns an aggregated rule score (0.0 to 1.0) 
    and a list of triggered rule descriptions.
    """
    total_score = 0.0
    triggered_rules = []
    
    # Check Velocity
    # Assuming transaction_evidence has a 'history' key or we just pass a mock list
    history = state.get("transaction_evidence", {}).get("recent_transactions", [])
    v_score, v_reason = check_velocity(history, state.get("transaction_evidence", {}))
    if v_score > 0:
        total_score += v_score
        triggered_rules.append(v_reason)
        
    # Check Device
    d_score, d_reason = check_device(state.get("device_evidence", {}))
    if d_score > 0:
        total_score += d_score
        triggered_rules.append(d_reason)
        
    # Check Merchant
    m_score, m_reason = check_merchant(state.get("merchant_evidence", {}))
    if m_score > 0:
        total_score += m_score
        triggered_rules.append(m_reason)
        
    # Check Geolocation
    l_score, l_reason = check_geolocation(
        state.get("location_evidence", {"country": "RU"}), 
        state.get("customer_evidence", {}).get("home_country", "US")
    )
    if l_score > 0:
        total_score += l_score
        triggered_rules.append(l_reason)
        
    # Cap score at 1.0
    final_score = min(total_score, 1.0)
    
    return final_score, triggered_rules
