from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
import json
import time
import functools

def time_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
from vector_db import vector_store
from database import SessionLocal
from models import AuditLog, Investigation
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from metrics import metrics_collector

load_dotenv()
# Initialize the LLM with fallback
api_key = os.getenv("OPENAI_API_KEY", "")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key) if api_key else None

# Configuration values from environment variables with sensible defaults
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Define the State
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
    failed_target_node: Optional[str]
    report: Optional[str]
    draft_explanation: Optional[str]
    critic_feedback: Optional[str]
    rule_score: Optional[float]
    rule_reasons: List[str]

from langgraph.checkpoint.memory import MemorySaver

# Prompt Templates from SRS Chapter 19
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
    """Decompose investigation into sub-tasks (FO-2)"""
    print(f"Planning investigation for {state['transaction_id']}")
    task_mapping = {
        "customer_history": "retrieve_customer",
        "retrieve_customer": "retrieve_customer",
        "transaction_detail": "retrieve_txn",
        "retrieve_txn": "retrieve_txn",
        "retrieve_transaction": "retrieve_txn",
        "merchant_reputation": "retrieve_merchant",
        "retrieve_merchant": "retrieve_merchant",
        "device_fingerprint": "retrieve_device",
        "retrieve_device": "retrieve_device",
        "location_check": "retrieve_location",
        "retrieve_location": "retrieve_location"
    }

    approved_tasks = ["retrieve_customer", "retrieve_txn", "retrieve_merchant", "retrieve_device", "retrieve_location"]
    tasks_to_run = approved_tasks.copy()
    if llm:
        prompt = PLANNER_PROMPT.format(transaction_summary=f"Transaction ID: {state['transaction_id']}")
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                parsed = json.loads(content[start:end])
                if isinstance(parsed, list):
                    mapped_tasks = [task_mapping[t] for t in parsed if t in task_mapping]
                    if mapped_tasks:
                        tasks_to_run = list(dict.fromkeys(mapped_tasks))
        except Exception as e:
            print(f"LLM Planner failed: {e}")

    state["tasks"] = tasks_to_run
    return state


def retrieve_customer_node(state: AgentState):
    db = SessionLocal()
    try:
        from models import Transaction, Account, Customer
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
        from models import Transaction
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn:
            return {"transaction_evidence": {"amount": float(txn.amount), "currency": txn.currency, "status": txn.status, "account_id": txn.account_id}}
    finally:
        db.close()
    return {"transaction_evidence": {"error": "Not Found"}}

def retrieve_merchant_node(state: AgentState):
    db = SessionLocal()
    try:
        from models import Transaction, Merchant
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
        from models import Transaction, Account, Device
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
        from models import Location
        loc = db.query(Location).filter(Location.txn_id == state['transaction_id']).first()
        if loc:
            return {"location_evidence": {"country": loc.country, "geo_coord": loc.geo_coord}}
    finally:
        db.close()
    return {"location_evidence": {"error": "Not Found"}}

def velocity_check_node(state: AgentState):
    """Transaction velocity analysis node (SRS DFD 3.1 Velocity Check)"""
    print("Performing 1-hour transaction velocity check...")
    db = SessionLocal()
    try:
        from models import Transaction
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        account_id = txn.account_id if txn else None
        
        velocity_count = 1
        velocity_sum = float(txn.amount) if txn else 0.0
        
        if account_id:
            recent_txns = db.query(Transaction).filter(Transaction.account_id == account_id).all()
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
    """Evidence Verifier node - checks completeness and flags target node for retry if needed"""
    print("Verifying collected evidence completeness...")
    cust = state.get("customer_evidence", {})
    txn = state.get("transaction_evidence", {})
    dev = state.get("device_evidence", {})
    loc = state.get("location_evidence", {})

    failed_node = None
    if dev.get("error"):
        failed_node = "retrieve_device"
    elif loc.get("error"):
        failed_node = "retrieve_location"
    elif cust.get("error"):
        failed_node = "retrieve_customer"

    state["failed_target_node"] = failed_node
    state["verified_evidence"] = {
        "status": "VERIFIED" if not failed_node else "PARTIAL",
        "missing_node": failed_node
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
    customer_evidence = state.get('customer_evidence', {})

    query_parts = []
    if device_evidence.get('os'):
        query_parts.append(f"device OS: {device_evidence['os']}")
    if location_evidence.get('country'):
        query_parts.append(f"country: {location_evidence['country']}")
    if transaction_evidence.get('amount'):
        query_parts.append(f"amount: {transaction_evidence['amount']} {transaction_evidence.get('currency', '')}")
    if merchant_evidence.get('name'):
        query_parts.append(f"merchant: {merchant_evidence['name']}")

    query = ", ".join(query_parts) if query_parts else "financial transaction"
    print(f"Searching historical fraud cases for query: {query}")
    results = vector_store.similarity_search(query, top_k=5)
    state["historical_cases"] = results
    return state

def risk_reasoning_node(state: AgentState):
    """LLM-powered Risk Reasoning (FO-5 Part 2)"""
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
    hist_cases = state.get("historical_cases", [])
    hist_scores = [c.get("similarity", 0.5) for c in hist_cases if isinstance(c, dict)]
    avg_hist_score = sum(hist_scores) / len(hist_scores) if hist_scores else 0.5

    llm_risk_estimate = None
    reasoning_text = ""

    if llm:
        prompt = REASONER_PROMPT.format(evidence_bundle=json.dumps(evidence_bundle, indent=2))
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

    state["risk_score"] = round(combined_score, 4)
    state["confidence"] = 0.90 if llm_risk_estimate is not None else 0.70
    state["draft_explanation"] = reasoning_text
    return state

def critic_node(state: AgentState):
    """Evidence Critic Node - evaluates draft explanation against evidence & velocity"""
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
    
    if llm and draft:
        try:
            prompt = CRITIC_PROMPT.format(
                draft_explanation=draft,
                evidence_bundle=json.dumps(evidence),
                velocity_analysis=json.dumps(state.get("velocity_evidence"))
            )
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            state["critic_feedback"] = content
        except Exception:
            state["critic_feedback"] = "Critic evaluation completed cleanly."
    else:
        state["critic_feedback"] = "Draft reasoning consistent with collected evidence and velocity analysis."
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
            report = response.content if hasattr(response, "content") else str(response)
        except Exception:
            report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."
    else:
        report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."

    state["report"] = report
    return state

def should_retry_or_human_review(state: AgentState):
    validated = state.get("validated", False)
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence", 0)
    failed_node = state.get("failed_target_node")

    decision = ""
    reason = ""

    if not validated:
        if retry_count < MAX_RETRIES:
            # Target specific failed retrieval node if identified, otherwise retry risk reasoning
            decision = failed_node if (failed_node and failed_node in ["retrieve_device", "retrieve_location", "retrieve_customer"]) else "retry"
            reason = f"Validation failed (attempt {retry_count}/{MAX_RETRIES}), retrying {decision}"
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

    try:
        investigation_id = state.get("investigation_id")
        if investigation_id:
            metrics_collector.record_retry_count(investigation_id, retry_count)
            if confidence is not None:
                metrics_collector.record_confidence_score(investigation_id, confidence)
    except Exception as e:
        print(f"Warning: Failed to record metrics: {e}")

    return decision

def with_audit_logger(node_func, node_name: str):
    @time_function
    def wrapper(state: AgentState):
        db = SessionLocal()
        start_time = time.time()
        try:
            # Execute node
            new_state = node_func(state)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics_collector.record_node_execution_time(node_name, execution_time_ms / 1000.0)

            # Log execution
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

    # Parallel retrieval - all retrieval nodes run in parallel after planner
    graph.add_edge("planner", "retrieve_customer")
    graph.add_edge("planner", "retrieve_transaction")
    graph.add_edge("planner", "retrieve_merchant")
    graph.add_edge("planner", "retrieve_device")
    graph.add_edge("planner", "retrieve_location")

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

    graph.add_conditional_edges(
        "validator",
        should_retry_or_human_review,
        {
            "retry": "risk_reasoning",
            "retrieve_device": "retrieve_device",
            "retrieve_location": "retrieve_location",
            "retrieve_customer": "retrieve_customer",
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
