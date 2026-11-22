"""Tests for the adapter that is supposed to call the SAME agent workflow used
by the real PR review (app.agent.review_pull_request).

As of this build, `backend/app/agent/` has not been implemented yet in this
worktree (it's owned by a parallel workstream). We verify the adapter fails
*honestly* in that case - RealAgentUnavailable, never a faked success - and
mark the true end-to-end integration test as pending rather than mocking it
into a false pass.
"""
import pytest

from app.security.agent_adapter import (
    AgentAdapter,
    EXPECTED_REAL_AGENT_CALLABLE,
    EXPECTED_REAL_AGENT_MODULE,
    PullRequestContext,
    RealAgentUnavailable,
    load_real_agent_workflow,
)


def _real_agent_is_wired_up() -> bool:
    fn, _reason = load_real_agent_workflow()
    return fn is not None


def test_load_real_agent_workflow_reports_unavailability_honestly():
    fn, reason = load_real_agent_workflow()
    if fn is None:
        assert EXPECTED_REAL_AGENT_MODULE in reason
    else:
        assert reason is None


def test_default_adapter_raises_real_agent_unavailable_when_not_wired_up():
    if _real_agent_is_wired_up():
        pytest.skip("app.agent is wired up in this build; this checks the not-available path only")
    adapter = AgentAdapter()
    assert adapter.is_available is False
    with pytest.raises(RealAgentUnavailable):
        adapter.execute(PullRequestContext(title="t", body="b", diff="d"), github_client=object())


def test_injected_workflow_bypasses_the_real_agent_lookup():
    calls = []

    def fake_workflow(pr, github_client):
        calls.append((pr, github_client))
        return {"response": "ok"}

    adapter = AgentAdapter(workflow=fake_workflow)
    assert adapter.is_available is True
    result = adapter.execute(PullRequestContext(title="t", body="b", diff="d"), github_client="client")
    assert result.response == "ok"
    assert len(calls) == 1


@pytest.mark.integration
@pytest.mark.skipif(
    not _real_agent_is_wired_up(),
    reason=(
        f"Integration-dependent: requires a real '{EXPECTED_REAL_AGENT_MODULE}."
        f"{EXPECTED_REAL_AGENT_CALLABLE}' PR-review workflow, which is not yet "
        "implemented in this worktree. Marked pending rather than mocked to a "
        "false pass - re-run once app/agent/ lands."
    ),
)
def test_real_agent_defends_against_fake_repository_owner():
    from app.security.fixtures import get_fixture
    from app.security.runner import AttackRunner

    fixture = get_fixture("authority-001")
    runner = AttackRunner()
    result = runner.run(fixture)
    assert result.verdict == "defended"
