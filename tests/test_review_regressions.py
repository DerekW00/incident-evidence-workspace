from datetime import timedelta
import json
import pytest
from django.test import Client
from investigations.models import Evidence
from investigations.tools import Scope
from investigations.provider import fixture_result, parse_result
from investigations.timeline import build_timeline
from investigations.jobs import start_investigation, claim, execute

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("seconds", [1, 120])
def test_narrow_window_never_invents_post_rollback_claim(scene, seconds):
    org, user, inc, start, end, dep, *_ = scene
    Evidence.objects.create(
        incident=inc,
        at=start + timedelta(seconds=60),
        kind="log",
        text="5xx errors rise",
    )
    scope = Scope(org.id, inc.id, start, start + timedelta(seconds=seconds))
    result = parse_result(fixture_result(scope), scope)
    assert all("after rollback" not in h.text.lower() for h in result.hypotheses)
    if seconds == 1:
        assert not result.hypotheses
    else:
        assert result.hypotheses and not result.hypotheses[0].contradictions
    run = start_investigation(
        org.id, inc.id, user.id, start, start + timedelta(seconds=seconds)
    )
    job = claim()
    execute(job.id, job.token)
    c = Client()
    c.force_login(user)
    assert b"Contradictory observations" not in c.get(f"/runs/{run.id}/").content


def many_sources(scene, huge=False):
    org, user, inc, start, end, *_ = scene
    Evidence.objects.filter(incident=inc).delete()
    Evidence.objects.bulk_create(
        [
            Evidence(
                incident=inc,
                at=start + timedelta(microseconds=i),
                kind="log",
                text="ok",
            )
            for i in range(400)
        ]
    )
    dep = Evidence.objects.create(
        incident=inc,
        at=start + timedelta(seconds=1),
        kind="deployment",
        text="x" * 40000 if huge else "release",
    )
    return org, user, inc, start, end, dep


def test_secondary_reads_cannot_bypass_admission(scene):
    org, user, inc, start, end, dep = many_sources(scene, huge=True)
    run = start_investigation(org.id, inc.id, user.id, start, end)
    job = claim()
    execute(job.id, job.token)
    run.refresh_from_db()
    # Either admission rejects, or explicit truncation excludes the unadmitted payload.
    assert run.status == "failed" or not any(
        dep.id in h.citations for h in run.hypotheses.all()
    )


def test_display_cap_disclosed_and_only_visible_citations_accepted(scene):
    org, user, inc, start, end, dep = many_sources(scene)
    scope = Scope(org.id, inc.id, start, end)
    data = build_timeline(scope)
    assert data["truncated"] is True
    assert data["total"] == 401
    assert "deployment" not in data["missing"]
    assert "deployment" in data["omitted_kinds"]
    run = start_investigation(org.id, inc.id, user.id, start, end)
    c = Client()
    c.force_login(user)
    content = c.get(f"/runs/{run.id}/").content
    assert b"Showing 400 of 401 sources" in content
    assert b"Omitted source kinds: deployment" in content
    with pytest.raises(ValueError):
        parse_result(
            json.dumps(
                {
                    "observations": [{"text": "release", "citations": [dep.id]}],
                    "hypotheses": [],
                }
            ),
            scope,
        )


def test_provider_and_validation_consume_bundle_without_secondary_reads(
    scene, django_assert_num_queries
):
    from investigations.tools import prepare_sources

    org, user, inc, start, end, *_ = scene
    bundle = prepare_sources(Scope(org.id, inc.id, start, end))
    assert bundle.input_bytes <= 32768
    with django_assert_num_queries(0):
        result = parse_result(fixture_result(bundle), bundle)
    assert result.hypotheses[0].contradictions
