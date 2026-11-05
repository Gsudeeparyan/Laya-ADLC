---
name: production-ready
description: Make services, integrations and jobs survive production failures. Use when a change adds or modifies an outbound call, API integration, Microsoft Graph or third-party call, queue, scheduled job, Azure Function, health check, deployment or migration, or when reviewing an incident or a slow, flaky or overloaded service.
license: Proprietary - Laya Healthcare internal use
---

# Production Ready

A passing happy path is not production readiness. Every **integration point** (an outbound call, a queue, a pool, a job, a migration) will fail slowly, partially or for a long time. Decide its failure behaviour now, before production decides it for you. Full rule set (Michael Nygard, _Release It!_): [RULES.md](RULES.md), the checklist to run through for a review or an incident.

## For each integration point in the change

Work through these, writing the answer next to the code or in the PR:

1. **Timeout.** An explicit, intentional limit on every outbound call and wait. Library defaults and infinite waits don't count. Know the host's own ceiling (an Azure Function's execution limit, a gateway timeout) and finish inside it.
2. **Retry.** Only for safe operations (idempotent, or carrying an idempotency key). Bounded count and total time, exponential backoff with jitter, and never for validation or other permanent errors. Honour `Retry-After` on throttling responses: Microsoft Graph returns 429 and expects you to wait. Retry at one layer only.
3. **Failure isolation.** Fail fast when the dependency is known down (a circuit breaker). Keep a slow dependency from consuming every thread, connection or worker (a bulkhead: a separate pool or limit).
4. **Bounds.** Every queue, buffer, cache, batch and result set has a size, and a rule for what happens when it's full. Paginate or stream large payloads.
5. **Untrusted responses.** Validate status, shape and plausibility before the data reaches state, caches or queues.
6. **Diagnosis.** Structured logs with a correlation ID, latency, outcome and dependency name, with no personal data (read and follow the `member-data-safety` skill (`../member-data-safety/SKILL.md`) if member data is involved). Health checks that report real readiness.
7. **Operations.** Deployments, migrations and one-off jobs are restartable or idempotent, observable, and have a rollback or roll-forward path.

Done when every integration point in the diff has a stated timeout, retry policy, failure behaviour and bound, and each one is tested or justified in writing.

## Incidents

For an incident or performance problem, name the failure chain: the trigger, the missing defence, why it spread, and why detection was late. Recommend design changes, not just a fix. Then hand the hard bug to the `diagnosing-bugs` skill (`../diagnosing-bugs/SKILL.md`) to build a loop that goes red on it.
