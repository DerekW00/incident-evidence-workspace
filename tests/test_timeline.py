import pytest
from investigations.tools import Scope
from investigations.timeline import build_timeline


@pytest.mark.django_db
def test_skew_contradiction_and_missing_metrics(scene):
    org, u, inc, start, end, *_ = scene
    data = build_timeline(Scope(org.id, inc.id, start, end))
    assert "metric" in data["missing"]
    assert any(x.skew_seconds == 12 for x in data["evidence"])
    assert all(x.text != "Outside window" for x in data["evidence"])
