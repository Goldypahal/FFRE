"""
Minimal HTTP clients for calling real LLM APIs from FFIRE-Bench runners.

Only the Python standard library is used, so the benchmark has no SDK
dependencies. Each factory returns a callable ``(system: str, user: str) -> dict``
that sends one chat request and returns the model's JSON answer as a dict.

Supported providers:
- ``openai``: any OpenAI-compatible Chat Completions endpoint (OpenAI,
  OpenRouter, Together, Groq, vLLM, Ollama, LM Studio, ...). Set ``base_url``
  to point at a non-OpenAI server.
- ``anthropic``: the Anthropic Messages API.

API keys are read from the environment, never from files in the repository.
"""

import json
import os
import re
import urllib.request
from typing import Any, Callable, Dict, Optional

LLMCaller = Callable[..., Dict[str, Any]]

DEFAULT_TIMEOUT_S = 120


def _post_json(url: str, headers: Dict[str, str], body: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_json_object(text: str) -> Dict[str, Any]:
    """Parse the first JSON object in a model reply (tolerates ```json fences and prose)."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model reply contains no JSON object")
        text = text[start:end + 1]
    return json.loads(text)


def make_openai_compatible_caller(
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> LLMCaller:
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

    def call(system: str, user: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        body = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        data = _post_json(f"{base_url}/chat/completions", headers, body, timeout)
        return extract_json_object(data["choices"][0]["message"]["content"])

    return call


def make_anthropic_caller(
    model: str,
    api_key: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> LLMCaller:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    def call(system: str, user: str) -> Dict[str, Any]:
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        data = _post_json("https://api.anthropic.com/v1/messages", headers, body, timeout)
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        return extract_json_object(text)

    return call


def make_caller(provider: str, model: str, base_url: Optional[str] = None) -> LLMCaller:
    provider = provider.lower()
    if provider == "openai":
        return make_openai_compatible_caller(model=model, base_url=base_url)
    if provider == "anthropic":
        return make_anthropic_caller(model=model)
    raise ValueError(f"Unknown LLM provider '{provider}'. Use 'openai' (any OpenAI-compatible API) or 'anthropic'.")
