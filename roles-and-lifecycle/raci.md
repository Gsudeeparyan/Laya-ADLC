# RACI: who does what

**R** does the work. **A** answers for it. **C** is asked first. **I** is told afterwards.

Each row has exactly one **A**, and it's always a person. An agent can do work (R), but never answers for it: its R always means under a named person's supervision. A test in the library keeps this table honest.

**Status: draft.** Adapt it to Laya's organisation **[to confirm]**. At lower [risk tiers](risk-tiers.md), most of the C and I roles drop away.

## Everyday and non-technical work

| Activity | AI agent | Staff member | Team lead | Business owner | AI champion | DPO | Compliance |
|---|---|---|---|---|---|---|---|
| Draft an email, summary or document | R | A | I | - | - | - | - |
| Send something to a member | R | R | A | C | - | - | C |
| Use personal data with AI for a new purpose | - | R | I | A | - | C | C |
| Build or change a team spreadsheet | R | A | I | - | C | - | - |
| Write a procedure | R | R | I | A | C | - | C |
| Report figures to senior management | R | R | A | C | - | - | - |
| Report an AI mistake | - | R | A | I | I | C | I |
| Help the team learn to use AI | R | - | A | - | R | - | - |

## Building and running something (the lifecycle)

| Stage | AI agent | Business owner | Developer | Tech lead | Test engineer | Security | Service owner | DPO | Compliance | AI owner |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Idea | R | A | C | C | - | - | C | C | C | C |
| 2. Spec | R | A | R | C | C | C | C | C | C | - |
| 3. Design | R | C | R | A | C | C | C | C | C | C |
| 4. Build | R | I | A | C | C | - | - | - | - | - |
| 5. Verify | R | C | R | C | A | C | - | C | - | - |
| 6. Release | R | C | R | C | C | C | A | I | I | - |
| 7. Operate | R | I | C | C | - | C | A | I | I | - |
| 8. Learn | R | C | R | A | R | C | C | - | I | I |

## Governing AI across Laya

| Activity | Board | AI owner | DPO | Compliance | Internal audit | Actuarial | Vendor owner | Platform admins |
|---|---|---|---|---|---|---|---|---|
| Set the vision and policy for AI | A | R | C | C | I | C | - | - |
| Keep the AI use register | I | A | C | C | I | - | - | - |
| Decide whether a T3 use may go ahead | I | A | C | C | I | C | - | - |
| Check personal data use complies with data protection law | I | C | A | C | I | - | - | - |
| Check AI use complies with other rules | I | C | C | A | I | - | - | - |
| Independently test the controls | I | I | I | I | A | - | - | - |
| Control AI affecting underwriting, pricing or reserving | I | C | C | C | I | A | - | - |
| Manage AI suppliers | I | C | C | C | - | - | A | C |
| Set Microsoft 365 and GitHub controls | I | C | C | C | I | - | - | A |
| Report a data breach to the regulator | I | I | A | C | I | - | - | - |

## The rules this follows

- **Exactly one A per row.** Two people answering for something means neither does.
- **Whoever does the work doesn't approve it.** At Verify, the test engineer answers for the result, not the developer who wrote the code.
- **The DPO and Compliance advise and verify.** They aren't accountable for business decisions, except for the areas the law gives them.
- **An independent function stays independent.** Internal audit tests and reports, and doesn't help design what it audits.
