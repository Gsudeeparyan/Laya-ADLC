---
name: ask-laya
description: Ask which skill, agent or flow fits your situation. A router over Laya's developer skills and Matt Pocock's skills.
disable-model-invocation: true
license: Proprietary - Laya Healthcare internal use
---

# Ask Laya

You don't remember every skill, so ask. Before saying what a skill does, or that a step can be skipped, read that skill's `SKILL.md`: the summaries here are for orientation only.

Laya's developer skill set has two layers:

- **Matt Pocock's skills:** the process, from idea to merged code. `/ask-matt` maps all of them in depth.
- **The Laya layer:** the discipline his process calls on when Laya's data, systems and regulation make the work risky. These load on their own when the work calls for them.

Pick a role agent from Copilot's agent picker when the job fits one. Each has only the tools its job needs.

| Agent | Use it to |
|---|---|
| Laya Planner | Turn an idea into a spec and tickets. It reads and doesn't edit |
| Laya Implementer | Build a ticket, test first |
| Laya Reviewer | Review a diff on Standards, Spec and Member data. Read-only |
| Laya Security Reviewer | Threat-model and security-review a change. Read-only |
| Laya Test Engineer | Decide what to test and write it |
| Laya Data Engineer | Change Snowflake, Oracle or a pipeline safely |
| Laya Release Manager | Prepare a release, with evidence and a way back |
| Laya Incident Responder | Run an incident, including one an agent caused |

## The main flow, with the Laya stops

1. **Start from the business.** Requirements often arrive as a Word document and a user-story CSV from the Laya Requirements Writer agent. Bring them in as material. New AI in the product? Run **`ai-feature-check`** first.
2. **`/grill-with-docs`** sharpens the idea and keeps `GLOSSARY.md` and ADRs up to date. Work spanning business areas or systems: **`bounded-contexts`**.
3. **`/to-spec`**, then **`/to-tickets`**. While specifying, bring in:
   - **`member-data-safety`** for any member, policyholder or staff data
   - **`production-ready`** for any integration, job or deployment
   - **`data-design`** for any pipeline, schema or warehouse change
   - **`test-strategy`** for what proves it works

   Their answers belong in the spec, not discovered in review.
4. **`/implement`**, or `/tdd` on its own. Code with no trustworthy tests goes through **`legacy-change`** first: characterise, seam, then change.
5. **`/code-review`** reviews on two axes: Standards (`CODING_STANDARDS.md`) and Spec. If the change touches member data, add **`member-data-safety`** as a third axis, reported on its own. If it touches security or agent files, add **`security-review`**.
6. **`/pr`** writes the pull request. A person owns it, reads every line and merges it.
7. **`release-change`** gets it to production with evidence and a way back.
8. **`/retro`** after the build: turn mistakes into checks before you turn them into prose.

## On-ramps

- **Something's broken** → `/diagnosing-bugs`. An outage, data exposure or an agent misbehaving → **`incident-response`**.
- **Old code needs one change** → **`legacy-change`**, then back onto the main flow at `/implement`.
- **Cleanup** → **`refactoring-pass`**, in small green steps. Behaviour changes don't belong in it.
- **A question only someone else can answer** (a DPO, a vendor, another team) → `/to-questionnaire`.
- **Setting up a repo, or Copilot keeps making the same mistake** → **`harness-setup`**.
- **Someone found a skill or MCP server online** → **`skill-intake`**, before anyone installs it.

## Vocabulary underneath

- `GLOSSARY.md`: Laya's words (member vs policyholder, pseudonymised vs anonymised). Use them in code, tests and tickets.
- `codebase-design`: deep modules, seams, leverage, locality.
- `bounded-contexts`: where one business area's words stop and another's begin.

## Precondition

Run `/setup-matt-pocock-skills` once per repo, to set the issue tracker (GitHub, Azure DevOps via "anything else", or local files) and the doc layout.
