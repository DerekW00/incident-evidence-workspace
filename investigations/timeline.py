from .tools import Scope, SourceBundle, prepare_sources


def build_timeline(scope: Scope | SourceBundle):
    bundle = prepare_sources(scope) if isinstance(scope, Scope) else scope
    visible = {row.kind for row in bundle.sources}
    return {
        "evidence": bundle.sources,
        "missing": [
            kind
            for kind in ["log", "deployment", "config", "metric"]
            if kind not in bundle.all_kinds
        ],
        "truncated": bundle.total > len(bundle.sources),
        "total": bundle.total,
        "omitted_kinds": [kind for kind in bundle.all_kinds if kind not in visible],
    }
