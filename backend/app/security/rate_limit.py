"""Reusable rate-limiter FastAPI dependency.

Uses Redis when `BUILDERGUARD_REDIS_URL` (or `REDIS_URL`) is configured and
reachable. Otherwise falls back to a clearly-labeled in-memory limiter meant
only for local development - it is process-local and does not coordinate
across multiple workers/instances.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Optional, Protocol

from fastapi import HTTPException, Request

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover - exercised only when redis isn't installed
    redis_lib = None


class RateLimitBackend(Protocol):
    def hit(self, key: str, window_seconds: int, max_requests: int) -> tuple[bool, int]:
        """Record one hit for `key`. Returns (allowed, remaining)."""
        ...


class InMemoryRateLimitBackend:
    """Local-development fallback ONLY.

    Process-local sliding window. Does not coordinate across multiple worker
    processes or instances - do not rely on this for production deployments.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._hits: dict[str, deque] = {}

    def hit(self, key: str, window_seconds: int, max_requests: int) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            dq = self._hits.setdefault(key, deque())
            while dq and now - dq[0] > window_seconds:
                dq.popleft()
            if len(dq) >= max_requests:
                return False, 0
            dq.append(now)
            return True, max_requests - len(dq)


class RedisRateLimitBackend:
    """Redis-backed fixed-window counter, safe across multiple processes/instances."""

    def __init__(self, client):
        self._client = client

    def hit(self, key: str, window_seconds: int, max_requests: int) -> tuple[bool, int]:
        redis_key = f"builderguard:ratelimit:{key}"
        pipe = self._client.pipeline()
        pipe.incr(redis_key, 1)
        pipe.ttl(redis_key)
        count, ttl = pipe.execute()
        if ttl is None or ttl < 0:
            self._client.expire(redis_key, window_seconds)
        allowed = count <= max_requests
        remaining = max(0, max_requests - count)
        return allowed, remaining


def _build_default_backend() -> RateLimitBackend:
    redis_url = os.environ.get("BUILDERGUARD_REDIS_URL") or os.environ.get("REDIS_URL")
    if redis_url and redis_lib is not None:
        try:
            client = redis_lib.from_url(redis_url, socket_connect_timeout=0.5)
            client.ping()
            return RedisRateLimitBackend(client)
        except Exception:
            # Redis configured but unreachable - fall back rather than hard-fail.
            pass
    return InMemoryRateLimitBackend()


class RateLimiter:
    """A reusable FastAPI dependency: `Depends(RateLimiter(max_requests=30, window_seconds=60))`."""

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
        backend: Optional[RateLimitBackend] = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._backend = backend or _build_default_backend()

    def __call__(self, request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_host}"
        allowed, _remaining = self._backend.hit(key, self.window_seconds, self.max_requests)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
