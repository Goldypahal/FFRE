"""
Production AI Investigation Agent Subsystem (Phase 5).

Provides dynamic, tool-calling autonomous financial crime investigation agents
equipped with 10 specialized forensic tools:
- get_customer_history
- get_transaction_history
- get_device_history
- get_merchant_risk
- get_ip_risk
- search_historical_cases
- run_fraud_rules
- run_ml_model
- get_graph_neighbors
- create_investigation_report
"""

from backend.agent.tools import (
    InvestigationToolRegistry,
    get_customer_history,
    get_transaction_history,
    get_device_history,
    get_merchant_risk,
    get_ip_risk,
    search_historical_cases,
    run_fraud_rules,
    run_ml_model,
    get_graph_neighbors,
    create_investigation_report,
)
from backend.agent.agent import (
    AutonomousInvestigationAgent,
    AgentInvestigationState,
    run_autonomous_investigation,
)

__all__ = [
    "InvestigationToolRegistry",
    "get_customer_history",
    "get_transaction_history",
    "get_device_history",
    "get_merchant_risk",
    "get_ip_risk",
    "search_historical_cases",
    "run_fraud_rules",
    "run_ml_model",
    "get_graph_neighbors",
    "create_investigation_report",
    "AutonomousInvestigationAgent",
    "AgentInvestigationState",
    "run_autonomous_investigation",
]
