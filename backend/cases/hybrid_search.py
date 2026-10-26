"""
4-Way Hybrid Search Engine (Phase 3).

Implements:
Hybrid Search = Metadata Filtering + Vector Similarity + Temporal Similarity + Risk Similarity

Equation:
Score_hybrid = (w_vec * Sim_vec) + (w_temp * Sim_temp) + (w_risk * Sim_risk)
"""

import math
import datetime
import re
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.cases.schema import HistoricalCase, HybridSearchQuery, HybridSearchResult
from backend.cases.database import HistoricalCaseStore, get_case_store


def _parse_iso_dt(ts: Optional[str]) -> Optional[datetime.datetime]:
    if not ts:
        return None
    try:
        clean = ts.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        return None


def _tokenize_text(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-\$]+\b", text)]


def _compute_text_cosine_sim(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    q_counts: Dict[str, float] = {}
    for t in query_tokens:
        q_counts[t] = q_counts.get(t, 0.0) + 1.0

    d_counts: Dict[str, float] = {}
    for t in doc_tokens:
        d_counts[t] = d_counts.get(t, 0.0) + 1.0

    dot = 0.0
    for t, q_val in q_counts.items():
        if t in d_counts:
            dot += q_val * d_counts[t]

    q_norm = math.sqrt(sum(v * v for v in q_counts.values()))
    d_norm = math.sqrt(sum(v * v for v in d_counts.values()))

    if q_norm == 0.0 or d_norm == 0.0:
        return 0.0
    return min(max(float(dot / (q_norm * d_norm)), 0.0), 1.0)


class HybridSearchEngine:
    """
    Orchestrates metadata filtering, vector semantic search, temporal decay,
    and risk profile matching for historical fraud investigations.
    """

    def __init__(
        self,
        store: Optional[HistoricalCaseStore] = None,
        chroma_client: Optional[Any] = None,
        decay_half_life_days: float = 60.0
    ):
        self.store = store or get_case_store()
        self.chroma_client = chroma_client
        self.decay_half_life_days = decay_half_life_days

    def search(self, query: HybridSearchQuery) -> List[HybridSearchResult]:
        """
        Executes full 4-stage hybrid search pipeline:
        1. Metadata Filtering (SQL predicate pushdown)
        2. Vector Semantic Similarity
        3. Temporal Similarity
        4. Risk Profile Similarity
        5. Weighted Hybrid Aggregation
        """
        # Step 1: Metadata Filtering
        candidates: List[HistoricalCase] = self.store.filter_candidates(query)

        if not candidates:
            # If strict metadata filter yielded 0, retry without channel/amount filters for fallback
            relaxed_query = HybridSearchQuery(
                query_text=query.query_text,
                transaction_amount=query.transaction_amount,
                timestamp=query.timestamp,
                estimated_risk=query.estimated_risk,
                tenant_id=query.tenant_id,
                top_k=query.top_k
            )
            candidates = self.store.filter_candidates(relaxed_query)

        if not candidates:
            return []

        # Weights normalization
        w_vec = max(0.0, query.weight_vector)
        w_temp = max(0.0, query.weight_temporal)
        w_risk = max(0.0, query.weight_risk)
        total_w = w_vec + w_temp + w_risk
        if total_w == 0.0:
            w_vec, w_temp, w_risk = 0.40, 0.20, 0.40
            total_w = 1.0
        w_vec, w_temp, w_risk = w_vec / total_w, w_temp / total_w, w_risk / total_w

        # Prepare Query Signals
        query_text = query.query_text or ""
        if not query_text and query.transaction_amount:
            query_text = f"Transaction amount {query.transaction_amount} {query.channel or ''}"
        query_tokens = _tokenize_text(query_text)

        query_dt = _parse_iso_dt(query.timestamp) or datetime.datetime.now(datetime.timezone.utc)
        query_risk = query.estimated_risk
        if query_risk is None:
            # Heuristic default based on amount and channel
            amt = query.transaction_amount or 0.0
            query_risk = 0.65 if (8000.0 <= amt <= 9999.0) else (0.75 if amt >= 50000.0 else 0.20)

        results: List[Tuple[float, HybridSearchResult]] = []

        for case in candidates:
            # 2. Vector Semantic Similarity
            doc_str = case.generate_search_document()
            doc_tokens = _tokenize_text(doc_str)
            sim_vec = _compute_text_cosine_sim(query_tokens, doc_tokens)

            # 3. Temporal Similarity (Exponential Decay)
            sim_temp = self._compute_temporal_similarity(query_dt, case)

            # 4. Risk Profile Similarity
            sim_risk = self._compute_risk_similarity(query, query_risk, case)

            # 5. Hybrid Weighted Aggregation
            hybrid_score = (w_vec * sim_vec) + (w_temp * sim_temp) + (w_risk * sim_risk)
            hybrid_score = min(max(hybrid_score, 0.0), 1.0)

            # Generate Explainability Rationale
            explanation = (
                f"Hybrid Match [{case.outcome.disposition}]: "
                f"Vector={sim_vec:.2f}, Temporal={sim_temp:.2f}, Risk={sim_risk:.2f} "
                f"-> Hybrid={hybrid_score:.2f} ({case.outcome.typology})"
            )

            res = HybridSearchResult(
                case_id=case.case_id,
                tenant_id=case.tenant_id,
                case=case,
                vector_similarity=round(sim_vec, 4),
                temporal_similarity=round(sim_temp, 4),
                risk_similarity=round(sim_risk, 4),
                hybrid_score=round(hybrid_score, 4),
                explanation=explanation
            )
            results.append((hybrid_score, res))

        # Sort descending by hybrid_score
        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results[:query.top_k]]

    def _compute_temporal_similarity(self, query_dt: datetime.datetime, case: HistoricalCase) -> float:
        """Exponential decay based on day difference."""
        case_dt = _parse_iso_dt(case.transaction.timestamp) or _parse_iso_dt(case.created_at)
        if not case_dt:
            return 0.50

        # Ensure tz-awareness compatibility
        if query_dt.tzinfo is None and case_dt.tzinfo is not None:
            query_dt = query_dt.replace(tzinfo=datetime.timezone.utc)
        elif query_dt.tzinfo is not None and case_dt.tzinfo is None:
            case_dt = case_dt.replace(tzinfo=datetime.timezone.utc)

        delta_days = abs((query_dt - case_dt).total_seconds()) / 86400.0
        # Sim = exp(-delta_days / tau)
        sim = math.exp(-delta_days / max(1.0, self.decay_half_life_days))
        return min(max(float(sim), 0.0), 1.0)

    def _compute_risk_similarity(
        self,
        query: HybridSearchQuery,
        query_risk: float,
        case: HistoricalCase
    ) -> float:
        """Computes similarity of estimated vs precedent fraud risk and amount magnitude."""
        case_risk = case.outcome.ground_truth_score
        risk_diff = abs(query_risk - case_risk)
        score_sim = 1.0 - min(risk_diff, 1.0)

        # Amount scale similarity (orders of magnitude)
        amt_q = max(1.0, query.transaction_amount or 1000.0)
        amt_c = max(1.0, case.transaction.amount)
        log_diff = abs(math.log10(amt_q) - math.log10(amt_c))
        amt_sim = max(0.0, 1.0 - (log_diff / 3.0))

        # Channel match bonus
        chan_bonus = 0.10 if query.channel and query.channel.upper() == case.transaction.channel.upper() else 0.0

        risk_sim = (0.60 * score_sim) + (0.40 * amt_sim) + chan_bonus
        return min(max(float(risk_sim), 0.0), 1.0)


_global_engine: Optional[HybridSearchEngine] = None


def get_hybrid_search_engine() -> HybridSearchEngine:
    global _global_engine
    if _global_engine is None:
        _global_engine = HybridSearchEngine()
    return _global_engine
