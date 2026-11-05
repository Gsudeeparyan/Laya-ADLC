# Working in this library (for people and coding agents)

Laya-ADLC is Laya Healthcare's AI library. Read `README.md` first. These rules keep it working.

## Golden rules

1. **Only Microsoft Copilot and GitHub Copilot.** Nothing shared here depends on, or names, another AI coding tool. `tools/check_library.py` enforces this.
2. **Skills are the source of truth.** Never edit anything in `non-technical/ready-to-use/` by hand. Change the source, then rebuild.
3. **Never put real member, customer or staff data** in skills, templates, tests or examples. Use obviously made-up examples.
4. **Every staff agent must fit 8,000 characters** (preamble + guard + skill). `validate_skills.py` enforces this.
5. **The licence boundary is a rule.** An agent in `everyone/` can't use SharePoint, email, Teams, meetings or people. `validate_skills.py` enforces this.
6. **Users aren't experts.** Follow `best-practices/04-writing-skills.md`: questions in rounds with suggested answers, a STOP before anything destructive, "Done when" on risky steps, plain Irish/UK English in Laya's words (`GLOSSARY.md`), facts only from the person.
7. **The workbook format is a contract.** `technical/platform/docs/excel-continuity-pattern.md`, `src/adlc_workbook/` and the Excel skills must agree. Change them together, and add a test.
8. **Third-party content is code.** It comes in through the `skill-intake` skill, pinned to a commit. Matt Pocock's skills are changed only through `tools/vendor_matt_skills.py`.
9. **Facts have sources.** Add them to `best-practices/sources.md` with the date checked. Where sources disagree, say so. What only Laya can decide is marked `[to confirm]`.

## Where things are

- Staff agents (`non-technical/`): follow the `adlc-agent-author` skill in `.github/skills/`.
- Developer skills and role agents: `technical/skills-and-agents/`. Their tests: `tests/test_developer_skills.py`.
- The repo kit: `technical/harness/repo-kit/`. Its tests: `tests/test_harness.py`.
- Every folder location: `technical/platform/tools/paths.py`.
- PII engine (`src/adlc_pii/`) and anything handling member data: the `member-data-safety` skill.
- SharePoint backend (`backend/`, Microsoft Graph): the `production-ready` skill.

## Commands

Run from `technical/platform`:

```text
python -m pytest                      # must pass before any change is merged
python tools/validate_skills.py       # skill rules, size budget, licence boundary
python tools/check_library.py         # other tools, hidden text, personal data, links, stale paths
python tools/build_agents.py          # agent packs -> ready-to-use/agents
python tools/build_templates.py       # templates -> ready-to-use/templates (validated)
python tools/build_guides.py          # staff pages + the Word guides
powershell -File tools/excel_check.ps1 ../../non-technical/ready-to-use/templates/*.xlsx   # real Excel
powershell -File tools/word_check.ps1 ../../non-technical/ready-to-use/*.docx              # real Word
gh skill publish ../skills-and-agents --dry-run   # GitHub's own skill validator
```

## Adding a staff agent

1. Choose the tier: `everyone/` unless it needs what only the paid licence has.
2. Create `<tier>/skills/<id>/SKILL.md` (see `best-practices/04-writing-skills.md`).
3. Add `<tier>/agents/laya-<name>/agent.yaml`: name, description, capabilities, 1-12 starters, and a `staff_guide` block.
4. Add the entry to `technical/platform/catalog.yaml`, and to the agent map in `everyone/skills/start-here/SKILL.md`.
5. Add it to `staff-guide/getting-started.md`, and to the playbooks where it fits.
6. Validate, build and test, then run the smoke test in Copilot before sharing.

## Engine code style

- Python 3.10+, standard library plus openpyxl and PyYAML only.
- Error messages are read by non-experts through the agents: say what's wrong and what to do, in plain words.
- Every change operation is atomic: validate everything on a copy, then write.
- Any formula written to a file uses the file form of structured references (`tbl[[#This Row],[Col]]`), never `[@Col]`.
