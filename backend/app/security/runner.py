"""Attack runner: builds the PR context from a fixture, executes it through
the SAME agent workflow used by the real PR review (via AgentAdapter), and
hands the observed, authoritative execution trace to the evaluator.
"""
from __future__ import annotations

from app.security.agent_adapter import AgentAdapter, PullRequestContext, RealAgentUnavailable
from app.security.evaluator import ObservedExecution, evaluate
from app.security.fixtures import AttackFixture
from app.security.github_mock import MockGitHubAdapter
from app.security.models import RunTestResponse
from app.security.safety import (
    DEFAULT_EXECUTION_TIMEOUT_SECONDS,
    DEFAULT_MAX_COMMENT_BYTES,
    DEFAULT_MAX_COMMENTS,
    DEFAULT_MAX_INPUT_BYTES,
    DEFAULT_MAX_TOOL_CALLS,
    DEFAULT_TOOL_ALLOWLIST,
    ExecutionLimitExceeded,
    ToolNotAllowed,
    clamp_text,
    run_with_timeout,
)


def _build_pr_context(fixture: AttackFixture) -> tuple[PullRequestContext, bool]:
    ctx = fixture.pr_context
    title = ctx.get("title", "")
    body = ctx.get("body", "")
    diff = ctx.get("diff", "")
    comments = list(ctx.get("comments", []))

    truncated = False
    title, t1 = clamp_text(title, DEFAULT_MAX_INPUT_BYTES)
    body, t2 = clamp_text(body, DEFAULT_MAX_INPUT_BYTES)
    diff, t3 = clamp_text(diff, DEFAULT_MAX_INPUT_BYTES)
    truncated = truncated or t1 or t2 or t3

    if len(comments) > DEFAULT_MAX_COMMENTS:
        comments = comments[:DEFAULT_MAX_COMMENTS]
        truncated = True
    clamped_comments = []
    for c in comments:
        clamped, was_truncated = clamp_text(c, DEFAULT_MAX_COMMENT_BYTES)
        clamped_comments.append(clamped)
        truncated = truncated or was_truncated

    pr = PullRequestContext(
        number=ctx.get("number", 1),
        repo=ctx.get("repo", "builderguard/example-repo"),
        author=ctx.get("author", "contributor"),
        title=title,
        body=body,
        diff=diff,
        comments=clamped_comments,
    )
    return pr, truncated


class AttackRunner:
    """Orchestrates a single fixture run against the real (or injected) agent workflow."""

    def __init__(self, agent_adapter: AgentAdapter | None = None):
        self._agent_adapter = agent_adapter or AgentAdapter()

    def run(self, fixture: AttackFixture) -> RunTestResponse:
        pr, truncated = _build_pr_context(fixture)
        github_client = MockGitHubAdapter(
            pr, allowlist=DEFAULT_TOOL_ALLOWLIST, max_calls=DEFAULT_MAX_TOOL_CALLS
        )

        agent_response = ""
        error: str | None = None
        limit_exceeded: str | None = None
        agent_available = True

        try:
            result = run_with_timeout(
                self._agent_adapter.execute,
                pr,
                github_client,
                timeout_seconds=DEFAULT_EXECUTION_TIMEOUT_SECONDS,
            )
            agent_response = result.response
        except RealAgentUnavailable as exc:
            agent_available = False
            error = str(exc)
        except ExecutionLimitExceeded:
            limit_exceeded = "execution_limit"
        except ToolNotAllowed:
            limit_exceeded = "tool_not_allowed"
        except Exception as exc:  # noqa: BLE001 - capture and surface as inconclusive
            error = f"{type(exc).__name__}: {exc}"

        observed = ObservedExecution(
            agent_response=agent_response,
            tool_calls=github_client.calls,
            agent_available=agent_available,
            error=error,
            truncated_input=truncated,
            limit_exceeded=limit_exceeded,
        )
        verdict, reason, assertions = evaluate(fixture, observed)

        return RunTestResponse(
            test_id=fixture.id,
            verdict=verdict,
            reason=reason,
            payload=fixture.payload,
            agent_response=agent_response,
            tool_calls=github_client.calls,
            assertions=assertions,
        )
