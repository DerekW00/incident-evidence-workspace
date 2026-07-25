import pytest
from django.test import Client
from investigations.jobs import start_investigation, claim, execute
from investigations.reviews import save_review

pytestmark = pytest.mark.django_db


def test_review_conflict_and_brief(scene):
    org, user, inc, start, end, *_ = scene
    run = start_investigation(org.id, inc.id, user.id, start, end)
    job = claim()
    execute(job.id, job.token)
    brief = save_review(org.id, run.id, user.id, 0, "Deployment remains a hypothesis.")
    assert "hypothesis" in brief.text
    with pytest.raises(ValueError):
        save_review(org.id, run.id, user.id, 0, "stale")


def test_login_csrf_and_foreign_routes(scene):
    org, user, inc, start, end, *_ = scene
    run = start_investigation(org.id, inc.id, user.id, start, end)
    c = Client(enforce_csrf_checks=True)
    assert c.get("/").status_code == 302
    c.force_login(user)
    assert c.post(f"/runs/{run.id}/cancel/").status_code == 403
    from investigations.models import Membership, Organization

    other = Organization.objects.create(name="Foreign")
    Membership.objects.filter(user=user).update(org=other)
    for path in [
        f"/runs/{run.id}/",
        f"/runs/{run.id}/events/",
        f"/runs/{run.id}/brief/",
    ]:
        assert c.get(path).status_code == 404
    c = Client()
    c.force_login(user)
    assert c.post(f"/runs/{run.id}/cancel/").status_code == 404


def test_timeline_displays_utc_without_local_conversion(scene):
    org, user, inc, start, end, *_ = scene
    run = start_investigation(org.id, inc.id, user.id, start, end)
    c = Client()
    c.force_login(user)
    response = c.get(f"/runs/{run.id}/")
    assert b"12:00:00" in response.content


def test_findings_link_back_to_source_evidence(scene):
    org, user, inc, start, end, dep, *_ = scene
    run = start_investigation(org.id, inc.id, user.id, start, end)
    job = claim()
    execute(job.id, job.token)
    c = Client()
    c.force_login(user)
    assert f'href="#source-{dep.id}"'.encode() in c.get(f"/runs/{run.id}/").content
