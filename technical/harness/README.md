# The GitHub Copilot harness

The harness is everything around the model that makes good work likely and bad work get caught. The reasoning is in [the agent harness](../../best-practices/03-agent-harness.md). This page is what's in the kit and how to use it. **The `harness-setup` skill walks you through it step by step.**

## Install

```text
python technical/harness/install_harness.py --target <path to your repo>
```

## What goes in your repo

| File | What it is | On re-install |
|---|---|---|
| `.github/skills/` | All library skills | Replaced |
| `.github/agents/` | The 8 role agents | Replaced |
| `.github/hooks/laya-guard.*` | The guard hook and its patterns | Replaced |
| `.github/scripts/laya_scan.py`, `laya_pii_detectors.py` | The scan for personal data and secrets | Replaced |
| `.github/copilot-instructions.md` | Rules for every request. **Fill this in** | Kept |
| `.github/instructions/` | Rules by file type: member data, SQL, Python, tests, infrastructure, frontend | Kept |
| `.github/workflows/laya-checks.yml` | CI. **Add your test command: it fails on purpose until you do** | Kept |
| `.github/workflows/copilot-setup-steps.yml` | Prepares the cloud agent. **Add your install steps** | Kept |
| `.github/CODEOWNERS` | Harness files need the owner's review. **Put your team in** | Kept |
| `.github/rulesets/main-protection.json` | Branch protection to import | Kept |
| `.github/pull_request_template.md` | Records AI use, the risk tier and the human owner | Kept |
| `.vscode/settings.json`, `.vscode/mcp.json` | No auto-approve; no MCP servers until reviewed | Kept |
| `GLOSSARY.md`, `CODING_STANDARDS.md`, `docs/adr/0000-template.md` | Shared language, review standards, decision records | Kept |

## Guides and sensors

| | Guides: steer before | Sensors: catch after |
|---|---|---|
| **On the developer's machine** | Instructions, skills, role agents | Tests, linters, the guard hook |
| **On the server** | Org-level agents | CI, required checks, code owners, secret scanning, CodeQL |

**Only what's on the server can't be skipped.** That's where anything that must always hold goes.

## The guard hook

`.github/hooks/laya-guard.json` runs before each tool call. It blocks force-pushes, hard resets, `--no-verify`, piping downloads into a shell, destructive SQL and cloud commands, reading secret files, and writing what look like secrets, PPSNs or Irish IBANs. One table of patterns drives a PowerShell script and a POSIX shell script, and `tests/test_harness.py` runs both against the same payloads.

**It's a second layer, not a wall:**

- A crash denies the call, but a **timeout allows it** (GitHub's design).
- Visual Studio and JetBrains don't run hooks. VS Code support is in preview.
- The cloud agent reads hooks only from the default branch, and runs only the `bash` command.
- **PowerShell execution policy:** on a machine set to `Restricted` or `AllSigned`, the script can't run, so every tool call is denied. Sign the script, or agree a policy with IT.

To change what it blocks, edit `laya-guard-patterns.txt` in this kit, add a case to `tests/test_harness.py`, and re-install.

## Sharing across Laya

**Default: copy into each repo**, as above. It's pinned by Git, reviewed in a pull request, and it reaches every Copilot surface.

**Optional: the private plugin marketplace.** This library's repo is already set up as one: `.github/plugin/marketplace.json` points at `technical/skills-and-agents/`. Once it's in Laya's GitHub organisation:

```text
copilot plugin marketplace add <laya-org>/laya-adlc
copilot plugin install laya-engineering@laya-adlc
```

People need read access to the repo. In VS Code, see [agent plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins), where marketplace settings are marked experimental. Use one source or the other: a project's own skill wins over a plugin's with the same name. **[Not yet tested in real Copilot.]**

Admins can make it the default with enterprise managed settings. See the [org admin checklist](org-admin-checklist.md).

## What isn't tested

This kit has been tested with automated checks only: GitHub's skill validator, both hook scripts, the installer on a scratch repo, and the scan. **It hasn't run in a real Copilot session or a real GitHub organisation.** The `harness-setup` skill's step 4 is the proof that it works in your repo.
