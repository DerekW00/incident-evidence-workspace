import json
from dataclasses import dataclass
from typing import Callable
from .tools import Scope, SourceBundle, bounded_sources, search_logs, list_deployments
from .timeline import build_timeline


@dataclass(frozen=True)
class Finding:
    text: str
    citations: list[int]
    confidence: str = "unconfirmed"
    contradictions: list[int] | None = None


@dataclass(frozen=True)
class Result:
    observations: list[Finding]
    hypotheses: list[Finding]
    usage: dict[str, int] | None


Provider = Callable[[SourceBundle], str]


def parse_result(raw: str, scope: Scope | SourceBundle) -> Result:
    if len(raw.encode()) > 8192:
        raise ValueError("Provider output exceeds 8 KiB")
    try:
        data = json.loads(raw)
        if (
            not isinstance(data, dict)
            or not {"observations", "hypotheses"} <= data.keys()
        ):
            raise ValueError("Both observations and hypotheses are required")
        allowed = {row.id for row in bounded_sources(scope).sources}
        findings = []
        for key in ["observations", "hypotheses"]:
            rows = data.get(key, [])
            if not isinstance(rows, list) or len(rows) > 20:
                raise ValueError("Malformed findings")
            values = []
            for row in rows:
                if (
                    not isinstance(row, dict)
                    or not isinstance(row.get("text"), str)
                    or not 0 < len(row["text"]) <= 2000
                ):
                    raise ValueError("Malformed finding text")
                citations = row.get("citations", [])
                contradictions = row.get("contradictions", [])
                if (
                    not isinstance(citations, list)
                    or not citations
                    or not isinstance(contradictions, list)
                ):
                    raise ValueError("Findings require evidence")
                if any(
                    type(i) is not int or i not in allowed
                    for i in citations + contradictions
                ):
                    raise ValueError("Invalid, foreign or out-of-window citation")
                confidence = row.get("confidence", "unconfirmed")
                if confidence not in ["unconfirmed", "weakened"]:
                    raise ValueError("Provider cannot establish root cause")
                if contradictions and confidence != "weakened":
                    raise ValueError("Contradictions must weaken hypothesis")
                values.append(
                    Finding(row["text"], citations, confidence, contradictions)
                )
            findings.append(values)
        usage = data.get("usage")
        if (
            not isinstance(usage, dict)
            or set(usage) != {"input", "output"}
            or any(type(v) is not int or v < 0 for v in usage.values())
        ):
            usage = None
        return Result(findings[0], findings[1], usage)
    except (TypeError, KeyError, json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("Malformed fixture response") from exc


def fixture_result(scope: Scope | SourceBundle) -> str:
    scope = bounded_sources(scope)
    timeline = build_timeline(scope)
    rows = timeline["evidence"]
    observations = [
        {"text": f"{row.kind}: {row.text[:500]}", "citations": [row.id]}
        for row in rows[:8]
    ]
    deployments = [r.id for r in list_deployments(scope)]
    logs = search_logs(scope, "", 100)
    spike = [r.id for r in logs if "error" in r.text.lower() or "5xx" in r.text.lower()]
    contrary = [
        r.id for r in logs if r.id in spike and "after rollback" in r.text.lower()
    ]
    hypotheses = []
    if deployments and spike:
        hypotheses = [
            {
                "text": (
                    "A deployment and error observations coexist in the selected window. A scoped log reports errors after rollback, weakening the deployment-cause hypothesis. Root cause remains unconfirmed."
                    if contrary
                    else "A deployment and error observations coexist in the selected window. This supports only a working hypothesis; root cause remains unconfirmed."
                ),
                "citations": deployments + spike,
                "contradictions": contrary,
                "confidence": "weakened" if contrary else "unconfirmed",
            }
        ]
    return json.dumps({"observations": observations, "hypotheses": hypotheses})
