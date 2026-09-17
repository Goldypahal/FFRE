import os
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_docker_compose_structure():
    """Verify docker-compose.yml specifies full enterprise topology."""
    compose_path = os.path.join(ROOT_DIR, "docker-compose.yml")
    assert os.path.exists(compose_path)

    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify all 5 core production services exist
    assert "db:" in content
    assert "redis:" in content
    assert "backend:" in content
    assert "worker:" in content
    assert "frontend:" in content

    # Verify network and volume topology
    assert "ffire_net:" in content
    assert "postgres_data:" in content
    assert "redis_data:" in content

    # Verify healthchecks are configured
    assert "healthcheck:" in content
    assert "pg_isready" in content
    assert "redis-cli" in content

def test_backend_dockerfile():
    """Verify backend Dockerfile implements secure multi-stage build with non-root user."""
    dockerfile_path = os.path.join(ROOT_DIR, "backend", "Dockerfile")
    assert os.path.exists(dockerfile_path)

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FROM python:3.12-slim as builder" in content
    assert "FROM python:3.12-slim as runner" in content
    assert "useradd" in content
    assert "ffireuser" in content
    assert "USER ffireuser" in content
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content

def test_frontend_dockerfile_and_nginx():
    """Verify frontend Dockerfile and Nginx configuration for production SPA delivery."""
    dockerfile_path = os.path.join(ROOT_DIR, "frontend", "Dockerfile")
    nginx_path = os.path.join(ROOT_DIR, "frontend", "nginx.conf")

    assert os.path.exists(dockerfile_path)
    assert os.path.exists(nginx_path)

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        df_content = f.read()

    assert "FROM node:20-alpine as builder" in df_content
    assert "FROM nginx:alpine as runner" in df_content
    assert "npm run build" in df_content
    assert "HEALTHCHECK" in df_content

    with open(nginx_path, "r", encoding="utf-8") as f:
        ng_content = f.read()

    assert "location /api/" in ng_content
    assert "proxy_pass http://backend:8000/api/;" in ng_content
    assert "try_files $uri $uri/ /index.html;" in ng_content
    assert "gzip on;" in ng_content
