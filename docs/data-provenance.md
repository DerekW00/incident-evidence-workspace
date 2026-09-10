# Data provenance

seed_demo generates two organizations, two local users, two services/incidents, ten evidence records and two runbook sections. All text, identifiers, release names and timestamps are fictional and newly authored. Primary incident: release at 14:00 UTC, error spike at 14:01, rollback at 14:03, continued errors at 14:04 with 12-second reported source skew, and an end-boundary marker at 14:06. Metrics are deliberately absent.

fixtures/provider-malformed.json, provider-partial-usage.json and provider-error.json are hand-authored synthetic failure recordings, not captured provider traffic. Evaluations are frozen functional expectations, not live model evaluations. HTMX 2.0.4 was fetched from its public npm distribution, with LICENSE retained in static/HTMX-LICENSE.txt.

Structured facts are newly authored fixture values: at14:01 error_sample count76; at14:03 rollback_complete; at14:04 error_sample count31. The remaining records have unknown structured facts. seed_demo refreshes only its exact controlled synthetic fixture keys with these authored values. Database migration leaves other preexisting rows unknown rather than deriving facts from words such as error or rollback.
