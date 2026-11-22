from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security.rate_limit import InMemoryRateLimitBackend, RateLimiter


def make_app(limiter: RateLimiter) -> TestClient:
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(limiter)])
    def limited():
        return {"ok": True}

    return TestClient(app)


def test_in_memory_backend_allows_up_to_the_limit_then_blocks():
    backend = InMemoryRateLimitBackend()
    allowed1, remaining1 = backend.hit("k", window_seconds=60, max_requests=2)
    allowed2, remaining2 = backend.hit("k", window_seconds=60, max_requests=2)
    allowed3, remaining3 = backend.hit("k", window_seconds=60, max_requests=2)
    assert (allowed1, allowed2, allowed3) == (True, True, False)
    assert remaining1 == 1
    assert remaining2 == 0
    assert remaining3 == 0


def test_rate_limiter_dependency_returns_429_once_exceeded():
    limiter = RateLimiter(max_requests=2, window_seconds=60, backend=InMemoryRateLimitBackend())
    client = make_app(limiter)
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    resp = client.get("/limited").status_code
    assert resp == 429


def test_rate_limiter_keys_are_isolated_per_path():
    limiter = RateLimiter(max_requests=1, window_seconds=60, backend=InMemoryRateLimitBackend())
    app = FastAPI()

    @app.get("/a", dependencies=[Depends(limiter)])
    def a():
        return {"ok": True}

    @app.get("/b", dependencies=[Depends(limiter)])
    def b():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/a").status_code == 200
    assert client.get("/b").status_code == 200  # different path key, not exhausted
    assert client.get("/a").status_code == 429
