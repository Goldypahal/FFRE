"""
Metrics collection utilities for monitoring FFIRE performance.
"""

import time
from threading import Lock
from typing import Dict, List, Optional
from collections import defaultdict, deque

MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-4o-mini": {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000},
    "gpt-4-turbo": {"prompt": 10.00 / 1_000_000, "completion": 30.00 / 1_000_000},
    "gemini-1.5-pro": {"prompt": 1.25 / 1_000_000, "completion": 5.00 / 1_000_000},
    "gemini-1.5-flash": {"prompt": 0.075 / 1_000_000, "completion": 0.30 / 1_000_000},
    "claude-3-5-sonnet": {"prompt": 3.00 / 1_000_000, "completion": 15.00 / 1_000_000},
    "default": {"prompt": 0.50 / 1_000_000, "completion": 1.50 / 1_000_000}
}

class MetricsCollector:
    """Collects and stores performance metrics for monitoring."""

    def __init__(self, max_history: int = 1000):
        self._lock = Lock()
        self._max_history = max_history

        # Investigation metrics
        self._investigation_durations: Dict[str, List[float]] = defaultdict(list)
        self._retry_counts: Dict[str, List[int]] = defaultdict(list)
        self._confidence_scores: Dict[str, List[float]] = defaultdict(list)
        self._risk_scores: Dict[str, List[float]] = defaultdict(list)

        # Node execution metrics
        self._node_execution_times: Dict[str, List[float]] = defaultdict(list)

        # Counters
        self._total_investigations = 0
        self._successful_investigations = 0
        self._failed_investigations = 0
        self._escalated_investigations = 0

        # Timing for current investigations
        self._investigation_start_times: Dict[str, float] = {}

        # LLM Observability & Cost Intelligence (Chapter 89)
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_llm_cost_usd = 0.0
        self._total_llm_calls = 0
        self._tokens_by_model = defaultdict(lambda: {"prompt": 0, "completion": 0, "cost": 0.0, "calls": 0})
        self._tokens_by_node = defaultdict(lambda: {"prompt": 0, "completion": 0, "cost": 0.0, "calls": 0})
        self._cost_by_tenant = defaultdict(float)
        self._tokens_by_tenant = defaultdict(lambda: {"prompt": 0, "completion": 0, "total": 0})
        self._llm_latencies: List[float] = []
        self._cost_per_investigation = defaultdict(float)
        self._recent_llm_calls = deque(maxlen=100)

    def start_investigation_timer(self, investigation_id: str):
        """Start timing an investigation."""
        with self._lock:
            self._investigation_start_times[investigation_id] = time.time()

    def stop_investigation_timer(self, investigation_id: str, status: str = "completed"):
        """Stop timing an investigation and record the duration."""
        with self._lock:
            if investigation_id in self._investigation_start_times:
                duration = time.time() - self._investigation_start_times[investigation_id]
                self._investigation_durations[investigation_id].append(duration)
                # Keep only the most recent entries
                if len(self._investigation_durations[investigation_id]) > self._max_history:
                    self._investigation_durations[investigation_id] = \
                        self._investigation_durations[investigation_id][-self._max_history:]

                # Update counters
                self._total_investigations += 1
                if status == "completed":
                    self._successful_investigations += 1
                elif status == "failed":
                    self._failed_investigations += 1
                elif status == "escalated":
                    self._escalated_investigations += 1

                # Clean up
                del self._investigation_start_times[investigation_id]

    def record_retry_count(self, investigation_id: str, retry_count: int):
        """Record the retry count for an investigation."""
        with self._lock:
            self._retry_counts[investigation_id].append(retry_count)
            if len(self._retry_counts[investigation_id]) > self._max_history:
                self._retry_counts[investigation_id] = \
                    self._retry_counts[investigation_id][-self._max_history:]

    def record_confidence_score(self, investigation_id: str, confidence: float):
        """Record the confidence score for an investigation."""
        with self._lock:
            self._confidence_scores[investigation_id].append(confidence)
            if len(self._confidence_scores[investigation_id]) > self._max_history:
                self._confidence_scores[investigation_id] = \
                    self._confidence_scores[investigation_id][-self._max_history:]

    def record_risk_score(self, investigation_id: str, risk_score: float):
        """Record the risk score for an investigation."""
        with self._lock:
            self._risk_scores[investigation_id].append(risk_score)
            if len(self._risk_scores[investigation_id]) > self._max_history:
                self._risk_scores[investigation_id] = \
                    self._risk_scores[investigation_id][-self._max_history:]

    def record_node_execution_time(self, node_name: str, execution_time_ms: float):
        """Record the execution time for a node."""
        with self._lock:
            self._node_execution_times[node_name].append(execution_time_ms)
            if len(self._node_execution_times[node_name]) > self._max_history:
                self._node_execution_times[node_name] = \
                    self._node_execution_times[node_name][-self._max_history:]

    def get_investigation_duration_stats(self) -> dict:
        """Get statistics for investigation durations."""
        with self._lock:
            all_durations = []
            for durations in self._investigation_durations.values():
                all_durations.extend(durations)

            if not all_durations:
                return {"count": 0, "mean": 0, "median": 0, "p95": 0, "p99": 0}

            sorted_durations = sorted(all_durations)
            count = len(sorted_durations)
            mean = sum(sorted_durations) / count
            median = sorted_durations[count // 2] if count % 2 == 1 else \
                     (sorted_durations[count // 2 - 1] + sorted_durations[count // 2]) / 2
            p95_index = int(count * 0.95)
            p99_index = int(count * 0.99)
            p95 = sorted_durations[min(p95_index, count - 1)]
            p99 = sorted_durations[min(p99_index, count - 1)]

            return {
                "count": count,
                "mean": mean,
                "median": median,
                "p95": p95,
                "p99": p99
            }

    def get_retry_count_stats(self) -> dict:
        """Get statistics for retry counts."""
        with self._lock:
            all_retries = []
            for retries in self._retry_counts.values():
                all_retries.extend(retries)

            if not all_retries:
                return {"count": 0, "mean": 0, "max": 0}

            return {
                "count": len(all_retries),
                "mean": sum(all_retries) / len(all_retries),
                "max": max(all_retries)
            }

    def get_confidence_score_stats(self) -> dict:
        """Get statistics for confidence scores."""
        with self._lock:
            all_scores = []
            for scores in self._confidence_scores.values():
                all_scores.extend(scores)

            if not all_scores:
                return {"count": 0, "mean": 0, "min": 0, "max": 0}

            return {
                "count": len(all_scores),
                "mean": sum(all_scores) / len(all_scores),
                "min": min(all_scores),
                "max": max(all_scores)
            }

    def get_risk_score_stats(self) -> dict:
        """Get statistics for risk scores."""
        with self._lock:
            all_scores = []
            for scores in self._risk_scores.values():
                all_scores.extend(scores)

            if not all_scores:
                return {"count": 0, "mean": 0, "min": 0, "max": 0}

            return {
                "count": len(all_scores),
                "mean": sum(all_scores) / len(all_scores),
                "min": min(all_scores),
                "max": max(all_scores)
            }

    def get_node_execution_time_stats(self) -> dict:
        """Get statistics for node execution times."""
        with self._lock:
            result = {}
            for node_name, times in self._node_execution_times.items():
                if times:
                    result[node_name] = {
                        "count": len(times),
                        "mean": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times)
                    }
                else:
                    result[node_name] = {
                        "count": 0,
                        "mean": 0,
                        "min": 0,
                        "max": 0
                    }
            return result

    def get_investment_outcome_counts(self) -> dict:
        """Get counts of investigation outcomes."""
        with self._lock:
            return {
                "total": self._total_investigations,
                "successful": self._successful_investigations,
                "failed": self._failed_investigations,
                "escalated": self._escalated_investigations
            }

    def record_investigation_time(self, investigation_id: str, duration: float):
        """Record the total investigation time for metrics."""
        with self._lock:
            self._investigation_durations[investigation_id].append(duration)
            # Keep only the most recent entries
            if len(self._investigation_durations[investigation_id]) > self._max_history:
                self._investigation_durations[investigation_id] = \
                    self._investigation_durations[investigation_id][-self._max_history:]

    def record_failed_investigation(self):
        """Increment the failed investigations counter."""
        with self._lock:
            self._failed_investigations += 1
            self._total_investigations += 1

    def calculate_token_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate USD cost for prompt and completion tokens based on model rate card."""
        rate = MODEL_PRICING.get(model, MODEL_PRICING["default"])
        cost = (prompt_tokens * rate["prompt"]) + (completion_tokens * rate["completion"])
        return cost

    def record_llm_call(
        self,
        investigation_id: str,
        node_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        tenant_id: str = "default_tenant"
    ) -> float:
        """Record an LLM invocation telemetry event with token accounting and cost tracking."""
        cost = self.calculate_token_cost(model, prompt_tokens, completion_tokens)
        total_toks = prompt_tokens + completion_tokens

        with self._lock:
            self._total_prompt_tokens += prompt_tokens
            self._total_completion_tokens += completion_tokens
            self._total_llm_cost_usd += cost
            self._total_llm_calls += 1

            self._tokens_by_model[model]["prompt"] += prompt_tokens
            self._tokens_by_model[model]["completion"] += completion_tokens
            self._tokens_by_model[model]["cost"] += cost
            self._tokens_by_model[model]["calls"] += 1

            self._tokens_by_node[node_name]["prompt"] += prompt_tokens
            self._tokens_by_node[node_name]["completion"] += completion_tokens
            self._tokens_by_node[node_name]["cost"] += cost
            self._tokens_by_node[node_name]["calls"] += 1

            self._cost_by_tenant[tenant_id] += cost
            self._tokens_by_tenant[tenant_id]["prompt"] += prompt_tokens
            self._tokens_by_tenant[tenant_id]["completion"] += completion_tokens
            self._tokens_by_tenant[tenant_id]["total"] += total_toks

            self._cost_per_investigation[investigation_id] += cost
            self._llm_latencies.append(latency_ms)
            if len(self._llm_latencies) > self._max_history:
                self._llm_latencies = self._llm_latencies[-self._max_history:]

            self._recent_llm_calls.append({
                "timestamp": time.time(),
                "investigation_id": investigation_id,
                "node_name": node_name,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_toks,
                "latency_ms": round(latency_ms, 2),
                "cost_usd": round(cost, 6),
                "tenant_id": tenant_id
            })

        return cost

    def get_llm_observability_stats(self, tenant_id: Optional[str] = None) -> dict:
        """Return aggregated LLM token usage, cost intelligence, and latency percentiles."""
        with self._lock:
            total_tokens = self._total_prompt_tokens + self._total_completion_tokens

            # Compute latency percentiles
            if self._llm_latencies:
                sorted_lats = sorted(self._llm_latencies)
                count = len(sorted_lats)
                mean_lat = sum(sorted_lats) / count
                median_lat = sorted_lats[count // 2]
                p95 = sorted_lats[min(int(count * 0.95), count - 1)]
                p99 = sorted_lats[min(int(count * 0.99), count - 1)]
            else:
                count = 0
                mean_lat = median_lat = p95 = p99 = 0.0

            # Tenant-scoped metrics if tenant_id is provided
            if tenant_id:
                tenant_cost = self._cost_by_tenant.get(tenant_id, 0.0)
                tenant_toks = self._tokens_by_tenant.get(tenant_id, {"prompt": 0, "completion": 0, "total": 0})
                recent = [c for c in self._recent_llm_calls if c.get("tenant_id") == tenant_id]
            else:
                tenant_cost = self._total_llm_cost_usd
                tenant_toks = {
                    "prompt": self._total_prompt_tokens,
                    "completion": self._total_completion_tokens,
                    "total": total_tokens
                }
                recent = list(self._recent_llm_calls)

            return {
                "total_prompt_tokens": self._total_prompt_tokens if not tenant_id else tenant_toks["prompt"],
                "total_completion_tokens": self._total_completion_tokens if not tenant_id else tenant_toks["completion"],
                "total_tokens": total_tokens if not tenant_id else tenant_toks["total"],
                "total_cost_usd": round(tenant_cost, 6),
                "total_llm_calls": self._total_llm_calls,
                "latency_stats_ms": {
                    "count": count,
                    "mean": round(mean_lat, 2),
                    "median": round(median_lat, 2),
                    "p95": round(p95, 2),
                    "p99": round(p99, 2)
                },
                "tokens_by_model": dict(self._tokens_by_model),
                "tokens_by_node": dict(self._tokens_by_node),
                "cost_by_tenant": dict(self._cost_by_tenant),
                "recent_calls": recent[-20:]
            }

    def reset_llm_metrics(self):
        """Reset LLM metrics for testing isolation."""
        with self._lock:
            self._total_prompt_tokens = 0
            self._total_completion_tokens = 0
            self._total_llm_cost_usd = 0.0
            self._total_llm_calls = 0
            self._tokens_by_model.clear()
            self._tokens_by_node.clear()
            self._cost_by_tenant.clear()
            self._tokens_by_tenant.clear()
            self._llm_latencies.clear()
            self._cost_per_investigation.clear()
            self._recent_llm_calls.clear()

    def get_summary(self) -> dict:
        """Get aggregated summary of all metrics."""
        dur_stats = self.get_investigation_duration_stats()
        return {
            "investigation_count": dur_stats["count"],
            "duration_stats": dur_stats,
            "risk_score_stats": self.get_risk_score_stats(),
            "confidence_score_stats": self.get_confidence_score_stats(),
            "node_execution_stats": self.get_node_execution_time_stats(),
            "outcomes": self.get_investment_outcome_counts(),
            "llm_observability": self.get_llm_observability_stats()
        }


# Global instance
metrics_collector = MetricsCollector()