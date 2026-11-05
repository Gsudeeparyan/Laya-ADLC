---
name: legacy-change
description: Change code that has no trustworthy tests without breaking what depends on it. Use when the user wants to modify legacy code, untested or poorly understood code, an old service, stored procedures or PL/SQL, or when a change is risky because behaviour is unclear.
license: Proprietary - Laya Healthcare internal use
---

# Legacy Change

Any code without trustworthy tests is **legacy**, whatever its age. The aim is to gain control before improving design: pin what must stay, open the smallest **seam**, make the requested change, and leave the area easier to test. Full rule set (Michael Feathers, _Working Effectively with Legacy Code_): [RULES.md](RULES.md). Read it when a dependency blocks testing and the steps below don't name the technique you need.

When exploring, read `GLOSSARY.md` and the ADRs in the area (if they exist), so tests and names use the domain's words.

## The legacy loop

1. **Change point.** Name the exact place the behaviour must change, and state two things: the **behaviour delta** (what will be different) and the **behaviour to preserve** (what callers rely on, including the ugly parts). Done when both are written down and the user agrees.

2. **Characterise.** Write **characterisation tests** that pin current behaviour at the nearest point you can observe it, odd results included (assert what the code _does_, not what it should do). Done when they pass against the unchanged code and would fail if the preserved behaviour broke. Prove that: mutate the line under test once and watch one go red.

3. **Seam.** Find or create the smallest seam that lets a test sense or substitute what it needs. Break only the dependency that blocks the test: constructor work, a global, a static call, time, the network, the database. Say whether the seam is for sensing, separation, or both.

4. **Change.** Make the behaviour change test-first. Read and follow the `tdd` skill (`../tdd/SKILL.md`) for the loop. When editing in place is risky, add the new behaviour beside the old: **sprout** (a new method or class called from the old code) or **wrap** (a new method around the old one).

5. **Refactor locally.** Only now, and only inside the area you characterised, with tests green after every step. Keep behaviour changes, refactoring and cleanup in separate commits.

6. **Leave a trail.** Any temporary seam, public-for-test member or subclass trick gets a cleanup note (an issue or a `TODO(legacy-seam)` comment).

The loop is done when the characterisation tests and the new tests all pass, the diff separates behaviour from structure, and every temporary seam has a cleanup note.

## Steer away from

- a rewrite or module-wide cleanup when the request is one behaviour change
- mocking around untestable structure instead of opening a seam
- renaming and reformatting while the real dependency knot stays tied
