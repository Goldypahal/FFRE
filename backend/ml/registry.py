"""
Model Registry & Artifact Persistence for Fraud Models (Phase 2).

Manages model lifecycle, versioning, staging (production / staging / archived),
schema metadata tracking, cryptographic SHA-256 integrity checks, and serialized
artifact storage using joblib.
"""

import os
import json
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple
import joblib


def compute_file_sha256(filepath: str) -> str:
    """Compute cryptographic SHA-256 digest of a model artifact."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelRegistry:
    """Local, auditable model registry for ML fraud detection artifacts with cryptographic verification."""

    def __init__(self, registry_dir: Optional[str] = None):
        if registry_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_dir = os.path.join(backend_dir, "ml", "model_store")

        self.registry_dir = os.path.abspath(registry_dir)
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

    def resolve_artifact_path(self, artifact_path: str) -> str:
        """
        Resolves artifact path portably. If an absolute path from another machine
        is stored in the manifest, gracefully falls back to the local registry_dir.
        """
        if os.path.isabs(artifact_path) and os.path.exists(artifact_path):
            return artifact_path
        
        # Check relative to self.registry_dir
        local_path = os.path.join(self.registry_dir, os.path.basename(artifact_path))
        if os.path.exists(local_path):
            return local_path

        # Also check relative path if specified
        rel_path = os.path.join(self.registry_dir, artifact_path)
        if os.path.exists(rel_path):
            return rel_path

        return local_path

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
        Saves a trained model artifact, verifies its SHA-256 digest, and registers metadata.
        """
        artifact_filename = f"{model_id}.joblib"
        artifact_full_path = os.path.join(self.registry_dir, artifact_filename)
        joblib.dump(model, artifact_full_path)

        # Compute SHA-256 digest for supply-chain integrity verification
        artifact_hash = compute_file_sha256(artifact_full_path)

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
            "artifact_path": artifact_filename,
            "sha256": artifact_hash,
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
        artifact_path = self.resolve_artifact_path(meta["artifact_path"])
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact not found at resolved path: {artifact_path}")

        # Cryptographic integrity check: enforce mandatory SHA-256 before loading untrusted binary
        expected_hash = meta.get("sha256")
        if not expected_hash:
            raise ValueError(
                f"Security violation: Model '{model_id}' lacks a SHA-256 provenance digest in manifest. "
                f"Loading unverified model artifacts is strictly prohibited under zero-trust policy."
            )
        actual_hash = compute_file_sha256(artifact_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Model integrity violation: SHA-256 mismatch for model '{model_id}'. "
                f"Expected: {expected_hash}, Actual: {actual_hash}"
            )

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
