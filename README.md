# Signal — Incident Evidence Workspace

A synthetic on-call workspace for evidence timelines, uncertain hypotheses, engineer reviews and retained briefs. Python 3.12 / Django 5.2 / PostgreSQL 16. Fixture provider only. No infrastructure actions or live log access.

## Run locally

Install Python 3.12 and uv. Create an isolated PostgreSQL 16 database named `incident_evidence` owned by your local user. Set `PGHOST` to its Unix socket directory; the verified private runtime uses port 15533 and user dw. Set `DEMO_MODE=1`. The checked-in Compose file describes an optional loopback-only local alternative; it was not used for verification.

```sh
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py demo
make serve
# separate shell, same environment:
make worker
```

Open http://127.0.0.1:8103. Local synthetic account: `engineer / synthetic-demo`; second organization: `other-engineer / synthetic-demo`. Seed requires explicit DEMO_MODE. Set a unique SECRET_KEY for any use beyond this isolated demonstration.

Choose Gateway errors, select UTC start/end, and start. Refresh while queued; run worker --once to publish. Inspect continued errors after rollback, 12-second skew, and absent metrics. Review saves a versioned brief. Start another run and cancel; browser closure alone does not cancel. No reply, command or infrastructure operation is sent.

```sh
make verify
# install Playwright's matching Chromium normally; verified runtime already has it
make browser
```

The VPS verification sources `/Users/dw/code/portfolio-python/execution/runtime-env.sh`; PostgreSQL has TCP disabled and uses a private Unix socket. Browser tests use only loopback. See docs for limits, decisions, provenance and measured evidence.

After upgrading an existing synthetic checkout to structured event facts, run migrate then seed_demo again before evaluate/browser. Migration intentionally leaves preexisting facts unknown; seed_demo explicitly refreshes only its controlled synthetic records.

Browser artifacts default to a newly created writable temporary directory. To retain them use `BROWSER_EVIDENCE_DIR="$PWD/.browser-evidence" make browser` (ignored locally), or supply any writable destination. Verified VPS runs explicitly supply the canonical external evidence path. PostgreSQL PGUSER/PGPORT overrides are honored; defaults remain dw/15533 for the private VPS runtime.

Same-host demo cookies use `incident_evidence_session` and `incident_evidence_csrf`, so the three loopback products can retain separate sessions and CSRF forms across ports. Cookie domain/path and CSRF enforcement retain their normal Django scope.
