from app.security.evaluator import ASSERTION_CHECKERS
from app.security.fixtures import CATEGORIES, FIXTURES, get_fixture, list_fixtures


def test_at_least_twelve_fixtures():
    assert len(FIXTURES) >= 12


def test_all_eight_categories_covered():
    assert {f.category for f in FIXTURES} == CATEGORIES
    assert len(CATEGORIES) == 8


def test_fixture_ids_are_unique():
    ids = [f.id for f in FIXTURES]
    assert len(ids) == len(set(ids))


def test_authority_001_matches_shared_contract_example():
    fixture = get_fixture("authority-001")
    assert fixture is not None
    assert fixture.name == "Fake repository owner"
    assert fixture.category == "authority_spoofing"
    assert "override" in fixture.description.lower()


def test_unknown_test_id_returns_none():
    assert get_fixture("does-not-exist") is None


def test_every_assertion_kind_is_known_to_the_evaluator():
    for fixture in list_fixtures():
        for spec in fixture.assertions:
            assert spec.kind in ASSERTION_CHECKERS, f"{fixture.id} uses unknown assertion kind {spec.kind!r}"


def test_every_fixture_has_at_least_one_assertion():
    for fixture in list_fixtures():
        assert fixture.assertions, f"{fixture.id} has no assertions"
