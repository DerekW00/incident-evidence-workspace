import pytest
from datetime import timedelta
from django.utils import timezone
from investigations.jobs import start_investigation, claim, execute, cancel
from investigations.models import Investigation, Job
from investigations.provider import fixture_result
from investigations.budget import reserve

pytestmark = pytest.mark.django_db(transaction=True)


def begin(scene):
    org, user, inc, start, end, *_ = scene
    return start_investigation(org.id, inc.id, user.id, start, end)


def test_durable_completion_and_reserved_unknown_usage(scene):
    run = begin(scene)
    job = claim()
    execute(job.id, job.token)
    run.refresh_from_db()
    assert run.status == "completed"
    assert run.guard_units == 2000 and run.measured_usage is None
    assert run.observations.exists() and run.hypotheses.exists()
    assert list(run.events.values_list("sequence", flat=True)) == [1, 2, 3]


def test_failure_keeps_reservation(scene):
    run = begin(scene)
    job = claim()
    execute(
        job.id,
        job.token,
        provider=lambda scope: (_ for _ in ()).throw(RuntimeError("fixture failure")),
    )
    run.refresh_from_db()
    assert (
        run.status == "failed"
        and run.guard_units == 2000
        and run.measured_usage is None
    )


def test_cancel_before_claim(scene):
    run = begin(scene)
    cancel(run.org_id, run.id)
    assert claim() is None


def test_cancel_during_provider_rejects_late_result(scene):
    run = begin(scene)
    job = claim()

    def provider(scope):
        cancel(run.org_id, run.id)
        return fixture_result(scope)

    execute(job.id, job.token, provider)
    run.refresh_from_db()
    assert run.status == "cancelled" and not run.observations.exists()


def test_expired_lease_and_stale_token_reject_publication(scene):
    run = begin(scene)
    job = claim()
    Job.objects.filter(id=job.id).update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    execute(job.id, job.token)
    assert not run.observations.exists()
    newer = claim()
    assert newer.token != job.token
    execute(job.id, job.token)
    assert not run.observations.exists()


def test_step_and_tool_bounds_prevent_next_call(scene):
    run = begin(scene)
    Investigation.objects.filter(id=run.id).update(steps=4)
    with pytest.raises(ValueError):
        reserve(run.id, 0, 0)
    run.refresh_from_db()
    assert run.guard_units == 0


def test_claim_race_one_winner(scene):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections

    begin(scene)

    def contender():
        close_old_connections()
        j = claim()
        from django.db import connections

        connections.close_all()
        return j.id if j else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        answers = list(pool.map(lambda _: contender(), range(2)))
    assert answers.count(None) == 1


def test_deadline_expiry_while_publication_waits_for_lock(scene):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event as ThreadEvent
    import time
    from django.db import transaction, connections

    run = begin(scene)
    job = claim()
    callback = ThreadEvent()
    release = ThreadEvent()

    def provider(scope):
        callback.set()
        release.wait(5)
        return fixture_result(scope)

    def worker():
        try:
            execute(job.id, job.token, provider)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        assert callback.wait(5)
        with transaction.atomic():
            locked = Investigation.objects.select_for_update().get(id=run.id)
            locked.deadline = timezone.now() + timedelta(milliseconds=200)
            locked.save(update_fields=["deadline"])
            release.set()
            time.sleep(0.35)
        future.result(timeout=5)
    run.refresh_from_db()
    assert not run.observations.exists()
    assert run.guard_units == 2000


def test_excessive_input_rejected_before_reservation(scene):
    from investigations.models import Evidence

    org, u, inc, start, end, *_ = scene
    Evidence.objects.create(incident=inc, kind="log", at=start, text="x" * 32769)
    run = begin(scene)
    job = claim()
    execute(job.id, job.token)
    run.refresh_from_db()
    assert run.status == "failed"
    assert run.guard_units == 0 and not run.observations.exists()


def test_tool_and_input_reservation_bounds(scene):
    run = begin(scene)
    for size, tools in [(32769, 0), (0, 9)]:
        with pytest.raises(ValueError):
            reserve(run.id, size, tools)
    run.refresh_from_db()
    assert run.steps == 0 and run.guard_units == 0


def test_reclaimed_unknown_usage_cannot_become_complete(scene):
    import json

    run = begin(scene)
    first = claim()

    def lose_lease(scope):
        Job.objects.filter(id=first.id).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        return fixture_result(scope)

    execute(first.id, first.token, lose_lease)
    second = claim()

    def reported(scope):
        data = json.loads(fixture_result(scope))
        data["usage"] = {"input": 10, "output": 20}
        return json.dumps(data)

    execute(second.id, second.token, reported)
    run.refresh_from_db()
    assert run.status == "completed" and run.guard_units == 4000
    assert run.measured_usage is None
