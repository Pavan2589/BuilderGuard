"""Adapter that invokes the SAME agent workflow used by the real PR review.

This module intentionally contains no pretend/alternate agent implementation.
It defines the contract the production PR-review workflow is expected to
satisfy, tries to load the real implementation from ``app.agent``, and if
that is not available yet (e.g. this worktree was built before app/agent/
landed), it fails honestly: callers get `RealAgentUnavailable` rather than a
faked verdict.

Expected integration contract
------------------------------
``app.agent`` must expose a callable:

    review_pull_request(pr: PullRequestContext, github_client: Any) -> AgentRunResult | dict | str

- ``pr`` carries the (possibly malicious) PR title/body/diff/comments.
- ``github_client`` is the tool surface the agent calls to read PR data
  (see app.security.github_mock.MockGitHubAdapter for the mock implementation
  used by the Security Lab; the real workflow should accept any object
  exposing the same methods, so the real GitHub client and this mock are
  interchangeable).
- The return value's ``response`` text is the agent's review output, and
  ``tool_calls`` (if the agent self-reports them) is informational only -
  the authoritative tool-call log for evaluation comes from the mock client
  itself (see runner.py), not from the agent's self-report.

Tests may inject a stand-in workflow via `AgentAdapter(workflow=...)` for unit
testing the runner/evaluator in isolation. That stand-in is a test double, not
a production code path: the live API always goes through `load_real_agent_workflow`.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable, Optional, Protocol

from pydantic import BaseModel, Field

from app.security.models import ToolCallRecord

EXPECTED_REAL_AGENT_MODULE = "app.agent"
EXPECTED_REAL_AGENT_CALLABLE = "review_pull_request"


class PullRequestContext(BaseModel):
    number: int = 1
    repo: str = "builderguard/example-repo"
    author: str = "contributor"
    title: str = ""
    body: str = ""
    diff: str = ""
    comments: list[str] = Field(default_factory=list)


class AgentRunResult(BaseModel):
    response: str = ""
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class AgentWorkflow(Protocol):
    def __call__(self, pr: PullRequestContext, github_client: Any) -> Any: ...


class RealAgentUnavailable(Exception):
    """Raised when the real app.agent PR-review workflow cannot be loaded."""


def load_real_agent_workflow() -> tuple[Optional[Callable[..., Any]], Optional[str]]:
    """Try to import the production agent workflow.

    Returns (callable_or_None, reason_if_unavailable_or_None).
    """
    try:
        module = importlib.import_module(EXPECTED_REAL_AGENT_MODULE)
    except ModuleNotFoundError as exc:
        return None, (
            f"module '{EXPECTED_REAL_AGENT_MODULE}' not found ({exc}). "
            "The real PR-review agent has not been wired into this build yet."
        )
    fn = getattr(module, EXPECTED_REAL_AGENT_CALLABLE, None)
    if fn is None or not callable(fn):
        return None, (
            f"module '{EXPECTED_REAL_AGENT_MODULE}' does not expose a callable "
            f"'{EXPECTED_REAL_AGENT_CALLABLE}(pr, github_client)'."
        )
    return fn, None


def _coerce_result(result: Any) -> AgentRunResult:
    if isinstance(result, AgentRunResult):
        return result
    if isinstance(result, dict):
        return AgentRunResult(**result)
    if isinstance(result, str):
        return AgentRunResult(response=result)
    raise TypeError(f"Unsupported agent workflow return type: {type(result)!r}")


class AgentAdapter:
    """Thin, replaceable wrapper around the real (or injected test-double) workflow."""

    def __init__(self, workflow: Optional[AgentWorkflow] = None):
        if workflow is not None:
            self._workflow: Optional[Callable[..., Any]] = workflow
            self._unavailable_reason: Optional[str] = None
        else:
            self._workflow, self._unavailable_reason = load_real_agent_workflow()

    @property
    def is_available(self) -> bool:
        return self._workflow is not None

    @property
    def unavailable_reason(self) -> Optional[str]:
        return self._unavailable_reason

    def execute(self, pr: PullRequestContext, github_client: Any) -> AgentRunResult:
        if self._workflow is None:
            raise RealAgentUnavailable(
                self._unavailable_reason or "agent workflow not configured"
            )
        raw_result = self._workflow(pr, github_client)
        return _coerce_result(raw_result)
