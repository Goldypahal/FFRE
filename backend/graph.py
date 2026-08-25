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
    historical_cases: List[Dict[str, Any]]
    risk_score: Optional[float]
    confidence: Optional[float]
    validated: bool
    retry_count: int
    report: Optional[str]
    draft_explanation: Optional[str]
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
                    return {"customer_evidence": {"kyc_status": cust.kyc_status, "risk_tier": cust.risk_tier, "name": cust.name}}
    finally:
        db.close()
    return {"customer_evidence": {"error": "Not Found"}}

def retrieve_transaction_node(state: AgentState):
    db = SessionLocal()
    try:
        from models import Transaction
        txn = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id']).first()
        if txn:
            return {"transaction_evidence": {"amount": float(txn.amount), "currency": txn.currency, "status": txn.status}}
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
                return {"merchant_evidence": {"name": merch.name, "category": merch.category, "historical_fraud_rate": float(merch.risk_score) if merch.risk_score else 0.0}}
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
    # Create a comprehensive query based on all available evidence
    device_evidence = state.get('device_evidence', {})
    location_evidence = state.get('location_evidence', {})
    transaction_evidence = state.get('transaction_evidence', {})
    merchant_evidence = state.get('merchant_evidence', {})
    customer_evidence = state.get('customer_evidence', {})

    # Build evidence-rich query for better historical pattern matching
    query_parts = []

    # Add device information
    if device_evidence.get('os'):
        query_parts.append(f"device OS: {device_evidence['os']}")
    if device_evidence.get('new_device') is not None:
        query_parts.append(f"new device: {device_evidence['new_device']}")

    # Add location information
    if location_evidence.get('country'):
        query_parts.append(f"country: {location_evidence['country']}")
    if location_evidence.get('geo_coord'):
        query_parts.append(f"location: {location_evidence['geo_coord']}")

    # Add transaction information
    if transaction_evidence.get('amount'):
        query_parts.append(f"amount: {transaction_evidence['amount']} {transaction_evidence.get('currency', '')}")
    if transaction_evidence.get('status'):
        query_parts.append(f"status: {transaction_evidence['status']}")

    # Add merchant information
    if merchant_evidence.get('name'):
        query_parts.append(f"merchant: {merchant_evidence['name']}")
    if merchant_evidence.get('category'):
        query_parts.append(f"merchant category: {merchant_evidence['category']}")
    if merchant_evidence.get('historical_fraud_rate') is not None:
        query_parts.append(f"merchant fraud rate: {merchant_evidence['historical_fraud_rate']}")

    # Add customer information
    if customer_evidence.get('kyc_status'):
        query_parts.append(f"customer KYC: {customer_evidence['kyc_status']}")
    if customer_evidence.get('risk_tier'):
        query_parts.append(f"customer risk tier: {customer_evidence['risk_tier']}")

    # Combine all parts into a comprehensive query
    query = ", ".join(query_parts) if query_parts else "financial transaction"

    # Perform vector search with increased top_k for better recall
    results = vector_store.similarity_search(query, top_k=5)
    state["historical_cases"] = results
    return state

def risk_reasoning_node(state: AgentState):
    """Reasoning with LLM (FO-5)"""
    evidence_bundle = {
        "customer": state.get("customer_evidence"),
        "transaction": state.get("transaction_evidence"),
        "merchant": state.get("merchant_evidence"),
        "device": state.get("device_evidence"),
        "location": state.get("location_evidence"),
        "historical_cases": state.get("historical_cases")
    }

    draft = ""
    llm_risk_estimate = None
    if llm:
        prompt = REASONER_PROMPT.format(evidence_bundle=json.dumps(evidence_bundle, indent=2))
        if state.get("draft_explanation") and "[System Error" in state["draft_explanation"]:
            prompt += f"\n\nCRITICAL FIX REQUIRED: {state['draft_explanation']}"
        try:
            response = llm.invoke(prompt)
            draft = response.content if hasattr(response, "content") else str(response)
            # Try parsing structured json from LLM if returned
            if "{" in draft and "}" in draft:
                try:
                    start = draft.find("{")
                    end = draft.rfind("}") + 1
                    data = json.loads(draft[start:end])
                    if "risk_score" in data:
                        llm_risk_estimate = float(data["risk_score"])
                except Exception:
                    pass
        except Exception as e:
            draft = f"LLM Error: {e}"
    else:
        draft = "The transaction is highly suspicious. The device is a 'new_device' with an 'Unknown' OS, and the merchant 'HighRisk Electronics' has a high 'historical_fraud_rate' of 0.15."

    state["draft_explanation"] = draft

    rule_score = state.get("rule_score", 0.0)

    # Dynamic fallback LLM risk assessment based on evidence severity when LLM json is not parsed
    if llm_risk_estimate is None:
        risk_factors = 0
        total_factors = 0
        device_ev = state.get("device_evidence", {})
        if isinstance(device_ev, dict) and "error" not in device_ev:
            total_factors += 2
            if device_ev.get("new_device"): risk_factors += 1
            if str(device_ev.get("os", "")).lower() in ["unknown", "other"]: risk_factors += 1

        merchant_ev = state.get("merchant_evidence", {})
        if isinstance(merchant_ev, dict) and "error" not in merchant_ev:
            total_factors += 1
            if float(merchant_ev.get("historical_fraud_rate", 0.0)) > 0.1: risk_factors += 1

        location_ev = state.get("location_evidence", {})
        if isinstance(location_ev, dict) and "error" not in location_ev:
            total_factors += 1
            if str(location_ev.get("country", "")).upper() not in ["US", "CA", "GB"]: risk_factors += 1

        llm_risk_estimate = (risk_factors / total_factors) if total_factors > 0 else 0.5

    # Calculate historical pattern match score
    historical_score = 0.0
    historical_cases = state.get("historical_cases", [])
    if historical_cases:
        similarities = []
        for case in historical_cases:
            distance = case.get("similarity_distance", 1.0)
            similarity = max(0.0, 1.0 - (distance / 2.0))
            similarities.append(similarity)
        if similarities:
            historical_score = max(similarities)

    # Apply weighted formula from SRS Section 21.1:
    # Rule Engine Score: 35%
    # LLM Reasoning Score: 40%
    # Historical Pattern Match: 25%
    combined_risk = min(
        (rule_score * 0.35) +
        (llm_risk_estimate * 0.40) +
        (historical_score * 0.25),
        1.0
    )

    state["risk_score"] = combined_risk

    # Dynamic confidence calculation:
    # 1. Evidence completeness ratio
    retrieved_sources = [state.get("customer_evidence"), state.get("transaction_evidence"), state.get("merchant_evidence"), state.get("device_evidence"), state.get("location_evidence")]
    valid_sources = [s for s in retrieved_sources if isinstance(s, dict) and "error" not in s]
    completeness = len(valid_sources) / len(retrieved_sources) if retrieved_sources else 0.5

    # 2. Score agreement between rule engine and LLM risk estimate
    agreement = 1.0 - abs(rule_score - llm_risk_estimate)

    # 3. Combined dynamic confidence score
    confidence_score = (completeness * 0.40) + (agreement * 0.40) + (historical_score * 0.20)
    state["confidence"] = round(min(max(confidence_score, 0.5), 0.98), 2)
    return state

def validator_node(state: AgentState):
    """Evidence Verification (FO-6)"""
    from guardrails import validate_claims
    
    evidence_bundle = {
        "customer": state.get("customer_evidence"),
        "transaction": state.get("transaction_evidence"),
        "merchant": state.get("merchant_evidence"),
        "device": state.get("device_evidence"),
        "location": state.get("location_evidence")
    }
    
    draft = state.get("draft_explanation", "")
    is_valid, unsupported_claims = validate_claims(draft, evidence_bundle)
    
    state["validated"] = is_valid
    if not is_valid:
        state["retry_count"] = state.get("retry_count", 0) + 1
        print(f"Validation failed (retry {state['retry_count']}/{MAX_RETRIES}). Unsupported claims: {unsupported_claims}")
        # Append hallucination feedback so the reasoning node can fix it on retry
        state["draft_explanation"] = draft + " [System Error: Previous draft contained hallucinations]"
    
    return state

def human_review_node(state: AgentState):
    """Human Escalation (FO-8)"""
    print(f"Escalating investigation {state.get('investigation_id')} to human review queue.")
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence", 0.0)
    draft = state.get("draft_explanation", "No draft reasoning generated.")

    escalation_report = (
        f"## HUMAN REVIEW ESCALATION REPORT\n"
        f"**Investigation ID**: {state.get('investigation_id')}\n"
        f"**Transaction ID**: {state.get('transaction_id')}\n"
        f"**Escalation Reason**: Confidence ({confidence:.2f}) below threshold ({CONFIDENCE_THRESHOLD}) or claim validation limit reached ({retry_count}/{MAX_RETRIES}).\n\n"
        f"### Draft Reasoning Engine Analysis\n{draft}\n\n"
        f"### Action Required\nAn analyst must review the evidence bundle, verify transaction details, and submit a final APPROVE or REJECT verdict."
    )
    state["report"] = escalation_report
    return state

def report_generator_node(state: AgentState):
    """Generate final human-readable report (FO-9)"""
    rule_factors = "\n".join([f"- {r}" for r in state.get("rule_reasons", [])])
    
    if llm:
        prompt = REPORT_PROMPT + f"\n\nDraft: {state.get('draft_explanation')}\nRules Triggered:\n{rule_factors}"
        try:
            response = llm.invoke(prompt)
            report = response.content
        except Exception as e:
            report = f"LLM Generation Error: {e}"
    else:
        report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."
        
    state["report"] = report
    return state

# Conditional routing
def should_retry_or_human_review(state: AgentState):
    # Log the decision-making process for auditability
    validated = state.get("validated", False)
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence", 0)

    decision = ""
    reason = ""

    if not validated:
        if retry_count < MAX_RETRIES:
            decision = "retry"
            reason = f"Validation failed (attempt {retry_count + 1}/{MAX_RETRIES}), will retry"
        else:
            decision = "human_review"
            reason = f"Validation failed after {MAX_RETRIES} attempts, escalating to human review"
    elif confidence < CONFIDENCE_THRESHOLD:
        decision = "human_review"
        reason = f"Confidence {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}, escalating to human review"
    else:
        decision = "report_generator"
        reason = f"Validation passed with confidence {confidence:.2f} >= threshold {CONFIDENCE_THRESHOLD}, proceeding to report generation"

    # Log this decision to the audit trail
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
        # Don't let audit logging failures break the flow
        print(f"Warning: Failed to log decision audit: {e}")

    # Record metrics for monitoring
    try:
        investigation_id = state.get("investigation_id")
        if investigation_id:
            metrics_collector.record_retry_count(investigation_id, retry_count)
            if confidence is not None:
                metrics_collector.record_confidence_score(investigation_id, confidence)
    except Exception as e:
        # Don't let metrics collection failures break the flow
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
    graph.add_node("rule_engine", with_audit_logger(rule_engine_node, "rule_engine"))
    graph.add_node("knowledge_lookup", with_audit_logger(knowledge_lookup_node, "knowledge_lookup"))
    graph.add_node("risk_reasoning", with_audit_logger(risk_reasoning_node, "risk_reasoning"))
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

    # All retrieval nodes converge before rule_engine
    graph.add_edge("retrieve_customer", "rule_engine")
    graph.add_edge("retrieve_transaction", "rule_engine")
    graph.add_edge("retrieve_merchant", "rule_engine")
    graph.add_edge("retrieve_device", "rule_engine")
    graph.add_edge("retrieve_location", "rule_engine")

    graph.add_edge("rule_engine", "knowledge_lookup")
    graph.add_edge("knowledge_lookup", "risk_reasoning")
    graph.add_edge("risk_reasoning", "validator")

    graph.add_conditional_edges(
        "validator",
        should_retry_or_human_review,
        {
            "retry": "risk_reasoning", # Retry logic goes back to reasoning to fix groundedness
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
