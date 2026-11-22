import time

import pytest

from app.security.safety import (
    DEFAULT_TOOL_ALLOWLIST,
    ExecutionLimitExceeded,
    ToolAllowlist,
    clamp_text,
    run_with_timeout,
)


def test_clamp_text_under_limit_is_unchanged():
    text = "hello world"
    clipped, truncated = clamp_text(text, max_bytes=1024)
    assert clipped == text
    assert truncated is False


def test_clamp_text_over_limit_is_truncated():
    text = "x" * 100
    clipped, truncated = clamp_text(text, max_bytes=10)
    assert truncated is True
    assert len(clipped.encode("utf-8")) <= 10


def test_tool_allowlist_blocks_unknown_tools():
    allowlist = ToolAllowlist({"safe_tool"})
    assert allowlist.is_allowed("safe_tool")
    assert not allowlist.is_allowed("dangerous_tool")


def test_default_allowlist_excludes_dangerous_tools():
    for dangerous in ("merge_pull_request", "approve_pull_request", "read_file", "grant_admin_access"):
        assert not DEFAULT_TOOL_ALLOWLIST.is_allowed(dangerous)
    for safe in ("get_pull_request", "list_changed_files", "get_file_content"):
        assert DEFAULT_TOOL_ALLOWLIST.is_allowed(safe)


def test_run_with_timeout_returns_fast_result():
    assert run_with_timeout(lambda x: x + 1, 1, timeout_seconds=1.0) == 2


def test_run_with_timeout_raises_on_slow_call():
    def slow():
        time.sleep(0.5)
        return "done"

    with pytest.raises(ExecutionLimitExceeded):
        run_with_timeout(slow, timeout_seconds=0.05)
