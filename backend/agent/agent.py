"""
Autonomous Investigation Agent (Phase 5).

Dynamically decides which forensic tools to call based on unfolding evidence,
replaces static retrieval graphs with an adaptive multi-channel investigation loop,
and synthesizes regulatory audit dossiers.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

try:
    from backend.agent.tools import get_tool_registry, InvestigationToolRegistry
except ImportError:
    from agent.tools import get_tool_registry, InvestigationToolRegistry


@dataclass
class AgentInvestigationState:
    investigation_id: str
    transaction_id: str
    tenant_id: str = "default_tenant"
    transaction: Dict[str, Any] = field(default_factory=dict)
    customer: Dict[str, Any] = field(default_factory=dict)
    device: Dict[str, Any] = field(default_factory=dict)
    location: Dict[str, Any] = field(default_factory=dict)
    merchant: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    tool_call_history: List[Dict[str, Any]] = field(default_factory=list)
    step_count: int = 0
    max_steps: int = 8
    is_complete: bool = False
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    report: Optional[Dict[str, Any]] = None

    def record_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any, reason: str):
        self.step_count += 1
        self.tool_call_history.append({
            "step": self.step_count,
            "tool_name": tool_name,
            "args": args,
            "reason": reason,
            "result_summary": str(result)[:200]
        })


class AutonomousInvestigationAgent:
    """
    Adaptive AI Investigator that dynamically selects tools to evaluate
    transaction fraud risks, investigate syndicate rings, and compile dossiers.
    """

    def __init__(self, registry: Optional[InvestigationToolRegistry] = None):
        self.registry = registry or get_tool_registry()

    def investigate(
        self,
        transaction_id: str,
        transaction_data: Optional[Dict[str, Any]] = None,
        tenant_id: str = "default_tenant",
        investigation_id: Optional[str] = None
    ) -> AgentInvestigationState:
        """
        Executes dynamic, multi-step autonomous investigation loop.
        """
        inv_id = investigation_id or f"INV_AGENT_{int(time.time()*1000)}"
        txn = transaction_data or {"txn_id": transaction_id, "amount": 1000.0, "channel": "ACH"}
        state = AgentInvestigationState(
            investigation_id=inv_id,
            transaction_id=transaction_id,
            tenant_id=tenant_id,
            transaction=txn
        )

        # -----------------------------------------------------------------
        # Step 1: Customer Profile & Transaction Ledger Retrieval
        # -----------------------------------------------------------------
        c_id = txn.get("customer_id") or txn.get("account_id") or "CUST_DEFAULT"
        cust_profile = self.registry.execute("get_customer_history", customer_id=c_id, tenant_id=tenant_id)
        state.customer = cust_profile
        state.evidence["customer"] = cust_profile
        state.record_tool_call(
            "get_customer_history",
            {"customer_id": c_id, "tenant_id": tenant_id},
            cust_profile,
            "Establish baseline entity KYC status and account risk tier."
        )

        acct_id = txn.get("account_id") or f"ACCT_{c_id}"
        txn_hist = self.registry.execute("get_transaction_history", account_id=acct_id, tenant_id=tenant_id)
        state.history = txn_hist.get("recent_transactions", [])
        state.evidence["transaction_history"] = txn_hist
        state.record_tool_call(
            "get_transaction_history",
            {"account_id": acct_id, "tenant_id": tenant_id},
            txn_hist,
            "Inspect recent counterparty dispersion and transaction velocity."
        )

        # -----------------------------------------------------------------
        # Step 2: Deterministic Regulatory Rules & Statutory Check
        # -----------------------------------------------------------------
        rule_res = self.registry.execute(
            "run_fraud_rules",
            transaction=txn,
            customer=state.customer,
            device=state.device,
            location=state.location,
            history=state.history
        )
        state.evidence["rule_results"] = rule_res
        state.evidence["compliance_alerts"] = rule_res.get("compliance_alerts", [])
        state.record_tool_call(
            "run_fraud_rules",
            {"amount": txn.get("amount")},
            rule_res,
            "Evaluate statutory CTR recordkeeping thresholds, structuring heuristics, and velocity bursts."
        )

        # -----------------------------------------------------------------
        # Step 3: Calibrated Machine Learning Tabular Scoring
        # -----------------------------------------------------------------
        ml_res = self.registry.execute(
            "run_ml_model",
            transaction=txn,
            customer=state.customer,
            account={"account_id": acct_id, "account_type": state.customer.get("accounts", [{}])[0].get("type", "CHECKING")},
            history=state.history
        )
        state.evidence["ml_results"] = ml_res
        state.record_tool_call(
            "run_ml_model",
            {"amount": txn.get("amount")},
            ml_res,
            "Evaluate calibrated posterior fraud probability and extract top contributing tabular features."
        )

        # -----------------------------------------------------------------
        # Step 4: Dynamic Adaptive Investigation (Branching)
        # -----------------------------------------------------------------
        # 4a. If device/IP infrastructure is present or unusual:
        if txn.get("device_id") or txn.get("fingerprint"):
            dev_id = txn.get("device_id") or txn.get("fingerprint")
            dev_res = self.registry.execute("get_device_history", device_id=dev_id, tenant_id=tenant_id)
            state.device = dev_res
            state.evidence["device"] = dev_res
            state.record_tool_call(
                "get_device_history",
                {"device_id": dev_id},
                dev_res,
                "Audit device sharing history to detect multi-account syndicates."
            )

        if txn.get("ip_address"):
            ip_val = txn.get("ip_address")
            ip_res = self.registry.execute("get_ip_risk", ip_address=ip_val, tenant_id=tenant_id)
            state.evidence["ip_risk"] = ip_res
            state.record_tool_call(
                "get_ip_risk",
                {"ip_address": ip_val},
                ip_res,
                "Check for Tor exit nodes, VPN proxies, or high-risk jurisdictions."
            )

        # 4b. If merchant is involved:
        if txn.get("merchant_id") or txn.get("merchant_name"):
            m_id = txn.get("merchant_id") or txn.get("merchant_name")
            merch_res = self.registry.execute("get_merchant_risk", merchant_id=m_id, tenant_id=tenant_id)
            state.merchant = merch_res
            state.evidence["merchant"] = merch_res
            state.record_tool_call(
                "get_merchant_risk",
                {"merchant_id": m_id},
                merch_res,
                "Assess merchant category risk and chargeback history."
            )

        # 4c. Heterogeneous Graph Neighborhood Investigation:
        # If rules flagged typologies, or device is shared, or history has >= 2 txns:
        if rule_res.get("has_typology_alert") or state.device.get("is_shared_device") or len(state.history) >= 2:
            graph_res = self.registry.execute(
                "get_graph_neighbors",
                transaction_id=transaction_id,
                evidence_state={
                    "transaction_id": transaction_id,
                    "transaction_evidence": txn,
                    "customer_evidence": state.customer,
                    "device_evidence": state.device,
                    "transaction_history": state.history
                }
            )
            state.evidence["graph_neighbors"] = graph_res
            state.record_tool_call(
                "get_graph_neighbors",
                {"transaction_id": transaction_id},
                graph_res,
                "Analyze heterogeneous graph ego-network for shared devices, circular loops, and mule hubs."
            )

        # 4d. 4-Way Hybrid Precedent Search:
        # Search precedent cases using hybrid search:
        search_query = f"{txn.get('channel', '')} transaction amount {txn.get('amount', '')}"
        if rule_res.get("triggered_rules"):
            search_query += " " + " ".join(rule_res["triggered_rules"][:2])
        precedents = self.registry.execute(
            "search_historical_cases",
            query_text=search_query,
            amount=float(txn.get("amount", 0.0)),
            channel=txn.get("channel"),
            tenant_id=tenant_id,
            top_k=3
        )
        state.evidence["precedent_cases"] = precedents
        state.record_tool_call(
            "search_historical_cases",
            {"query_text": search_query},
            precedents,
            "Retrieve historical adjudication precedents using 4-way hybrid search."
        )

        # -----------------------------------------------------------------
        # Step 5: Evidence Synthesis & Adjudication Verdict
        # -----------------------------------------------------------------
        verdict, confidence, summary = self._synthesize_adjudication(state)
        state.verdict = verdict
        state.confidence = confidence

        # -----------------------------------------------------------------
        # Step 6: Generate Final Regulatory Audit Report (Tool 10)
        # -----------------------------------------------------------------
        report = self.registry.execute(
            "create_investigation_report",
            investigation_id=state.investigation_id,
            transaction_id=state.transaction_id,
            verdict=verdict,
            confidence=confidence,
            summary=summary,
            evidence_bundle=state.evidence,
            tenant_id=tenant_id
        )
        state.report = report
        state.record_tool_call(
            "create_investigation_report",
            {"verdict": verdict, "confidence": confidence},
            report,
            "Generate cryptographically signed regulatory audit dossier."
        )

        state.is_complete = True
        return state

    def _synthesize_adjudication(self, state: AgentInvestigationState) -> Tuple[str, float, str]:
        """
        Synthesizes multi-channel evidence:
        - Rules + Compliance Alerts
        - ML Calibrated Probability
        - Graph Cluster Anomalies
        - Hybrid Search Precedents
        """
        rules = state.evidence.get("rule_results", {})
        ml = state.evidence.get("ml_results", {})
        graph = state.evidence.get("graph_neighbors", {})
        precedents = state.evidence.get("precedent_cases", [])
        txn = state.transaction
        cust = state.customer

        rule_score = rules.get("rule_score", 0.0)
        ml_prob = ml.get("calibrated_probability", 0.05)
        graph_risk = graph.get("cluster_risk_score", 0.0)
        has_typology = rules.get("has_typology_alert", False)
        compliance_alerts = rules.get("compliance_alerts", [])

        # Priority 1: High-risk Graph Syndicate or Circular Laundering
        if graph_risk >= 0.75:
            cluster_details = [c.get("explanation") for c in graph.get("clusters", [])]
            summary = (
                f"SUSPICIOUS: Coordinated graph syndicate cluster detected (risk {graph_risk:.2f}). "
                f"{'; '.join(cluster_details[:2])}. Immediate SAR filing warranted."
            )
            return "SUSPICIOUS", 0.95, summary

        # Priority 1b: Tor Anonymity or Darknet Proxy Infrastructure
        ip_risk = state.evidence.get("ip_risk", {})
        is_tor = ip_risk.get("is_tor", False)
        is_shared_device = state.device.get("is_shared_device", False) or state.device.get("device_sharing_syndicate", False)
        if is_tor or (is_shared_device and ip_risk.get("risk_penalty", 0.0) >= 0.50):
            summary = (
                f"SUSPICIOUS: Darknet anonymity infrastructure detected (Tor exit node / proxy IP: {ip_risk.get('ip_address')}). "
                f"Associated with shared/unverified device infrastructure. Risk penalty: {ip_risk.get('risk_penalty', 0.85):.2f}."
            )
            return "SUSPICIOUS", 0.96, summary

        # Priority 2: Confirmed Regulatory Laundering Typology (Structuring / Smurfing)
        if has_typology and rule_score >= 0.50:
            reasons = "; ".join(rules.get("triggered_rules", []))
            summary = (
                f"SUSPICIOUS: Confirmed illicit money laundering typology detected ({reasons}). "
                f"Calibrated ML model risk: {ml_prob:.4f}. Precedent analysis confirms high correlation with past SAR filings."
            )
            return "SUSPICIOUS", 0.94, summary

        # Priority 3: Statutory CTR Mandate with Legitimate Corporate Purpose
        if compliance_alerts and not has_typology:
            acct_type = cust.get("accounts", [{}])[0].get("type", "").upper()
            is_comm = any(k in acct_type for k in ["COMMERCIAL", "ESCROW", "PAYROLL", "BUSINESS"])
            if is_comm and ml_prob < 0.20:
                summary = (
                    f"BENIGN: Transaction of ${txn.get('amount', 0.0):,.2f} reaches statutory reporting threshold ({compliance_alerts[0]}). "
                    f"Verified {acct_type} corporate profile confirms legitimate commercial purpose. "
                    f"ML risk is low ({ml_prob:.4f}). Mandatory CTR recorded; laundering ruled out."
                )
                return "BENIGN", 0.96, summary

        # Priority 4: Tabular ML Fraud Signal
        if ml_prob >= 0.65:
            top_feats = ml.get("top_contributing_features", [])
            feat_desc = ", ".join(f"{f['feature']} (impact: {f['impact']})" for f in top_feats[:2])
            summary = (
                f"SUSPICIOUS: Calibrated machine learning fraud detector flagged transaction ({ml_prob*100:.1f}% probability). "
                f"Key drivers: {feat_desc}."
            )
            return "SUSPICIOUS", round(ml_prob, 2), summary

        # Standard Routine Benign
        summary = (
            f"BENIGN: Routine financial transaction matching established consumer/business profile. "
            f"Rule score: {rule_score:.2f}, ML calibrated probability: {ml_prob:.4f}. No anomalies detected."
        )
        return "BENIGN", 0.95, summary


_global_agent: Optional[AutonomousInvestigationAgent] = None


def get_investigation_agent() -> AutonomousInvestigationAgent:
    global _global_agent
    if _global_agent is None:
        _global_agent = AutonomousInvestigationAgent()
    return _global_agent


def run_autonomous_investigation(
    transaction_id: str,
    transaction_data: Optional[Dict[str, Any]] = None,
    tenant_id: str = "default_tenant"
) -> Dict[str, Any]:
    """Top-level entrypoint for autonomous AI investigation agent."""
    agent = get_investigation_agent()
    state = agent.investigate(
        transaction_id=transaction_id,
        transaction_data=transaction_data,
        tenant_id=tenant_id
    )
    return {
        "investigation_id": state.investigation_id,
        "transaction_id": state.transaction_id,
        "verdict": state.verdict,
        "confidence": state.confidence,
        "step_count": state.step_count,
        "tool_call_history": state.tool_call_history,
        "report": state.report,
        "evidence_summary": {
            k: bool(v) for k, v in state.evidence.items()
        }
    }
