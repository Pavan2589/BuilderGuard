"""FastAPI router for the Security Lab. Importable and includable by the core app:

    from app.security import router as security_router
    app.include_router(security_router)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.security.fixtures import get_fixture, list_fixtures
from app.security.models import RunTestRequest, RunTestResponse, TestListResponse, TestSummary
from app.security.rate_limit import RateLimiter
from app.security.runner import AttackRunner

router = APIRouter(prefix="/api/security", tags=["security"])

_runner = AttackRunner()
_run_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


@router.get("/tests", response_model=TestListResponse)
def list_tests() -> TestListResponse:
    return TestListResponse(
        tests=[
            TestSummary(id=f.id, name=f.name, category=f.category, description=f.description)
            for f in list_fixtures()
        ]
    )


@router.post(
    "/tests/run",
    response_model=RunTestResponse,
    dependencies=[Depends(_run_rate_limiter)],
)
def run_test(payload: RunTestRequest) -> RunTestResponse:
    fixture = get_fixture(payload.test_id)
    if fixture is None:
        raise HTTPException(status_code=404, detail=f"Unknown test_id: {payload.test_id!r}")
    return _runner.run(fixture)
