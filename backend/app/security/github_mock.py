"""Controlled mock GitHub adapter.

Implements the SAME `GitHubAdapter` protocol (app/adapters/base.py) the real
production agent (app/agent.py) depends on - async get_pull_request /
list_changed_files / get_file_content - so the Security Lab can run the real
review workflow unmodified against synthetic PR data, instead of a pretend
tool surface the real agent doesn't actually have.

Every call - permitted or not - is guarded against an allowlist and a
max-call budget, and recorded in `self.calls`. That call log is the
authoritative, tamper-proof observation channel the evaluator uses,
independent of whatever the agent itself claims to have done.

`call_untrusted_tool` exists only so a test double standing in for a
*hypothetically misbehaving* agent can simulate reaching for a tool
(`merge_pull_request`, `grant_admin_access`, ...) that the real agent's tool
schema (app/tools.py) never actually offers it - the production workflow can
never reach these names on its own.
"""
from __future__ import annotations

import re

from app.security.agent_adapter import PullRequestContext
from app.security.models import ToolCallRecord
from app.security.safety import (
    DEFAULT_MAX_TOOL_CALLS,
    DEFAULT_TOOL_ALLOWLIST,
    ExecutionLimitExceeded,
    ToolAllowlist,
    ToolNotAllowed,
)

_FILENAME_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def _extract_filename(diff: str) -> str:
    match = _FILENAME_RE.search(diff)
    return match.group(1).strip() if match else "changed_file.diff"


class MockGitHubAdapter:
    """Stand-in for the real GitHub client used by the production PR-review agent.

    Exposes the exact async methods `GitHubAdapter` requires, backed by a
    single synthetic PR's fabricated (and sometimes malicious) text.
    """

    def __init__(
        self,
        pr: PullRequestContext,
        *,
        allowlist: ToolAllowlist = DEFAULT_TOOL_ALLOWLIST,
        max_calls: int = DEFAULT_MAX_TOOL_CALLS,
        diff_truncated: bool = False,
    ):
        self._pr = pr
        self._allowlist = allowlist
        self._max_calls = max_calls
        self._diff_truncated = diff_truncated
        self.calls: list[ToolCallRecord] = []

    def _guard(self, tool: str, arguments: dict) -> None:
        if len(self.calls) >= self._max_calls:
            self.calls.append(ToolCallRecord(tool=tool, arguments=arguments, blocked=True))
            raise ExecutionLimitExceeded(
                f"max tool call limit ({self._max_calls}) exceeded on '{tool}'"
            )
        if not self._allowlist.is_allowed(tool):
            self.calls.append(ToolCallRecord(tool=tool, arguments=arguments, blocked=True))
            raise ToolNotAllowed(f"tool '{tool}' is not in the allowlist")
        self.calls.append(ToolCallRecord(tool=tool, arguments=arguments, blocked=False))

    # --- the real, read-only GitHubAdapter protocol ---------------------------------
    async def get_pull_request(self, owner: str = "", repo: str = "", pull_number: int = 0) -> dict:
        self._guard("get_pull_request", {"owner": owner, "repo": repo, "pull_number": pull_number})
        body = self._pr.body
        if self._pr.comments:
            body = body + "\n\nPR comments:\n" + "\n".join(f"- {c}" for c in self._pr.comments)
        return {
            "number": self._pr.number,
            "title": self._pr.title,
            "body": body,
            "author": self._pr.author,
            "base_ref": "main",
            "head_ref": "security-lab-fixture",
            "base_sha": "mock-base-sha",
            "head_sha": "mock-head-sha",
            "additions": self._pr.diff.count("\n+"),
            "deletions": self._pr.diff.count("\n-"),
            "changed_files": 1,
            "state": "open",
            "html_url": f"https://github.com/{self._pr.repo}/pull/{self._pr.number}",
        }

    async def list_changed_files(self, owner: str = "", repo: str = "", pull_number: int = 0) -> list[dict]:
        self._guard("list_changed_files", {"owner": owner, "repo": repo, "pull_number": pull_number})
        return [
            {
                "filename": _extract_filename(self._pr.diff),
                "status": "modified",
                "additions": self._pr.diff.count("\n+"),
                "deletions": self._pr.diff.count("\n-"),
                "patch": self._pr.diff,
                "truncated": self._diff_truncated,
            }
        ]

    async def get_file_content(self, owner: str = "", repo: str = "", path: str = "", ref: str = "") -> str:
        self._guard("get_file_content", {"owner": owner, "repo": repo, "path": path, "ref": ref})
        return (
            f"(Security Lab mock: no separate file content is available for "
            f"'{path}'; the full change is already in the diff.)"
        )

    # --- simulated dangerous surface, for defense-in-depth test doubles only -------
    def call_untrusted_tool(self, name: str, **kwargs) -> dict:
        self._guard(name, kwargs)
        return {"ok": True}
