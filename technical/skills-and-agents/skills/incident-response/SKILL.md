---
name: incident-response
description: Run a production or AI incident from first alert to lessons learned. Use when a service is down, slow or wrong, when data may have been exposed, when an AI agent did something it shouldn't have, or when writing a post-incident review.
license: Proprietary - Laya Healthcare internal use
---

# Incident Response

Stop the harm first, then find out why. An agent can gather evidence, draft updates and suggest causes; a named person leads and makes the calls. For the failure-chain analysis use `production-ready` (`../production-ready/SKILL.md`), and for the root cause use `diagnosing-bugs` (`../diagnosing-bugs/SKILL.md`).

## 1. Take the roles

Name an **incident lead** (decides), a **scribe** (keeps a timestamped log) and **comms** (updates people). In a small incident one person may hold two. Start the log now: decisions, times, who did what.

## 2. Stabilise

Choose the fastest safe move: roll back, turn off a feature flag, fail over, or block the traffic. A rollback beats a clever fix under pressure. Any action that deletes data or can't be undone waits for the incident lead.

Done when the harm has stopped growing, or you've told the lead why it can't be stopped yet.

## 3. Check the clocks

Regulatory clocks may already be running, so tell the people who own them at once. They decide what's reportable; you give them the facts.

- **Personal data possibly exposed, lost or altered:** tell the DPO immediately. The GDPR gives 72 hours to notify the Data Protection Commission, from becoming aware of a notifiable breach.
- **Serious service impact:** tell Compliance immediately. DORA sets short deadlines for major ICT incidents. **[to confirm with Compliance: Laya's classification and route]**
- **Members affected:** tell the service owner, who decides on member communications with Compliance.

**STOP** before contacting anyone outside Laya. That's for the people above to do.

## 4. If an AI agent was involved

Treat it as a compromised identity until you know otherwise:

1. **Capture** the session log, the prompt, the files and tools it used, and what it changed. Do this before cleaning up.
2. **Contain:** stop the session, close its pull requests, and rotate any token or secret it could reach. If a skill, hook, instruction file or MCP server may be the cause, remove it from the default branch.
3. **Ask whether it was steered:** did it read an issue, a comment, a web page or a document containing instructions? If so, that's prompt injection, so tell Security.
4. **Check the reach:** what else could it have touched with those permissions?

## 5. Find the failure chain

Trigger, missing defence, why it spread, why detection was late. No fix without a root cause: if three attempts fail, stop and escalate rather than trying a fourth. Keep evidence free of personal data, or restrict who can see it.

## 6. Communicate

Update on a fixed rhythm, even when there's nothing new: what's affected, what's being done, when the next update is. Say what you know and label what you don't. Don't name individuals, and don't speculate about cause.

## 7. Learn

Within a few days, write a blameless review: timeline, impact, failure chain, what helped, what didn't. Each action has one owner and a date. Prefer actions that change the system: a new check, a tighter permission, a better alert, rather than "be more careful". A mistake a machine could catch becomes a check, through `retro` (`../retro/SKILL.md`).

Done when service is restored and verified, the DPO and Compliance have been told or have confirmed they don't need to be, the log is complete, and every review action has an owner and a date.
