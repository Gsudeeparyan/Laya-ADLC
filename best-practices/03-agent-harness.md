# The agent harness

**For developers and IT.** The harness is everything around the AI model that makes good work likely and catches bad work. The same model does far better in a good harness than a bare one, and the harness is the part Laya controls.

## Guides and sensors

[Birgitta Böckeler's article on martinfowler.com](https://martinfowler.com/articles/harness-engineering.html) splits a harness into two halves:

| | What it is | Examples |
|---|---|---|
| **Guides** | Steer the agent before it acts | Instructions, skills, the glossary |
| **Sensors** | Observe after it acts, so it can correct itself | Tests, linters, type checks, review agents, CI |

A harness with only sensors repeats the same mistakes. One with only guides never learns whether its rules worked.

Controls are also either:

- **Computational:** deterministic, fast and cheap, such as tests and linters. Run them on every change.
- **Inferential:** semantic and probabilistic, such as AI review. They bring judgement, but they cost more and vary.

Your job is to be the **steerer**: when a problem recurs, improve the guides or sensors so that it's less likely, or impossible.

## Which control goes where

Pick the cheapest control that will really work:

| If the problem is | Use | Because |
|---|---|---|
| Mechanical, and a machine can spot it | A test, linter or CI check | It can't be ignored |
| Must never happen | A server-side rule: ruleset, required check, permission | It holds whatever anyone types |
| A dangerous action on someone's machine | A hook (second layer) | It stops it before it runs |
| A judgement call | `CODING_STANDARDS.md`, read at review | Only a person or review agent can judge |
| A job with steps | A skill | It loads only when needed |
| A recurring role | A custom agent | It has its own tools and limits |
| True of almost every task | A line in `copilot-instructions.md` | It loads on every request, so keep this short |

**Prefer designing a mistake out to documenting it.** A rule people must remember is the weakest kind of control.

## What Copilot gives you

From [GitHub's customisation cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet):

| Type | Where it lives | Reaches |
|---|---|---|
| Repository instructions | `.github/copilot-instructions.md` | Every Copilot surface |
| Path-specific instructions | `.github/instructions/*.instructions.md` | Most, but not code review in VS Code or Visual Studio |
| `AGENTS.md` | Repo root | VS Code, CLI, cloud agent, GitHub.com code review |
| Skills | `.github/skills/<name>/SKILL.md` | VS Code, Visual Studio, GitHub.com, CLI; JetBrains in preview |
| Custom agents | `.github/agents/*.agent.md`; org: `/agents` in `.github-private` | VS Code, Visual Studio, GitHub.com, CLI; others in preview |
| Hooks | `.github/hooks/*.json` | GitHub.com and CLI; VS Code in preview; not Visual Studio or JetBrains |
| MCP servers | `mcp.json`, or repo settings | All |
| Prompt files | `.github/prompts/*.prompt.md` | Not GitHub.com or CLI. [VS Code](https://code.visualstudio.com/docs/copilot/customization/overview) says to use a skill for reusable workflows |
| Organisation instructions | Organisation settings | [GitHub.com only](https://docs.github.com/en/copilot/reference/custom-instructions-support), and not local IDE sessions |

So Laya puts its always-on rules in `.github/copilot-instructions.md`, which reaches every surface, and uses skills for everything else.

## Good instructions

- **A map, not a manual.** Short, stable, and pointing at deeper documents.
- **Every line earns its place.** It's something the agent got wrong or couldn't find. Delete anything it would do anyway.
- **Exact commands** to build, test and lint.
- **Reviewed like code,** because they steer every agent in the repo.

## Hooks: useful, but not a wall

[GitHub](https://docs.github.com/en/copilot/reference/hooks-reference) and [VS Code](https://code.visualstudio.com/docs/copilot/customization/hooks) are clear on the limits:

- **A hook crash denies the call; a timeout doesn't.** Timeouts fail open, even for policy hooks.
- **Not every surface runs them.** Visual Studio and JetBrains don't, and the cloud agent honours only `bash` commands.
- **The cloud agent reads hooks only from the default branch.**
- **Hooks aren't a substitute** for enforced permissions, sandboxing or enterprise controls (VS Code's words).
- **Hook scripts are code.** Review them, and never paste untrusted arguments into a shell command.

So Laya's guard hook catches common mistakes, and rulesets and CI do the real enforcement.

## The server-side rules

These hold however someone works:

- **Rulesets:** pull requests required, code owner review, required checks, no force push.
- **CODEOWNERS over harness files:** instructions, skills, agents, hooks, workflows ([GitHub recommends this](https://docs.github.com/en/enterprise-cloud@latest/copilot/tutorials/cloud-agent/build-guardrails)).
- **Secret scanning with push protection, CodeQL and dependency review.**
- **Copilot's own limits:** the [cloud agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations) pushes only to its own branch, can't approve or merge its own pull request, and its workflows need approval to run.

The full list is in the [org admin checklist](../technical/harness/org-admin-checklist.md).

## Running many agents

- **Delegation only narrows.** A sub-agent never has more access than the agent that started it.
- **One writer at a time** in a working copy.
- **Whoever did the work doesn't approve it,** agent or person.
- **Add automation one trigger at a time,** with limits and a person reviewing every pull request, and open up as the brakes earn trust. Matt Pocock's name for automation without brakes: a slop cannon.
- **Cap retry loops** at a few tries before a person steps in.

## Sharing it across Laya

| Route | How | Good for |
|---|---|---|
| **Copy into each repo** (default) | `technical/harness/install_harness.py` | Reaches every surface; pinned by Git; reviewed in a pull request |
| **Private plugin marketplace** | [`.github/plugin/marketplace.json`](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace) in a private Laya repo | Company-wide skills and agents with one install |
| **Enterprise managed settings** | [`extraKnownMarketplaces`, `strictKnownMarketplaces`, `enabledPlugins`](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/use-managed-settings/manage-plugin-marketplaces-and-plugins) | Requiring or blocking plugins |

A project's own skill beats a plugin's with the same name ([GitHub](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)), so a repo can always override.

## The Microsoft side

Staff agents have a harness too: the shared preamble and PII guard (guides), the validator and smoke test (sensors), and tenant settings (server-side rules). See [tenant settings](../non-technical/admin/tenant-settings.md).
