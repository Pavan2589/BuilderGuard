"""Real, read-only GitHub REST API adapter.

Only ever issues GET requests. GITHUB_TOKEN (if set) is attached as a bearer
header for higher rate limits; it is never logged or returned to callers.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from ..config import Settings
from ..errors import AgentTimeoutError, GitHubAPIError, PRNotFoundError
from .base import ChangedFile, PullRequestMeta


class GitHubAPIAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "BuilderGuard-PR-Reviewer",
        }
        if self._settings.github_token:
            headers["Authorization"] = f"Bearer {self._settings.github_token}"
        return headers

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                resp = await client.get(url, headers=self._headers(), params=params)
        except httpx.TimeoutException as exc:
            raise AgentTimeoutError("GitHub API request timed out") from exc
        except httpx.HTTPError as exc:
            raise GitHubAPIError(f"GitHub API request failed: {exc}") from exc

        if resp.status_code == 404:
            raise PRNotFoundError("Pull request or repository not found")
        if resp.status_code == 403:
            raise GitHubAPIError(
                "GitHub API forbidden or rate-limited (set GITHUB_TOKEN to raise limits)"
            )
        if resp.status_code >= 400:
            raise GitHubAPIError(f"GitHub API returned HTTP {resp.status_code}")

        try:
            return resp.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub API returned a non-JSON response") from exc

    async def get_pull_request(
        self, owner: str, repo: str, pull_number: int
    ) -> PullRequestMeta:
        url = f"{self._settings.github_api_base}/repos/{owner}/{repo}/pulls/{pull_number}"
        data = await self._get(url)
        try:
            return PullRequestMeta(
                number=data["number"],
                title=data.get("title") or "",
                body=(data.get("body") or "")[:4000],
                author=(data.get("user") or {}).get("login", "unknown"),
                base_ref=data["base"]["ref"],
                head_ref=data["head"]["ref"],
                base_sha=data["base"]["sha"],
                head_sha=data["head"]["sha"],
                additions=data.get("additions", 0),
                deletions=data.get("deletions", 0),
                changed_files=data.get("changed_files", 0),
                state=data.get("state", "unknown"),
                html_url=data.get("html_url", ""),
            )
        except (KeyError, TypeError) as exc:
            raise GitHubAPIError("GitHub API returned an unexpected PR shape") from exc

    async def list_changed_files(
        self, owner: str, repo: str, pull_number: int
    ) -> list[ChangedFile]:
        url = f"{self._settings.github_api_base}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        collected: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self._get(url, params={"per_page": 100, "page": page})
            if not isinstance(batch, list) or not batch:
                break
            collected.extend(batch)
            if len(batch) < 100 or len(collected) >= self._settings.max_files_considered:
                break
            page += 1

        results: list[ChangedFile] = []
        for item in collected[: self._settings.max_files_considered]:
            patch = item.get("patch", "") or ""
            truncated = len(patch) > self._settings.max_diff_bytes
            if truncated:
                patch = patch[: self._settings.max_diff_bytes]
            results.append(
                ChangedFile(
                    filename=item["filename"],
                    status=item.get("status", "modified"),
                    additions=item.get("additions", 0),
                    deletions=item.get("deletions", 0),
                    patch=patch,
                    truncated=truncated,
                )
            )
        return results

    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        url = f"{self._settings.github_api_base}/repos/{owner}/{repo}/contents/{path}"
        data = await self._get(url, params={"ref": ref})
        if isinstance(data, list):
            raise GitHubAPIError(f"{path} is a directory, not a file")
        content_b64 = data.get("content", "") if isinstance(data, dict) else ""
        try:
            content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as exc:
            raise GitHubAPIError(f"Could not decode file content for {path}") from exc
        if len(content) > self._settings.max_diff_bytes:
            content = content[: self._settings.max_diff_bytes]
        return content
