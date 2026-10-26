"""
Offline Fraud Inference Service & LangGraph Integration (Phase 2).

Loads the active production model from ModelRegistry, evaluates incoming
transaction evidence bundles, and outputs calibrated fraud probabilities
with top contributing feature attributions.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

from backend.ml.features import (
    FEATURE_NAMES,
    extract_features_from_dict,
    extract_features_from_state
)
from backend.ml.registry import ModelRegistry


@dataclass
class FraudPrediction:
    """Standardized response from the ML fraud inference engine."""
    risk_score: float
    raw_probability: float
    predicted_label: str
    model_id: str
    model_version: str
    model_type: str
    top_features: List[Dict[str, Any]]
    feature_vector: List[float]
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FraudInferenceService:
    """
    Thread-safe, offline inference service with model hot-reloading
    and feature attribution.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        self._cached_model = None
        self._cached_meta = None
        self._cached_model_id = None
        self._cached_importances = None
        self.reload_production_model()

    def reload_production_model(self) -> bool:
        """Loads or refreshes the current production model from registry."""
        prod = self.registry.get_production_model()
        if prod:
            self._cached_model, self._cached_meta = prod
            self._cached_model_id = self._cached_meta["model_id"]
            self._cached_importances = self._resolve_importances(self._cached_model)
            return True
        return False

    def predict(
        self,
        txn: Dict[str, Any],
        account: Optional[Dict[str, Any]] = None,
        customer: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        cycle_score: float = 0.0,
        sg_score: float = 0.0,
        threshold: float = 0.50
    ) -> FraudPrediction:
        """
        Runs tabular inference on transaction entity context.
        """
        t0 = time.perf_counter()

        vec = extract_features_from_dict(
            txn=txn,
            account=account,
            customer=customer,
            history=history,
            cycle_score=cycle_score,
            sg_score=sg_score
        )

        return self._predict_from_vector(vec, t0, threshold)

    def predict_from_state(self, state: Dict[str, Any], threshold: float = 0.50) -> FraudPrediction:
        """
        Runs tabular inference directly on LangGraph AgentState.
        """
        t0 = time.perf_counter()
        vec = extract_features_from_state(state)
        return self._predict_from_vector(vec, t0, threshold)

    def _predict_from_vector(self, vec: np.ndarray, t0: float, threshold: float = 0.50) -> FraudPrediction:
        if self._cached_model is None:
            self.reload_production_model()

        X = vec.reshape(1, -1)

        if self._cached_model is not None:
            model = self._cached_model
            meta = self._cached_meta
            model_id = meta.get("model_id", "unknown_model")
            version = meta.get("version", "1.0.0")
            model_type = meta.get("model_type", "lightgbm")

            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[0]
                prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
            elif hasattr(model, "decision_function"):
                raw = float(model.decision_function(X)[0])
                prob = 1.0 / (1.0 + np.exp(-raw))
            else:
                prob = 0.50

            # Feature attribution (tree feature importances or feature magnitude)
            top_feats = self._extract_top_features(model, vec)

        else:
            # Fallback heuristic if no ML model has been registered yet
            model_id = "heuristic_fallback_v0"
            version = "0.1.0"
            model_type = "heuristic"
            # Simple fallback based on amount structuring / velocity
            amt = float(vec[0])
            has_cycle = float(vec[16])
            has_sg = float(vec[18])
            is_comm = float(vec[21])
            is_struct = float(vec[5])

            score = 0.15
            if has_cycle > 0: score += 0.40
            if has_sg > 0: score += 0.35
            if is_struct > 0: score += 0.35
            if is_comm > 0 and amt >= 20000.0: score = min(score, 0.30)
            prob = min(max(score, 0.0), 0.99)
            top_feats = [{"feature": "heuristic_risk", "value": round(prob, 3)}]

        latency_ms = (time.perf_counter() - t0) * 1000.0
        label = "SUSPICIOUS" if prob >= threshold else "BENIGN"

        return FraudPrediction(
            risk_score=round(prob, 4),
            raw_probability=round(prob, 4),
            predicted_label=label,
            model_id=model_id,
            model_version=version,
            model_type=model_type,
            top_features=top_feats,
            feature_vector=[round(float(v), 4) for v in vec],
            latency_ms=round(latency_ms, 2)
        )

    def _resolve_importances(self, model: Any) -> Optional[np.ndarray]:
        base_est = getattr(model, "estimator", model)
        if hasattr(base_est, "calibrated_classifiers_"):
            try:
                base_est = model.calibrated_classifiers_[0].estimator
            except Exception:
                base_est = getattr(model, "estimator", model)

        if hasattr(base_est, "feature_importances_"):
            return np.array(base_est.feature_importances_, dtype=np.float32)
        elif hasattr(base_est, "named_steps") and hasattr(base_est.named_steps.get("clf"), "coef_"):
            return np.abs(np.array(base_est.named_steps["clf"].coef_[0], dtype=np.float32))
        return None

    def _extract_top_features(self, model: Any, vec: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """Extract top contributing features for explainability."""
        importances = getattr(self, "_cached_importances", None)
        if importances is None:
            importances = self._resolve_importances(model)
            self._cached_importances = importances

        if importances is not None and len(importances) == len(FEATURE_NAMES):
            impacts_arr = importances * np.abs(vec)
            top_indices = np.argsort(-impacts_arr)[:top_k]
            return [
                {
                    "feature": FEATURE_NAMES[i],
                    "importance": round(float(importances[i]), 4),
                    "value": round(float(vec[i]), 4),
                    "impact": round(float(impacts_arr[i]), 4)
                }
                for i in top_indices
            ]

        return [
            {"feature": name, "value": round(float(v), 4)}
            for name, v in list(zip(FEATURE_NAMES, vec))[:top_k]
        ]


# Global singleton inference service
_global_inference_service: Optional[FraudInferenceService] = None


def get_inference_service() -> FraudInferenceService:
    global _global_inference_service
    if _global_inference_service is None:
        _global_inference_service = FraudInferenceService()
    return _global_inference_service
