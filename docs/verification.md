# Verification

Use make verify with the documented PostgreSQL runtime, after migrate/seed_demo. It checks frozen lock consistency, Django configuration/migration drift, Ruff lint/format, mypy, all pytest tests and five scripted functional evaluation checks. Browser gate is separate: run private loopback server and make browser.

Tests exercise real second-tenant sources, half-open end exclusion, foreign runbooks, literal hostile query text, citation rejection (unknown/foreign/outside window), malformed/excessive output, partial usage, missing metrics, post-rollback contradiction, reserved failed usage, cancelled and expired worker publication, stale tokens, concurrent claim, lock-delayed deadline expiry, stale review, login/CSRF, organization-scoped detail/events/cancel/brief endpoints and UTC display.

Browser test logs in, selects window, starts, refreshes during work, invokes the real management worker, inspects persisted contradiction, saves/downloads a brief, then starts/cancels a second investigation and refreshes terminal state. Screenshots and RED/GREEN logs live outside source in python-evidence/incident-evidence-workspace. The implementation report records exact results and commit.

Round-one regressions cover deployment-only/pre-rollback windows, a400-row prefix before an oversized hidden deployment, omitted-kind/truncation disclosure, rejection of non-visible citations and zero secondary database reads during provider/validation. Browser now downloads the saved brief and asserts filename and reviewer content.

Round-two regressions use the exact healthy/negated prose strings, preserve raw inspection, verify zero-count/unknown rows cannot create hypotheses, require typed prior rollback timestamps, and migrate a legacy positive-prose row from0001 to0002 without invented facts.

Whole-delivery portability: browser artifacts use a writable temporary directory by default; BROWSER_EVIDENCE_DIR overrides/creates the destination (for example `$PWD/.browser-evidence`). Final VPS evidence explicitly sets BROWSER_EVIDENCE_DIR=/Users/dw/code/portfolio-python/python-evidence/incident-evidence-workspace. Per-product session/CSRF cookie names preserve same-browser logins across loopback ports; a retained cross-product Playwright probe exercises concurrent sessions and saved CSRF forms without disabling protection.
