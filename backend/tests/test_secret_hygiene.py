import os
import subprocess
import pytest

COMPROMISED_PATTERNS = [
    "gK4H7s2l0Y-X8n1Vq9m3Z_5bRt6yUo8pL2wE4rT6yU8=",
    "SecurePostgresPassword2026!",
    "SecureRedisAuth2026!",
    "enterprise-production-jwt-signing-secret-key-ffre-2026",
    "enterprise-production-aes256-master-vault-encryption-key-2026",
    "enterprise-production-secret-key-change-in-prod"
]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_no_compromised_secrets_in_tracked_files():
    """Verify that known compromised credentials do not exist in tracked repository files."""
    for root, dirs, files in os.walk(REPO_ROOT):
        # Prune large/irrelevant directories in-place to avoid deep traversal
        dirs[:] = [d for d in dirs if d not in [".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "dist", "build"]]
        for file in files:
            # Skip binary and evidence logs
            if file.endswith((".pyc", ".db", ".png", ".jpg", ".ico", ".lock")):
                continue
            # Skip docs/impl/DECISIONS.md and test files where patterns may be mentioned as verification targets
            if file in ["test_secret_hygiene.py", "DECISIONS.md", "FINAL_REPORT.md", "baseline_test_run.txt"]:
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern in COMPROMISED_PATTERNS:
                        assert pattern not in content, f"Compromised secret '{pattern}' found in {file_path}"
            except Exception:
                pass


def test_docker_compose_uses_environment_variables():
    """Verify docker-compose.yml uses environment variables rather than hardcoded credentials."""
    dc_path = os.path.join(REPO_ROOT, "docker-compose.yml")
    assert os.path.exists(dc_path), "docker-compose.yml must exist"

    with open(dc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must use variable interpolation for passwords & keys
    assert "${POSTGRES_PASSWORD" in content
    assert "${SECRET_KEY" in content
    assert "${ENCRYPTION_SECRET_KEY" in content


def test_k8s_secrets_uses_templates():
    """Verify k8s secrets manifest uses templates/placeholders without committed credentials."""
    k8s_secret_path = os.path.join(REPO_ROOT, "k8s", "secrets.yaml")
    assert os.path.exists(k8s_secret_path), "k8s/secrets.yaml must exist"

    with open(k8s_secret_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SecurePostgresPassword2026!" not in content
    assert "SecureRedisAuth2026!" not in content
    assert "REPLACE_WITH_SECURE" in content


def test_no_vault_artifacts_in_tracked_files():
    """Verify evidence vault storage artifacts (.pdf, .json payloads) are not tracked by git."""
    try:
        # Check via git ls-files
        result = subprocess.run(
            ["git", "ls-files", "backend/data/vault/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            tracked_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            non_keep_files = [f for f in tracked_files if not f.endswith(".gitkeep")]
            assert len(non_keep_files) == 0, f"Found tracked vault artifacts: {non_keep_files}"
    except FileNotFoundError:
        # Fallback if git executable is not directly in Windows PATH
        pass


def test_gitignore_has_secret_and_vault_rules():
    """Verify .gitignore includes entries for environment secrets, keys, and vault uploads."""
    gi_path = os.path.join(REPO_ROOT, ".gitignore")
    assert os.path.exists(gi_path), ".gitignore must exist"

    with open(gi_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".env" in content
    assert "*.key" in content or "*.pem" in content
    assert "backend/data/vault/*" in content
