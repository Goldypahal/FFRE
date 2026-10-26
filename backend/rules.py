from typing import Dict, Any, Tuple, List, Optional
from collections import deque

def check_velocity(transaction_history: list, current_txn: Dict[str, Any]) -> Tuple[float, str]:
    """
    Checks the velocity of transactions. 
    Rule: If more than 3 transactions in the observation window for this account, flag as high risk.
    """
    if not transaction_history:
        return 0.0, ""

    curr_acct = (
        current_txn.get("account_id") 
        or current_txn.get("nameOrig") 
        or current_txn.get("source_account")
    )
    if curr_acct:
        acct_txns = [
            t for t in transaction_history
            if (t.get("account_id") or t.get("nameOrig") or t.get("source_account")) == curr_acct
        ]
        if len(acct_txns) > 3:
            return 0.3, "High transaction velocity detected (>3 in 1 hour)."
    else:
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

def check_geolocation(location_evidence: Dict[str, Any], customer_home: str = "US") -> Tuple[float, str]:
    """
    Checks for geolocation mismatch.
    Rule: If country does not match customer's home country, add risk.
    """
    if not location_evidence:
        return 0.0, ""
    txn_country = location_evidence.get("country")
    if txn_country and customer_home and txn_country.strip().upper() != customer_home.strip().upper():
        return 0.3, f"Geolocation mismatch: Txn in {txn_country}, Home in {customer_home}."
    return 0.0, ""

def check_graph_cycle(
    transaction_history: List[Dict[str, Any]], 
    current_txn: Dict[str, Any],
    max_depth: int = 5
) -> Tuple[float, str]:
    """
    Checks if current transaction participates in or closes a directed circular money flow.
    E.g. A -> B -> C -> A.

    Safeguards:
    - Enforces tenant isolation if tenant_id is present.
    - Requires cycle length >= 2 (A -> B -> C -> A) to distinguish layering from bilateral refunds (A -> B -> A),
      unless bilateral flow involves large structuring amounts (>= $10,000).
    - Uses path-specific visited tracking to support split transfers and multi-branch networks.
    - Stops traversal strictly at max_depth.
    """
    if not transaction_history or not current_txn:
        return 0.0, ""

    src = current_txn.get("account_id") or current_txn.get("nameOrig") or current_txn.get("source_account")
    dst = current_txn.get("counterparty") or current_txn.get("nameDest") or current_txn.get("dest_account")
    curr_tenant = current_txn.get("tenant_id")
    curr_amt = float(current_txn.get("amount") or 0.0)

    if not src or not dst or src == dst:
        return 0.0, ""

    # Build adjacency with tenant scoping and minimum materiality threshold ($500)
    adj: Dict[str, List[Tuple[str, float]]] = {}
    for tx in transaction_history:
        # Enforce tenant isolation if tenant_id is specified
        if curr_tenant and tx.get("tenant_id") and tx.get("tenant_id") != curr_tenant:
            continue
        s = tx.get("account_id") or tx.get("nameOrig") or tx.get("source_account")
        d = tx.get("counterparty") or tx.get("nameDest") or tx.get("dest_account")
        amt = float(tx.get("amount") or 0.0)
        if s and d and amt >= 500.0:
            if s not in adj:
                adj[s] = []
            adj[s].append((d, amt))

    queue = deque([(dst, [dst])])

    while queue:
        curr, path = queue.popleft()
        if len(path) > max_depth:
            continue

        for neighbor, edge_amt in adj.get(curr, []):
            if neighbor == src:
                cycle_len = len(path)
                cycle_str = " -> ".join([src] + path + [src])
                # Distinguish 1-hop bilateral reversal (A -> B -> A) from multi-hop layering cycle (A -> B -> C -> A)
                if cycle_len == 1:
                    # Bilateral refund / reversal: only flag if large structuring amount
                    if curr_amt >= 10000.0 and edge_amt >= 10000.0:
                        return 0.40, f"High-value bilateral round-trip flow detected ({cycle_str})."
                    # Otherwise legitimate bilateral refund/payment
                    continue
                else:
                    return 0.50, f"Circular flow detected: directed cycle of length {cycle_len} ({cycle_str})."

            if neighbor not in path and len(path) < max_depth:
                queue.append((neighbor, path + [neighbor]))

    return 0.0, ""

def check_scatter_gather(
    transaction_history: List[Dict[str, Any]], 
    current_txn: Dict[str, Any]
) -> Tuple[float, str]:
    """
    Checks if current transaction is part of a scatter-gather typology:
    Fan-out from originator to multiple intermediaries followed by reconsolidation onto a common sink.
    """
    if not transaction_history or not current_txn:
        return 0.0, ""

    src = current_txn.get("account_id") or current_txn.get("nameOrig") or current_txn.get("source_account")
    dst = current_txn.get("counterparty") or current_txn.get("nameDest") or current_txn.get("dest_account")
    curr_amt = float(current_txn.get("amount") or 0.0)

    if not src or not dst or curr_amt < 1000.0:
        return 0.0, ""

    # Check 1: Intermediate Pass-Through / Relay Mule
    for tx in transaction_history:
        d = tx.get("counterparty") or tx.get("nameDest") or tx.get("dest_account")
        if d == src:
            in_amt = float(tx.get("amount") or 0.0)
            if in_amt >= 5000.0 and 0.70 <= (curr_amt / in_amt) <= 1.30:
                in_src = tx.get("account_id") or tx.get("nameOrig") or tx.get("source_account")
                return 0.40, f"Scatter-gather intermediate pass-through detected: {in_src} -> {src} -> {dst}."

    # Check 2: Fan-out Scatter Disbursement
    outflows = set()
    for tx in transaction_history:
        s = tx.get("account_id") or tx.get("nameOrig") or tx.get("source_account")
        d = tx.get("counterparty") or tx.get("nameDest") or tx.get("dest_account")
        amt = float(tx.get("amount") or 0.0)
        if s == src and d and amt >= 5000.0:
            outflows.add(d)
    if dst:
        outflows.add(dst)

    if len(outflows) >= 2 and curr_amt >= 5000.0:
        return 0.35, f"Scatter disbursement detected: {src} transferring to {len(outflows)} distinct accounts."

    return 0.0, ""

def evaluate_rules(state: Dict[str, Any]) -> Tuple[float, list]:
    """
    Evaluates all rules and returns an aggregated rule score (0.0 to 1.0) 
    and a list of triggered rule descriptions.
    """
    total_score = 0.0
    triggered_rules = []
    
    # Check Velocity & History
    history = (
        state.get("transaction_history")
        or state.get("transaction_evidence", {}).get("recent_transactions", [])
    )
    curr_txn = state.get("transaction") or state.get("transaction_evidence", {})

    v_score, v_reason = check_velocity(history, curr_txn)
    if v_score > 0:
        total_score += v_score
        triggered_rules.append(v_reason)

    # Check Amount Anomaly / Structuring Proxy
    # Regulatory context:
    # - 31 CFR § 1010.311 mandates Currency Transaction Reports (CTR) for transactions > $10,000.
    # - The $8,000–$9,999 band is an operational AML investigative heuristic (proxy for intentional
    #   threshold avoidance / smurfing under 31 U.S.C. § 5324), NOT a statutory regulatory threshold.
    if curr_txn and curr_txn.get("amount") is not None:
        try:
            amt = float(curr_txn["amount"])
            if amt >= 20000.0:
                total_score += 0.85
                triggered_rules.append(f"High-value transaction anomaly (${amt:,.2f} >= $20,000.00).")
            elif 10000.0 <= amt < 20000.0:
                total_score += 0.55
                triggered_rules.append(f"CTR reporting threshold transfer (${amt:,.2f} >= $10,000.00).")
            elif 8000.0 <= amt <= 9999.0:
                total_score += 0.65
                triggered_rules.append(f"Structuring threshold pattern detected (${amt:,.2f} between $8,000 and $9,999; CTR avoidance heuristic proxy).")
        except (ValueError, TypeError):
            pass
        
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
    loc_ev = state.get("location_evidence")
    if loc_ev and loc_ev.get("country"):
        cust_home = state.get("customer_evidence", {}).get("home_country") or state.get("customer_evidence", {}).get("country", "US")
        l_score, l_reason = check_geolocation(loc_ev, cust_home)
        if l_score > 0:
            total_score += l_score
            triggered_rules.append(l_reason)

    # Check Graph Cycles and Typologies
    if history and curr_txn:
        c_score, c_reason = check_graph_cycle(history, curr_txn)
        if c_score > 0:
            total_score += c_score
            triggered_rules.append(c_reason)

        sg_score, sg_reason = check_scatter_gather(history, curr_txn)
        if sg_score > 0:
            total_score += sg_score
            triggered_rules.append(sg_reason)
        
    # Cap score at 1.0
    final_score = min(total_score, 1.0)
    
    return final_score, triggered_rules


def is_typology_rule(rule_text: str) -> bool:
    """
    Identifies whether a triggered rule represents an illicit AML money laundering typology
    or fraud pattern (e.g. directed cycle, scatter-gather mule, intentional structuring avoidance),
    as distinguished from routine statutory reporting mandates.
    """
    text = rule_text.lower()
    return any(
        kw in text for kw in [
            "circular flow",
            "bilateral round-trip",
            "scatter-gather",
            "scatter disbursement",
            "structuring threshold pattern",
            "high transaction velocity",
            "geolocation mismatch",
            "historical fraud rate",
            "new device",
            "unknown os",
            "graph cluster anomaly",
            "device-sharing syndicate",
            "ip-sharing syndicate",
            "syndicate ring",
            "directed circular laundering",
        ]
    )


def is_compliance_mandate_rule(rule_text: str) -> bool:
    """
    Identifies whether a triggered rule represents a statutory regulatory reporting mandate
    (such as CTR recordkeeping under 31 CFR § 1010.311 for currency transfers >= $10,000),
    which must be preserved in the audit log but does not inherently establish criminal laundering.
    """
    text = rule_text.lower()
    return any(
        kw in text for kw in [
            "ctr reporting threshold",
            "ctr statutory",
            "31 cfr",
            "statutory recordkeeping",
            "high-value transaction anomaly",
        ]
    )
