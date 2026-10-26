"""
Model Registry & Artifact Persistence for Fraud Models (Phase 2).

Manages model lifecycle, versioning, staging (production / staging / archived),
schema metadata tracking, and serialized artifact storage using joblib.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
import joblib


class ModelRegistry:
    """Local, auditable model registry for ML fraud detection artifacts."""

    def __init__(self, registry_dir: Optional[str] = None):
        if registry_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_dir = os.path.join(backend_dir, "ml", "model_store")

        self.registry_dir = registry_dir
        self.manifest_path = os.path.join(self.registry_dir, "registry_manifest.json")
        os.makedirs(self.registry_dir, exist_ok=True)
        self._ensure_manifest()

    def _ensure_manifest(self):
        if not os.path.exists(self.manifest_path):
            initial_data = {
                "active_production_model_id": None,
                "models": {}
            }
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def _load_manifest(self) -> Dict[str, Any]:
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_manifest(self, manifest: Dict[str, Any]):
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def register_model(
        self,
        model: Any,
        model_id: str,
        model_type: str,
        version: str,
        metrics: Dict[str, Any],
        feature_names: List[str],
        stage: str = "staging",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Saves a trained model artifact and registers its metadata.
        """
        artifact_filename = f"{model_id}.joblib"
        artifact_path = os.path.join(self.registry_dir, artifact_filename)
        joblib.dump(model, artifact_path)

        manifest = self._load_manifest()

        # If promoting directly to production, demote prior production model
        if stage == "production":
            for m_id, meta in manifest["models"].items():
                if meta.get("stage") == "production":
                    meta["stage"] = "archived"
            manifest["active_production_model_id"] = model_id

        entry = {
            "model_id": model_id,
            "model_type": model_type,
            "version": version,
            "stage": stage,
            "metrics": metrics,
            "feature_names": feature_names,
            "artifact_path": artifact_path,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "notes": notes
        }
        manifest["models"][model_id] = entry
        self._save_manifest(manifest)
        return entry

    def promote_to_production(self, model_id: str) -> Dict[str, Any]:
        manifest = self._load_manifest()
        if model_id not in manifest["models"]:
            raise ValueError(f"Model ID '{model_id}' not found in registry")

        for m_id, meta in manifest["models"].items():
            if meta.get("stage") == "production":
                meta["stage"] = "archived"

        manifest["models"][model_id]["stage"] = "production"
        manifest["active_production_model_id"] = model_id
        self._save_manifest(manifest)
        return manifest["models"][model_id]

    def get_model(self, model_id: str) -> Tuple[Any, Dict[str, Any]]:
        manifest = self._load_manifest()
        if model_id not in manifest["models"]:
            raise ValueError(f"Model ID '{model_id}' not found in registry")

        meta = manifest["models"][model_id]
        artifact_path = meta["artifact_path"]
        model = joblib.load(artifact_path)
        return model, meta

    def get_production_model(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        manifest = self._load_manifest()
        prod_id = manifest.get("active_production_model_id")
        if not prod_id or prod_id not in manifest["models"]:
            return None
        return self.get_model(prod_id)

    def list_models(self) -> List[Dict[str, Any]]:
        manifest = self._load_manifest()
        return list(manifest.get("models", {}).values())
