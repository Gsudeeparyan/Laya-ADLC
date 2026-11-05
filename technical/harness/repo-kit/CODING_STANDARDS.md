# Coding standards

Read at **review** time, by the `code-review` skill (its Standards axis) and by human reviewers. It is not loaded during implementation.

Mechanical rules belong in a linter, a test or a CI job, not here. This file holds the judgement calls no tool can make. When a rule here keeps being broken the same way, turn it into a check and delete it from this file.

Add this repo's own standards under **Repo-specific** at the end. The installer keeps your changes.

## Laya rules (hard: a breach blocks merge)

1. **Member data stays out of logs, errors, analytics and fixtures.** Log internal IDs or tokens. Fixtures are synthetic, and `.github/scripts/laya_scan.py` finds nothing in them. See the `member-data-safety` skill.
2. **Queries on member, policy and claim data name their columns.** No `SELECT *`. Reports suppress groups smaller than 5.
3. **Secrets live in Key Vault (or the platform's secret store).** Never in code, config files, test data or pipeline YAML.
4. **Every outbound call has an explicit timeout.** Retries are bounded, backed off, and only on safe operations. See the `production-ready` skill.
5. **Jobs and pipeline steps are safe to run twice.** See the `data-design` skill.
6. **Domain names come from `GLOSSARY.md`.** Say `member` or `policyholder`, not `customer`. Say `pseudonymised` when a key exists.

## Design (judgement calls; label them "possible...")

- **Deep modules.** Prefer a small interface hiding real behaviour over many shallow pass-through layers. (Ousterhout, _A Philosophy of Software Design_; the `codebase-design` skill)
- **One owner per fact.** A business rule, mapping, status meaning or calculation lives in one place, and everything else derives from it. (Hunt & Thomas, _The Pragmatic Programmer_)
- **Translate at boundaries.** Another system's model is translated where it enters, not passed through the domain. (Vernon, _DDD Distilled_; the `bounded-contexts` skill)
- **Separate behaviour from structure.** A refactor and a behaviour change go in separate commits. (Fowler, _Refactoring_)
- **Characterise before changing untested code.** (Feathers, _Working Effectively with Legacy Code_; the `legacy-change` skill)
- **Fail visibly and inside a boundary.** Errors carry diagnostic context (without personal data) and do not cascade. (Nygard, _Release It!_)

## AI-written code (hard: a breach blocks merge)

7. **A named person owns the change.** They've read every line, and can explain it.
8. **Every new dependency has been looked up** on the official registry, and is the one intended.
9. **No test was deleted, skipped or loosened** without a reason given in the pull request.

## Tests

- Test behaviour through public interfaces. A test that breaks on a refactor with no behaviour change is coupled to the implementation.
- Expected values come from an independent source (a worked example, the spec), never recomputed the way the code computes them.
- A bug fix comes with a regression test at a seam that reproduces the real bug pattern, or a written note of why no such seam exists.

## Repo-specific

<!-- Add this repo's standards here: language idioms, framework conventions, naming. -->
