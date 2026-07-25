import json
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from investigations.models import Incident, Evidence
from investigations.provider import parse_result, fixture_result
from investigations.tools import Scope


class Command(BaseCommand):
    help = "Scripted functional fixture evaluation; no live model quality measurement."

    def handle(self, *args, **options):
        inc = Incident.objects.filter(service__org__name="Signal Lab").first()
        if inc is None:
            raise CommandError("Run seed_demo first")
        first = inc.evidence_set.order_by("at").first()
        assert first is not None, "Seed evidence required"
        start = first.at
        scope = Scope(inc.service.org_id, inc.id, start, start + timedelta(minutes=6))
        result = parse_result(fixture_result(scope), scope)
        assert result.hypotheses[0].confidence == "weakened"
        assert result.usage is None
        foreign = Evidence.objects.exclude(incident=inc).first()
        assert foreign is not None, "Second-tenant fixture required"
        cases = [
            "{",
            "x" * 8193,
            json.dumps({"observations": [{"text": "bad", "citations": [foreign.id]}]}),
        ]
        rejected = 0
        for raw in cases:
            try:
                parse_result(raw, scope)
            except ValueError:
                rejected += 1
        assert rejected == 3
        self.stdout.write(
            "5/5 scripted checks: weakened correlation, unknown usage, malformed, oversized, foreign citations. No live quality or billing claim."
        )
