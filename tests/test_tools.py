import pytest
from datetime import datetime, timezone, timedelta
from investigations.tools import Scope, search_logs
from investigations.models import Organization, Service, Incident, Evidence


@pytest.mark.django_db
def test_scope_half_open_and_foreign():
    a = Organization.objects.create(name="A")
    b = Organization.objects.create(name="B")
    s = Service.objects.create(org=a, name="API")
    i = Incident.objects.create(service=s, title="Spike")
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    Evidence.objects.create(incident=i, kind="log", text="inside", at=t)
    Evidence.objects.create(
        incident=i, kind="log", text="end", at=t + timedelta(hours=1)
    )
    other = Incident.objects.create(
        service=Service.objects.create(org=b, name="Other"), title="Secret"
    )
    Evidence.objects.create(incident=other, kind="log", text="secret", at=t)
    assert [
        x.text
        for x in search_logs(Scope(a.id, i.id, t, t + timedelta(hours=1)), "", 100)
    ] == ["inside"]
    with pytest.raises(ValueError):
        search_logs(Scope(b.id, i.id, t, t + timedelta(hours=1)), "", 100)
    with pytest.raises(ValueError):
        search_logs(Scope(a.id, i.id, t, t + timedelta(hours=1)), "x" * 2001, 100)


@pytest.mark.django_db
def test_runbook_and_deployment_scope_and_tool_caps(scene):
    from investigations.tools import get_runbook, list_deployments
    from investigations.models import RunbookSection

    org, u, inc, start, end, dep, err, foreign, outside = scene
    scope = Scope(org.id, inc.id, start, end)
    book = RunbookSection.objects.create(
        incident=foreign.incident, title="Foreign", text="secret"
    )
    with pytest.raises(ValueError):
        get_runbook(scope, book.id)
    assert [e.id for e in list_deployments(scope)] == [dep.id]
    for limit in [0, 101, -1]:
        with pytest.raises(ValueError):
            search_logs(scope, "", limit)
    assert search_logs(scope, "DROP TABLE evidence; --", 10) == []
