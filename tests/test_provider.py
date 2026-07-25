import pytest
import json
from investigations.provider import parse_result, fixture_result
from investigations.tools import Scope


@pytest.mark.django_db
def test_provider_rejects_foreign_outside_and_unknown_citations(scene):
    org, u, inc, start, end, dep, err, foreign, outside = scene
    scope = Scope(org.id, inc.id, start, end)
    for bad in [foreign.id, outside.id, 99999]:
        with pytest.raises(ValueError):
            parse_result(
                json.dumps(
                    {
                        "observations": [{"text": "claim", "citations": [bad]}],
                        "hypotheses": [],
                    }
                ),
                scope,
            )


@pytest.mark.django_db
def test_fixture_weakens_correlation_and_ignores_hostile_logs(scene):
    org, u, inc, start, end, *_ = scene
    result = parse_result(
        fixture_result(Scope(org.id, inc.id, start, end)),
        Scope(org.id, inc.id, start, end),
    )
    assert result.hypotheses[0].confidence == "weakened"
    assert result.hypotheses[0].contradictions
    assert result.usage is None


@pytest.mark.django_db
def test_malformed_oversized_and_partial_usage(scene):
    org, u, inc, start, end, *_ = scene
    scope = Scope(org.id, inc.id, start, end)
    for value in ["{}", "{", "x" * 8193, '{"observations":"wrong"}']:
        with pytest.raises(ValueError):
            parse_result(value, scope)
    result = parse_result(
        '{"observations":[],"hypotheses":[],"usage":{"input":3}}', scope
    )
    assert result.usage is None
