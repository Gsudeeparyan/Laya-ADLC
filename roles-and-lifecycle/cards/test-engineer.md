# Test engineer

Whoever decides what proves a change works.

## What you own

- The test strategy, by risk.
- Whether the evidence is good enough.
- Testing independently of whoever built it.

## What AI can do for you

- Generate test cases from a spec.
- Write and maintain tests.
- Find gaps in what's covered.

## What you must not hand over

- Deciding that it's good enough.
- Expected results: these come from the spec or a worked example, not from the code.

## Your tools

- `test-strategy`, `/tdd`.
- Laya Test Engineer.

## The evidence you leave

- A map of each requirement to a test seen to fail, plus known gaps.

## Watch out for

- AI writing both the code and its tests. They can share one misunderstanding.
- Synthetic data that's too tidy to catch real problems.
