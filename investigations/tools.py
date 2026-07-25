from dataclasses import dataclass
from datetime import datetime
from .models import Evidence, Incident, RunbookSection


@dataclass(frozen=True)
class Scope:
    org_id: int
    incident_id: int
    start: datetime
    end: datetime

    def validate(self) -> None:
        if (
            self.start.tzinfo is None
            or self.end.tzinfo is None
            or self.start >= self.end
        ):
            raise ValueError("Use an ordered, timezone-aware window")
        if not Incident.objects.filter(
            id=self.incident_id, service__org_id=self.org_id
        ).exists():
            raise ValueError("Incident outside organization")


def evidence(scope: Scope):
    scope.validate()
    return Evidence.objects.filter(
        incident_id=scope.incident_id, at__gte=scope.start, at__lt=scope.end
    ).order_by("at", "id")


def search_logs(scope: Scope, query: str, limit: int):
    if len(query) > 2000 or len(query.encode()) > 8000 or not 1 <= limit <= 100:
        raise ValueError("Log query exceeds bounds")
    return list(evidence(scope).filter(kind="log", text__icontains=query)[:limit])


def list_deployments(scope: Scope):
    return list(evidence(scope).filter(kind="deployment")[:100])


def get_runbook(scope: Scope, section_id: int):
    scope.validate()
    try:
        return RunbookSection.objects.get(id=section_id, incident_id=scope.incident_id)
    except RunbookSection.DoesNotExist as exc:
        raise ValueError("Runbook section outside scope") from exc
