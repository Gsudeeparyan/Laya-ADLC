# Changelog

## 2.0.0 (05/11/2026): Laya-ADLC

Moved from `ADLC-main` into one company-wide folder, split into technical and non-technical, for Microsoft Copilot and GitHub Copilot only.

### New for non-technical staff

- Free and paid tiers. The validator enforces Microsoft's licence boundary.
- Department playbooks for 12 kinds of work.
- Prompt packs: everyday prompts and Copilot Chat in Outlook (free); Word, Excel, PowerPoint, Outlook, Teams and work chat (paid).
- Training: AI basics, a quiz, one-page rules, a team session plan, the AI champion's guide.
- Staff pages: "Which Copilot do I have?" and "When something goes wrong".
- Two free agents: Laya Prompt Coach, Laya Second Check.
- Three paid agents: Laya Catch Me Up, Laya Meeting Recap, Laya Policy Finder.
- Laya Privacy Check became Laya Privacy & AI Check, with its agent id unchanged, so updates replace the live agent.
- Word versions of everything.

### New for everyone

- Roles and responsibilities: 21 role cards, risk tiers, lifecycle, RACI, AI use register.
- Best practices in one place, with sources.
- A rollout plan: owners, review gates, where it lives, who can see it.

### New for technical staff

- Eight role agents, seven new Laya skills, all 27 of Matt Pocock's stable skills adapted for Copilot by a repeatable script.
- A repo kit: instructions, guard hooks, CI, setup steps, CODEOWNERS, PR template, ruleset.
- A cross-platform installer, a private plugin marketplace, and an organisation admin checklist.

### Removed

- Legacy tool-specific folders and installer artifacts from earlier research experiments.
- The skills landscape research note, which compared tools Laya won't use. It's in the backup.

### Corrected

- **Building agents:** the old guide said free Copilot Chat users could build agents in Agent Builder. Microsoft's admin guide says this needs a licence or pay-as-you-go. Licensed people or IT now build them.
- **Personal data rule:** the staff guide said "never share personal data" while agents were built to protect it and carry on. They now agree.
- **Files:** agents now say to download before closing the chat, because files last only for the session.
- **Agent schema:** moved from v1.5 to v1.9, and plugin from v2.2 to v2.4, with packages validated against Microsoft's published schemas.
- **Smoke test:** it still tested behaviour from before the last rewrite, and named a skill that no longer exists.
- **Missing guide:** `deploy-sharepoint-backend.md` was referenced but never written.
- **`adlc-pii`:** documented as a command, but it wasn't installed as one. It's now in `pyproject.toml`.
- **Excel Expert:** "splitting or combining columns" restored.
- **Counts:** the last research note said 17 skills restated the question rule. The real figure is 14.

### Where things went

| Old place in `ADLC-main` | New place |
|---|---|
| `skills/` | `non-technical/everyone/skills/` |
| `skills/_shared/` | `non-technical/shared/` |
| `agents/m365/` | `non-technical/everyone/agents/` |
| `agents/m365/package.yaml` | `non-technical/package.yaml` |
| `templates/` | `non-technical/templates/` |
| `docs/staff-guide/` | `non-technical/staff-guide/` |
| `docs/builder/` | `non-technical/admin/` (two deployment guides became `deploy-agents.md`) |
| `docs/m365-free-tier-constraints.md` | `non-technical/admin/licences.md` |
| `docs/skill-authoring-guide.md` | `best-practices/04-writing-skills.md` |
| `docs/laya-glossary.md` | `GLOSSARY.md` |
| `docs/excel-continuity-pattern.md` | `technical/platform/docs/` |
| `docs/research/skills-and-books-filter.md` | `technical/skills-and-agents/WHERE-THE-SKILLS-CAME-FROM.md` |
| `developer/skills/` | `technical/skills-and-agents/skills/` |
| `developer/CODING_STANDARDS.md` | `technical/harness/repo-kit/` |
| `developer/AGENTS.template.md` | `technical/harness/repo-kit/.github/copilot-instructions.md` |
| `developer/install-skills.ps1` | `technical/harness/install_harness.py` |
| legacy tool-specific skill folders | `.github/skills/adlc-agent-author/` |
| `src/`, `backend/`, `tools/`, `tests/`, `catalog.yaml`, `pyproject.toml` | `technical/platform/` |
| `dist/` | `non-technical/ready-to-use/` (generated) |

The old folder's backups are in `D:\ADLC\_backups\` on the machine where this was built.

## 1.x

The first ADLC library: 19 staff agents for free Copilot Chat, and an early developer skill set.
