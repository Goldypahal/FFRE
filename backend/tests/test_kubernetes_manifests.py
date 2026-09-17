import os
import yaml
import pytest
from pathlib import Path

def test_kubernetes_manifests_syntax_and_structure():
    """Verify all Kubernetes manifests in k8s/ are valid YAML and contain required metadata."""
    k8s_dir = Path("k8s")
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
    with open("k8s/gateway-deployment.yaml", "r", encoding="utf-8") as f:
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
    assert container["readinessProbe"]["httpGet"]["path"] == "/api/v1/health"

    # Security Context
    assert container["securityContext"]["runAsNonRoot"] is True

def test_ingress_tls_security_standards():
    """Verify Ingress enforces TLS 1.2+, HTTPS redirect, and HSTS security headers (NFR-4)."""
    with open("k8s/ingress-and-network-policy.yaml", "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))

    ingress_doc = next(d for d in docs if d.get("kind") == "Ingress")
    annotations = ingress_doc["metadata"]["annotations"]
    assert annotations["nginx.ingress.kubernetes.io/ssl-redirect"] == "true"
    assert "TLSv1.2" in annotations["nginx.ingress.kubernetes.io/ssl-protocols"]
    assert "AES256" in annotations["nginx.ingress.kubernetes.io/ssl-ciphers"]
    assert "Strict-Transport-Security" in annotations["nginx.ingress.kubernetes.io/configuration-snippet"]
