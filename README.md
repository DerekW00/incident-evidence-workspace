# Signal — Incident Evidence Workspace

A Django workspace that keeps incident evidence, working hypotheses and engineer review separate. An on-call engineer selects a synthetic incident and UTC window, investigates a persisted timeline, challenges a deployment hypothesis, and saves a reviewed brief.

**Python 3.12 · Django 5.2 · PostgreSQL 16 · HTML/CSS · local HTMX**

![Synthetic incident timeline with typed evidence and a weakened deployment hypothesis](docs/images/workflow-review.jpg)

## Engineering focus

- **Evidence before narrative.** One immutable, bounded source bundle feeds the fixture provider, tools and citation validator. Every accepted citation points to a displayed source. Truncation and omitted source kinds are explicit.
- **Typed facts and uncertainty.** Positive error claims require authored event codes and counts. Raw log prose stays untrusted and inspectable. Half-open UTC windows, clock skew, missing telemetry and contradictory evidence remain visible.
- **Durable work with publication fences.** PostgreSQL jobs use claims, leases, deadlines and fresh post-lock checks. Cancellation or a stale token prevents late worker publication. Ordered activity survives refresh.
- **Human review with history.** Optimistic revisions reject stale edits; reviews and saved briefs retain their own versions. Sessions, CSRF and server-owned organization scope protect the workflow, including real second-tenant fixtures.

The provider is a deterministic fixture adapter. No live model, production logs or infrastructure action is involved.

## Run locally

Prerequisites: Python **3.12**, [uv](https://docs.astral.sh/uv/), PostgreSQL **16** with its command-line tools, and Make for the convenience targets. The PostgreSQL role must be able to create test databases for pytest.

Create a development role/database, or use an existing suitable role. As your local PostgreSQL administrator, for example:

```sh
createuser --createdb --pwprompt incident_demo
createdb --owner=incident_demo incident_evidence
```

From the repository root:

```sh
uv sync --frozen
cp .env.example .env
# Edit .env: use your local PostgreSQL host, port, role and chosen password.
set -a
. ./.env
set +a
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver 127.0.0.1:8103 --noreload
```

The example uses TCP at `127.0.0.1:5432`; a local Unix socket directory also works as `PGHOST`. Environment variables are loaded by your shell, not automatically by Django. `.env` is ignored by Git.

Open **http://127.0.0.1:8103/**. These public credentials are for the explicitly enabled **local synthetic demo only**:

| Account | Password | Organization |
|---|---|---|
| `engineer` | `synthetic-demo` | Signal Lab |
| `other-engineer` | `synthetic-demo` | Separate Lab |

Choose **Gateway errors after release**, keep the seeded window, and start an investigation. In a second terminal at the same checkout:

```sh
set -a
. ./.env
set +a
uv run python manage.py worker --once
```

Refresh the workspace. Inspect the typed samples, 12-second source skew, missing metrics and the evidence after rollback. Save an engineer assessment and download the brief. Start another investigation and cancel it; closing the page alone does not cancel durable work.

`uv run python manage.py worker` continuously polls. For a command-line fixture walkthrough before starting a continuous worker, `uv run python manage.py demo` seeds, investigates, saves a brief and demonstrates cancellation.

[compose.yaml](compose.yaml) optionally describes a loopback PostgreSQL database: `docker compose up -d postgres`. That route was **not used for verification**. If choosing it, set `PGHOST=127.0.0.1`, `PGPORT=15533`, `PGUSER=dw`, `PGDATABASE=incident_evidence` and `PGPASSWORD=local-synthetic-only` in your local environment; the Python application still runs through uv.

## Verify

After migration and seeding, with the same database environment:

```sh
make verify
# Install the matching browser on a new workstation:
uv run playwright install chromium
# Keep the loopback app server running; this journey controls its own worker.
BROWSER_EVIDENCE_DIR="$PWD/.browser-evidence" make browser
```

Stop a continuously polling worker before the browser journey. Playwright also requires the operating-system libraries documented for Chromium on your platform. Browser artifacts default to a newly created writable temporary directory; `BROWSER_EVIDENCE_DIR` creates/uses an explicit destination. The checkout-local example above is ignored by Git.

Verified at application code revision `dd85eeae4272d7ea08bc799005f63ced8d47afc3`:

| Check | Observed result |
|---|---|
| PostgreSQL/domain suite | **37 passed**, separate browser test skipped |
| Chromium workflow | **1 passed**, including saved-brief download and cancellation |
| Frozen functional evaluation | **5/5 passed** |
| Dependency, Django/migration, Ruff and mypy gates | Passed |

These are functional fixture results, not live-model accuracy, billing or production-scale measurements. See [verification details](docs/verification.md).

## Design and limits

Read the [architecture](docs/architecture.md) and [tradeoffs](docs/tradeoffs.md) for the source boundary, lock order, guard reservations and recovery behavior.

This is a local portfolio application. It uses one active organization per user and one fixture-provider pass. Reasoning is limited to 400 displayed sources and a 32 KiB admitted input bundle; omitted sources cannot supply citations. Cancellation fences publication but does not interrupt Python already executing. Live telemetry ingestion, hosted authentication and production deployment are outside this release.

## Provenance and contribution

An AI-assisted portfolio project. The fixtures, identifiers and screenshot are synthetic. No employer source, customer data or private telemetry was used. [Contribution notes](docs/contributions.md) explain AI assistance; [data provenance](docs/data-provenance.md) records the authored fixture facts. No customer adoption, business impact or live-model quality is claimed.

Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Project code and documentation are available under the [MIT License](LICENSE), copyright 2026 Derek Derui Wang. Third-party components retain their own licenses; the vendored HTMX runtime retains its [Zero-Clause BSD notice](investigations/static/HTMX-LICENSE.txt).
