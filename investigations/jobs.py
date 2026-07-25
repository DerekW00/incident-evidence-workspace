import secrets
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Investigation, Job, Event, Membership, Observation, Hypothesis
from .tools import Scope
from .provider import Provider, fixture_result, parse_result
from .timeline import build_timeline


def append_event(run: Investigation, text: str) -> None:
    last = run.events.order_by("-sequence").first()
    Event.objects.create(
        run=run, sequence=(last.sequence + 1 if last else 1), text=text
    )


def start_investigation(
    org_id: int, incident_id: int, actor_id: int, start: datetime, end: datetime
) -> Investigation:
    Scope(org_id, incident_id, start, end).validate()
    if not Membership.objects.filter(org_id=org_id, user_id=actor_id).exists():
        raise ValueError("Membership required")
    if end - start > timedelta(hours=24):
        raise ValueError("Maximum window is 24 hours")
    with transaction.atomic():
        run = Investigation.objects.create(
            org_id=org_id,
            incident_id=incident_id,
            actor_id=actor_id,
            start=start,
            end=end,
            deadline=timezone.now() + timedelta(seconds=120),
        )
        Job.objects.create(run=run)
        append_event(run, "Investigation queued; fixture provider only.")
        return run


def claim() -> Job | None:
    # All paths lock Investigation before Job.
    with transaction.atomic():
        now = timezone.now()
        runs = (
            Investigation.objects.filter(status__in=["queued", "running"])
            .filter(Q(job__lease_until__isnull=True) | Q(job__lease_until__lt=now))
            .order_by("id")
        )
        run = runs.select_for_update(skip_locked=True, of=("self",)).first()
        if run is None:
            return None
        job = Job.objects.select_for_update().get(run=run)
        now = timezone.now()
        if now >= run.deadline or job.attempts >= 2:
            run.status = "failed"
            run.failure = "Deadline or attempt limit exhausted"
            run.save()
            append_event(run, run.failure)
            return None
        job.token = secrets.token_hex(24)
        job.lease_until = now + timedelta(seconds=45)
        job.attempts += 1
        job.save()
        run.status = "running"
        run.save(update_fields=["status"])
        append_event(run, "Worker claimed investigation.")
        return job


def valid(run: Investigation, job: Job, token: str) -> bool:
    now = timezone.now()
    return (
        run.status == "running"
        and job.token == token
        and job.lease_until is not None
        and now < job.lease_until
        and now < run.deadline
    )


def execute(job_id: int, token: str, provider: Provider = fixture_result) -> None:
    run_id = Job.objects.values_list("run_id", flat=True).get(id=job_id)
    with transaction.atomic():
        run = Investigation.objects.select_for_update().get(id=run_id)
        job = Job.objects.select_for_update().get(id=job_id)
        if not valid(run, job, token):
            return
        scope = Scope(run.org_id, run.incident_id, run.start, run.end)
        timeline = build_timeline(scope)
        size = sum(len(e.text.encode()) for e in timeline["evidence"])
        if run.steps >= 4 or run.tools + 3 > 8 or size > 32768:
            run.status = "failed"
            run.failure = "Input, step or tool budget exhausted"
            run.save()
            append_event(run, run.failure)
            return
        run.steps += 1
        run.tools += 3
        run.guard_units += 2000
        run.save()
    # Provider is outside locks. Cancellation can commit while it runs.
    try:
        result = parse_result(provider(scope), scope)
        failure = ""
    except Exception as exc:
        result = None
        failure = f"Fixture provider failed: {type(exc).__name__}"
    with transaction.atomic():
        run = Investigation.objects.select_for_update().get(id=run_id)
        job = Job.objects.select_for_update().get(id=job_id)
        if not valid(run, job, token):
            return
        if result is None:
            run.status = "failed"
            run.failure = failure
        else:
            for finding in result.observations:
                Observation.objects.create(
                    run=run, text=finding.text, citations=finding.citations
                )
            for finding in result.hypotheses:
                Hypothesis.objects.create(
                    run=run,
                    text=finding.text,
                    citations=finding.citations,
                    confidence=finding.confidence,
                    contradictions=finding.contradictions or [],
                )
            run.status = "completed"
            run.measured_usage = result.usage if run.steps == 1 else None
        run.save()
        append_event(
            run,
            "Fixture investigation completed; causality unconfirmed."
            if result
            else failure,
        )


def cancel(org_id: int, run_id: int) -> None:
    with transaction.atomic():
        run = Investigation.objects.select_for_update().get(id=run_id, org_id=org_id)
        job = Job.objects.select_for_update().get(run=run)
        if run.status in ["queued", "running"]:
            run.status = "cancelled"
            run.save(update_fields=["status"])
            job.token = ""
            job.save(update_fields=["token"])
            append_event(run, "Cancelled by engineer; later publication fenced.")
