# AI for developers: GitHub Copilot

For developers, data engineers, testers and anyone else writing code at Laya. Most of the typing will be done with AI, so your job shifts to deciding what to build and reviewing what comes back.

## Five minutes to start

1. **In your repo, install the harness** (Python 3.10+):
   ```text
   python technical/harness/install_harness.py --target <path to your repo>
   ```
2. **Fill in what only your repo knows:** follow the `harness-setup` skill, or [the harness guide](harness/README.md).
3. **In Copilot Chat, type `/ask-laya`** to see which skill or role agent fits.

Just want the skills on your own machine? Add `--personal` in place of `--target`. They go to `~/.copilot/skills`.

## What you get

| | What | Where |
|---|---|---|
| **Process** | 27 of Matt Pocock's skills: align, spec, slice into tickets, test first, review, retro | `skills-and-agents/skills/` |
| **Laya layer** | 14 skills for Laya's data, systems and regulation | `skills-and-agents/skills/` |
| **Role agents** | 8 agents, each with only the tools its job needs | `skills-and-agents/agents/` |
| **Harness** | Instructions, guard hooks, CI, CODEOWNERS, PR template, ruleset | `harness/repo-kit/` |

## The Laya skills

| Skill | Reach for it when | Built from |
|---|---|---|
| `ask-laya` | You're not sure what to use (you type `/ask-laya`) | |
| `member-data-safety` | Code reads, stores, logs, sends or tests with member, policyholder or staff data | Laya's PII engine, and GDPR rules on special category data |
| `security-review` | Security review, threat model, or changes to agent files | STRIDE, OWASP's agentic list |
| `test-strategy` | Deciding what to test; judging AI-written tests | |
| `release-change` | Getting a change to production with evidence and a way back | |
| `incident-response` | An outage, a data exposure, or an agent misbehaving | |
| `ai-feature-check` | A feature that uses AI, or that makes decisions about people | EU AI Act, EIOPA |
| `harness-setup` | Setting up a repo, or Copilot keeps making the same mistake | |
| `skill-intake` | Someone found a skill or MCP server online | |
| `legacy-change` | Changing code with no trustworthy tests | Feathers, *Working Effectively with Legacy Code* |
| `production-ready` | Outbound calls, Graph, queues, jobs, Azure Functions, deployments | Nygard, *Release It!* |
| `data-design` | Snowflake or Oracle schemas, pipelines, CDC, migrations | Kleppmann, *Designing Data-Intensive Applications* |
| `bounded-contexts` | Work spanning business areas, or one word meaning two things | Vernon, *Domain-Driven Design Distilled* |
| `refactoring-pass` | Refactoring or cleanup, in small green steps | Fowler, *Refactoring* |

Why these skills and books: [WHERE-THE-SKILLS-CAME-FROM.md](skills-and-agents/WHERE-THE-SKILLS-CAME-FROM.md). What we changed in Matt's: [MATT-POCOCK-SKILLS.md](skills-and-agents/MATT-POCOCK-SKILLS.md).

## The role agents

Choose one in Copilot's agent picker. They work in VS Code, Visual Studio, GitHub.com and the Copilot CLI.

| Agent | Tools | Does |
|---|---|---|
| Laya Planner | read, search | Idea to spec and tickets |
| Laya Implementer | read, search, edit, run | One ticket, test first |
| Laya Reviewer | read, search | Reviews Standards, Spec and Member data |
| Laya Security Reviewer | read, search | Threat model and security review |
| Laya Test Engineer | read, search, edit, run | What to test, and writing it |
| Laya Data Engineer | read, search, edit, run | Snowflake, Oracle, pipelines, in development |
| Laya Release Manager | read, search, run | Release evidence, rollback, change record |
| Laya Incident Responder | read, search, run | Timeline, evidence, updates, lessons |

## Your responsibilities

Your [role card](../roles-and-lifecycle/cards/developer.md) says what you own. In short: you own every line you merge, you read it all, and you can explain it. The [best practices for building with Copilot](../best-practices/02-building-with-github-copilot.md) go into more depth.

## Known gotchas

- **Skills that need setup.** `to-spec`, `to-tickets`, `implement` and `code-review` expect the issue tracker config that `/setup-matt-pocock-skills` writes. For Azure DevOps, describe it as "anything else".
- **Subagents.** `implement-spec` and `wayfinder` start subagents, which GitHub lists for VS Code and the Copilot CLI, but not Visual Studio or GitHub.com.
- **Bash.** `wizard` and the reproduction script in `diagnosing-bugs` need Git Bash, WSL or Linux.
- **Name clashes with built-in commands.** Copilot may have its own `/` command with the same name as a skill, such as `/research` or `/pr` in the Copilot CLI. **[Not yet tested in real Copilot.]** If one clashes, ask for the skill by name: "use the research skill".
- **`[to confirm]` items.** These are in `member-data-safety`, `data-design`, `bounded-contexts` and the glossary. They need a Laya owner to fill them in.

## Updating

- **Matt's skills:** pull your clone, read the diff, then run `python tools/vendor_matt_skills.py --from <clone>` from `platform/`. See [MATT-POCOCK-SKILLS.md](skills-and-agents/MATT-POCOCK-SKILLS.md).
- **Book rules:** re-copy the `mini` file into the skill's `RULES.md`, keeping its attribution header.
- **The Laya layer:** edit `skills-and-agents/skills/`, run `python -m pytest` from `platform/`, then re-run the installer in each repo.
