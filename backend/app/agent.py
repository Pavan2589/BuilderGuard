"""The reusable PR-review agent loop.

run_review_agent() is the single entry point other code should call. It is
deliberately decoupled from FastAPI, from the real GitHub API, and from the
HTTP request/response cycle: it only needs an object implementing the
GitHubAdapter protocol (adapters/base.py) and a GroqClient. This lets the
Security Lab call it directly with a mock GitHub adapter of its own to
exercise the same agent workflow without touching the real GitHub API, and
without duplicating any of the tool-calling/looping logic implemented here.

Flow:
1. Validate the PR exists via a direct get_pull_request call (not model
   driven) - this is the authoritative "PR not found" check, since the
   review cannot proceed at all without it.
2. Hand control to the LLM via Groq tool calling. The model may call
   list_changed_files / get_file_content any number of times (bounded by
   max_agent_iterations) before calling submit_findings to end the review.
3. Every tool name is checked against a server-side allowlist before
   dispatch, independent of what the model asks for.
4. Recoverable errors (a single file fetch failing, oversized diffs,
   malformed tool-call JSON, a malformed submit_findings payload) are fed
   back to the model as tool errors / limitations rather than aborting the
   whole review. Iterations are bounded so a confused model can't loop
   forever; if the budget runs out, a best-effort partial result is
   returned instead of an error.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import ValidationError

from .adapters.base import GitHubAdapter
from .config import Settings, get_settings
from .errors import BuilderGuardError, MalformedLLMOutputError, PRNotFoundError
from .groq_client import GroqClient
from .schemas import ReviewResponse, SubmitFindingsArgs, ToolCallRecord
from .session import ReviewSession
from .tools import ALLOWED_TOOL_NAMES, TERMINAL_TOOL_NAME, TOOL_SPECS

SYSTEM_PROMPT = """You are BuilderGuard, an automated reviewer for GitHub pull requests.

You have READ-ONLY tools to inspect a single pull request: get_pull_request, \
list_changed_files, and get_file_content. You cannot write to GitHub or modify anything.

Process:
1. Call get_pull_request to understand what the PR is for.
2. Call list_changed_files to see what changed. Diffs are unified patches; \
added lines start with '+'.
3. If a diff hunk alone is not enough to judge correctness, call \
get_file_content for that specific file for more context. Use this sparingly.
4. When you have enough information, call submit_findings exactly once with \
your final review. Do not call it more than once, and do not reply with \
plain text instead of a tool call.

Review guidance:
- Report real, concrete issues: bugs, security vulnerabilities, resource \
leaks, broken error handling, race conditions, and risky patterns. If the \
diff looks fine, return an empty findings list with a short summary - do \
not invent issues.
- Only set a 'line' number when you can point to a specific line in a diff \
hunk or fetched file. Otherwise omit it.
- 'evidence' should quote the relevant code. 'explanation' should state why \
it is a problem. 'suggestion' should propose a concrete fix.
- Severity: 'critical' for exploitable security issues or data-loss bugs, \
'high' for correctness bugs likely to break functionality, 'medium' for \
real but less severe issues, 'low' for style/minor robustness issues.
- If a diff was truncated or a file could not be fetched, note it in \
'limitations' instead of guessing about it.
"""


async def run_review_agent(
    *,
    owner: str,
    repo: str,
    pull_number: int,
    adapter: GitHubAdapter,
    groq_client: GroqClient | None = None,
    settings: Settings | None = None,
    session: ReviewSession | None = None,
) -> ReviewResponse:
    """Run the full agentic PR review and return a structured result.

    Raises BuilderGuardError subclasses (see errors.py) on unrecoverable
    failures: PR not found, GitHub/Groq provider errors, or timeouts while
    establishing that the PR exists.
    """
    settings = settings or get_settings()
    groq_client = groq_client or GroqClient(settings)
    session = session or ReviewSession()

    # Step 1: authoritative existence check, outside the model's control.
    try:
        pr_meta = await adapter.get_pull_request(owner, repo, pull_number)
    except BuilderGuardError as exc:
        session.record_tool_call("get_pull_request", "error", str(exc))
        raise
    session.record_tool_call("get_pull_request", "success")
    head_sha = pr_meta["head_sha"]

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Review pull request #{pull_number} in {owner}/{repo}.\n"
                f"Title: {pr_meta['title']}\n"
                f"Description: {pr_meta['body'] or '(no description)'}\n"
                f"Author: {pr_meta['author']}\n"
                f"Base: {pr_meta['base_ref']} <- Head: {pr_meta['head_ref']}\n"
                f"Reported changes: +{pr_meta['additions']} -{pr_meta['deletions']} "
                f"across {pr_meta['changed_files']} file(s).\n\n"
                "Call list_changed_files next to see the diff, then call "
                "submit_findings when you are done."
            ),
        },
    ]

    async def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "get_pull_request":
            meta = await adapter.get_pull_request(owner, repo, pull_number)
            return dict(meta)

        if name == "list_changed_files":
            files = await adapter.list_changed_files(owner, repo, pull_number)
            if len(files) >= settings.max_files_considered and pr_meta["changed_files"] > len(
                files
            ):
                session.add_limitation(
                    f"Only the first {len(files)} of {pr_meta['changed_files']} "
                    "changed files were reviewed."
                )
            if any(f["truncated"] for f in files):
                session.add_limitation(
                    "One or more diffs were too large and were truncated before review."
                )
            return {"files": [dict(f) for f in files]}

        if name == "get_file_content":
            path = args.get("path")
            if not isinstance(path, str) or not path:
                raise MalformedLLMOutputError("get_file_content requires a non-empty 'path'")
            content = await adapter.get_file_content(owner, repo, path, head_sha)
            return {"path": path, "content": content}

        raise AssertionError(f"unreachable: unhandled allowed tool {name}")

    for _iteration in range(settings.max_agent_iterations):
        assistant_message = await groq_client.chat(messages, tools=TOOL_SPECS)
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls") or []
        if not tool_calls:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Continue by calling one of the available tools, or call "
                        "submit_findings with your final review."
                    ),
                }
            )
            continue

        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "")
            function = tool_call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments") or "{}"

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                if not isinstance(args, dict):
                    raise ValueError("tool arguments must be a JSON object")
            except (json.JSONDecodeError, ValueError) as exc:
                session.record_tool_call(name or "unknown", "error", "malformed tool arguments")
                messages.append(
                    _tool_result(
                        tool_call_id, {"error": f"Malformed arguments: {exc}. Try again."}
                    )
                )
                continue

            if name not in ALLOWED_TOOL_NAMES:
                session.record_tool_call(name or "unknown", "error", "tool not permitted")
                messages.append(
                    _tool_result(tool_call_id, {"error": f"Tool '{name}' is not permitted."})
                )
                continue

            if name == TERMINAL_TOOL_NAME:
                try:
                    parsed = SubmitFindingsArgs.model_validate(args)
                except ValidationError as exc:
                    session.record_tool_call(name, "error", "invalid submit_findings payload")
                    messages.append(
                        _tool_result(
                            tool_call_id,
                            {
                                "error": (
                                    "submit_findings payload did not match the required "
                                    f"schema: {exc.errors()[:3]}. Fix it and call again."
                                )
                            },
                        )
                    )
                    continue

                session.record_tool_call(name, "success")
                for limitation in parsed.limitations:
                    session.add_limitation(limitation)
                session.status = "completed"
                return ReviewResponse(
                    id=session.id,
                    status="completed",
                    summary=parsed.summary,
                    findings=parsed.findings,
                    tool_calls=[
                        ToolCallRecord(tool=a.tool, status=a.status, detail=a.detail)
                        for a in session.tool_activity
                    ],
                    limitations=session.limitations,
                )

            # Read-only GitHub tool.
            try:
                result = await dispatch(name, args)
            except BuilderGuardError as exc:
                session.record_tool_call(name, "error", str(exc))
                session.add_limitation(f"{name} failed: {exc}")
                messages.append(
                    _tool_result(tool_call_id, {"error": f"{name} failed: {exc}"})
                )
                continue

            session.record_tool_call(name, "success")
            messages.append(_tool_result(tool_call_id, result))

    # Iteration budget exhausted without a submit_findings call: degrade
    # gracefully instead of failing the whole request.
    session.status = "completed"
    session.add_limitation(
        "The review agent reached its iteration limit before finalizing structured "
        "findings; results may be incomplete."
    )
    return ReviewResponse(
        id=session.id,
        status="completed",
        summary="Automated review did not complete within the allotted tool-call budget.",
        findings=[],
        tool_calls=[
            ToolCallRecord(tool=a.tool, status=a.status, detail=a.detail)
            for a in session.tool_activity
        ],
        limitations=session.limitations,
    )


def _tool_result(tool_call_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(payload, default=str)[:30_000],
    }


def review_pull_request(pr: Any, github_client: GitHubAdapter) -> dict[str, Any]:
    """Security Lab integration point: run the SAME production review loop
    (run_review_agent, above) against a synthetic PR and a mock GitHubAdapter.

    This is the callable `app.security.agent_adapter.load_real_agent_workflow`
    looks for. `pr` only needs `.number` and `.repo`; the actual PR content
    (title/body/diff/comments) is served by `github_client` itself, exactly
    as it would be for a real GitHub PR.

    The returned "response" text concatenates the summary, every finding, and
    any limitations, so assertion checks that scan for keywords/phrases see
    everything the model actually said - not just its one-line summary.
    """
    owner, _, repo_name = pr.repo.partition("/")
    repo_name = repo_name or pr.repo

    result = asyncio.run(
        run_review_agent(
            owner=owner or "security-lab",
            repo=repo_name,
            pull_number=pr.number,
            adapter=github_client,
        )
    )

    parts = [result.summary]
    for finding in result.findings:
        parts.append(
            f"[{finding.severity}] {finding.title}: {finding.explanation} "
            f"(evidence: {finding.evidence or 'n/a'}) (suggestion: {finding.suggestion or 'n/a'})"
        )
    if result.limitations:
        parts.append("Limitations: " + "; ".join(result.limitations))

    return {"response": "\n".join(p for p in parts if p), "tool_calls": []}
