# FFIRE Open Benchmark Package

The **FFIRE Open Benchmark Package** is a deterministic, offline-capable benchmarking and evaluation suite designed to validate the reasoning engine's latency SLAs, multi-worker concurrency scaling, and checkpoint safety.

---

## 1. Features
- **Zero Paid API Requirements**: Uses the pluggable `NullProvider` or local models by default. No OpenAI/Anthropic API keys or external networks are required.
- **Deterministic Synthetic Data**: Configurable pseudo-random generator with fixed seeds producing customers, accounts, merchants, devices, locations, and transactions across 6 fraud archetypes (`BENIGN`, `HIGH_VELOCITY_BURST`, `GEOGRAPHIC_IMPOSSIBILITY`, `AMOUNT_ANOMALY`, `NEW_DEVICE_ATO`, `STRUCTURING_SMURFING`).
- **Comprehensive Concurrency Tiers**: Evaluates 1, 5, 10, and 20 worker threads measuring p50, p90, p95, p99 latency, min/max/mean/stddev, and throughput (ops/sec).
- **Dual Execution Modes**:
  - `engine`: Measures pure LangGraph workflow execution, node timings, and checkpoint persistence.
  - `api`: Measures end-to-end FastAPI HTTP router, JWT auth, tenant isolation, database commits, worker queuing, and response serialization.
- **Checkpoint Safety Verification**: Evaluates state integrity, confirms zero lineage breaks, validates channel isolation, and checks cross-process state recovery.
- **Standardized Reports**: Automatically generates machine-readable JSON and GitHub Markdown summary tables.

---

## 2. Load Manifests
The suite ships with three standard manifests in `benchmarks/manifests/`:
1. `standard_load.json`: Concurrency tiers [1, 5, 10, 20], 3 repetitions per tier, SLA targets p95 <= 5.0s, p99 <= 8.0s.
2. `stress_load.json`: Concurrency tiers [10, 20, 40], burst arrival, SLA targets p95 <= 8.0s, p99 <= 12.0s.
3. `soak_load.json`: Concurrency tier 5 sustained over 10 repetitions, validating checkpointer and memory stability.

---

## 3. Quickstart & Usage

### Fast Smoke Test (1 Worker, Quick Verification)
```bash
python -m benchmarks.cli --smoke
```

### Full Standard Benchmark (Engine + API, Tiers 1, 5, 10, 20)
```bash
python -m benchmarks.cli --manifest benchmarks/manifests/standard_load.json --mode both
```

### Engine-Only Concurrency Run
```bash
python -m benchmarks.cli --tiers 1,5,10,20 --mode engine
```

### API Gateway Concurrency Run
```bash
python -m benchmarks.cli --tiers 1,5,10,20 --mode api
```

### Custom Output Directory & Seed
```bash
python -m benchmarks.cli --manifest benchmarks/manifests/standard_load.json --out-dir data/benchmarks/custom_run --seed 999
```

---

## 4. Output Artifacts
Benchmark runs write the following artifacts:
- `engine_benchmark_results.json`: Full statistical metrics and configuration for engine execution.
- `engine_benchmark_report.md`: Markdown summary table with SLA verdicts.
- `api_benchmark_results.json`: Metrics for full HTTP gateway stack.
- `api_benchmark_report.md`: Markdown summary table for API execution.
