---
name: data-design
description: Design data flows that stay correct under retries, replays, lag and change. Use when a change touches a Snowflake or Oracle schema, a data pipeline, ETL or ELT job, CDC, events, a cache, a read model, a report table, a schema migration, or any write path where duplicates, ordering or consistency matter.
license: Proprietary - Laya Healthcare internal use
---

# Data Design

Treat crashes, duplicate work, timeouts, stale reads and "did it succeed?" as normal inputs, not edge cases. Every piece of data is either a **source of truth** or **derived** from one, and derived data needs a way to be rebuilt. Full rule set (Martin Kleppmann, _Designing Data-Intensive Applications_): [RULES.md](RULES.md), for replication, partitioning, isolation and consensus questions.

## Steps

1. **Ownership.** For every table, stream, file or cache the change touches, write down: source of truth or derived, who owns it, and (if derived) what it is derived from. Done when nothing is unlabelled.

2. **Write semantics.** For each write path, state:
   - when the write is durable, and when it becomes visible
   - what a reader sees in between
   - what happens after a timeout where success is unknown

3. **Replay safety.** Make every job, consumer and pipeline step safe to run twice, using a deduplication key, a naturally idempotent transition, or a `MERGE` on a business key rather than a blind `INSERT`. Done when you can say what happens if yesterday's run is replayed today.

4. **Ordering.** Keep only the ordering the business logic needs, and scope it: per member, per claim, per policy. Nothing more global.

5. **Schema evolution.** Treat a column, enum, status or payload change as a contract with old readers, old writers, old stored data and in-flight messages. Prefer expand-then-contract:
   1. Add the new form.
   2. Migrate readers and writers.
   3. Backfill.
   4. Remove the old form.

6. **Repair.** Every derived table has a rebuild path and a reconciliation check (row counts, sums or hashes against the source). In Snowflake, know which repair Time Travel gives you and how far back. **[to confirm]** Laya's retention setting.

7. **Personal data.** Member and claim data in a pipeline or warehouse: read and follow the `member-data-safety` skill (`../member-data-safety/SKILL.md`).

The design is done when every touched dataset is labelled, every job has a replay story, every schema change has a compatibility plan, and every derived table can be rebuilt and reconciled.

## Steer away from

- exactly-once wishful thinking
- one business concept split across services that must stay consistent
- chatty cross-service joins on a hot path
- an unrebuildable projection
