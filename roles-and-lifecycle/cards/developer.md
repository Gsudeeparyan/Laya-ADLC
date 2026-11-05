# Developer

Anyone writing code with GitHub Copilot. Much of the typing is now done by agents, and your job moves to steering and reviewing.

## What you own

- Every line you merge, whoever or whatever wrote it. You read it all, and you can explain it.
- Keeping changes small: one ticket, one pull request.
- Tests that prove the behaviour.
- Saying what you ran and what you didn't.

## What AI can do for you

- Write code and tests, from a clear ticket.
- Explain unfamiliar code.
- Refactor in small green steps.
- Draft the pull request.

## What you must not hand over

- Deciding what to build, and the design of anything hard to undo.
- Approving your own work.
- Checking that a dependency is real and is the one intended.
- Anything touching production.

## Your tools

- `/ask-laya` and the role agents.
- `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`, `/tdd`, `/code-review`, `/pr`.
- `member-data-safety`, `legacy-change`, `production-ready`.

## The evidence you leave

- The pull request, which records AI use, the risk tier and you as the human owner.
- Tests and CI results.

## Watch out for

- Huge changes from AI, which nobody can review well.
- Tests weakened or removed to get to green.
- Packages AI invented.
