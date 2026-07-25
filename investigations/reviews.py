from django.db import transaction
from .models import Investigation, Review, Brief, Membership
from .jobs import append_event


def save_review(
    org_id: int, run_id: int, actor_id: int, revision: int, text: str
) -> Brief:
    if not text.strip() or len(text) > 4000:
        raise ValueError("Review must be 1–4000 characters")
    with transaction.atomic():
        run = Investigation.objects.select_for_update().get(id=run_id, org_id=org_id)
        if not Membership.objects.filter(org_id=org_id, user_id=actor_id).exists():
            raise ValueError("Membership required")
        if run.status != "completed" or run.revision != revision:
            raise ValueError("Stale review or incomplete investigation; refresh")
        run.revision += 1
        run.save(update_fields=["revision"])
        review = Review.objects.create(
            run=run, actor_id=actor_id, revision=run.revision, text=text
        )
        hypotheses = "\n".join(
            f"HYPOTHESIS ({h.confidence}): {h.text}; sources {h.citations}; contradictions {h.contradictions}"
            for h in run.hypotheses.all()
        )
        brief = Brief.objects.create(
            run=run,
            review=review,
            text=f"SYNTHETIC INCIDENT BRIEF · revision {run.revision}\n{run.incident.title}\n{hypotheses}\nMissing telemetry must be checked independently.\nEngineer review: {text}",
        )
        append_event(run, f"Review revision {run.revision} saved; brief retained.")
        return brief
