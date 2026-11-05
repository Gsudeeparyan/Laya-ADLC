# Platform engineer (harness owner)

Whoever owns the GitHub Copilot harness: the instructions, skills, hooks and checks around the model.

## What you own

- The repo kit, and getting it into each repo.
- `CODEOWNERS` over harness files, rulesets and required checks.
- Turning repeated mistakes into automated checks.
- Reviewing any new skill, agent, hook or MCP server.

## What AI can do for you

- Draft hooks, checks and setup steps.
- Find what repeated mistakes have in common.

## What you must not hand over

- Approving changes to harness files without a second reviewer.
- Testing that each control really fails when it should.

## Your tools

- `harness-setup`, `skill-intake`, `security-review`.
- [The harness guide](../../technical/harness/README.md) and [org checklist](../../technical/harness/org-admin-checklist.md).

## The evidence you leave

- The harness version in each repo, and red-check results.
- Intake records for outside skills.
