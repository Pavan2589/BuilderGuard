"""Reusable safety primitives: input-size clamping, tool allowlisting, and
execution limits. These are the controls the attack fixtures exercise, and
they are also meant to be reusable by the production review pipeline.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable, TypeVar

T = TypeVar("T")

DEFAULT_MAX_INPUT_BYTES = 64 * 1024  # 64 KiB of combined PR text
DEFAULT_MAX_COMMENTS = 50
DEFAULT_MAX_COMMENT_BYTES = 4 * 1024
# The real agent makes up to settings.max_agent_iterations (8) live Groq API
# round trips per run. 5s was only ever enough for a simulated/instant test
# double; a real multi-turn LLM workflow needs real wall-clock budget.
DEFAULT_EXECUTION_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_TOOL_CALLS = 20


class SafetyLimitExceeded(Exception):
    """Base class for all safety-control violations."""


class ExecutionLimitExceeded(SafetyLimitExceeded):
    """Raised when a run exceeds its time or tool-call budget."""


class ToolNotAllowed(SafetyLimitExceeded):
    """Raised when something attempts to invoke a tool outside the allowlist."""


def clamp_text(text: str, max_bytes: int = DEFAULT_MAX_INPUT_BYTES) -> tuple[str, bool]:
    """Clip ``text`` to at most ``max_bytes`` UTF-8 bytes.

    Returns (possibly_clipped_text, was_truncated).
    """
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, False
    clipped = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return clipped, True


class ToolAllowlist:
    """A reusable, explicit allowlist of permitted tool/function names."""

    def __init__(self, allowed: set[str]):
        self._allowed = set(allowed)

    def is_allowed(self, name: str) -> bool:
        return name in self._allowed

    def __contains__(self, name: str) -> bool:
        return self.is_allowed(name)


# The minimal read-only surface the real PR-review agent legitimately needs
# (must match app/tools.py's READ_ONLY_TOOL_NAMES exactly - these are the only
# tool names the production agent's tool schema ever offers the model).
DEFAULT_TOOL_ALLOWLIST = ToolAllowlist(
    {"get_pull_request", "list_changed_files", "get_file_content"}
)


def run_with_timeout(
    fn: Callable[..., T], *args, timeout_seconds: float = DEFAULT_EXECUTION_TIMEOUT_SECONDS, **kwargs
) -> T:
    """Run ``fn`` in a worker thread and enforce a wall-clock timeout.

    Raises ExecutionLimitExceeded if the call does not finish in time. This is
    used to defend against resource-exhaustion attacks (runaway loops, giant
    inputs) regardless of whether the agent itself has its own limits.
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            raise ExecutionLimitExceeded(
                f"execution exceeded {timeout_seconds}s timeout"
            ) from exc
