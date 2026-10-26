"""
FFIRE Synthetic Data Generators
Generates deterministic, schema-compliant synthetic transactions, entities, and fraud attack patterns for offline benchmarking.
"""

from .synthetic_data import SyntheticDataGenerator, FraudArchetype, GeneratedDataset

__all__ = ["SyntheticDataGenerator", "FraudArchetype", "GeneratedDataset"]
