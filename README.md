# Laya-ADLC: how Laya works with AI

Everything Laya needs to use AI well, in one place: the agents and skills, who's responsible for what, and best practice. ADLC stands for Agentic Development Life Cycle.

**Laya uses two AI tools, and only these two:**

| Who | Tool |
|---|---|
| Non-technical staff | **Microsoft Copilot.** Most people have the free version, some the paid licence |
| Technical staff | **GitHub Copilot** |

## Where do you start?

| You are... | Go to |
|---|---|
| **Anyone who doesn't write code** | **[non-technical/](non-technical/README.md).** Find out which Copilot you have, open your department's playbook, and start |
| **A developer, data engineer or tester** | **[technical/](technical/README.md).** Skills, role agents and the harness for GitHub Copilot |
| **A team lead or manager** | [The playbook for leading a team](non-technical/by-role/team-leads-and-managers.md) and [your role card](roles-and-lifecycle/cards/team-lead.md) |
| **Compliance, the DPO, risk, audit or leadership** | [Roles and responsibilities](roles-and-lifecycle/README.md) and [regulation](best-practices/07-regulation.md) |
| **IT, or building the agents** | [Deploy the agents](non-technical/admin/deploy-agents.md) and the [GitHub checklist](technical/harness/org-admin-checklist.md) |
| **Running the rollout** | [ROLLOUT.md](ROLLOUT.md) |

## What's here

```text
non-technical/        Microsoft Copilot
  by-role/            a playbook for each of 12 departments
  prompts/            ready-to-use prompts
  training/           AI basics, a quiz, a team session plan
  everyone/           21 agents that work on the free version
  paid-licence/       3 more agents, and prompt packs for Word, Excel, PowerPoint, Outlook and Teams
  staff-guide/        how the agents work, and what to do when something goes wrong
  templates/          AI-safe workbooks and Word templates
  admin/              for IT: licences, tenant settings, deployment, smoke test
  ready-to-use/       generated: Word guides, templates and agent packs

technical/            GitHub Copilot
  skills-and-agents/  14 Laya skills, 27 of Matt Pocock's skills, 8 role agents
  harness/            the kit to drop into any repo, and the GitHub admin checklist
  platform/           the engines, build tools and tests behind it all

roles-and-lifecycle/  who's responsible for what, risk tiers, the lifecycle, 21 role cards
best-practices/       all best practice in one place, each with its source
GLOSSARY.md           Laya's shared language
ROLLOUT.md            how this reaches everyone, and who does what
```

## The one idea behind it

**AI does the work. A named person stays accountable.**

The [ten rules](best-practices/README.md#the-ten-rules) apply to everyone.

## Status

This is a **draft for review**:

- **No agent has run in Laya's real Copilot yet.** They've passed automated checks only. The [smoke test](non-technical/admin/smoke-test.md) comes first.
- **Compliance and the DPO haven't reviewed it yet.** That has to happen before it goes to all staff. See [ROLLOUT.md](ROLLOUT.md).
- **`[to confirm]` marks what only Laya can decide or fill in,** such as contacts, policies and named owners.

## For people changing the library

Read [AGENTS.md](AGENTS.md). From `technical/platform`:

```text
pip install -e ".[dev]"
python -m pytest
python tools/validate_skills.py
python tools/check_library.py
```
