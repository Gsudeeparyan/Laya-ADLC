# Rollout: how this reaches everyone

**For:** the library owner and whoever sponsors AI at Laya. Today this library sits on one drive. This is how it gets to the whole company, safely.

## Stage 1: Name the owners (week 1)

Nothing moves until these people exist. One person can hold more than one of these roles to start.

| Role | Job | Name |
|---|---|---|
| Executive sponsor | Backs it, and takes it to the board | [to confirm] |
| [AI owner](roles-and-lifecycle/cards/ai-owner.md) | Decides on higher-risk uses; keeps the register | [to confirm] |
| [Library owner](roles-and-lifecycle/cards/library-owner.md) | Runs this library and this rollout | [to confirm] |
| Microsoft 365 admin | Deploys agents and sets the tenant up | [to confirm] |
| GitHub admin | Sets up the organisation and repo | [to confirm] |
| Compliance lead, DPO | Review and sign off | [to confirm] |

## Stage 2: Review before anyone relies on it (weeks 1-3)

| Who | Reviews | Done when |
|---|---|---|
| Compliance | [Regulation](best-practices/07-regulation.md), [roles](roles-and-lifecycle/README.md), [risk tiers](roles-and-lifecycle/risk-tiers.md), how duties split between Laya and AXA | Corrected, and "draft" removed |
| DPO | [Data protection](best-practices/06-data-protection.md), Laya PII Guard, Laya Privacy & AI Check, [when something goes wrong](non-technical/staff-guide/when-something-goes-wrong.md) | What staff may put into Copilot is decided; the retention period is agreed |
| HR | Logging and monitoring wording, [training](non-technical/training/README.md), the [team session's](non-technical/training/run-a-team-session.md) answers about jobs | The company's message is agreed |
| Security | [Security](best-practices/05-security-for-ai.md), [the guard hook](technical/harness/README.md), the backend | Agreed |
| Department heads | Their [playbook](non-technical/by-role/README.md) | Matches how the team really works; contradictions with procedures are fixed |

Fill in every `[to confirm]` as you go. Run `grep -r "to confirm"` to find them.

**Gate:** Compliance and the DPO sign off before stage 4.

## Stage 3: Give it a home, and prove it works (weeks 2-4)

**Where it lives:**

| What | Where | Who can see it |
|---|---|---|
| The whole library | A **private repository in Laya's GitHub organisation** | Technical staff read it. Changes go through pull requests |
| Word guides, templates, one-page rules | A **SharePoint site** all staff can read: "ADLC Templates" | All staff |
| The agents | **Microsoft Copilot,** deployed by IT | Free-tier agents to all; paid agents to licensed staff |

**Non-technical staff never need GitHub.** They get the agents in Copilot and the guides on SharePoint.

**Keep the full repo internal.** It includes the backend's infrastructure and admin checklists, which aren't for general circulation. There should be no secrets in it (`tools/check_library.py` and secret scanning check this), but it still isn't for sharing outside Laya.

**To create the repo** (from this folder, signed in to GitHub with your **Laya** account, not a personal one):

```text
git init -b main
git add .
git commit -m "Laya-ADLC first version"
gh repo create <laya-org>/laya-adlc --private --source . --push
```

Then replace `@LAYA-ORG/...` in `.github/CODEOWNERS`, and import the ruleset (`technical/harness/repo-kit/.github/rulesets/main-protection.json`).

**Prove it works:**

1. Run the [smoke test](non-technical/admin/smoke-test.md), with a licensed account and an **unlicensed** one. Whether free users get Code Interpreter comes first: Microsoft's pages disagree, and the Excel agents depend on it.
2. Agree the [tenant settings](non-technical/admin/tenant-settings.md) and the [GitHub settings](technical/harness/org-admin-checklist.md).
3. Install the harness in one real repo, following the `harness-setup` skill.

**Gate:** the smoke test passes for both kinds of account.

## Stage 4: Pilot (weeks 4-8)

**Non-technical:** 10-15 volunteers from 2-3 teams, including people on the free version and on the paid licence.

| Week | They get |
|---|---|
| 1 | AI basics and a team session. Laya AI Helper, Prompt Coach, Second Check, Comms Writer, Document Summariser, PII Guard, Privacy & AI Check |
| 2 | The Excel agents |
| 3 | Document Co-author, Meeting Actions, Presentation Builder; the three paid agents, for licensed people |
| 4 | Planning agents |

**Technical:** one team, one real repo. Start with T0 and T1 work, and let the cloud agent earn its way up.

**Choose AI champions** from the pilot teams. They run the wider rollout.

**Each week:** collect what worked and what went wrong, with the exact prompt and no personal data. Fix the skill, and re-test.

**Gate:** the pilot teams would recommend it, nothing serious has gone wrong, and problems have owners.

## Stage 5: Everyone (from week 8)

| Step | Owner |
|---|---|
| Sponsor's message: why, what's OK, that reporting mistakes is welcome | Executive sponsor |
| Publish the agents; pin the Laya AI Helper for everyone | Microsoft 365 admin |
| Put the guides on SharePoint | Library owner |
| A 30-minute session in every team, run by the champions | Team leads |
| Everyone reads the AI basics | Team leads; HR records it |
| Roll the harness out repo by repo | Platform engineer |
| Start the AI use register | AI owner |

**Support:** first your AI champion, then the library owner. IT service desk for access and security. Manager and DPO when something goes wrong.

## Stage 6: Keep it alive

| How often | What | Owner |
|---|---|---|
| Monthly | Champions report in; review the Agent Registry | Library owner, Microsoft 365 admin |
| Quarterly | Re-check [sources](best-practices/sources.md), because Microsoft and GitHub change often. Re-run part of the smoke test, since Copilot's models change automatically. Review who has the paid licence | Library owner |
| Quarterly | Report [the measures](best-practices/08-measuring-value.md) to the AI owner | Library owner |
| Yearly | Review AI at senior management level, and review each role and the policy | AI owner, senior management |
| On a regulatory change | Update regulation and tell people | Compliance |

**Versions:** the library has one version number, in `technical/platform/catalog.yaml`, and each skill has its own. Changes go through a pull request, reviewed by someone other than the author. See [CHANGELOG.md](CHANGELOG.md).

## What could go wrong

| Risk | What we do |
|---|---|
| The free version can't do what we expect | Smoke test before anything else. Fallback: pay-as-you-go, or fewer agents |
| People trust it too much | Training, Second Check, and managers asking "how did you check it?" |
| People hide their use | A clear position, and thanks for reporting |
| The paid and free groups drift apart | Every process has a free route |
| Documents fall out of date | Quarterly checks with a named owner |
| Shadow AI | Good official tools, a clear rule, and a way to ask |
