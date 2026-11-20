"""
Abstract Base Runner interface for benchmark model adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ffire_bench.schema.models import Case, PredictionCase, PredictionBundle, Track


class BaseRunner(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def predict_case(self, case: Case) -> PredictionCase:
        """Generate predictions for a single case."""
        pass

    def run_benchmark(self, cases: List[Case], track: Track = Track.T1) -> PredictionBundle:
        """Run evaluation over a batch of cases, returning a standard PredictionBundle."""
        predictions = []
        for case in cases:
            p = self.predict_case(case)
            predictions.append(p)

        return PredictionBundle(
            benchmark_version="0.1.0",
            model_name=self.name,
            track=track,
            predictions=predictions
        )
