"""
Enterprise Sliding-Window Rate Limiter & Anti-Abuse Protection (Chapters 47 & 88)
Provides multi-tenant & IP-level request rate limiting, token throttling, and abuse mitigation.
"""

import time
import os
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

DEFAULT_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
AUTH_RATE_LIMIT = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10"))

class SlidingWindowRateLimiter:
    """Sliding-window request rate limiter tracking requests across fixed time windows."""

    def __init__(self, default_limit: int = DEFAULT_RATE_LIMIT, window_seconds: int = 60):
        self._lock = Lock()
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        # client_key -> deque of timestamps
        self._requests: Dict[str, deque] = defaultdict(deque)
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")

    def is_allowed(self, client_key: str, limit: Optional[int] = None) -> Tuple[bool, int, int, int]:
        """
        Check if the request from client_key is allowed within the current window.
        Returns:
            (allowed: bool, limit: int, remaining: int, retry_after: int)
        """
        if not self.enabled:
            return True, self.default_limit, self.default_limit, 0

        max_reqs = limit if limit is not None else self.default_limit
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_key]

            # Purge timestamps outside current sliding window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            current_count = len(timestamps)
            if current_count >= max_reqs:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                return False, max_reqs, 0, retry_after

            timestamps.append(now)
            remaining = max(0, max_reqs - len(timestamps))
            return True, max_reqs, remaining, 0

    def reset(self):
        """Clear state for test isolation."""
        with self._lock:
            self._requests.clear()

rate_limiter = SlidingWindowRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware enforcing sliding-window rate limits."""

    EXEMPT_PATHS = {
        "/health",
        "/api/v1/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc"
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Exempt paths skip rate limiting
        if path in self.EXEMPT_PATHS or not rate_limiter.enabled:
            return await call_next(request)

        # Client key is combination of client IP and tenant if header present
        client_ip = request.client.host if request.client else "127.0.0.1"
        tenant_hdr = request.headers.get("X-Tenant-ID", "default")
        client_key = f"{client_ip}:{tenant_hdr}"

        # Assign stricter limit for sensitive auth endpoints
        limit = AUTH_RATE_LIMIT if "/api/v1/auth/" in path else rate_limiter.default_limit
        if "/api/v1/auth/" in path:
            client_key = f"auth:{client_key}"

        allowed, max_limit, remaining, retry_after = rate_limiter.is_allowed(client_key, limit=limit)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry after some time.",
                    "retry_after_seconds": retry_after,
                    "limit_per_minute": max_limit
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(rate_limiter.window_seconds)
        return response
