"""Strict validation/parsing of GitHub pull request URLs."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from .errors import InvalidPRUrlError

_PR_PATH_RE = re.compile(r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([0-9]+)/?$")


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parse and strictly validate a GitHub PR URL.

    Returns (owner, repo, pull_number). Raises InvalidPRUrlError for anything
    that isn't exactly https://github.com/<owner>/<repo>/pull/<number>.
    """
    if not isinstance(pr_url, str) or not pr_url.strip():
        raise InvalidPRUrlError("pr_url must be a non-empty string")

    parts = urlsplit(pr_url.strip())

    if parts.scheme != "https":
        raise InvalidPRUrlError("pr_url must use the https scheme")

    if parts.username or parts.password:
        raise InvalidPRUrlError("pr_url must not contain embedded credentials")

    if parts.port is not None:
        raise InvalidPRUrlError("pr_url must not specify a custom port")

    hostname = (parts.hostname or "").lower()
    if hostname != "github.com":
        raise InvalidPRUrlError(
            "pr_url must point to github.com (no subdomains or other hosts)"
        )

    match = _PR_PATH_RE.match(parts.path)
    if not match:
        raise InvalidPRUrlError(
            "pr_url must look like https://github.com/<owner>/<repo>/pull/<number>"
        )

    owner, repo, number_str = match.group(1), match.group(2), match.group(3)
    if repo.endswith(".git"):
        raise InvalidPRUrlError("pr_url repo segment must not end in .git")

    try:
        pull_number = int(number_str)
    except ValueError as exc:  # pragma: no cover - regex guarantees digits
        raise InvalidPRUrlError("pr_url pull request number is invalid") from exc

    if pull_number <= 0:
        raise InvalidPRUrlError("pr_url pull request number must be positive")

    return owner, repo, pull_number
