"""
Benchmark Report Generator for FFIRE.
Computes statistical percentiles (p50, p90, p95, p99), throughput (ops/sec),
evaluates SLA thresholds, and exports structured JSON and GitHub Markdown reports.
"""

import os
import json
import math
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class TierMetrics:
    workers: int
    total_requests: int
    successes: int
    failures: int
    failure_rate_pct: float
    total_duration_sec: float
    throughput_ops_sec: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    stddev_ms: float
    meets_p95_sla: bool
    meets_p99_sla: bool

@dataclass
class BenchmarkSummary:
    title: str
    manifest_name: str
    runner_mode: str
    llm_provider: str
    llm_model: str
    timestamp: str
    tiers: Dict[str, TierMetrics] = field(default_factory=dict)
    all_slas_met: bool = True
    checkpoint_safety_verified: bool = True
    notes: List[str] = field(default_factory=list)

class BenchmarkReportGenerator:
    """Calculates statistical metrics and formats reports."""

    @staticmethod
    def calculate_percentiles(durations_sec: List[float]) -> Dict[str, float]:
        """Calculates exact statistical percentiles from durations in seconds."""
        if not durations_sec:
            return {
                "p50_ms": 0.0, "p90_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0,
                "mean_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0, "stddev_ms": 0.0
            }

        sorted_ms = sorted([d * 1000.0 for d in durations_sec])
        n = len(sorted_ms)

        def get_pct(p: float) -> float:
            idx = int(math.ceil(p * n)) - 1
            idx = max(0, min(idx, n - 1))
            return sorted_ms[idx]

        mean = statistics.mean(sorted_ms)
        stddev = statistics.stdev(sorted_ms) if n > 1 else 0.0

        return {
            "p50_ms": round(get_pct(0.50), 2),
            "p90_ms": round(get_pct(0.90), 2),
            "p95_ms": round(get_pct(0.95), 2),
            "p99_ms": round(get_pct(0.99), 2),
            "mean_ms": round(mean, 2),
            "min_ms": round(min(sorted_ms), 2),
            "max_ms": round(max(sorted_ms), 2),
            "stddev_ms": round(stddev, 2)
        }

    @classmethod
    def build_tier_metrics(
        cls,
        workers: int,
        durations_sec: List[float],
        wall_time_sec: float,
        failures: int = 0,
        p95_target_ms: float = 5000.0,
        p99_target_ms: float = 8000.0
    ) -> TierMetrics:
        total = len(durations_sec) + failures
        successes = len(durations_sec)
        fail_pct = (failures / total * 100.0) if total > 0 else 0.0
        throughput = total / wall_time_sec if wall_time_sec > 0 else 0.0

        pcts = cls.calculate_percentiles(durations_sec)

        meets_p95 = pcts["p95_ms"] <= p95_target_ms and fail_pct == 0.0
        meets_p99 = pcts["p99_ms"] <= p99_target_ms and fail_pct == 0.0

        return TierMetrics(
            workers=workers,
            total_requests=total,
            successes=successes,
            failures=failures,
            failure_rate_pct=round(fail_pct, 2),
            total_duration_sec=round(wall_time_sec, 3),
            throughput_ops_sec=round(throughput, 2),
            p50_ms=pcts["p50_ms"],
            p90_ms=pcts["p90_ms"],
            p95_ms=pcts["p95_ms"],
            p99_ms=pcts["p99_ms"],
            mean_ms=pcts["mean_ms"],
            min_ms=pcts["min_ms"],
            max_ms=pcts["max_ms"],
            stddev_ms=pcts["stddev_ms"],
            meets_p95_sla=meets_p95,
            meets_p99_sla=meets_p99
        )

    @staticmethod
    def generate_markdown(summary: BenchmarkSummary) -> str:
        """Renders GitHub Markdown table and report from BenchmarkSummary."""
        lines = []
        lines.append(f"# {summary.title}")
        lines.append("")
        lines.append(f"- **Manifest**: `{summary.manifest_name}`")
        lines.append(f"- **Execution Mode**: `{summary.runner_mode}`")
        lines.append(f"- **Model Provider**: `{summary.llm_provider}` (`{summary.llm_model}`)")
        lines.append(f"- **Timestamp**: `{summary.timestamp}`")
        verdict = "[PASS] ALL SLAS MET" if summary.all_slas_met else "[FAIL] SLA VIOLATION"
        safety = "[PASS] Zero Lineage Breaks" if summary.checkpoint_safety_verified else "[FAIL] Integrity Issue Detected"
        lines.append(f"- **Overall SLA Status**: {verdict}")
        lines.append(f"- **Checkpoint Safety**: {safety}")
        lines.append("")
        lines.append("## Concurrency Tier Performance Summary")
        lines.append("")
        lines.append("| Concurrency | Requests | Success / Fail | Throughput | p50 Latency | p95 Latency | p99 Latency | SLA Status |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for w_str, m in sorted(summary.tiers.items(), key=lambda x: int(x[0])):
            sla_icon = "[MET]" if m.meets_p95_sla and m.meets_p99_sla else "[EXCEEDED]"
            lines.append(
                f"| **{m.workers} workers** | {m.total_requests} | {m.successes} / {m.failures} ({m.failure_rate_pct:.1f}%) | "
                f"**{m.throughput_ops_sec:.2f} ops/s** | {m.p50_ms:.1f} ms | **{m.p95_ms:.1f} ms** | {m.p99_ms:.1f} ms | {sla_icon} |"
            )

        lines.append("")
        if summary.notes:
            lines.append("## Notes & Observations")
            for note in summary.notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def export_results(
        cls,
        summary: BenchmarkSummary,
        output_json_path: str,
        output_md_path: Optional[str] = None
    ):
        """Exports benchmark results to JSON and optionally Markdown."""
        os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
        summary_dict = asdict(summary)

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2)

        if output_md_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_md_path)), exist_ok=True)
            md_content = cls.generate_markdown(summary)
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
