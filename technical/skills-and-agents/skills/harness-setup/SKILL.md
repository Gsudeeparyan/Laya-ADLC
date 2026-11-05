---
name: harness-setup
description: Set up or improve the GitHub Copilot harness in a Laya repo. Use when adding Copilot instructions, skills, agents, hooks or CI checks to a repo, onboarding a repo to the Laya harness, or when Copilot keeps making the same kind of mistake in a repo.
license: Proprietary - Laya Healthcare internal use
---

# Harness Setup

The harness is everything around the model that makes good work likely and bad work get caught. It has two halves. **Guides** steer the agent before it acts: instructions, skills, the glossary. **Sensors** catch problems after it acts: tests, linters, CI, code review. Guides without sensors never learn whether they worked; sensors without guides repeat the same mistakes.

## 1. Install the kit

From the Laya-ADLC library:

```text
python technical/harness/install_harness.py --target <repo path>
```

It copies the skills, role agents and hooks, and creates the other kit files only where they're missing. Done when the script's report lists no errors.

## 2. Fill in what only this repo knows

- `.github/copilot-instructions.md`: what the repo is, its business area, and the exact commands to build, test and lint. Keep it short: it loads on every request. Every line should be something the agent got wrong or couldn't find.
- `.github/workflows/laya-checks.yml`: replace the failing placeholder with the real test command. The job fails on purpose until you do.
- `.github/workflows/copilot-setup-steps.yml`: install what the repo needs, so the cloud agent can run its own tests. If a step fails, Copilot carries on without the rest, so check the run.
- `.github/CODEOWNERS`: replace the placeholder with your harness owners and code owners.
- `GLOSSARY.md`: add this repo's terms.
- `CODING_STANDARDS.md`: add this repo's standards under **Repo-specific**.

Run `/setup-matt-pocock-skills` once to set the issue tracker.

Done when `grep -r "<" .github/copilot-instructions.md` finds no placeholder left and the test command runs.

## 3. Turn on what lives on the server

Hooks and instructions can be skipped. These can't, so they're the real enforcement. A repo admin does this:

- Import `.github/rulesets/main-protection.json` (Settings > Rules > Rulesets).
- Turn on secret scanning with push protection, Dependabot alerts and CodeQL default setup.

Merge the kit to the default branch: Copilot's cloud agent reads hooks and setup steps only from there.

## 4. Prove it works

Run a red check on each sensor. A control you've never seen fail isn't a control.

1. Pipe a test payload into the hook: `echo '{"toolName":"bash","toolArgs":{"command":"git push --force"}}' | sh .github/hooks/laya-guard.sh` must print a deny.
2. Open a test PR with a failing test: the merge must be blocked.
3. Open a test PR changing `.github/hooks/`: it must ask for the code owner.
4. Give Copilot a small real task: it should use the repo's commands and open a PR you'd accept.

Done when all four behave as described. Report any that don't.

## 5. Keep improving it

When Copilot makes a mistake, ask what would have prevented it, then pick the cheapest control that works, in this order:

1. **A check** (test, linter, CI, hook): it can't be ignored, so prefer this for anything mechanical.
2. **A standard** in `CODING_STANDARDS.md`: for judgement calls, read at review time.
3. **A line in the instructions:** only if it applies to almost every task and the agent can't work it out.

Remove instruction lines that have become checks. Run `/retro` after any build that went badly. Keep agent files under the same review as code.
