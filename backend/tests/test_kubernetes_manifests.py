import os
import yaml
import pytest
from pathlib import Path

def _get_k8s_dir() -> Path:
    candidates = [
        Path("k8s"),
        Path(__file__).resolve().parent.parent.parent / "k8s",
        Path(__file__).resolve().parent.parent / "k8s",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return Path("k8s")

def test_kubernetes_manifests_syntax_and_structure():
    """Verify all Kubernetes manifests in k8s/ are valid YAML and contain required metadata."""
    k8s_dir = _get_k8s_dir()
    assert k8s_dir.exists(), "k8s directory must exist"

    manifest_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
    assert len(manifest_files) >= 4, "At least 4 Kubernetes manifest files required"

    found_kinds = set()
    for mf in manifest_files:
        with open(mf, "r", encoding="utf-8") as f:
            docs = yaml.safe_load_all(f)
            for doc in docs:
                if doc:
                    assert "apiVersion" in doc
                    assert "kind" in doc
                    assert "metadata" in doc
                    found_kinds.add(doc["kind"])

    required_kinds = {"Deployment", "Service", "ConfigMap", "Secret", "HorizontalPodAutoscaler", "Ingress", "NetworkPolicy"}
    missing = required_kinds - found_kinds
    assert not missing, f"Missing required Kubernetes resources: {missing}"

def test_gateway_deployment_production_specs():
    """Verify gateway deployment enforces 3 replicas, health probes, non-root user, and resource limits."""
    k8s_dir = _get_k8s_dir()
    with open(k8s_dir / "gateway-deployment.yaml", "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    assert doc["kind"] == "Deployment"
    assert doc["spec"]["replicas"] == 3
    assert doc["spec"]["strategy"]["type"] == "RollingUpdate"

    container = doc["spec"]["template"]["spec"]["containers"][0]
    assert "resources" in container
    assert "limits" in container["resources"]
    assert "requests" in container["resources"]
    assert container["resources"]["limits"]["cpu"] == "2000m"

    # Liveness and Readiness probes
    assert "livenessProbe" in container
    assert container["livenessProbe"]["httpGet"]["path"] == "/api/v1/health"
    assert "readinessProbe" in container
    # Readiness checks the database; liveness only checks that the process answers.
    assert container["readinessProbe"]["httpGet"]["path"] == "/api/v1/ready"

    # Security Context
    assert container["securityContext"]["runAsNonRoot"] is True

def test_ingress_tls_security_standards():
    """Verify Ingress enforces TLS 1.2+, HTTPS redirect, and HSTS security headers (NFR-4)."""
    k8s_dir = _get_k8s_dir()
    with open(k8s_dir / "ingress-and-network-policy.yaml", "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))

    ingress_doc = next(d for d in docs if d.get("kind") == "Ingress")
    annotations = ingress_doc["metadata"]["annotations"]
    assert annotations["nginx.ingress.kubernetes.io/ssl-redirect"] == "true"
    assert "TLSv1.2" in annotations["nginx.ingress.kubernetes.io/ssl-protocols"]
    assert "AES256" in annotations["nginx.ingress.kubernetes.io/ssl-ciphers"]
    assert "Strict-Transport-Security" in annotations["nginx.ingress.kubernetes.io/configuration-snippet"]


def test_secret_template_provides_every_key_the_application_requires():
    """The app reads SECRET_KEY; a secret named anything else leaves production pods unable to start."""
    import os
    import yaml
    path = os.path.join(os.path.dirname(__file__), "..", "..", "k8s", "secrets.yaml")
    with open(path, encoding="utf-8") as fh:
        keys = set(yaml.safe_load(fh)["stringData"])
    for required in ("SECRET_KEY", "ENCRYPTION_SECRET_KEY", "VERIFIER_PRIVATE_KEY_PEM", "BOOTSTRAP_SECRET_KEY", "DATABASE_URL"):
        assert required in keys, f"k8s/secrets.yaml is missing {required}"
    assert "JWT_SECRET_KEY" not in keys
