import pytest

from app.security.agent_adapter import PullRequestContext
from app.security.github_mock import MockGitHubAdapter
from app.security.safety import ExecutionLimitExceeded, ToolAllowlist, ToolNotAllowed


def make_pr(**overrides):
    base = dict(title="t", body="b", diff="d", comments=["c1"])
    base.update(overrides)
    return PullRequestContext(**base)


def test_allowed_calls_are_recorded_and_not_blocked():
    client = MockGitHubAdapter(make_pr(), allowlist=ToolAllowlist({"get_diff"}), max_calls=10)
    assert client.get_diff() == "d"
    assert len(client.calls) == 1
    assert client.calls[0].tool == "get_diff"
    assert client.calls[0].blocked is False


def test_disallowed_call_is_blocked_and_recorded():
    client = MockGitHubAdapter(make_pr(), allowlist=ToolAllowlist({"get_diff"}), max_calls=10)
    with pytest.raises(ToolNotAllowed):
        client.merge_pull_request()
    assert len(client.calls) == 1
    assert client.calls[0].tool == "merge_pull_request"
    assert client.calls[0].blocked is True


def test_max_call_budget_is_enforced():
    client = MockGitHubAdapter(make_pr(), allowlist=ToolAllowlist({"get_diff"}), max_calls=2)
    client.get_diff()
    client.get_diff()
    with pytest.raises(ExecutionLimitExceeded):
        client.get_diff()
    assert len(client.calls) == 3
    assert client.calls[-1].blocked is True
