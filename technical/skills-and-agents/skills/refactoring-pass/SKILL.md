---
name: refactoring-pass
description: Improve code structure in small, behaviour-preserving steps. Use when the user asks to refactor, clean up, simplify or restructure code, or acts on code smells raised in a review.
license: Proprietary - Laya Healthcare internal use
---

# Refactoring Pass

Refactoring changes structure, never behaviour, in steps small enough that the tests stay green after each one. Full rule set (Martin Fowler, _Refactoring_): [RULES.md](RULES.md), for the smell catalogue and the named refactorings.

## Steps

1. **Protection.** Run the tests that cover the code. If none cover it, it is legacy: read and follow the `legacy-change` skill (`../legacy-change/SKILL.md`) and characterise it first. Done when a green test run covers every behaviour you are about to restructure.
2. **Scope.** Agree with the user which smells to treat and where to stop. Name each smell with Fowler's terms (Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Shotgun Surgery, Divergent Change, Speculative Generality...), so the plan reads as a list of known moves.
3. **One move at a time.** Apply one named refactoring (Extract Function, Move Function, Introduce Parameter Object, Replace Primitive with Object, Inline...) and run the tests. Green: commit or checkpoint. Red: undo the move rather than debugging forward.
4. **Deepen, don't scatter.** Prefer moves that put more behaviour behind a smaller interface. When the question is module shape, read and follow the `codebase-design` skill (`../codebase-design/SKILL.md`), which has the deep-module vocabulary.
5. **Stop at the scope.** Note new smells you find for later rather than chasing them.

Done when every agreed smell is treated, the tests were green after every step, and the diff contains no behaviour change. A behaviour change found along the way goes in its own commit, with its own test.
