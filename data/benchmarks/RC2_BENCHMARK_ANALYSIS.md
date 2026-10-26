# FFRE Representative Production Benchmark & Latency SLA Analysis

**Deliverable**: Release Candidate 2 (RC2) Benchmark Report  
**Target Environment**: PostgreSQL 15 (`ffire_test_postgres` on port 5433), Redis 7 (`ffire_test_redis` on port 6379)  
**Execution Script**: `scripts/benchmark_full_production_path.py`  
**Raw Dataset**: `data/benchmarks/representative_production_benchmark.json`  

---

## 1. Executive Summary

This report documents the performance, latency profile, and throughput characteristics of the **Representative Full Production Path** in FFRE:
$$\text{HTTP API Gateway} \longrightarrow \text{JWT Auth \& Idempotency} \longrightarrow \text{PostgreSQL Storage} \longrightarrow \text{LangGraph Checkpointer (psycopg\_pool)} \longrightarrow \text{Audit Log Hash Chain}$$

The benchmark was executed across **four concurrency tiers** (1, 5, 10, and 20 workers) with **three repetitions per tier** to evaluate repeatability, stability, and SLA adherence.

---

## 2. Benchmark Measurement Summary

Across all 108 requests executed during the benchmark:
- **Total Requests**: 108
- **Failed Requests**: 0
- **Overall Failure Rate**: **0.00%** (100% success rate across all concurrency tiers)

### Summary Table by Concurrency Tier

| Concurrency Tier | Total Requests | Mean Throughput (ops/s) | Aggregate p50 (ms) | Aggregate p95 (ms) | Aggregate p99 (ms) | Mean Latency (ms) | Meets p95 SLA (<5,000ms) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1 Worker** | 3 | **1.16** | 858.83 | **873.89** | 873.89 | 859.15 | **PASS** |
| **5 Workers** | 15 | **1.88** | 2,554.48 | **2,911.47** | 2,911.47 | 2,614.99 | **PASS** |
| **10 Workers** | 30 | **1.85** | 5,073.43 | **5,632.56** | 5,637.06 | 4,899.20 | **FAIL (Slight)** |
| **20 Workers** | 60 | **1.96** | 8,582.71 | **10,190.48** | 10,292.09 | 8,533.75 | **FAIL** |

---

## 3. Repetition Breakdown

### Tier 1 (1 Worker)
- **Rep #1**: 1 request in 0.860s | p50: 858.8ms | p95: 858.8ms | Throughput: 1.16 ops/s
- **Rep #2**: 1 request in 0.875s | p50: 873.9ms | p95: 873.9ms | Throughput: 1.14 ops/s
- **Rep #3**: 1 request in 0.846s | p50: 844.7ms | p95: 844.7ms | Throughput: 1.18 ops/s
- *Aggregate p95*: **873.89ms** (< 1,000ms, sub-second baseline)

### Tier 5 (5 Workers)
- **Rep #1**: 5 requests in 2.919s | p50: 2,863.1ms | p95: 2,911.5ms | Throughput: 1.71 ops/s
- **Rep #2**: 5 requests in 2.606s | p50: 2,554.5ms | p95: 2,598.3ms | Throughput: 1.92 ops/s
- **Rep #3**: 5 requests in 2.493s | p50: 2,472.1ms | p95: 2,489.5ms | Throughput: 2.01 ops/s
- *Aggregate p95*: **2,911.47ms** (meets 5s SLA comfortably)

### Tier 10 (10 Workers)
- **Rep #1**: 10 requests in 5.650s | p50: 5,484.0ms | p95: 5,637.1ms | Throughput: 1.77 ops/s
- **Rep #2**: 10 requests in 5.399s | p50: 5,325.3ms | p95: 5,372.2ms | Throughput: 1.85 ops/s
- **Rep #3**: 10 requests in 5.150s | p50: 4,949.7ms | p95: 5,128.3ms | Throughput: 1.94 ops/s
- *Aggregate p95*: **5,632.56ms** (exceeds 5s SLA by 632ms due to worker queueing)

### Tier 20 (20 Workers)
- **Rep #1**: 20 requests in 10.117s | p50: 8,603.9ms | p95: 10,111.3ms | Throughput: 1.98 ops/s
- **Rep #2**: 20 requests in 10.302s | p50: 8,661.5ms | p95: 10,292.1ms | Throughput: 1.94 ops/s
- **Rep #3**: 20 requests in 10.128s | p50: 8,476.4ms | p95: 10,122.1ms | Throughput: 1.97 ops/s
- *Aggregate p95*: **10,190.48ms**

---

## 4. Root Cause Analysis of Throughput Plateau

1. **Throughput Saturation at ~1.96 ops/s**:
   - As concurrency scales from 5 to 20 workers, throughput plateaus at approximately 1.9 - 2.0 investigations per second.
   - **Reason**: Each investigation executes a full multi-node LangGraph pipeline comprising:
     - Feature extraction & knowledge lookup
     - Rule evaluation engine
     - Graph anomaly & community detection
     - LLM reasoning generation
     - Evidence grounding critic
     - Dual-table PostgreSQL state checkpointing
     - Tamper-evident SHA-256 blockchain audit log commit
   - When run locally on a single host where the benchmark client, Uvicorn API server, background threads, PostgreSQL 15, and Redis all share the same CPU cores, the host becomes CPU-bound on graph execution and cryptography.

2. **Latency Queuing at High Concurrency**:
   - Because throughput is capped at ~2 ops/s by local CPU capacity, submitting 10 simultaneous requests causes an average queue wait of $10 / 2 = 5$ seconds; submitting 20 simultaneous requests causes an average queue wait of $20 / 2 = 10$ seconds.
   - **Crucial Reliability Finding**: Even under 20-worker saturation, **zero requests failed**, **zero database deadlocks occurred**, and **zero checkpoints corrupted**. The system degraded gracefully into queuing rather than dropping requests or crashing.

3. **Production Recommendation**:
   - In production, scale worker processes horizontally across multiple nodes behind a reverse proxy / load balancer.
   - Set a concurrency target of 5 parallel investigations per worker pod to guarantee sub-3-second p95 investigation response times.
