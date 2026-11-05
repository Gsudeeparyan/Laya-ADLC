---
name: release-change
description: Get a change safely into production, with the evidence to show it. Use when preparing a release or deployment, writing a change record or rollback plan, running a database migration in production, or deciding whether something is ready to ship.
license: Proprietary - Laya Healthcare internal use
---

# Release Change

Green CI is not readiness. A release is ready when a named person can show what's going out, why it's safe, how to undo it, and how you'd know it went wrong. For how the code handles failure, use the `production-ready` skill (`../production-ready/SKILL.md`).

## 1. Pin what's going out

Name the exact commit and list what it contains, compared with what's live. Approvals and test evidence belong to that commit. A new push makes them stale, so check they still match. Done when the commit under review is the commit being deployed.

## 2. Gather the evidence

- **Tests:** which ran, against that commit, and what didn't run.
- **Review:** a named person approved it, and a code owner did where required.
- **Risk tier** (`roles-and-lifecycle/risk-tiers.md`): every sign-off that tier requires is recorded.
- **Security and data:** `security-review` and `member-data-safety` findings are closed or accepted by a named owner.
- **Dependencies:** nothing new since review.

Report any gap as a gap. Don't fill it with "should be fine".

## 3. Plan the way back

Write the rollback or roll-forward steps, who runs them and how long they take. Migrations need extra care:

- Prefer expand, migrate, contract, so old and new code both work during the change.
- A destructive step (a dropped column, deleted data) is a one-way door, so it goes in its own later release, after a verified backup.
- Run it against a production-sized copy of synthetic data first.

Done when someone other than the author could carry out the rollback from what's written.

## 4. Plan how you'd know

Name the signals to watch (errors, latency, the business number the change affects), the threshold that triggers rollback, and who's watching and for how long.

## 5. Record and approve

Write the change record: what, why, risk tier, evidence, rollback, monitoring, owner. Follow Laya's change process **[to confirm: tool and approvers]**. DORA expects ICT change management with an audit trail, so keep the record where auditors can find it.

**STOP** for the named owner's approval. An agent prepares the release; a person decides it goes.

## 6. After release

Check the signals, confirm the change works in production, and close the record with what happened. Anything that surprised you goes through `retro` (`../retro/SKILL.md`).

Done when the change record shows the commit, the evidence, the approver, the outcome, and that monitoring stayed inside its thresholds for the agreed period.
