"""The GitHub tool interface the review agent depends on.

This is intentionally a structural Protocol, not a base class: any object
with matching async methods satisfies it. That lets another consumer (e.g.
the Security Lab) pass in a mock adapter that fabricates PR data, without
importing or subclassing anything from this package.
"""
from __future__ import annotations

from typing import Protocol, TypedDict


class PullRequestMeta(TypedDict):
    number: int
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    base_sha: str
    head_sha: str
    additions: int
    deletions: int
    changed_files: int
    state: str
    html_url: str


class ChangedFile(TypedDict):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str
    truncated: bool


class GitHubAdapter(Protocol):
    """Read-only access to a single pull request. No write methods exist."""

    async def get_pull_request(
        self, owner: str, repo: str, pull_number: int
    ) -> PullRequestMeta: ...

    async def list_changed_files(
        self, owner: str, repo: str, pull_number: int
    ) -> list[ChangedFile]: ...

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str: ...
