---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
license: MIT
metadata:
  source: mattpocock/skills@4ae2317
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Read and follow the `tdd` skill (`../tdd/SKILL.md`) where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, read and follow the `code-review` skill (`../code-review/SKILL.md`) to review the work.

Commit your work to the current branch.
