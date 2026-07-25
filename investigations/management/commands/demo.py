from datetime import timedelta
from django.core.management import call_command
from django.core.management.base import BaseCommand
from investigations.models import Incident, Membership
from investigations.jobs import start_investigation, claim, execute, cancel
from investigations.reviews import save_review


class Command(BaseCommand):
    help = "Seed and demonstrate correlation, contradiction, persisted review and cancellation."

    def handle(self, *args, **options):
        call_command("seed_demo")
        member = Membership.objects.get(user__username="engineer")
        inc = Incident.objects.get(service__org=member.org)
        first = inc.evidence_set.order_by("at").first()
        assert first is not None, "Seed evidence required"
        start = first.at
        run = start_investigation(
            member.org_id, inc.id, member.user_id, start, start + timedelta(minutes=6)
        )
        job = claim()
        while job:
            execute(job.id, job.token)
            if job.run_id == run.id:
                break
            job = claim()
        brief = save_review(
            member.org_id,
            run.id,
            member.user_id,
            0,
            "Deployment correlation is weakened; missing metrics require follow-up.",
        )
        stopped = start_investigation(
            member.org_id, inc.id, member.user_id, start, start + timedelta(minutes=6)
        )
        cancel(member.org_id, stopped.id)
        self.stdout.write(
            f"Completed run {run.id}, saved brief {brief.id}, cancelled run {stopped.id}."
        )
