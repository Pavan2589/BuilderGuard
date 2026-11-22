"""Pydantic models for the public API contract."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
ToolStatus = Literal["success", "error"]
ReviewStatus = Literal["completed", "failed"]


class ReviewRequest(BaseModel):
    pr_url: str = Field(..., description="GitHub pull request URL")


class Finding(BaseModel):
    severity: Severity
    file: str | None = None
    line: int | None = None
    title: str
    explanation: str
    evidence: str | None = None
    suggestion: str | None = None


class ToolCallRecord(BaseModel):
    tool: str
    status: ToolStatus
    detail: str | None = None


class ReviewResponse(BaseModel):
    id: str
    status: ReviewStatus
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SubmitFindingsArgs(BaseModel):
    """Schema the LLM's final submit_findings tool call must satisfy."""

    summary: str
    findings: list[Finding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
