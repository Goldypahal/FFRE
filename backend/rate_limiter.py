"""

Enterprise Distributed Sliding-Window Rate Limiter & Anti-Abuse Protection (Chapters 47 & 88).

Provides multi-tenant & IP-level request rate limiting, token throttling, and abuse mitigation.

Uses Redis with atomic Lua sliding-window script for cross-replica synchronization

(Kubernetes multi-pod & multi-worker Uvicorn), with thread-safe in-memory fallback for local development.

"""



import time

import os

import uuid

import math

from collections import defaultdict, deque

from threading import Lock

from typing import Dict, Tuple, Optional

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import JSONResponse, Response



DEFAULT_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

AUTH_RATE_LIMIT = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10"))



LUA_SLIDING_WINDOW = """

local key = KEYS[1]

local now = tonumber(ARGV[1])

local window_start = tonumber(ARGV[2])

local max_reqs = tonumber(ARGV[3])

local ttl = tonumber(ARGV[4])

local entry_id = ARGV[5]



redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

local current_count = redis.call('ZCARD', key)



if current_count < max_reqs then

    redis.call('ZADD', key, now, entry_id)

    redis.call('EXPIRE', key, ttl)

    return {1, max_reqs - current_count - 1, 0}

else

    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')

    local retry_after = ttl

    if #oldest > 0 then

        retry_after = math.max(1, math.ceil(tonumber(oldest[2]) + (ttl - 5) - now))

    end

    return {0, 0, retry_after}

end

"""





def _get_redis_client():

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:

        import redis

        client = redis.Redis.from_url(redis_url, socket_timeout=1, decode_responses=True)

        client.ping()

        return client

    except Exception:

        return None





class DistributedRateLimiter:

    """

    Sliding-window rate limiter supporting Redis-backed distributed synchronization

    across multi-pod Kubernetes clusters and multi-worker gateways via atomic Lua scripts.

    """



    def __init__(self, default_limit: int = DEFAULT_RATE_LIMIT, window_seconds: int = 60):

        self._lock = Lock()

        self.default_limit = default_limit

        self.window_seconds = window_seconds

        self._memory_requests: Dict[str, deque] = defaultdict(deque)

        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")

        self.strict_enterprise = (

            os.getenv("STRICT_ENTERPRISE_MODE", "false").lower() in ("true", "1", "yes") or

            os.getenv("ENVIRONMENT") == "production" or

            os.getenv("ENV") == "production"

        )

        self._redis = None

        self._redis_checked = False

        self._lua_script = None



    def _redis_conn(self):

        if not self._redis_checked:

            self._redis = _get_redis_client()

            if self._redis is not None:

                try:

                    self._lua_script = self._redis.register_script(LUA_SLIDING_WINDOW)

                except Exception:

                    self._lua_script = None

            self._redis_checked = True

        return self._redis



    def is_allowed(self, client_key: str, limit: Optional[int] = None) -> Tuple[bool, int, int, int]:

        """

        Check if request from client_key is allowed within current sliding window.

        Returns:

            (allowed: bool, limit: int, remaining: int, retry_after: int)

        """

        if not self.enabled:

            return True, self.default_limit, self.default_limit, 0



        max_reqs = limit if limit is not None else self.default_limit

        now = time.time()

        window_start = now - self.window_seconds

        r = self._redis_conn()



        # 1. Distributed Redis sliding-window implementation (Atomic Lua script)

        if r is not None and self._lua_script is not None:

            try:

                redis_key = f"ffre:ratelimit:{client_key}"

                entry_id = f"{now}_{uuid.uuid4().hex[:6]}"

                res = self._lua_script(

                    keys=[redis_key],

                    args=[now, window_start, max_reqs, self.window_seconds + 5, entry_id]

                )

                allowed = bool(res[0] == 1)

                remaining = int(res[1])

                retry_after = int(res[2])

                return allowed, max_reqs, remaining, retry_after

            except Exception as e:

                if self.strict_enterprise:

                    raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Redis rate limiter failure ({e}). In-memory fallback is disabled in production.")

                # Local development fallback

                pass

        elif self.strict_enterprise:

            raise RuntimeError("STRICT_ENTERPRISE_MODE: Redis broker is unavailable for rate limiting. In-memory fallback is disabled in production.")



        # 2. Resilient In-Memory Sliding-Window Fallback

        with self._lock:

            timestamps = self._memory_requests[client_key]

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

        """Reset limiter state for test isolation."""

        with self._lock:

            self._memory_requests.clear()

        r = self._redis_conn()

        if r is not None:

            try:

                keys = r.keys("ffre:ratelimit:*")

                if keys:

                    r.delete(*keys)

            except Exception:

                pass





rate_limiter = DistributedRateLimiter()





class RateLimitMiddleware(BaseHTTPMiddleware):

    """FastAPI/Starlette middleware enforcing distributed sliding-window rate limits."""



    EXEMPT_PATHS = {

        "/health",

        "/metrics",

        "/docs",

        "/redoc",

        "/openapi.json",

        "/api/v1/health",

        "/api/v1/verifier/public-key",

        "/favicon.ico"

    }



    async def dispatch(self, request: Request, call_next) -> Response:

        path = request.url.path



        if any(path == p or path.startswith(p + "/") for p in self.EXEMPT_PATHS):

            return await call_next(request)



        client_ip = request.client.host if request.client else "unknown"



        # Cryptographically verified tenant identity; unauthenticated requests use client IP bucket

        tenant_id = None

        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):

            token_str = auth_header.split(" ")[1]

            try:

                import auth

                payload = auth.decode_access_token(token_str)

                if isinstance(payload, dict) and payload.get("tenant_id"):

                    tenant_id = str(payload["tenant_id"])

            except Exception:

                tenant_id = None



        is_auth = path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register") or path.startswith("/api/v1/auth/bootstrap")

        limit = AUTH_RATE_LIMIT if is_auth else rate_limiter.default_limit



        if is_auth:

            key = f"ip:{client_ip}:auth"

        elif tenant_id:

            key = f"tenant:{tenant_id}:ip:{client_ip}"

        else:

            key = f"anon:ip:{client_ip}"

        try:

            allowed, req_limit, remaining, retry_after = rate_limiter.is_allowed(key, limit=limit)

        except RuntimeError as re:

            return JSONResponse(

                status_code=503,

                content={"detail": str(re)}

            )



        if not allowed:

            return JSONResponse(

                status_code=429,

                content={

                    "detail": "Rate limit exceeded. Please wait before submitting more requests.",

                    "limit": req_limit,

                    "retry_after_seconds": retry_after

                },

                headers={

                    "Retry-After": str(retry_after),

                    "X-RateLimit-Limit": str(req_limit),

                    "X-RateLimit-Remaining": "0",

                    "X-RateLimit-Reset": str(int(time.time() + retry_after))

                }

            )



        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(req_limit)

        response.headers["X-RateLimit-Remaining"] = str(remaining)

        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response

