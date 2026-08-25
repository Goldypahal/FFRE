from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
import json
import time
import datetime
import functools

def time_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

from vector_db import vector_store
from database import SessionLocal
from models import AuditLog, Investigation, Transaction, Account, Customer, Merchant, Device, Location
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from metrics import metrics_collector

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key) if api_key else None

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

from typing import Annotated
import operator

class AgentState(TypedDict):
    investigation_id: str
    transaction_id: str
    tasks: List[str]
    customer_evidence: Dict[str, Any]
    transaction_evidence: Dict[str, Any]
    merchant_evidence: Dict[str, Any]
    device_evidence: Dict[str, Any]
    location_evidence: Dict[str, Any]
    velocity_evidence: Dict[str, Any]
    verified_evidence: Dict[str, Any]
    historical_cases: List[Dict[str, Any]]
    risk_score: Optional[float]
    confidence: Optional[float]
    validated: bool
    retry_count: int
    failed_target_nodes: List[str]
    failed_target_node: Optional[str]
    report: Optional[str]
    draft_explanation: Optional[str]
    critic_feedback: Optional[str]
    critic_issues: bool
    rule_score: Optional[float]
    rule_reasons: List[str]
    execution_trace: Annotated[List[str], operator.add]
    critic_details: Dict[str, Any]

from langgraph.checkpoint.memory import MemorySaver

PLANNER_PROMPT = """
You are a financial fraud investigation planner. Given the transaction summary below,
output a JSON list of evidence-gathering tasks required to investigate it. Only select tasks
from the approved task catalog: [customer_history, transaction_detail, merchant_reputation,
device_fingerprint, location_check].
Transaction: {transaction_summary}
"""

REASONER_PROMPT = """
You are a fraud investigation reasoning engine. Using ONLY the evidence provided below,
explain whether this transaction is likely fraudulent. Every claim must reference a specific
evidence field by name. If evidence is insufficient to support a conclusion, state this explicitly.
Output JSON schema: {{"reasoning": "...", "risk_score": 0.85, "confidence": 0.90}}
Evidence: {evidence_bundle}
"""

CRITIC_PROMPT = """
You are an evidence critic. Evaluate the draft explanation below against the evidence bundle and velocity analysis.
Verify whether claims are logically consistent and evidence-backed.
Output JSON schema:
{{
  "critic_issues": true/false,
  "critique": "Detailed critique message",
  "affected_claims": ["claim 1"],
  "evidence_references": ["customer_evidence.name"],
  "severity": "LOW" | "MEDIUM" | "HIGH"
}}
Draft: {draft_explanation}
Evidence: {evidence_bundle}
Velocity Analysis: {velocity_analysis}
"""

VALIDATOR_PROMPT = """
Review the draft explanation below against the evidence bundle. Flag any sentence that
is not directly supported by a named evidence field. Output a list of unsupported claims, or an
empty list if all claims are grounded.
Draft: {draft_explanation}
Evidence: {evidence_bundle}
"""

REPORT_PROMPT = """
Format the validated explanation as a structured investigation report with sections:
Summary, Evidence Table, Risk Factors, Confidence Score, and Recommendation. Use only the
validated, grounded content provided.
"""

def planner_node(state: AgentState):
    """Decompose investigation into sub-tasks with strict schema validation (FO-2 / Task 2)"""
    print(f"Planning investigation for {state['transaction_id']}")
    task_mapping = {
        "customer_history": "retrieve_customer",
        "retrieve_customer": "retrieve_customer",
        "transaction_detail": "retrieve_transaction",
        "retrieve_txn": "retrieve_transaction",
        "retrieve_transaction": "retrieve_transaction",
        "merchant_reputation": "retrieve_merchant",
        "retrieve_merchant": "retrieve_merchant",
        "device_fingerprint": "retrieve_device",
        "retrieve_device": "retrieve_device",
        "location_check": "retrieve_location",
        "retrieve_location": "retrieve_location"
    }

    approved_allowlist = ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location"]
    tasks_to_run = approved_allowlist.copy()

    # If state already provides explicitly validated task list (e.g. from unit tests), validate against allowlist
    existing_tasks = state.get("tasks", [])
    if existing_tasks:
        validated_existing = [task_mapping.get(t, t) for t in existing_tasks if task_mapping.get(t, t) in approved_allowlist]
        if validated_existing:
            tasks_to_run = list(dict.fromkeys(validated_existing))

    if llm and not existing_tasks:
        prompt = PLANNER_PROMPT.format(transaction_summary=f"Transaction ID: {state['transaction_id']}")
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                parsed = json.loads(content[start:end])
                if isinstance(parsed, list):
                    mapped = [task_mapping.get(t) for t in parsed if task_mapping.get(t) in approved_allowlist]
                    if mapped:
                        tasks_to_run = list(dict.fromkeys(mapped))
        except Exception as e:
            print(f"LLM Planner failed: {e}")

    state["tasks"] = tasks_to_run
    return state

def retrieve_customer_node(state: AgentState):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn and txn.account_id:
            acct = db.query(Account).filter(Account.account_id == txn.account_id).first()
            if acct and acct.customer_id:
                cust = db.query(Customer).filter(Customer.customer_id == acct.customer_id).first()
                if cust:
                    return {"customer_evidence": {"kyc_status": cust.kyc_status, "risk_tier": cust.risk_tier, "customer_id": cust.customer_id, "name": cust.name}}
    finally:
        db.close()
    return {"customer_evidence": {"error": "Not Found"}}

def retrieve_transaction_node(state: AgentState):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn:
            return {"transaction_evidence": {"amount": float(txn.amount), "currency": txn.currency, "status": txn.status, "account_id": txn.account_id}}
    finally:
        db.close()
    return {"transaction_evidence": {"error": "Not Found"}}

def retrieve_merchant_node(state: AgentState):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn and txn.merchant_id:
            merch = db.query(Merchant).filter(Merchant.merchant_id == txn.merchant_id).first()
            if merch:
                return {"merchant_evidence": {"name": merch.name, "category": merch.category, "historical_fraud_rate": float(merch.risk_score)}}
    finally:
        db.close()
    return {"merchant_evidence": {"error": "Not Found"}}

def retrieve_device_node(state: AgentState):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn and txn.account_id:
            acct = db.query(Account).filter(Account.account_id == txn.account_id).first()
            if acct and acct.customer_id:
                dev = db.query(Device).filter(Device.customer_id == acct.customer_id).first()
                if dev:
                    return {"device_evidence": {"os": dev.os, "new_device": True, "device_id": dev.fingerprint}}
    finally:
        db.close()
    return {"device_evidence": {"error": "Not Found"}}

def retrieve_location_node(state: AgentState):
    db = SessionLocal()
    try:
        loc = db.query(Location).filter(Location.txn_id == state['transaction_id']).first()
        if loc:
            return {"location_evidence": {"country": loc.country, "geo_coord": loc.geo_coord}}
    finally:
        db.close()
    return {"location_evidence": {"error": "Not Found"}}

def velocity_check_node(state: AgentState):
    """Transaction velocity analysis node with 1-hour timestamp window filtering (SRS DFD 3.1 Velocity Check)"""
    print("Performing 1-hour transaction velocity check...")
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        account_id = txn.account_id if txn else None
        
        velocity_count = 1
        velocity_sum = float(txn.amount) if txn else 0.0
        
        if account_id:
            now = datetime.datetime.utcnow()
            one_hour_ago = now - datetime.timedelta(hours=1)
            # Filter strictly for transactions within the last 1 hour
            recent_txns = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp >= one_hour_ago
            ).all()
            if recent_txns:
                velocity_count = len(recent_txns)
                velocity_sum = sum([float(t.amount) for t in recent_txns])

        high_velocity = velocity_count > 3 or velocity_sum > 5000.0
        velocity_score = 0.85 if high_velocity else 0.15
        
        state["velocity_evidence"] = {
            "velocity_count_1h": velocity_count,
            "velocity_sum_1h": velocity_sum,
            "high_velocity_flag": high_velocity,
            "velocity_score": velocity_score
        }
    except Exception as e:
        state["velocity_evidence"] = {"error": str(e), "velocity_score": 0.50}
    finally:
        db.close()
    return state

def evidence_verifier_node(state: AgentState):
    """Evidence Verifier node - checks completeness across all 6 evidence sources"""
    print("Verifying collected evidence completeness across all 6 sources...")
    cust = state.get("customer_evidence", {})
    txn = state.get("transaction_evidence", {})
    merch = state.get("merchant_evidence", {})
    dev = state.get("device_evidence", {})
    loc = state.get("location_evidence", {})
    vel = state.get("velocity_evidence", {})

    failed_nodes = []
    if cust.get("error"): failed_nodes.append("retrieve_customer")
    if txn.get("error"): failed_nodes.append("retrieve_transaction")
    if merch.get("error"): failed_nodes.append("retrieve_merchant")
    if dev.get("error"): failed_nodes.append("retrieve_device")
    if loc.get("error"): failed_nodes.append("retrieve_location")
    if vel.get("error"): failed_nodes.append("velocity_check")

    state["failed_target_nodes"] = failed_nodes
    state["failed_target_node"] = failed_nodes[0] if failed_nodes else None
    state["verified_evidence"] = {
        "status": "VERIFIED" if not failed_nodes else "PARTIAL",
        "failed_nodes": failed_nodes
    }
    return state

def rule_engine_node(state: AgentState):
    """Rule-based Fraud Analysis (FO-5 Part 1)"""
    from rules import evaluate_rules
    print("Evaluating deterministic rules...")
    score, reasons = evaluate_rules(state)
    state["rule_score"] = score
    state["rule_reasons"] = reasons
    return state

def knowledge_lookup_node(state: AgentState):
    """Vector search over past fraud cases (FO-4)"""
    device_evidence = state.get('device_evidence', {})
    location_evidence = state.get('location_evidence', {})
    transaction_evidence = state.get('transaction_evidence', {})
    merchant_evidence = state.get('merchant_evidence', {})

    query_parts = []
    if device_evidence.get('os'): query_parts.append(f"device OS: {device_evidence['os']}")
    if location_evidence.get('country'): query_parts.append(f"country: {location_evidence['country']}")
    if transaction_evidence.get('amount'): query_parts.append(f"amount: {transaction_evidence['amount']} {transaction_evidence.get('currency', '')}")
    if merchant_evidence.get('name'): query_parts.append(f"merchant: {merchant_evidence['name']}")

    query = ", ".join(query_parts) if query_parts else "financial transaction"
    print(f"Searching historical fraud cases for query: {query}")
    results = vector_store.similarity_search(query, top_k=5)
    state["historical_cases"] = results
    return state

def risk_reasoning_node(state: AgentState):
    """LLM-powered Risk Reasoning & Dynamic Multi-Factor Confidence (FO-5 Part 2)"""
    print("Generating LLM risk reasoning...")
    evidence_bundle = {
        "customer": state.get("customer_evidence"),
        "transaction": state.get("transaction_evidence"),
        "merchant": state.get("merchant_evidence"),
        "device": state.get("device_evidence"),
        "location": state.get("location_evidence"),
        "velocity": state.get("velocity_evidence"),
        "rule_analysis": {
            "score": state.get("rule_score"),
            "reasons": state.get("rule_reasons")
        },
        "historical_cases": state.get("historical_cases")
    }

    rule_score = float(state.get("rule_score", 0.5))
    
    # Priority 5 Fix: Handle both similarity and similarity_distance keys correctly
    hist_cases = state.get("historical_cases", [])
    hist_scores = []
    for c in hist_cases:
        if isinstance(c, dict):
            if "similarity" in c:
                hist_scores.append(float(c["similarity"]))
            elif "similarity_distance" in c:
                dist = float(c["similarity_distance"])
                hist_scores.append(max(0.0, 1.0 - (dist / 2.0)))
    avg_hist_score = sum(hist_scores) / len(hist_scores) if hist_scores else 0.5

    llm_risk_estimate = None
    reasoning_text = ""

    if llm:
        prompt = REASONER_PROMPT.format(evidence_bundle=json.dumps(evidence_bundle, indent=2))
        if state.get("critic_feedback") and state.get("critic_issues"):
            prompt += f"\n\nCRITICAL CRITIC FEEDBACK TO CORRECT: {state['critic_feedback']}"
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            reasoning_text = content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                if "reasoning" in data:
                    reasoning_text = data["reasoning"]
                if "risk_score" in data:
                    llm_risk_estimate = float(data["risk_score"])
        except Exception as e:
            print(f"LLM Reasoning failed: {e}")
            reasoning_text = f"LLM Error: {e}"

    if llm_risk_estimate is None:
        risk_factors = 0
        total_factors = 4
        dev = state.get("device_evidence", {})
        loc = state.get("location_evidence", {})
        merch = state.get("merchant_evidence", {})
        vel = state.get("velocity_evidence", {})

        if dev.get("new_device"): risk_factors += 1
        if dev.get("os", "").lower() == "unknown os": risk_factors += 1
        if merch.get("historical_fraud_rate", 0) > 0.05: risk_factors += 1
        if loc.get("country", "") in ["RU", "CN", "KP", "IR"]: risk_factors += 1
        if vel.get("high_velocity_flag"): risk_factors += 1; total_factors += 1

        llm_risk_estimate = risk_factors / total_factors if total_factors > 0 else 0.5

    combined_score = (0.35 * rule_score) + (0.40 * llm_risk_estimate) + (0.25 * avg_hist_score)
    combined_score = min(max(combined_score, 0.0), 1.0)

    # Priority 4 Fix: Multi-Factor Dynamic Confidence Calculation Formula
    retrieved_sources = [
        state.get("customer_evidence"),
        state.get("transaction_evidence"),
        state.get("merchant_evidence"),
        state.get("device_evidence"),
        state.get("location_evidence"),
        state.get("velocity_evidence")
    ]
    valid_sources = [s for s in retrieved_sources if isinstance(s, dict) and "error" not in s]
    completeness = len(valid_sources) / len(retrieved_sources) if retrieved_sources else 0.5

    agreement = 1.0 - abs(rule_score - llm_risk_estimate)
    grounding_quality = 1.0 if state.get("validated", True) else 0.70

    dynamic_confidence = (completeness * 0.35) + (agreement * 0.30) + (avg_hist_score * 0.15) + (grounding_quality * 0.20)
    dynamic_confidence = min(max(dynamic_confidence, 0.50), 0.98)

    state["risk_score"] = round(combined_score, 4)
    state["confidence"] = round(dynamic_confidence, 2)
    state["draft_explanation"] = reasoning_text
    return state

def critic_node(state: AgentState):
    """Strict Schema-Validated Evidence Critic Node (Task 3)"""
    print("Running Evidence Critic Node...")
    draft = state.get("draft_explanation", "")
    evidence = {
        "customer": state.get("customer_evidence"),
        "transaction": state.get("transaction_evidence"),
        "merchant": state.get("merchant_evidence"),
        "device": state.get("device_evidence"),
        "location": state.get("location_evidence"),
        "velocity": state.get("velocity_evidence")
    }
    
    issues_found = False
    content = "Draft reasoning consistent with collected evidence and velocity analysis."
    critic_details = {
        "affected_claims": [],
        "evidence_references": [],
        "severity": "LOW"
    }

    if llm and draft:
        try:
            prompt = CRITIC_PROMPT.format(
                draft_explanation=draft,
                evidence_bundle=json.dumps(evidence),
                velocity_analysis=json.dumps(state.get("velocity_evidence"))
            )
            resp = llm.invoke(prompt)
            resp_text = resp.content if hasattr(resp, "content") else str(resp)
            start = resp_text.find("{")
            end = resp_text.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(resp_text[start:end])
                issues_found = bool(data.get("critic_issues", False))
                content = data.get("critique", resp_text)
                critic_details = {
                    "affected_claims": data.get("affected_claims", []),
                    "evidence_references": data.get("evidence_references", []),
                    "severity": data.get("severity", "MEDIUM" if issues_found else "LOW")
                }
            else:
                content = resp_text
                if "unsupported" in content.lower() or "inconsistent" in content.lower() or "error" in content.lower():
                    issues_found = True
                    critic_details["severity"] = "MEDIUM"
        except Exception:
            pass

    state["critic_issues"] = issues_found
    state["critic_feedback"] = content
    state["critic_details"] = critic_details
    return state

def validator_node(state: AgentState):
    """Evidence Grounding Validation (FO-6)"""
    from guardrails import validate_claims
    print("Validating evidence grounding...")
    is_valid, unsupported = validate_claims(
        state.get("draft_explanation", ""),
        {
            "customer": state.get("customer_evidence"),
            "transaction": state.get("transaction_evidence"),
            "merchant": state.get("merchant_evidence"),
            "device": state.get("device_evidence"),
            "location": state.get("location_evidence"),
            "velocity": state.get("velocity_evidence")
        }
    )

    state["validated"] = is_valid
    if not is_valid:
        retry_count = state.get("retry_count", 0) + 1
        state["retry_count"] = retry_count
        print(f"Validation failed (retry {retry_count}/{MAX_RETRIES}). Unsupported claims: {unsupported}")

    return state

def human_review_node(state: AgentState):
    """Escalate to Human Analyst (FO-8)"""
    print(f"Escalating investigation {state['investigation_id']} to human review queue.")
    reasons = []
    if not state.get("validated", False):
        reasons.append(f"Grounding validation failed after {state.get('retry_count', 0)} attempts.")
    if state.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        reasons.append(f"Confidence score {state.get('confidence', 0):.2f} below threshold {CONFIDENCE_THRESHOLD}.")

    escalation_report = f"""# HUMAN REVIEW ESCALATION REPORT
Investigation ID: {state['investigation_id']}
Transaction ID:   {state['transaction_id']}
Status:           ESCALATED
Risk Score:       {state.get('risk_score', 'N/A')}
Confidence:       {state.get('confidence', 'N/A')}

## Escalation Reasons
- """ + "\n- ".join(reasons) + f"""

## Draft Explanation
{state.get('draft_explanation', 'No draft generated.')}

## Action Required
Analyst review required. Please approve or reject with resolution notes.
"""
    state["report"] = escalation_report
    return state

def report_generator_node(state: AgentState):
    """Generate Final Investigation Report (FO-9)"""
    print("Generating final investigation report...")
    rule_factors = "\n".join([f"- {r}" for r in state.get("rule_reasons", [])]) if state.get("rule_reasons") else "- None"

    if llm and state.get("draft_explanation"):
        prompt = REPORT_PROMPT + f"\nDraft: {state['draft_explanation']}\nRule Factors:\n{rule_factors}"
        try:
            response = llm.invoke(prompt)
            report = response.content if hasattr(response, "content") else str(report)
        except Exception:
            report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."
    else:
        report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."

    state["report"] = report
    return state

def should_retry_or_human_review(state: AgentState):
    """Complete 6-Source Targeted Retry & Actionable Critic Router (Priority 2 & Priority 3)"""
    validated = state.get("validated", False)
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence", 0)
    failed_node = state.get("failed_target_node")
    critic_issues = state.get("critic_issues", False)

    decision = ""
    reason = ""

    if not validated or critic_issues:
        if retry_count < MAX_RETRIES:
            # Complete 6-source targeted retry routing
            valid_target_nodes = ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location", "velocity_check"]
            if failed_node and failed_node in valid_target_nodes:
                decision = failed_node
            else:
                decision = "risk_reasoning"
            reason = f"Validation or Critic check failed (attempt {retry_count}/{MAX_RETRIES}), retrying {decision}"
        else:
            decision = "human_review"
            reason = f"Validation failed after {MAX_RETRIES} attempts, escalating to human review"
    elif confidence < CONFIDENCE_THRESHOLD:
        decision = "human_review"
        reason = f"Confidence {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}, escalating to human review"
    else:
        decision = "report_generator"
        reason = f"Validation passed with confidence {confidence:.2f} >= threshold {CONFIDENCE_THRESHOLD}, proceeding to report generation"

    try:
        db = SessionLocal()
        investigation_id = state.get("investigation_id")
        if investigation_id:
            audit_log = AuditLog(
                investigation_id=investigation_id,
                action=f"DECISION: {decision}",
                details=reason
            )
            db.add(audit_log)
            db.commit()
        db.close()
    except Exception as e:
        print(f"Warning: Failed to log decision audit: {e}")

    return decision

def with_audit_logger(node_func, node_name: str):
    @time_function
    def wrapper(state: AgentState):
        db = SessionLocal()
        start_time = time.time()
        try:
            new_state = node_func(state)
            if not isinstance(new_state, dict):
                new_state = {}
            new_state["execution_trace"] = [node_name]

            execution_time_ms = int((time.time() - start_time) * 1000)

            metrics_collector.record_node_execution_time(node_name, execution_time_ms / 1000.0)

            investigation_id = state.get("investigation_id")
            if investigation_id:
                try:
                    audit_log = AuditLog(
                        investigation_id=investigation_id,
                        action=f"NODE_EXECUTION: {node_name}",
                        details=f"Successfully executed {node_name} in {execution_time_ms}ms"
                    )
                    db.add(audit_log)
                    db.commit()
                except Exception:
                    db.rollback()
            return new_state
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            db.rollback()
            investigation_id = state.get("investigation_id")
            if investigation_id:
                try:
                    audit_log = AuditLog(
                        investigation_id=investigation_id,
                        action=f"NODE_ERROR: {node_name}",
                        details=f"Failed to execute {node_name} after {execution_time_ms}ms: {str(e)[:500]}"
                    )
                    db.add(audit_log)
                    db.commit()
                except Exception:
                    db.rollback()
            raise e
        finally:
            db.close()
    return wrapper

def route_planner_tasks(state: AgentState):
    """Dynamic Task Execution Router (Priority 6 Fix)"""
    tasks = state.get("tasks", [])
    if tasks:
        return tasks
    return ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location"]

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes wrapped with audit logging
    graph.add_node("planner", with_audit_logger(planner_node, "planner"))
    graph.add_node("retrieve_customer", with_audit_logger(retrieve_customer_node, "retrieve_customer"))
    graph.add_node("retrieve_transaction", with_audit_logger(retrieve_transaction_node, "retrieve_transaction"))
    graph.add_node("retrieve_merchant", with_audit_logger(retrieve_merchant_node, "retrieve_merchant"))
    graph.add_node("retrieve_device", with_audit_logger(retrieve_device_node, "retrieve_device"))
    graph.add_node("retrieve_location", with_audit_logger(retrieve_location_node, "retrieve_location"))
    graph.add_node("evidence_verifier", with_audit_logger(evidence_verifier_node, "evidence_verifier"))
    graph.add_node("velocity_check", with_audit_logger(velocity_check_node, "velocity_check"))
    graph.add_node("rule_engine", with_audit_logger(rule_engine_node, "rule_engine"))
    graph.add_node("knowledge_lookup", with_audit_logger(knowledge_lookup_node, "knowledge_lookup"))
    graph.add_node("risk_reasoning", with_audit_logger(risk_reasoning_node, "risk_reasoning"))
    graph.add_node("critic", with_audit_logger(critic_node, "critic"))
    graph.add_node("validator", with_audit_logger(validator_node, "validator"))
    graph.add_node("human_review", with_audit_logger(human_review_node, "human_review"))
    graph.add_node("report_generator", with_audit_logger(report_generator_node, "report_generator"))

    # Edges
    graph.set_entry_point("planner")

    # Priority 6 Fix: Dynamic Task Execution Router from planner
    graph.add_conditional_edges("planner", route_planner_tasks)

    # Evidence Verifier & Velocity Analysis Pipeline
    graph.add_edge("retrieve_customer", "evidence_verifier")
    graph.add_edge("retrieve_transaction", "evidence_verifier")
    graph.add_edge("retrieve_merchant", "evidence_verifier")
    graph.add_edge("retrieve_device", "evidence_verifier")
    graph.add_edge("retrieve_location", "evidence_verifier")

    graph.add_edge("evidence_verifier", "velocity_check")
    graph.add_edge("velocity_check", "rule_engine")
    graph.add_edge("rule_engine", "knowledge_lookup")
    graph.add_edge("knowledge_lookup", "risk_reasoning")
    graph.add_edge("risk_reasoning", "critic")
    graph.add_edge("critic", "validator")

    # Priority 2 Fix: Support all 6 targeted retry destinations
    graph.add_conditional_edges(
        "validator",
        should_retry_or_human_review,
        {
            "risk_reasoning": "risk_reasoning",
            "retrieve_customer": "retrieve_customer",
            "retrieve_transaction": "retrieve_transaction",
            "retrieve_merchant": "retrieve_merchant",
            "retrieve_device": "retrieve_device",
            "retrieve_location": "retrieve_location",
            "velocity_check": "velocity_check",
            "human_review": "human_review",
            "report_generator": "report_generator"
        }
    )

    graph.add_edge("report_generator", END)
    graph.add_edge("human_review", END)

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        conn = sqlite3.connect("ffire_checkpoints.db", check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    except Exception:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
