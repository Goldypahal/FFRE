"""
Metrics collection utilities for monitoring FFIRE performance.
"""

import time
from threading import Lock
from typing import Dict, List, Optional
from collections import defaultdict, deque

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

    def get_summary(self) -> dict:
        """Get aggregated summary of all metrics."""
        dur_stats = self.get_investigation_duration_stats()
        return {
            "investigation_count": dur_stats["count"],
            "duration_stats": dur_stats,
            "risk_score_stats": self.get_risk_score_stats(),
            "confidence_score_stats": self.get_confidence_score_stats(),
            "node_execution_stats": self.get_node_execution_time_stats(),
            "outcomes": self.get_investment_outcome_counts()
        }


# Global instance
metrics_collector = MetricsCollector()