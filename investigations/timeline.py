from .tools import Scope, evidence


def build_timeline(scope: Scope):
    rows = list(evidence(scope)[:400])
    kinds = {row.kind for row in rows}
    return {
        "evidence": rows,
        "missing": [
            kind
            for kind in ["log", "deployment", "config", "metric"]
            if kind not in kinds
        ],
    }
