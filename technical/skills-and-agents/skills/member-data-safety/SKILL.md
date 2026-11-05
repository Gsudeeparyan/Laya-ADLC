---
name: member-data-safety
description: Keep member, policyholder and staff data safe in code. Use when a change reads, stores, logs, sends, displays or tests with personal or health data, touches member, claim or policy tables, adds analytics or AI features over people's data, or when reviewing such a change.
license: Proprietary - Laya Healthcare internal use
---

# Member Data Safety

Laya is an Irish health insurer: most of its data is **personal data**, and claims and medical details are **special category** data under the GDPR. This skill is the data-flow discipline every change touching that data goes through. Use the terms in `GLOSSARY.md` (member, policyholder, claim, token, pseudonymised, anonymised).

## 1. Classify

Name what the change touches: **none**, **personal** (names, contact details, PPSN, DOB, Eircode, IBAN, member/policy/claim numbers), or **special category** (diagnosis, condition, treatment, medication, anything inferred from claims). Done when each field the change reads or writes has a class.

## 2. Trace the flow

Map every **sink** the data reaches from its source: database tables, files, logs, traces, error messages, analytics events, caches, queues, API responses, emails, test fixtures, and prompts to an AI model. Done when the map has no "and then it goes somewhere": every hop is named.

## 3. Check each sink

- **Queries**: select the columns the feature needs, never `SELECT *` on member tables. Aggregate when the feature needs totals. Reports suppress groups smaller than 5.
- **Logs, traces, errors, analytics**: carry an internal ID or token, never names, PPSN, DOB, contact details, health details or free-text notes. Exception messages that echo input are a leak path: log the type and the ID, not the payload.
- **Test fixtures and seed data**: synthetic and obviously fake, generated, never copied from production. `python .github/scripts/laya_scan.py <folder>` runs over them in CI; a finding fails the check.
- **Storage**: encrypted at rest, a stated retention period, and a deletion path. In Snowflake, PII columns sit behind masking or row access policies. **[to confirm]** Laya's standard policy names, and the Oracle equivalent.
- **Transport**: TLS only. Any transfer outside the EU is a DPO question, not a code decision.
- **AI and LLM calls**: pseudonymise before the prompt leaves Laya's tenant and keep the key inside it (the pattern in the library's `technical/platform/src/adlc_pii`). Logged prompts and responses are personal data too.
- **Access and secrets**: least privilege; service identities over shared accounts; secrets in Key Vault, never in code, config or test files.

Done when every sink in the map has a verdict: safe, fixed in this change, or raised.

## 4. Escalate what code can't decide

A new purpose for existing data, a new kind of processing (profiling, automated decisions about members, new AI use), large-scale processing of health data, or a new third party: tell the user it needs a DPIA. Point them to the Laya Privacy & AI Check agent and the DPO before it ships.

## 5. Report

List findings as `file:line`: the sink, the data class, the risk, the fix. Lead with special-category findings.

For a review of a diff, this is a third axis beside Standards and Spec: report it under its own `## Member data` heading so it cannot be ranked away.
