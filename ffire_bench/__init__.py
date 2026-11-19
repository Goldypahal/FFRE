"""
FFIRE-Bench: Financial Fraud Investigation Reasoning & Evidence Benchmark.

An independent, vendor-neutral benchmark for evaluating the factual grounding,
claim verification, error detection, and calibrated disposition of AI-written
financial crime investigations.
"""

__version__ = "0.1.0"
__benchmark_name__ = "FFIRE-Bench"
__author__ = "FFIRE-Bench Consortium"

from ffire_bench.schema.models import (
    Case,
    EvidenceItem,
    Claim,
    ClaimLabel,
    ErrorCode,
    Severity,
    Difficulty,
    CaseLabel,
    CaseDisposition,
    PredictionCase,
    PredictionClaim,
    PredictionBundle
)
