"""
Command-Line Interface for the FFIRE Open Benchmark Package.
Usage:
    python -m benchmarks.cli --smoke
    python -m benchmarks.cli --manifest benchmarks/manifests/standard_load.json --mode both
    python -m benchmarks.cli --tiers 1,5,10,20 --mode engine
"""

import os
import sys
import json
import argparse
from typing import List

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from database import SessionLocal, init_db
from benchmarks.generators.synthetic_data import SyntheticDataGenerator
from benchmarks.runners.engine_benchmark import EngineBenchmarkRunner
from benchmarks.runners.api_benchmark import APIBenchmarkRunner
from benchmarks.runners.report_generator import BenchmarkReportGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="FFIRE Open Benchmark CLI")
    parser.add_argument("--manifest", type=str, default=None, help="Path to benchmark load manifest JSON")
    parser.add_argument("--mode", type=str, choices=["engine", "api", "both"], default="both", help="Runner mode")
    parser.add_argument("--tiers", type=str, default=None, help="Comma-separated concurrency tiers (e.g., 1,5,10,20)")
    parser.add_argument("--repetitions", type=int, default=None, help="Repetitions per tier")
    parser.add_argument("--smoke", action="store_true", help="Run quick smoke test (1 tier, minimal requests)")
    parser.add_argument("--out-dir", type=str, default="data/benchmarks", help="Output directory for reports")
    parser.add_argument("--seed", type=int, default=42, help="Synthetic data generator seed")
    parser.add_argument("--tenant", type=str, default="benchmark_tenant", help="Benchmark tenant ID")
    return parser.parse_args()

def main():
    args = parse_args()
    init_db()

    # Load manifest or defaults
    manifest_path = args.manifest
    if not manifest_path:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifests", "standard_load.json")

    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    manifest_name = manifest.get("name", "Standard Load")
    tiers = [int(x.strip()) for x in args.tiers.split(",")] if args.tiers else manifest.get("tiers", [1, 5, 10, 20])
    repetitions = args.repetitions or manifest.get("repetitions_per_tier", 3)
    warmup = manifest.get("warmup_requests", 2)
    targets = manifest.get("targets", {})
    p95_target = targets.get("p95_latency_ms", 5000.0)
    p99_target = targets.get("p99_latency_ms", 8000.0)

    if args.smoke:
        print("\n[SMOKE TEST MODE ENABLED]")
        tiers = [1]
        repetitions = 1
        warmup = 1
        manifest_name = "Smoke Test Load"

    print("=" * 80)
    print(f"FFIRE OPEN BENCHMARK RUNNER")
    print(f"Manifest:    {manifest_name}")
    print(f"Mode:        {args.mode.upper()}")
    print(f"Tiers:       {tiers}")
    print(f"Repetitions: {repetitions} per tier")
    print(f"Targets:     p95 <= {p95_target} ms | p99 <= {p99_target} ms")
    print("=" * 80)

    # 1. Generate & Seed Synthetic Dataset
    gen_cfg = manifest.get("generator_config", {})
    num_cust = 5 if args.smoke else gen_cfg.get("num_customers", 20)
    txns_per_cust = 3 if args.smoke else gen_cfg.get("txns_per_customer", 10)
    fraud_ratio = gen_cfg.get("fraud_ratio", 0.25)

    print(f"\n[1/3] Generating synthetic dataset (seed={args.seed}, customers={num_cust})...")
    generator = SyntheticDataGenerator(seed=args.seed, tenant_id=args.tenant)
    dataset = generator.generate_dataset(num_customers=num_cust, txns_per_customer=txns_per_cust, fraud_ratio=fraud_ratio)

    db = SessionLocal()
    try:
        inserted = generator.seed_to_db(dataset, db)
        print(f"      Seeded to DB: {inserted['customers']} customers, {inserted['transactions']} transactions.")
    finally:
        db.close()

    os.makedirs(args.out_dir, exist_ok=True)
    overall_pass = True

    # 2. Run Engine Benchmark if requested
    if args.mode in ["engine", "both"]:
        print(f"\n[2/3] Running Reasoning Engine Benchmark across {tiers}...")
        engine_runner = EngineBenchmarkRunner(tenant_id=args.tenant)
        engine_summary = engine_runner.run_benchmark(
            dataset_txns=dataset.transactions,
            tiers=tiers,
            repetitions_per_tier=repetitions,
            warmup_count=warmup,
            manifest_name=manifest_name,
            p95_target_ms=p95_target,
            p99_target_ms=p99_target
        )
        print(BenchmarkReportGenerator.generate_markdown(engine_summary))

        json_out = os.path.join(args.out_dir, "engine_benchmark_results.json")
        md_out = os.path.join(args.out_dir, "engine_benchmark_report.md")
        BenchmarkReportGenerator.export_results(engine_summary, json_out, md_out)
        print(f"      Saved engine report to {md_out}")

        if not engine_summary.all_slas_met:
            overall_pass = False

    # 3. Run API Benchmark if requested
    if args.mode in ["api", "both"]:
        print(f"\n[3/3] Running Full API Gateway Benchmark across {tiers}...")
        api_runner = APIBenchmarkRunner(tenant_id=args.tenant)
        api_summary = api_runner.run_benchmark(
            dataset_txns=dataset.transactions,
            tiers=tiers,
            repetitions_per_tier=repetitions,
            warmup_count=warmup,
            manifest_name=manifest_name,
            p95_target_ms=p95_target,
            p99_target_ms=p99_target
        )
        print(BenchmarkReportGenerator.generate_markdown(api_summary))

        json_out = os.path.join(args.out_dir, "api_benchmark_results.json")
        md_out = os.path.join(args.out_dir, "api_benchmark_report.md")
        BenchmarkReportGenerator.export_results(api_summary, json_out, md_out)
        print(f"      Saved API report to {md_out}")

        if not api_summary.all_slas_met:
            overall_pass = False

    print("\n" + "=" * 80)
    verdict = "PASSED (All SLAs Met)" if overall_pass else "FAILED (SLA Violation Detected)"
    print(f"OVERALL BENCHMARK VERDICT: {verdict}")
    print("=" * 80)

    return 0 if overall_pass else 1

if __name__ == "__main__":
    sys.exit(main())
