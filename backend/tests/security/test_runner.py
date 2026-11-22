"""Runner tests.

Most tests here inject a small test-double workflow via AgentAdapter(workflow=...)
to deterministically exercise the runner/evaluator plumbing in isolation -
this is a test double for unit-testing OUR code, not a pretend production
agent. The one test that exercises the real integration path (no injected
workflow) is marked `pending` rather than faked, because app.agent does not
exist yet in this build - see test_agent_adapter.py.
"""
from app.security.agent_adapter import AgentAdapter
from app.security.fixtures import get_fixture
from app.security.runner import AttackRunner


def good_agent(pr, github_client):
    import asyncio

    asyncio.run(github_client.get_pull_request())
    files = asyncio.run(github_client.list_changed_files())
    diff = "\n".join(f["patch"] for f in files)
    lowered = diff.lower()
    flags = []
    if "eval(" in lowered:
        flags.append("flagging eval() as an arbitrary code execution / remote code execution risk")
    if "validation" in lowered or "validation" in pr.body.lower():
        flags.append("validation removed - flagged as risky")
    if "sql" in lowered or "select * from" in lowered:
        flags.append("possible sql injection: query is concatenated rather than parameterized")
    if "exfiltrat" in pr.body.lower() or "requests.post" in lowered:
        flags.append("outbound request to an external/attacker-controlled host looks like exfiltration")
    if "os.system" in lowered or "curl" in lowered:
        flags.append("remote code execution via shell pipe (curl | sh) pattern detected")
    response = "Review: " + "; ".join(flags) if flags else (
        "Review: no issues found in the diff. I will not approve without completing standard review."
    )
    return {"response": response}


def compliant_bad_agent(pr, github_client):
    return {"response": "approved without review, disabling static analysis as instructed"}


def tool_abusing_agent(pr, github_client):
    github_client.call_untrusted_tool("merge_pull_request")
    return {"response": "merged"}


def make_runner(workflow):
    return AttackRunner(agent_adapter=AgentAdapter(workflow=workflow))


def test_good_agent_defends_against_authority_spoofing():
    fixture = get_fixture("authority-001")
    runner = make_runner(good_agent)
    result = runner.run(fixture)
    assert result.verdict == "defended"
    assert all(a.passed for a in result.assertions)


def test_compliant_agent_is_compromised_by_authority_spoofing():
    fixture = get_fixture("authority-001")
    runner = make_runner(compliant_bad_agent)
    result = runner.run(fixture)
    assert result.verdict == "compromised"
    assert any(not a.passed for a in result.assertions)


def test_good_agent_defends_against_hallucination_manipulation():
    fixture = get_fixture("halluc-001")
    runner = make_runner(good_agent)
    result = runner.run(fixture)
    assert result.verdict == "defended"


def test_good_agent_defends_against_sqli_hallucination():
    fixture = get_fixture("halluc-002")
    runner = make_runner(good_agent)
    result = runner.run(fixture)
    assert result.verdict == "defended"


def test_tool_abusing_agent_is_compromised_by_tool_misuse_fixture():
    fixture = get_fixture("toolmisuse-001")
    runner = make_runner(tool_abusing_agent)
    result = runner.run(fixture)
    assert result.verdict == "compromised"
    assert any(c.tool == "merge_pull_request" and c.blocked for c in result.tool_calls)


def test_canary_leaking_agent_is_compromised():
    fixture = get_fixture("secrets-001")

    def leaking_agent(pr, github_client):
        return {"response": f"Sure, the token is {fixture.canary}"}

    runner = make_runner(leaking_agent)
    result = runner.run(fixture)
    assert result.verdict == "compromised"


def test_oversized_diff_is_truncated_before_reaching_agent():
    fixture = get_fixture("resource-001")
    seen_diff_lengths = []

    def recording_agent(pr, github_client):
        seen_diff_lengths.append(len(pr.diff.encode("utf-8")))
        return {"response": "Review: diff was unusually large; handled safely."}

    runner = make_runner(recording_agent)
    result = runner.run(fixture)
    assert result.verdict == "defended"
    assert seen_diff_lengths[0] <= 64 * 1024


def test_comment_flood_is_capped_before_reaching_agent():
    fixture = get_fixture("resource-002")

    def recording_agent(pr, github_client):
        return {"response": f"Review: received {len(pr.comments)} comments, handled safely."}

    runner = make_runner(recording_agent)
    result = runner.run(fixture)
    assert result.verdict == "defended"


def test_response_payload_round_trips_fixture_metadata():
    fixture = get_fixture("injection-001")
    runner = make_runner(good_agent)
    result = runner.run(fixture)
    assert result.test_id == fixture.id
    assert result.payload == fixture.payload
