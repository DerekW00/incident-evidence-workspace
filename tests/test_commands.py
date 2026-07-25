import pytest
from django.core.management import call_command
from investigations.models import Incident, Organization


@pytest.mark.django_db
def test_seed_idempotent_demo_and_evaluate(settings):
    settings.DEMO_MODE = True
    call_command("seed_demo")
    call_command("seed_demo")
    assert Organization.objects.count() == 2
    assert Incident.objects.count() == 2
    call_command("demo")
    call_command("evaluate")
