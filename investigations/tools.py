import json
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


@dataclass(frozen=True)
class Source:
    id: int
    kind: str
    text: str
    at: datetime
    skew_seconds: int
    event_code: str = ""
    error_count: int | None = None


@dataclass(frozen=True)
class SourceBundle:
    sources: tuple[Source, ...]
    total: int
    all_kinds: tuple[str, ...]

    @property
    def input_bytes(self) -> int:
        return len(
            json.dumps(
                {
                    "sources": [
                        [
                            r.id,
                            r.kind,
                            r.text,
                            r.at.isoformat(),
                            r.skew_seconds,
                            r.event_code,
                            r.error_count,
                        ]
                        for r in self.sources
                    ],
                    "total": self.total,
                    "all_kinds": self.all_kinds,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        )

    def validate_budget(self) -> None:
        if self.input_bytes > 32768:
            raise ValueError("Source bundle exceeds 32 KiB")


def evidence(scope: Scope):
    scope.validate()
    return Evidence.objects.filter(
        incident_id=scope.incident_id, at__gte=scope.start, at__lt=scope.end
    ).order_by("at", "id")


def prepare_sources(scope: Scope) -> SourceBundle:
    rows = evidence(scope)
    total = rows.count()
    kinds = tuple(rows.order_by().values_list("kind", flat=True).distinct())
    sources = tuple(
        Source(r.id, r.kind, r.text, r.at, r.skew_seconds, r.event_code, r.error_count)
        for r in rows[:400]
    )
    return SourceBundle(sources, total, kinds)


def bounded_sources(scope: Scope | SourceBundle) -> SourceBundle:
    bundle = prepare_sources(scope) if isinstance(scope, Scope) else scope
    bundle.validate_budget()
    return bundle


def search_logs(scope: Scope | SourceBundle, query: str, limit: int):
    if len(query) > 2000 or len(query.encode()) > 8000 or not 1 <= limit <= 100:
        raise ValueError("Log query exceeds bounds")
    bundle = bounded_sources(scope)
    return [
        r for r in bundle.sources if r.kind == "log" and query.lower() in r.text.lower()
    ][:limit]


def list_deployments(scope: Scope | SourceBundle):
    return [r for r in bounded_sources(scope).sources if r.kind == "deployment"][:100]


def get_runbook(scope: Scope, section_id: int):
    scope.validate()
    try:
        section = RunbookSection.objects.get(
            id=section_id, incident_id=scope.incident_id
        )
        if len(section.text.encode()) > 32768:
            raise ValueError("Runbook exceeds 32 KiB")
        return section
    except RunbookSection.DoesNotExist as exc:
        raise ValueError("Runbook section outside scope") from exc
