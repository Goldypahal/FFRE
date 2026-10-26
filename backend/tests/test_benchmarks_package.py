"""
Automated Test Suite for the FFIRE Open Benchmark Package.
Validates synthetic data generation, fraud archetypes, manifest schemas,
percentile calculation, checkpoint safety auditor, and smoke runner execution.
"""

import os
import sys
import json
import pytest

# Ensure root and backend are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from benchmarks.generators.synthetic_data import SyntheticDataGenerator, FraudArchetype
from benchmarks.runners.report_generator import BenchmarkReportGenerator, BenchmarkSummary, TierMetrics
from benchmarks.runners.checkpoint_safety import CheckpointSafetyAuditor
from benchmarks.runners.engine_benchmark import EngineBenchmarkRunner
from checkpointing import ThreadSafeMemorySaver

def test_synthetic_data_generator_deterministic_output():
    """Verify that same seed produces identical dataset and archetype distributions."""
    gen1 = SyntheticDataGenerator(seed=42, tenant_id="t_test_1")
    ds1 = gen1.generate_dataset(num_customers=5, txns_per_customer=4, fraud_ratio=0.5)

    gen2 = SyntheticDataGenerator(seed=42, tenant_id="t_test_1")
    ds2 = gen2.generate_dataset(num_customers=5, txns_per_customer=4, fraud_ratio=0.5)

    assert len(ds1.customers) == 5
    assert len(ds1.transactions) == 20
    assert ds1.customers[0]["customer_id"] == ds2.customers[0]["customer_id"]
    assert ds1.transactions[0]["amount"] == ds2.transactions[0]["amount"]
    assert ds1.transactions[0]["archetype"] == ds2.transactions[0]["archetype"]

    summary = ds1.summary()
    assert summary["total_customers"] == 5
    assert summary["total_transactions"] == 20
    assert len(summary["archetype_distribution"]) >= 2

def test_synthetic_data_csv_and_json_export(tmp_path):
    """Verify CSV and JSON file export functions."""
    generator = SyntheticDataGenerator(seed=101, tenant_id="t_export")
    dataset = generator.generate_dataset(num_customers=3, txns_per_customer=3)

    csv_path = str(tmp_path / "test_txns.csv")
    json_path = str(tmp_path / "test_txns.json")

    SyntheticDataGenerator.export_csv(dataset, csv_path)
    SyntheticDataGenerator.export_json(dataset, json_path)

    assert os.path.exists(csv_path)
    assert os.path.exists(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "summary" in data
    assert len(data["transactions"]) == 9

def test_manifest_files_exist_and_validate():
    """Verify standard, stress, and soak load manifest JSON schemas."""
    manifests_dir = os.path.join(root_dir, "benchmarks", "manifests")
    for m_file in ["standard_load.json", "stress_load.json", "soak_load.json"]:
        path = os.path.join(manifests_dir, m_file)
        assert os.path.exists(path), f"Missing manifest: {m_file}"
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        assert "name" in cfg
        assert "tiers" in cfg
        assert len(cfg["tiers"]) >= 1
        assert "targets" in cfg
        assert cfg["targets"]["p95_latency_ms"] > 0

def test_benchmark_report_generator_percentile_math():
    """Verify exact percentile calculations for known synthetic durations."""
    durations = [0.010, 0.020, 0.030, 0.040, 0.050, 0.060, 0.070, 0.080, 0.090, 0.100]
    pcts = BenchmarkReportGenerator.calculate_percentiles(durations)

    assert pcts["p50_ms"] == pytest.approx(50.0, rel=1e-2)
    assert pcts["p90_ms"] == pytest.approx(90.0, rel=1e-2)
    assert pcts["p95_ms"] == pytest.approx(100.0, rel=1e-2)
    assert pcts["min_ms"] == 10.0
    assert pcts["max_ms"] == 100.0
    assert pcts["mean_ms"] == pytest.approx(55.0, rel=1e-2)

    tier_m = BenchmarkReportGenerator.build_tier_metrics(
        workers=5,
        durations_sec=durations,
        wall_time_sec=0.25,
        failures=0,
        p95_target_ms=5000.0
    )
    assert tier_m.workers == 5
    assert tier_m.throughput_ops_sec == pytest.approx(40.0, rel=1e-2)
    assert tier_m.meets_p95_sla is True
    assert tier_m.failure_rate_pct == 0.0

def test_checkpoint_safety_auditor_detects_corrupt_and_valid_state():
    """Verify CheckpointSafetyAuditor correctly flags missing or invalid checkpoints."""
    from graph import build_graph
    saver = ThreadSafeMemorySaver()
    graph = build_graph(checkpointer=saver)
    tids = ["t_safe_1", "t_safe_2"]

    for tid in tids:
        config = {"configurable": {"thread_id": tid, "checkpoint_ns": ""}}
        graph.invoke({"investigation_id": tid, "transaction_id": f"TXN_{tid}"}, config=config)

    # Valid check
    report = CheckpointSafetyAuditor.audit_checkpointer(saver, tids)
    assert report.is_safe is True
    assert report.valid_threads == 2
    assert report.corrupted_threads == 0

    # Corrupted / Missing thread check
    report_missing = CheckpointSafetyAuditor.audit_checkpointer(saver, tids + ["t_nonexistent"])
    assert report_missing.is_safe is False
    assert report_missing.corrupted_threads == 1

def test_engine_benchmark_runner_smoke_execution():
    """Smoke test EngineBenchmarkRunner with synthetic transactions and NullProvider."""
    generator = SyntheticDataGenerator(seed=7, tenant_id="t_engine_smoke")
    dataset = generator.generate_dataset(num_customers=2, txns_per_customer=2)

    runner = EngineBenchmarkRunner(tenant_id="t_engine_smoke")
    summary = runner.run_benchmark(
        dataset_txns=dataset.transactions,
        tiers=[1],
        repetitions_per_tier=1,
        warmup_count=0,
        manifest_name="Test Smoke"
    )

    assert "1" in summary.tiers
    tier1 = summary.tiers["1"]
    assert tier1.total_requests == 1
    assert tier1.successes == 1
    assert tier1.failures == 0
    assert tier1.p95_ms > 0
    assert summary.checkpoint_safety_verified is True
