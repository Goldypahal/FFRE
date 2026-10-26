import threading
import threading
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
import json
import time
import datetime
import functools
from decimal import Decimal
from decimal import Decimal

def time_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

from vector_db import vector_store
from database import SessionLocal
from models import AuditLog, Investigation, Transaction, Account, Customer, Merchant, Device, Location

class SmartDatabaseLock:
    """Acquires lock only when connecting to SQLite (to protect in-memory StaticPool in unit tests).
    Does NOT block or serialize when running against multi-connection PostgreSQL."""
    def __init__(self):
        self._lock = threading.RLock()
        self._local = threading.local()

    def __enter__(self):
        from database import SQLALCHEMY_DATABASE_URL
        if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
            self._lock.acquire()
            self._local.locked = True
        else:
            self._local.locked = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if getattr(self._local, "locked", False):
            self._lock.release()
            self._local.locked = False

_audit_db_lock = SmartDatabaseLock()
import os
from dotenv import load_dotenv
from llm_gateway import get_llm_gateway
from metrics import metrics_collector

load_dotenv()
llm_gateway = get_llm_gateway()
llm = llm_gateway

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

from typing import Annotated
import operator

class AgentState(TypedDict):
    investigation_id: str
    transaction_id: str
    tenant_id: Optional[str]
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
    critic_cycle_count: int
    evidence_provenance: List[Dict[str, Any]]
    risk_signals: List[Dict[str, Any]]
    pii_vault: Optional[Dict[str, str]]
    compliance_alerts: Optional[List[str]]
    has_typology_alert: Optional[bool]
    predicted_verdict: Optional[str]
    workflow_status: Optional[str]
    compliance_alerts: Optional[List[str]]
    has_typology_alert: Optional[bool]
    predicted_verdict: Optional[str]
    workflow_status: Optional[str]
    ml_risk_score: Optional[float]
    ml_calibrated_probability: Optional[float]
    ml_top_features: Optional[List[Dict[str, Any]]]
    ml_model_id: Optional[str]
    graph_cluster_evidence: Optional[Dict[str, Any]]

from langgraph.checkpoint.memory import MemorySaver

from prompt_registry import get_prompt_template, DEFAULT_PROMPTS

# Dynamic Prompt Loaders (Chapters 36 & 85)
def get_planner_prompt(tenant_id: str = "default_tenant") -> str:
    return get_prompt_template("planner", tenant_id=tenant_id)

def get_reasoner_prompt(tenant_id: str = "default_tenant") -> str:
    return get_prompt_template("reasoner", tenant_id=tenant_id)

def get_critic_prompt(tenant_id: str = "default_tenant") -> str:
    return get_prompt_template("critic", tenant_id=tenant_id)

def get_validator_prompt(tenant_id: str = "default_tenant") -> str:
    return get_prompt_template("validator", tenant_id=tenant_id)

def get_report_prompt(tenant_id: str = "default_tenant") -> str:
    return get_prompt_template("reporter", tenant_id=tenant_id)

# Retain backward-compatible string references
PLANNER_PROMPT = DEFAULT_PROMPTS["planner"]["template"]
REASONER_PROMPT = DEFAULT_PROMPTS["reasoner"]["template"]
CRITIC_PROMPT = DEFAULT_PROMPTS["critic"]["template"]
VALIDATOR_PROMPT = DEFAULT_PROMPTS["validator"]["template"]
REPORT_PROMPT = DEFAULT_PROMPTS["reporter"]["template"]

def _get_or_init_pii_tokenizer(state: AgentState):
    """Initializes or restores PIITokenizer and registers all known evidence PII."""
    from security import PIITokenizer
    tokenizer = PIITokenizer(existing_vault=state.get("pii_vault"))

    # Register customer PII
    cust_ev = state.get("customer_evidence")
    if isinstance(cust_ev, dict):
        if cust_ev.get("name"):
            tokenizer.register_pii("CUSTOMER_NAME", str(cust_ev["name"]))
        if cust_ev.get("email"):
            tokenizer.register_pii("EMAIL", str(cust_ev["email"]))
        if cust_ev.get("customer_id"):
            tokenizer.register_pii("CUSTOMER_ID", str(cust_ev["customer_id"]))

    # Register transaction PII
    txn_ev = state.get("transaction_evidence")
    if isinstance(txn_ev, dict):
        if txn_ev.get("account_id"):
            tokenizer.register_pii("ACCOUNT_ID", str(txn_ev["account_id"]))
        if txn_ev.get("counterparty"):
            tokenizer.register_pii("COUNTERPARTY", str(txn_ev["counterparty"]))
        if txn_ev.get("ip_address"):
            tokenizer.register_pii("IP_ADDRESS", str(txn_ev["ip_address"]))

    # Register device PII
    dev_ev = state.get("device_evidence")
    if isinstance(dev_ev, dict):
        if dev_ev.get("fingerprint"):
            tokenizer.register_pii("DEVICE_FINGERPRINT", str(dev_ev["fingerprint"]))
        if dev_ev.get("ip_address"):
            tokenizer.register_pii("IP_ADDRESS", str(dev_ev["ip_address"]))

    return tokenizer


def _get_or_init_pii_tokenizer(state: AgentState):
    """Initializes or restores PIITokenizer and registers all known evidence PII."""
    from security import PIITokenizer
    tokenizer = PIITokenizer(existing_vault=state.get("pii_vault"))

    # Register customer PII
    cust_ev = state.get("customer_evidence")
    if isinstance(cust_ev, dict):
        if cust_ev.get("name"):
            tokenizer.register_pii("CUSTOMER_NAME", str(cust_ev["name"]))
        if cust_ev.get("email"):
            tokenizer.register_pii("EMAIL", str(cust_ev["email"]))
        if cust_ev.get("customer_id"):
            tokenizer.register_pii("CUSTOMER_ID", str(cust_ev["customer_id"]))

    # Register transaction PII
    txn_ev = state.get("transaction_evidence")
    if isinstance(txn_ev, dict):
        if txn_ev.get("account_id"):
            tokenizer.register_pii("ACCOUNT_ID", str(txn_ev["account_id"]))
        if txn_ev.get("counterparty"):
            tokenizer.register_pii("COUNTERPARTY", str(txn_ev["counterparty"]))
        if txn_ev.get("ip_address"):
            tokenizer.register_pii("IP_ADDRESS", str(txn_ev["ip_address"]))

    # Register device PII
    dev_ev = state.get("device_evidence")
    if isinstance(dev_ev, dict):
        if dev_ev.get("fingerprint"):
            tokenizer.register_pii("DEVICE_FINGERPRINT", str(dev_ev["fingerprint"]))
        if dev_ev.get("ip_address"):
            tokenizer.register_pii("IP_ADDRESS", str(dev_ev["ip_address"]))

    return tokenizer


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
        tenant = state.get("tenant_id", "default_tenant")
        prompt = get_planner_prompt(tenant).format(transaction_summary=f"Transaction ID: {state['transaction_id']}")
        start_t = time.time()
        try:
            response = llm.invoke(prompt)
            latency_ms = (time.time() - start_t) * 1000.0
            content = response.content if hasattr(response, "content") else str(response)
            metrics_collector.record_llm_call(
                investigation_id=state.get("investigation_id", "unknown"),
                node_name="planner",
                model=getattr(llm, "model_name", "gpt-4o-mini"),
                prompt_tokens=getattr(response, "prompt_tokens", max(1, len(prompt) // 4)),
                completion_tokens=getattr(response, "completion_tokens", max(1, len(content) // 4)),
                latency_ms=latency_ms,
                tenant_id=tenant
            )
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
    with _audit_db_lock:
        db = SessionLocal()
        try:
            tenant_req = state.get("tenant_id")
            txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
            if tenant_req:
                txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
            txn = txn_query.first()
            if txn and txn.account_id:
                tenant = txn.tenant_id
                acct = db.query(Account).filter(
                    Account.account_id == txn.account_id,
                    Account.tenant_id == tenant
                ).first()
                if acct and acct.customer_id:
                    cust = db.query(Customer).filter(
                        Customer.customer_id == acct.customer_id,
                        Customer.tenant_id == tenant
                    ).first()
                    if cust:
                        return {
                            "customer_evidence": {
                                "evidence_status": "OK",
                                "kyc_status": cust.kyc_status,
                                "risk_tier": cust.risk_tier,
                                "customer_id": cust.customer_id,
                                "name": cust.name,
                                "account_type": acct.account_type
                            }
                        }
            return {
                "customer_evidence": {
                    "evidence_status": "NOT_FOUND",
                    "error": "Customer Not Found"
                }
            }
        except Exception as e:
            return {
                "customer_evidence": {
                    "evidence_status": "UNAVAILABLE",
                    "error": f"Database error during customer retrieval: {str(e)}"
                }
            }
        finally:
            db.close()

def retrieve_transaction_node(state: AgentState):
    with _audit_db_lock:
        db = SessionLocal()
        try:
            tenant_req = state.get("tenant_id")
            txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
            if tenant_req:
                txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
            txn = txn_query.first()
            if txn:
                return {
                    "transaction_evidence": {
                        "evidence_status": "OK",
                        "amount": float(txn.amount),
                        "currency": txn.currency,
                        "status": txn.status,
                        "account_id": txn.account_id,
                        "counterparty": txn.counterparty,
                        "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,
                        "txn_id": txn.txn_id,
                    }
                }
            return {
                "transaction_evidence": {
                    "evidence_status": "NOT_FOUND",
                    "error": "Transaction Not Found"
                }
            }
        except Exception as e:
            return {
                "transaction_evidence": {
                    "evidence_status": "UNAVAILABLE",
                    "error": f"Database error during transaction retrieval: {str(e)}"
                }
            }
        finally:
            db.close()

def retrieve_merchant_node(state: AgentState):
    with _audit_db_lock:
        db = SessionLocal()
        try:
            tenant_req = state.get("tenant_id")
            txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
            if tenant_req:
                txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
            txn = txn_query.first()
            if txn and txn.merchant_id:
                tenant = txn.tenant_id
                merch = db.query(Merchant).filter(
                    Merchant.merchant_id == txn.merchant_id,
                    Merchant.tenant_id == tenant
                ).first()
                if merch:
                    return {
                        "merchant_evidence": {
                            "evidence_status": "OK",
                            "name": merch.name,
                            "category": merch.category,
                            "historical_fraud_rate": float(merch.risk_score) if merch.risk_score is not None else 0.0
                        }
                    }
            return {
                "merchant_evidence": {
                    "evidence_status": "NOT_FOUND",
                    "error": "Merchant Not Found"
                }
            }
        except Exception as e:
            return {
                "merchant_evidence": {
                    "evidence_status": "UNAVAILABLE",
                    "error": f"Database error during merchant retrieval: {str(e)}"
                }
            }
        finally:
            db.close()

def retrieve_device_node(state: AgentState):
    with _audit_db_lock:
        db = SessionLocal()
        try:
            tenant_req = state.get("tenant_id")
            txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
            if tenant_req:
                txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
            txn = txn_query.first()
            if txn and txn.account_id:
                tenant = txn.tenant_id
                acct = db.query(Account).filter(
                    Account.account_id == txn.account_id,
                    Account.tenant_id == tenant
                ).first()
                if acct and acct.customer_id:
                    dev = db.query(Device).filter(
                        Device.customer_id == acct.customer_id,
                        Device.tenant_id == tenant
                    ).first()
                    if dev:
                        # Compute new_device from actual history: has customer used this device before?
                        from models import Evidence
                        prior_txns = db.query(Transaction).join(Account).filter(
                            Account.customer_id == acct.customer_id,
                            Account.tenant_id == tenant,
                            Transaction.tenant_id == tenant,
                            Transaction.txn_id != txn.txn_id
                        ).all()
                        prior_txn_ids = [t.txn_id for t in prior_txns]

                        has_prior_usage = False
                        if prior_txn_ids and dev.fingerprint:
                            prior_ev = db.query(Evidence).join(Investigation).filter(
                                Investigation.tenant_id == tenant,
                                Evidence.tenant_id == tenant,
                                Investigation.txn_id.in_(prior_txn_ids),
                                Evidence.source == "device_evidence",
                                Evidence.snippet.like(f"%{dev.fingerprint}%")
                            ).first()
                            if prior_ev:
                                has_prior_usage = True

                        is_new_device = not has_prior_usage

                        return {
                            "device_evidence": {
                                "evidence_status": "OK",
                                "os": dev.os,
                                "new_device": is_new_device,
                                "device_id": dev.fingerprint
                            }
                        }
            return {
                "device_evidence": {
                    "evidence_status": "NOT_FOUND",
                    "error": "Device Not Found"
                }
            }
        except Exception as e:
            return {
                "device_evidence": {
                    "evidence_status": "UNAVAILABLE",
                    "error": f"Database error during device retrieval: {str(e)}"
                }
            }
        finally:
            db.close()

def retrieve_location_node(state: AgentState):
    with _audit_db_lock:
        db = SessionLocal()
        try:
            tenant_req = state.get("tenant_id")
            txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
            if tenant_req:
                txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
            txn = txn_query.first()
            if txn:
                tenant = txn.tenant_id
                loc = db.query(Location).filter(
                    Location.txn_id == state['transaction_id'],
                    Location.tenant_id == tenant
                ).first()
                if loc:
                    return {
                        "location_evidence": {
                            "evidence_status": "OK",
                            "geo_coord": loc.geo_coord,
                            "country": loc.country
                        }
                    }
            return {
                "location_evidence": {
                    "evidence_status": "NOT_FOUND",
                    "error": "Location Not Found"
                }
            }
        except Exception as e:
            return {
                "location_evidence": {
                    "evidence_status": "UNAVAILABLE",
                    "error": f"Database error during location retrieval: {str(e)}"
                }
            }
        finally:
            db.close()

VELOCITY_RULES_CONFIG = {
    "window_5m": {"count_threshold": 3, "amount_threshold": 2500.0},
    "window_1h": {"count_threshold": 4, "amount_threshold": 5000.0},
    "window_24h": {"count_threshold": 10, "amount_threshold": 15000.0},
    "window_7d": {"count_threshold": 30, "amount_threshold": 50000.0}
}

def velocity_check_node(state: AgentState):
    """Multi-window velocity check, anomaly detection, and decoupled RiskSignal generation (Tasks 6-9)"""
    print("Performing multi-window transaction velocity analysis & anomaly pattern detection...")
    try:
        now = datetime.datetime.utcnow()
        t_5m = now - datetime.timedelta(minutes=5)
        t_1h = now - datetime.timedelta(hours=1)
        t_24h = now - datetime.timedelta(hours=24)
        t_7d = now - datetime.timedelta(days=7)

        txns_5m, txns_1h, txns_24h, txns_7d = [], [], [], []
        with _audit_db_lock:
            db = SessionLocal()
            try:
                tenant_req = state.get("tenant_id")
                txn_query = db.query(Transaction).filter(Transaction.txn_id == state['transaction_id'])
                if tenant_req:
                    txn_query = txn_query.filter(Transaction.tenant_id == tenant_req)
                txn = txn_query.first()
                account_id = txn.account_id if txn else None
                tenant = txn.tenant_id if txn else (tenant_req or "default_tenant")

                if account_id:
                    txns_5m = db.query(Transaction).filter(
                        Transaction.tenant_id == tenant,
                        Transaction.account_id == account_id,
                        Transaction.timestamp >= t_5m
                    ).all()
                    txns_1h = db.query(Transaction).filter(
                        Transaction.tenant_id == tenant,
                        Transaction.account_id == account_id,
                        Transaction.timestamp >= t_1h
                    ).all()
                    txns_24h = db.query(Transaction).filter(
                        Transaction.tenant_id == tenant,
                        Transaction.account_id == account_id,
                        Transaction.timestamp >= t_24h
                    ).all()
                    txns_7d = db.query(Transaction).filter(
                        Transaction.tenant_id == tenant,
                        Transaction.account_id == account_id,
                        Transaction.timestamp >= t_7d
                    ).all()
            finally:
                db.close()

        c_5m = len(txns_5m)
        s_5m_dec = sum([Decimal(str(t.amount)) for t in txns_5m], Decimal("0.00"))
        c_1h = len(txns_1h)
        s_1h_dec = sum([Decimal(str(t.amount)) for t in txns_1h], Decimal("0.00"))
        c_24h = len(txns_24h)
        s_24h_dec = sum([Decimal(str(t.amount)) for t in txns_24h], Decimal("0.00"))
        c_7d = len(txns_7d)
        s_7d_dec = sum([Decimal(str(t.amount)) for t in txns_7d], Decimal("0.00"))

        s_5m, s_1h, s_24h, s_7d = float(s_5m_dec), float(s_1h_dec), float(s_24h_dec), float(s_7d_dec)

        # Task 8: Detect Velocity Anomaly Patterns & Task 9: RiskSignals
        anomalies = []
        signals = []

        if c_5m >= VELOCITY_RULES_CONFIG["window_5m"]["count_threshold"]:
            anomalies.append("BURST_TRANSACTIONS")
            signals.append({
                "signal": "BURST_TRANSACTIONS_5M",
                "severity": 0.85,
                "source": "velocity_check",
                "evidence": {"window": "5m", "count": c_5m, "sum": s_5m}
            })

        if s_1h >= (s_24h / max(c_24h, 1)) * 3.0 and c_1h > 1:
            anomalies.append("RAPID_AMOUNT_ESCALATION")
            signals.append({
                "signal": "RAPID_AMOUNT_ESCALATION_1H",
                "severity": 0.90,
                "source": "velocity_check",
                "evidence": {"sum_1h": s_1h, "sum_24h": s_24h}
            })

        unique_merchants_1h = len(set([t.merchant_id for t in txns_1h if t.merchant_id]))
        if unique_merchants_1h >= 3:
            anomalies.append("MULTI_MERCHANT_SPIKE")
            signals.append({
                "signal": "MULTI_MERCHANT_SPIKE_1H",
                "severity": 0.80,
                "source": "velocity_check",
                "evidence": {"unique_merchants": unique_merchants_1h}
            })

        high_velocity = c_1h >= VELOCITY_RULES_CONFIG["window_1h"]["count_threshold"] or (c_1h > 1 and s_1h >= VELOCITY_RULES_CONFIG["window_1h"]["amount_threshold"]) or len(anomalies) > 0
        velocity_score = 0.85 if high_velocity else 0.15

        state["velocity_evidence"] = {
            "evidence_status": "OK",
            "velocity_count_1h": c_1h,
            "velocity_sum_1h": s_1h,
            "velocity_5m": {"count": c_5m, "sum": s_5m},
            "velocity_1h": {"count": c_1h, "sum": s_1h},
            "velocity_24h": {"count": c_24h, "sum": s_24h},
            "velocity_7d": {"count": c_7d, "sum": s_7d},
            "high_velocity_flag": high_velocity,
            "anomaly_patterns": anomalies,
            "velocity_score": velocity_score
        }
        existing_signals = state.get("risk_signals", [])
        state["risk_signals"] = existing_signals + signals if existing_signals else signals
    except Exception as e:
        state["velocity_evidence"] = {
            "evidence_status": "UNAVAILABLE",
            "error": f"Database error during velocity analysis: {str(e)}",
            "velocity_score": None
        }
    return state

def evidence_verifier_node(state: AgentState):
    """Evidence Verifier node with Complete Evidence Provenance (FO-3 / Task 5)"""
    print("Verifying collected evidence completeness across all 6 sources...")
    cust = state.get("customer_evidence", {})
    txn = state.get("transaction_evidence", {})
    merch = state.get("merchant_evidence", {})
    dev = state.get("device_evidence", {})
    loc = state.get("location_evidence", {})
    vel = state.get("velocity_evidence", {})

    failed_nodes = []
    unavailable_sources = []
    for name, node_id, ev_dict in [
        ("customer", "retrieve_customer", cust),
        ("transaction", "retrieve_transaction", txn),
        ("merchant", "retrieve_merchant", merch),
        ("device", "retrieve_device", dev),
        ("location", "retrieve_location", loc),
        ("velocity", "velocity_check", vel),
    ]:
        status = ev_dict.get("evidence_status") if isinstance(ev_dict, dict) else None
        if status == "UNAVAILABLE":
            unavailable_sources.append(name)
            failed_nodes.append(node_id)
        elif isinstance(ev_dict, dict) and ev_dict.get("error"):
            failed_nodes.append(node_id)

    state["failed_target_nodes"] = failed_nodes
    state["failed_target_node"] = failed_nodes[0] if failed_nodes else None
    state["verified_evidence"] = {
        "status": "UNAVAILABLE" if unavailable_sources else ("VERIFIED" if not failed_nodes else "PARTIAL"),
        "failed_nodes": failed_nodes,
        "unavailable_sources": unavailable_sources
    }

    # P1 Security: Filter indirect prompt injection from retrieved evidence
    from guardrails import detect_prompt_injection, sanitize_prompt_input

    injection_alerts = []
    for src_name, src_dict in [
        ("customer_evidence", cust),
        ("transaction_evidence", txn),
        ("merchant_evidence", merch),
        ("device_evidence", dev),
        ("location_evidence", loc),
    ]:
        if isinstance(src_dict, dict):
            for k, v in list(src_dict.items()):
                if isinstance(v, str):
                    is_inj, matches, risk = detect_prompt_injection(v)
                    if is_inj:
                        injection_alerts.append({
                            "source": src_name,
                            "field": k,
                            "matches": matches,
                            "risk": risk
                        })
                        src_dict[k] = sanitize_prompt_input(v)

    if injection_alerts:
        existing_signals = state.get("risk_signals", [])
        injection_signal = {
            "signal": "INDIRECT_PROMPT_INJECTION_DETECTED",
            "severity": 0.99,
            "source": "evidence_verifier",
            "evidence": {"alerts": injection_alerts}
        }
        state["risk_signals"] = existing_signals + [injection_signal]

    # P1 Security: Filter indirect prompt injection from retrieved evidence
    from guardrails import detect_prompt_injection, sanitize_prompt_input

    injection_alerts = []
    for src_name, src_dict in [
        ("customer_evidence", cust),
        ("transaction_evidence", txn),
        ("merchant_evidence", merch),
        ("device_evidence", dev),
        ("location_evidence", loc),
    ]:
        if isinstance(src_dict, dict):
            for k, v in list(src_dict.items()):
                if isinstance(v, str):
                    is_inj, matches, risk = detect_prompt_injection(v)
                    if is_inj:
                        injection_alerts.append({
                            "source": src_name,
                            "field": k,
                            "matches": matches,
                            "risk": risk
                        })
                        src_dict[k] = sanitize_prompt_input(v)

    if injection_alerts:
        existing_signals = state.get("risk_signals", [])
        injection_signal = {
            "signal": "INDIRECT_PROMPT_INJECTION_DETECTED",
            "severity": 0.99,
            "source": "evidence_verifier",
            "evidence": {"alerts": injection_alerts}
        }
        state["risk_signals"] = existing_signals + [injection_signal]

    # Task 5: Build Complete Evidence Provenance Object Model with Dynamic Confidence
    provenance_records = []
    now_iso = datetime.datetime.utcnow().isoformat()
    inv_id = state.get("investigation_id", "N/A")

    CONFIDENCE_MAP = {
        "customer_evidence": 0.95,
        "transaction_evidence": 0.95,
        "merchant_evidence": 0.95,
        "device_evidence": 0.95,
        "location_evidence": 0.95,
        "velocity_evidence": 0.85
    }

    for src_name, src_dict in [
        ("customer_evidence", cust),
        ("transaction_evidence", txn),
        ("merchant_evidence", merch),
        ("device_evidence", dev),
        ("location_evidence", loc),
        ("velocity_evidence", vel)
    ]:
        if isinstance(src_dict, dict) and "error" not in src_dict:
            conf = CONFIDENCE_MAP.get(src_name, 0.90)
            for attr, val in src_dict.items():
                provenance_records.append({
                    "source": src_name,
                    "entity": state.get("transaction_id", "N/A"),
                    "attribute": attr,
                    "value": str(val),
                    "timestamp": now_iso,
                    "confidence": conf,
                    "provenance_citation": f"{src_name}.{attr}={val} [Inv: {inv_id}]"
                })

    state["evidence_provenance"] = provenance_records
    return state

def rule_engine_node(state: AgentState):
    """Rule-based Fraud Analysis & Decoupled RiskSignal Collection (FO-5 Part 1 / Task 9)"""
    from rules import evaluate_rules
    print("Evaluating deterministic rules...")
    score, reasons = evaluate_rules(state)

    # Phase 4: Heterogeneous Graph Fraud & Suspicious Cluster Detection
    try:
        from backend.graph_fraud.integration import analyze_graph_fraud_clusters
        graph_res = analyze_graph_fraud_clusters(state)
        state["graph_cluster_evidence"] = graph_res
        cluster_signals = graph_res.get("risk_signals", [])
        cluster_risk = float(graph_res.get("cluster_risk_score", 0.0))

        if cluster_risk >= 0.70 and graph_res.get("clusters"):
            score = max(score, cluster_risk)
            for cl in graph_res["clusters"]:
                reasons.append(f"Graph Cluster Anomaly: {cl.get('explanation')}")
    except Exception as g_err:
        print(f"Warning: Graph cluster detection fallback ({g_err})")
        state["graph_cluster_evidence"] = None
        cluster_signals = []

    state["rule_score"] = score
    state["rule_reasons"] = reasons

    rule_signals = []
    for reason in reasons:
        rule_signals.append({
            "signal": "DETERMINISTIC_RULE_TRIGGERED",
            "severity": min(round(score, 2), 1.0),
            "source": "rule_engine",
            "evidence": {"rule": reason}
        })

    existing_signals = state.get("risk_signals", [])
    combined_signals = (existing_signals or []) + rule_signals + cluster_signals
    state["risk_signals"] = combined_signals
    return state

def knowledge_lookup_node(state: AgentState):
    """4-Way Hybrid Search over Real Historical Fraud Cases (Phase 3)"""
    device_evidence = state.get('device_evidence', {})
    location_evidence = state.get('location_evidence', {})
    transaction_evidence = state.get('transaction_evidence', {})
    merchant_evidence = state.get('merchant_evidence', {})

    query_parts = []
    if device_evidence.get('os'): query_parts.append(f"device OS: {device_evidence['os']}")
    if location_evidence.get('country'): query_parts.append(f"country: {location_evidence['country']}")
    if transaction_evidence.get('amount'): query_parts.append(f"amount: {transaction_evidence['amount']} {transaction_evidence.get('currency', '')}")
    if merchant_evidence.get('name'): query_parts.append(f"merchant: {merchant_evidence['name']}")
    if transaction_evidence.get('channel'): query_parts.append(f"channel: {transaction_evidence['channel']}")

    query = ", ".join(query_parts) if query_parts else "financial transaction"
    tenant = state.get("tenant_id") or "default_tenant"
    amt = float(transaction_evidence.get("amount") or 0.0)
    chan = transaction_evidence.get("channel")
    curr = transaction_evidence.get("currency") or "USD"
    ts = transaction_evidence.get("timestamp")

    print(f"Executing 4-way Hybrid Case Search for query: {query} (tenant: {tenant})")
    formatted_results = []
    try:
        from backend.cases.hybrid_search import get_hybrid_search_engine, HybridSearchQuery
        engine = get_hybrid_search_engine()
        q = HybridSearchQuery(
            query_text=query,
            transaction_amount=amt if amt > 0 else None,
            channel=chan,
            currency=curr,
            timestamp=ts,
            estimated_risk=state.get("rule_score"),
            tenant_id=tenant,
            top_k=5
        )
        hybrid_results = engine.search(q)
        for r in hybrid_results:
            formatted_results.append({
                "case_id": r.case_id,
                "description": r.case.outcome.narrative,
                "outcome": "FRAUD" if r.case.outcome.ground_truth_score >= 0.50 else "LEGITIMATE",
                "similarity": r.hybrid_score,
                "hybrid_score": r.hybrid_score,
                "vector_similarity": r.vector_similarity,
                "temporal_similarity": r.temporal_similarity,
                "risk_similarity": r.risk_similarity,
                "disposition": r.case.outcome.disposition,
                "typology": r.case.outcome.typology,
                "explanation": r.explanation
            })
    except Exception as e:
        print(f"Warning: knowledge_lookup_node hybrid fallback ({e})")

    if not formatted_results:
        try:
            formatted_results = vector_store.similarity_search(query, top_k=5, tenant_id=tenant)
        except Exception as e:
            print(f"Warning: vector_store fallback ({e})")
            formatted_results = []

    state["historical_cases"] = formatted_results
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
    
    # Priority 5 Fix: Handle hybrid_score, similarity, and similarity_distance keys correctly
    hist_cases = state.get("historical_cases", [])
    hist_scores = []
    for c in hist_cases:
        if isinstance(c, dict):
            if "hybrid_score" in c:
                hist_scores.append(float(c["hybrid_score"]))
            elif "similarity" in c:
                hist_scores.append(float(c["similarity"]))
            elif "similarity_distance" in c:
                dist = float(c["similarity_distance"])
                hist_scores.append(max(0.0, 1.0 - (dist / 2.0)))
    avg_hist_score = sum(hist_scores) / len(hist_scores) if hist_scores else 0.5

    llm_risk_estimate = None
    reasoning_text = ""

    if llm:
        tenant = state.get("tenant_id", "default_tenant")
        tokenizer = _get_or_init_pii_tokenizer(state)
        raw_prompt = get_reasoner_prompt(tenant).format(evidence_bundle=json.dumps(evidence_bundle, indent=2))
        if state.get("critic_feedback") and state.get("critic_issues"):
            raw_prompt += f"\n\nCRITICAL CRITIC FEEDBACK TO CORRECT: {state['critic_feedback']}"
        prompt = tokenizer.redact_text(raw_prompt)
        start_t = time.time()
        try:
            response = llm.invoke(prompt)
            latency_ms = (time.time() - start_t) * 1000.0
            raw_content = response.content if hasattr(response, "content") else str(response)
            content = tokenizer.rehydrate_text(raw_content)
            reasoning_text = content
            state["pii_vault"] = tokenizer.export_vault()
            metrics_collector.record_llm_call(
                investigation_id=state.get("investigation_id", "unknown"),
                node_name="reasoner",
                model=getattr(llm, "model_name", "gpt-4o-mini"),
                prompt_tokens=getattr(response, "prompt_tokens", max(1, len(prompt) // 4)),
                completion_tokens=getattr(response, "completion_tokens", max(1, len(content) // 4)),
                latency_ms=latency_ms,
                tenant_id=tenant
            )
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
            c_name = state.get("customer_evidence", {}).get("name") or "customer"
            m_name = state.get("merchant_evidence", {}).get("name") or "merchant"
            reasoning_text = f"Transaction {state.get('transaction_id')} evidence analyzed for customer {c_name} and merchant {m_name}."

    if llm_risk_estimate is None:
        risk_factors = 0
        total_factors = 4
        dev = state.get("device_evidence", {})
        loc = state.get("location_evidence", {})
        merch = state.get("merchant_evidence", {})
        vel = state.get("velocity_evidence", {})

        if dev.get("new_device"): risk_factors += 1
        if (dev.get("os") or "").lower() == "unknown os": risk_factors += 1
        if merch.get("historical_fraud_rate", 0) > 0.05: risk_factors += 1
        if (loc.get("country") or "") in ["RU", "CN", "KP", "IR"]: risk_factors += 1
        if vel.get("high_velocity_flag"): risk_factors += 1; total_factors += 1

        llm_risk_estimate = risk_factors / total_factors if total_factors > 0 else 0.5

    # Multi-Channel Decision Separation & Adjudication Policy (P1 Fix):
    # 1. Deterministic Rule Channel: Regulatory checks and laundering typologies.
    # 2. Vector Retrieval Channel: Historical precedent corroboration.
    # 3. LLM Reasoning Channel: Narrative synthesis of KYC, account type, and business context.
    #
    # Explicit Adjudication vs Compliance Alert Policy:
    # - Typology Alerts (cycles, scatter-gather, structuring proxy, velocity bursts):
    #   Represent active illicit money laundering indicators. To prevent vector suppression (e.g. cold-start
    #   vector store dampening a 0.65 structuring finding), rule_score >= 0.50 enforces a hard score floor:
    #   combined_score = max(base_combined, rule_score).
    # - Mandatory Statutory Reporting Alerts (CTR reporting threshold >= $10,000 under 31 CFR § 1010.311,
    #   or high-value wire >= $20,000): These represent regulatory recordkeeping obligations. Amount alone
    #   does NOT establish criminal laundering. The mandatory compliance alert is preserved in
    #   state["compliance_alerts"] and state["risk_signals"]. If contextual evidence confirms legitimate
    #   business purpose (e.g. verified corporate payroll, title escrow, low customer risk tier), base_combined
    #   adjudicates the laundering verdict without being artificially forced to >= 0.50.
    from rules import is_typology_rule, is_compliance_mandate_rule

    rule_reasons = state.get("rule_reasons", [])
    has_typology_alert = any(is_typology_rule(r) for r in rule_reasons)
    compliance_alerts = [r for r in rule_reasons if is_compliance_mandate_rule(r)]
    state["compliance_alerts"] = compliance_alerts
    state["has_typology_alert"] = has_typology_alert

    # Phase 2: Tabular ML Fraud Inference (LightGBM with Platt Calibration)
    ml_score = None
    try:
        from backend.ml.inference import get_inference_service
        inf_svc = get_inference_service()
        ml_pred = inf_svc.predict_from_state(state)
        state["ml_risk_score"] = ml_pred.risk_score
        state["ml_calibrated_probability"] = ml_pred.raw_probability
        state["ml_top_features"] = ml_pred.top_features
        state["ml_model_id"] = ml_pred.model_id
        ml_score = ml_pred.risk_score
    except Exception as ml_err:
        print(f"Warning: ML inference fallback ({ml_err})")
        state["ml_risk_score"] = None
        state["ml_calibrated_probability"] = None
        state["ml_top_features"] = []
        state["ml_model_id"] = "fallback"

    if ml_score is not None:
        base_combined = (0.25 * rule_score) + (0.30 * ml_score) + (0.30 * llm_risk_estimate) + (0.15 * avg_hist_score)
    else:
        base_combined = (0.35 * rule_score) + (0.40 * llm_risk_estimate) + (0.25 * avg_hist_score)

    if rule_score >= 0.50 and has_typology_alert:
        combined_score = max(base_combined, rule_score)
    elif rule_score >= 0.50 and not has_typology_alert:
        # High value with no typology alert: combine multi-channel evidence.
        # If reasoner/context confirms legitimate entity/purpose, allow base_combined to adjudicate.
        combined_score = base_combined
    else:
        combined_score = base_combined
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

    rule_llm_agreement = 1.0 - abs(rule_score - llm_risk_estimate)
    if ml_score is not None:
        ml_agreement = 1.0 - abs(ml_score - rule_score)
        agreement = (rule_llm_agreement + ml_agreement) / 2.0
    else:
        agreement = rule_llm_agreement
    grounding_quality = 1.0 if state.get("validated", True) else 0.70

    dynamic_confidence = (completeness * 0.35) + (agreement * 0.30) + (avg_hist_score * 0.15) + (grounding_quality * 0.20)
    dynamic_confidence = min(max(dynamic_confidence, 0.50), 0.98)

    state["risk_score"] = round(combined_score, 4)
    state["confidence"] = round(dynamic_confidence, 2)
    state["draft_explanation"] = reasoning_text
    state["predicted_verdict"] = "SUSPICIOUS" if combined_score >= 0.50 else "BENIGN"
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
        tenant = state.get("tenant_id", "default_tenant")
        tokenizer = _get_or_init_pii_tokenizer(state)
        raw_prompt = get_critic_prompt(tenant).format(
            draft_explanation=draft,
            evidence_bundle=json.dumps(evidence),
            velocity_analysis=json.dumps(state.get("velocity_evidence"))
        )
        prompt = tokenizer.redact_text(raw_prompt)
        start_t = time.time()
        try:
            resp = llm.invoke(prompt)
            latency_ms = (time.time() - start_t) * 1000.0
            raw_resp = resp.content if hasattr(resp, "content") else str(resp)
            resp_text = tokenizer.rehydrate_text(raw_resp)
            state["pii_vault"] = tokenizer.export_vault()
            metrics_collector.record_llm_call(
                investigation_id=state.get("investigation_id", "unknown"),
                node_name="critic",
                model=getattr(llm, "model_name", "gpt-4o-mini"),
                prompt_tokens=getattr(resp, "prompt_tokens", max(1, len(prompt) // 4)),
                completion_tokens=getattr(resp, "completion_tokens", max(1, len(resp_text) // 4)),
                latency_ms=latency_ms,
                tenant_id=tenant
            )
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
                if ("unsupported" in content.lower() or "inconsistent" in content.lower()) and "api key" not in content.lower() and "401" not in content:
                    issues_found = True
                    critic_details["severity"] = "MEDIUM"
        except Exception as e:
            print(f"Critic Node LLM skipped: {e}")
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
    reasons = []
    evidence_sources = ["customer_evidence", "transaction_evidence", "merchant_evidence", "device_evidence", "location_evidence", "velocity_evidence"]
    unavailable_sources = [
        s for s in evidence_sources
        if isinstance(state.get(s), dict) and state[s].get("evidence_status") == "UNAVAILABLE"
    ]
    for s in unavailable_sources:
        err = state[s].get("error", "Source unavailable")
        reasons.append(f"UNAVAILABLE evidence source: {s} ({err})")

    if not state.get("validated", False):
        reasons.append(f"Grounding validation failed after {state.get('retry_count', 0)} attempts.")
    if state.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        reasons.append(f"Confidence score {state.get('confidence', 0):.2f} below threshold {CONFIDENCE_THRESHOLD}.")

    rule_alert = "ACTIVE (MANDATORY COMPLIANCE ALERT)" if state.get("rule_score", 0) >= 0.50 else "NONE"
    rule_reasons = state.get("rule_reasons", [])
    rule_section = "\n- ".join(rule_reasons) if rule_reasons else "None triggered"

    escalation_report = f"""# HUMAN REVIEW ESCALATION REPORT
Investigation ID: {state['investigation_id']}
Transaction ID:   {state['transaction_id']}
Status:           ESCALATED
Rule Alert:       {rule_alert}
Risk Score:       {state.get('risk_score', 'N/A')}
Confidence:       {state.get('confidence', 'N/A')}

## Triggered Compliance Rules
- {rule_section}

## Escalation Reasons
- """ + "\n- ".join(reasons) + f"""

## Draft Explanation
{state.get('draft_explanation', 'No draft generated.')}

## Action Required
Analyst review required. Mandatory rule findings must remain active unless explicitly dispositioned.
"""
    state["report"] = escalation_report
    state["workflow_status"] = "ESCALATED"
    if state.get("predicted_verdict") is None:
        state["predicted_verdict"] = "ESCALATED"
    return state

def report_generator_node(state: AgentState):
    """Generate Final Investigation Report (FO-9)"""
    print("Generating final investigation report...")
    rule_factors = "\n".join([f"- {r}" for r in state.get("rule_reasons", [])]) if state.get("rule_reasons") else "- None"

    if llm and state.get("draft_explanation"):
        tenant = state.get("tenant_id", "default_tenant")
        tokenizer = _get_or_init_pii_tokenizer(state)
        raw_prompt = get_report_prompt(tenant) + f"\nDraft: {state['draft_explanation']}\nRule Factors:\n{rule_factors}"
        prompt = tokenizer.redact_text(raw_prompt)
        start_t = time.time()
        try:
            response = llm.invoke(prompt)
            latency_ms = (time.time() - start_t) * 1000.0
            raw_report = response.content if hasattr(response, "content") else str(response)
            report = tokenizer.rehydrate_text(raw_report)
            state["pii_vault"] = tokenizer.export_vault()
            metrics_collector.record_llm_call(
                investigation_id=state.get("investigation_id", "unknown"),
                node_name="reporter",
                model=getattr(llm, "model_name", "gpt-4o-mini"),
                prompt_tokens=getattr(response, "prompt_tokens", max(1, len(prompt) // 4)),
                completion_tokens=getattr(response, "completion_tokens", max(1, len(report) // 4)),
                latency_ms=latency_ms,
                tenant_id=tenant
            )
        except Exception:
            report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."
    else:
        report = f"## Summary\n{state.get('draft_explanation')}\n\n## Triggered Rules\n{rule_factors}\n\n## Recommendation\nRecommend manual review or block."

    state["report"] = report
    state["workflow_status"] = "RESOLVED"
    return state

def should_retry_or_human_review(state: AgentState):
    """Complete 6-Source Targeted Retry & Bounded Critic Router (Task 4)"""
    validated = state.get("validated", False)
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence", 0)
    failed_node = state.get("failed_target_node")
    critic_issues = state.get("critic_issues", False)
    critic_cycles = state.get("critic_cycle_count", 0)
    MAX_CRITIC_CYCLES = 2

    decision = ""
    reason = ""

    evidence_sources = ["customer_evidence", "transaction_evidence", "merchant_evidence", "device_evidence", "location_evidence", "velocity_evidence"]
    unavailable_sources = [
        s for s in evidence_sources
        if isinstance(state.get(s), dict) and state[s].get("evidence_status") == "UNAVAILABLE"
    ]

    if unavailable_sources:
        decision = "human_review"
        reason = f"Evidence source(s) UNAVAILABLE ({', '.join(unavailable_sources)}), escalating immediately to human review"
    elif critic_issues and validated:
        if critic_cycles < MAX_CRITIC_CYCLES:
            state["critic_cycle_count"] = critic_cycles + 1
            decision = "risk_reasoning"
            reason = f"Critic check failed (cycle {critic_cycles + 1}/{MAX_CRITIC_CYCLES}), retrying risk_reasoning"
        else:
            decision = "human_review"
            reason = f"Critic correction cycle limit reached ({MAX_CRITIC_CYCLES}), escalating to human review"
    elif not validated:
        if retry_count < MAX_RETRIES:
            valid_target_nodes = ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location", "velocity_check"]
            if failed_node and failed_node in valid_target_nodes:
                decision = failed_node
            else:
                decision = "risk_reasoning"
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
        with _audit_db_lock:
            db = SessionLocal()
            try:
                investigation_id = state.get("investigation_id")
                if investigation_id:
                    audit_log = AuditLog(
                        investigation_id=investigation_id,
                        action=f"DECISION: {decision}",
                        details=reason
                    )
                    db.add(audit_log)
                    db.commit()
            finally:
                db.close()
    except Exception as e:
        print(f"Warning: Failed to log decision audit: {e}")

    return decision

def with_audit_logger(node_func, node_name: str):
    @time_function
    def wrapper(state: AgentState):
        start_time = time.time()
        investigation_id = state.get("investigation_id")

        # Task 14: Check for investigation cancellation
        if investigation_id:
            try:
                with _audit_db_lock:
                    db = SessionLocal()
                    try:
                        inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
                        if inv and inv.status == "CANCELLED":
                            print(f"Investigation {investigation_id} is CANCELLED. Skipping {node_name} execution.")
                            audit_log = AuditLog(
                                investigation_id=investigation_id,
                                action=f"NODE_CANCELLED_SKIPPED: {node_name}",
                                details=f"Skipped execution of {node_name} due to cancellation"
                            )
                            db.add(audit_log)
                            db.commit()
                            return {"execution_trace": [f"{node_name}_CANCELLED"]}
                    finally:
                        db.close()
            except Exception as e:
                print(f"Warning: Cancellation check failed: {e}")

        try:
            new_state = node_func(state)
            if not isinstance(new_state, dict):
                new_state = {}
            new_state["execution_trace"] = [node_name]

            execution_time_ms = int((time.time() - start_time) * 1000)
            metrics_collector.record_node_execution_time(node_name, execution_time_ms / 1000.0)

            if investigation_id:
                try:
                    with _audit_db_lock:
                        db = SessionLocal()
                        try:
                            audit_log = AuditLog(
                                investigation_id=investigation_id,
                                action=f"NODE_EXECUTION: {node_name}",
                                details=f"Successfully executed {node_name} in {execution_time_ms}ms"
                            )
                            db.add(audit_log)
                            db.commit()
                        finally:
                            db.close()
                except Exception:
                    pass
            return new_state
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            investigation_id = state.get("investigation_id")
            if investigation_id:
                try:
                    with _audit_db_lock:
                        db = SessionLocal()
                        try:
                            audit_log = AuditLog(
                                investigation_id=investigation_id,
                                action=f"NODE_ERROR: {node_name}",
                                details=f"Failed to execute {node_name} after {execution_time_ms}ms: {str(e)[:500]}"
                            )
                            db.add(audit_log)
                            db.commit()
                        finally:
                            db.close()
                except Exception:
                    pass
            raise e
    return wrapper

def route_planner_tasks(state: AgentState):
    """Dynamic Task Execution Router (Priority 6 Fix)"""
    tasks = state.get("tasks", [])
    if tasks:
        return tasks
    return ["retrieve_customer", "retrieve_transaction", "retrieve_merchant", "retrieve_device", "retrieve_location"]

def build_graph(checkpointer=None):
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

    if checkpointer is None:
        from checkpointing import get_durable_checkpointer
        checkpointer = get_durable_checkpointer()
    return graph.compile(checkpointer=checkpointer)
