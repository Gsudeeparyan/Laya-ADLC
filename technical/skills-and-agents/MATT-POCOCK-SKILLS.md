# Matt Pocock's skills in this library

Copied from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT licence) by `technical/platform/tools/vendor_matt_skills.py`.

- **Pinned commit:** `4ae2317`
- **Copied:** 05/11/2026
- **Skills (27):** `ask-matt`, `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`, `implement`, `implement-spec`, `improve-codebase-architecture`, `pr`, `prototype`, `research`, `retro`, `setup-matt-pocock-skills`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `wizard`, `grill-me`, `grilling`, `handoff`, `teach`, `to-questionnaire`, `wait-what`, `writing-for-agents`

His `misc` and `in-progress` folders are left out, because he doesn't ship them.

## What we changed, and why

Only these edits are made to his text. They come from the script, so they repeat on every update.

| Change | Why |
|---|---|
| "Call the Skill tool with X" becomes "Read and follow the X skill (`../X/SKILL.md`)" | GitHub's docs describe Copilot matching and loading skills, not a callable skill tool |
| Another tool's instruction file name becomes `.github/copilot-instructions.md` | It's the instruction file every Copilot surface reads |
| Each skill's `agents/` metadata file is removed | It's for another tool. Copilot uses `disable-model-invocation` in `SKILL.md` instead |
| `license` and `metadata.source` are added to the frontmatter | So the licence and pinned source travel with each skill |

## Where they work

- **Everywhere skills are supported:** the single-session skills.
- **VS Code and Copilot CLI only:** `implement-spec` and `wayfinder`, which start subagents. GitHub's cheat sheet doesn't list subagents for Visual Studio or GitHub.com.
- **Git Bash, WSL or Linux needed:** `wizard`, and the reproduction script in `diagnosing-bugs`.

## Updating

1. `git pull` in your clone and read the upstream diff.
2. `python tools/vendor_matt_skills.py --from <clone>` from `technical/platform`.
3. Review the changes, then run `python -m pytest`.
