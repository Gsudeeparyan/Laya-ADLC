---
name: test-strategy
description: Decide what to test and judge whether tests prove anything. Use when planning tests for a feature or release, reviewing tests written by AI, deciding how much testing a change needs, or when someone asks whether a change is tested enough.
license: Proprietary - Laya Healthcare internal use
---

# Test Strategy

A test answers one question: would this fail if the behaviour broke? When AI writes both the code and its tests, both can share one misunderstanding and agree with each other. So the evidence has to come from outside the code: the spec, a worked example, a person who knows the business.

For writing the tests themselves, use the `tdd` skill (`../tdd/SKILL.md`). This skill decides what's worth testing and whether the result can be trusted.

## 1. Size the risk

Find the change's risk tier in `roles-and-lifecycle/risk-tiers.md` and match the depth:

| Tier | Depth |
|---|---|
| T0-T1 | Behaviour tests on the changed path |
| T2 | Add failure paths, contract tests at each boundary, and a person checks the result against real scenarios using synthetic data |
| T3 | Add independent validation by someone who didn't build it, plus fairness and accuracy checks where people are affected |

## 2. Map the contracts

For each API, job, webhook, queue, file import and screen the change touches, write: what goes in, what comes out, what happens on failure, and who depends on it. Jobs and pipelines also need: what happens when it runs twice, runs late, or receives nothing.

Done when every boundary has a line in the map and each line has a test or a written reason why not.

## 3. Derive tests from the spec

Take each acceptance criterion and write down the expected result **before** reading the implementation, from the spec or a worked example. An expected value calculated the way the code calculates it proves nothing.

## 4. Prove each test can fail

A test you've never seen fail may not be testing anything. See it go red: write it first, or break the code temporarily and watch it fail.

Done when every acceptance criterion maps to a test you've seen fail, or to a written reason why no such test exists.

## 5. Review AI-written tests for these smells

- It asserts what the code does, not what the spec says.
- It mocks the thing under test, so nothing real runs.
- A test was deleted, skipped or loosened in the same change that altered behaviour. Treat this as a finding until explained.
- A snapshot was regenerated with no reason given.
- It covers only the happy path.
- It needs the implementation's internals, so a refactor would break it.

## 6. Include Laya's awkward cases

Use synthetic data only (`member-data-safety`, `../member-data-safety/SKILL.md`):

- Day-first dates, 29 February, and month-end boundaries.
- Eircodes with and without the space; leading zeros in IDs and phone numbers.
- Names with fadas and apostrophes: Ó Briain, O'Neill, Máire.
- € rounding, and totals that must reconcile.
- Dependants on a policy, group schemes, lapsed and reinstated cover, and backdated changes.
- Empty results and groups smaller than 5 in reports.

## 7. Report

Give a table of acceptance criterion, test and whether it's been seen failing. Then list gaps, each with its risk and a recommendation. A passing subset is not acceptance: say what didn't run.
