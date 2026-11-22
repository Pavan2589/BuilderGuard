"""Pydantic schemas for the Security Lab API contract."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Verdict = Literal["defended", "compromised", "inconclusive"]


class ToolCallRecord(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    blocked: bool = False


class TestSummary(BaseModel):
    id: str
    name: str
    category: str
    description: str


class TestListResponse(BaseModel):
    tests: list[TestSummary]


class RunTestRequest(BaseModel):
    test_id: str = Field(..., min_length=1, max_length=200)


class AssertionResult(BaseModel):
    name: str
    passed: bool
    detail: str | None = None


class RunTestResponse(BaseModel):
    test_id: str
    verdict: Verdict
    reason: str
    payload: str
    agent_response: str
    tool_calls: list[ToolCallRecord]
    assertions: list[AssertionResult]
