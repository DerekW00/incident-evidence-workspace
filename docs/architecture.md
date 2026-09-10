# Architecture

Django sessions identify a user; a one-to-one Membership selects the active organization on every request. Incident service ownership supplies tenant scope. The client supplies an incident identifier and UTC interval, never organization ownership. Tools validate a frozen Scope and use parameterized ORM queries. Logs use literal substring search; hostile text is rendered escaped and has no operational meaning. Runbook access requires current incident ownership.

Evidence is immutable synthetic source material in this release. Timeline preserves original source times and annotates skew rather than silently correcting timestamps. Intervals are half-open [start,end), at most 24 hours. Display and form parsing use UTC. Missing source kinds are explicit. Observations and hypotheses are separate tables; citations are validated against the current incident/window and hypotheses can only be unconfirmed or weakened.

An Investigation owns one durable Job. Transactions always lock Investigation then Job. Claim uses SELECT FOR UPDATE OF self SKIP LOCKED, a random 48-hex-character token, a 45-second lease and at most two attempts. Admission reserves 2,000 guard units before fixture execution. Provider work runs outside locks. Publication reacquires locks and samples fresh time after lock acquisition, rejecting terminal state, changed token, expired lease or deadline. Cancel clears the token and commits a terminal state. Reservation survives failure, cancellation and unknown usage. Complete reported input/output counts are accepted together; partial counts remain unknown. A reclaimed call has uncertain usage, so any eventual result keeps aggregate usage unknown rather than reporting only the final attempt.

Events are persisted under the run lock with a unique monotonically increasing per-run sequence. Worker failure is explicit. A periodic worker reclaims expired leases or marks deadline/attempt exhaustion failed. A process killed during an external call cannot reclaim knowledge of that call's measured usage; this implementation makes no external calls.

Review locks the run, compares the submitted revision, appends Review and Brief, increments revision and appends activity atomically. A stale tab receives HTTP 409. Brief snapshots preserve uncertainty and reviewer text. No model or reviewer action changes infrastructure.

Fixture execution is one bounded source timeline pass, one fixture response, and at most 20 findings per category. Source timeline is capped at 400 records; logs/deployments tools cap at 100. The fixed fixture workflow performs three scoped reads: timeline, deployment lookup and bounded log search. Three tool slots are admitted before each fixture call; these are guard reservations, not billing evidence.

## Round-one evidence boundary correction

Before provider admission the server prepares one immutable SourceBundle containing at most400 ordered sources, full-window source-kind metadata and total count. The 32KiB guard covers the compact UTF-8 source payload including IDs, timestamps, skew and metadata. The provider receives this bundle, never Scope or ORM query authority. Timeline, deployment/log tool views and citation validation reuse it without database reads. Findings may cite only its displayed sources. Sources beyond400 are explicitly omitted, cannot supply a hypothesis and cannot be cited; their source kinds are disclosed separately from truly missing telemetry.

Deployment-only windows generate observations without a correlation hypothesis. A correlation hypothesis requires a scoped deployment and scoped error log. Post-rollback narrative and contradiction UI appear only with scoped error logs explicitly reporting post-rollback errors. This is a fixture interpretation of source text, not independent causality verification.

## Round-two typed synthetic facts

Untrusted prose never authorizes a positive error or post-rollback claim. Evidence now has an explicitly authored event_code and nullable error_count. Database constraints permit only unknown facts (empty code/null count), log error samples with nonnegative counts, or config rollback records with null count. The migration gives every legacy row unknown facts; it performs no prose inference or historical backfill. Only the exact controlled seed generator assigns known fixture facts.

The frozen bundle carries these fields and includes them in its UTF-8 byte guard. Positive errors require an error_sample code and count greater than zero; count0 is healthy/zero, and unknown prose stays unknown. A post-rollback relation requires an actual scoped rollback_complete record with a source timestamp earlier than the positive sample. Narrative describes source timestamp ordering and explicitly retains clock-skew uncertainty. The source card exposes typed facts beside escaped raw text. Raw text may conflict with typed facts; it remains inspectable and is never parsed for authority.
