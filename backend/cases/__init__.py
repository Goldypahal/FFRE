"""
FFIRE Real Historical Case System & Hybrid Search Subsystem (Phase 3).

Provides:
- Comprehensive Historical Case Schema (Transaction + Customer + Merchant + Device + Location + Behavior + Outcome)
- Persistent Historical Case Database Store
- 4-Way Hybrid Search Engine (Metadata Filtering + Vector Sim + Temporal Sim + Risk Sim)
- Seeder with 100+ realistic AML/fraud precedent cases
- Native LangGraph Integration
"""

from backend.cases.schema import (
    TransactionFeatures,
    CustomerFeatures,
    MerchantFeatures,
    DeviceFeatures,
    LocationFeatures,
    BehaviorFeatures,
    CaseOutcome,
    HistoricalCase,
    HybridSearchQuery,
    HybridSearchResult,
)
from backend.cases.database import HistoricalCaseStore, get_case_store
from backend.cases.hybrid_search import HybridSearchEngine, get_hybrid_search_engine

__all__ = [
    "TransactionFeatures",
    "CustomerFeatures",
    "MerchantFeatures",
    "DeviceFeatures",
    "LocationFeatures",
    "BehaviorFeatures",
    "CaseOutcome",
    "HistoricalCase",
    "HybridSearchQuery",
    "HybridSearchResult",
    "HistoricalCaseStore",
    "get_case_store",
    "HybridSearchEngine",
    "get_hybrid_search_engine",
]
