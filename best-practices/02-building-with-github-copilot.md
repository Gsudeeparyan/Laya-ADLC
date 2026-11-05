# Building with GitHub Copilot

**For developers.** Most of Laya's code will be written with AI, so the job shifts: less typing, more deciding what to build and reviewing what comes back.

## What the research says

[Google's DORA research](https://dora.dev/dora-report-2025/) on AI-assisted software development (nearly 5,000 respondents; not the EU regulation of the same name) found that **AI is an amplifier**: it magnifies the strengths of high-performing organisations and the dysfunctions of struggling ones. The [seven capabilities](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model) that amplify AI's benefits are:

| Capability | At Laya |
|---|---|
| A clear AI stance | This library, and [the rules](README.md) |
| Healthy data ecosystems | Named owners, reconciliation, the `data-design` skill |
| AI-accessible internal data | Instructions, skills, `GLOSSARY.md`, ADRs |
| Strong version control | Everything in Git, with small commits and easy rollback |
| Working in small batches | One ticket, one pull request |
| A user-centric focus | Business owners in the spec; the `grill-with-docs` skill |
| Quality internal platforms | [The harness](03-agent-harness.md) |

**So fix the basics first.** Weak tests or unclear requirements will get worse faster with AI.

## The flow

1. **Align before you build.** `/grill-with-docs`: most AI failures start with a misunderstanding, not bad code.
2. **Specify:** `/to-spec`, then `/to-tickets`, as thin end-to-end slices.
3. **Build one ticket at a time,** test first: `/implement` and `/tdd`.
4. **Review on separate axes:** `/code-review`, plus `member-data-safety` or `security-review` where they apply.
5. **Write the pull request:** `/pr`. A person owns it and reads every line.
6. **Ship with evidence:** `release-change`.
7. **Learn:** `/retro`. Turn mistakes into checks.

Type `/ask-laya` if you aren't sure where you are.

## Giving Copilot good tasks

From [GitHub's guidance for the cloud agent](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks):

- **Treat the issue as the prompt:** a clear problem, complete acceptance criteria, and which files are involved.
- **Good tasks:** well-scoped bug fixes, tests, documentation and small features with a clear finish.
- **Keep for yourself:** complex cross-cutting refactors, security or production-critical work, ambiguous requirements, and anything you're doing in order to learn.
- **Iterate in the pull request:** mention `@copilot` in review comments, batching them into one review.
- **Pre-install dependencies** with `copilot-setup-steps.yml`, so it can run the tests.

## Staying in charge

- **Keep changes small.** AI can produce huge changes quickly, and those are hard to review and test ([DORA](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model)). Review capacity is the real limit now.
- **Read every line you merge.** If you can't explain it, it isn't ready.
- **Keep context fresh.** Start a new session for each ticket. A long session gets less sharp.
- **Define evidence before the work,** then have a separate step confirm it. An agent's "done" is a claim, not a fact.
- **A passing subset isn't acceptance.** Say what ran and what didn't.
- **Stop after three failed fixes.** No fix without a root cause; escalate instead of trying a fourth (`diagnosing-bugs`).

## Tests when AI writes both sides

Code and tests written together can share one misunderstanding.

- Take expected values from the spec or a worked example, not from the code.
- See each test fail before you trust it.
- Treat any deleted, skipped or loosened test as a finding until it's explained.
- Check whether mocks replace the very thing under test.
- Use synthetic data only.

See `test-strategy`.

## Review

- **The author doesn't approve.** That's true of people and of agents ([GitHub](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations) stops its cloud agent approving its own pull requests).
- **Findings give a line and a failure:** `file:line`, the input, the wrong result.
- **Look at what AI gets wrong:** invented packages, weakened tests, scope creep, errors swallowed, comments that don't match the code.
- **Copilot code review is an extra reader,** not the approver.
- **Reviewers shift** from style, which tools can check, to behaviour, security and rollout.

## Dependencies

AI invents package names, and attackers register them, a trick known as [slopsquatting](https://fossa.com/blog/slopsquatting-ai-hallucinations-new-software-supply-chain-risk/). FOSSA reports that roughly 20% of generated code samples in one set of tests included a package that doesn't exist.

- Look up every new package on the official registry.
- Treat a new dependency as a review gate.
- Install from approved registries, and keep a lock file.
- Pin GitHub Actions to a full commit SHA.

## Old code

An insurer has old systems, PL/SQL and untested services. AI is confident about code it doesn't understand, which makes this riskier.

Use `legacy-change`: characterise what the code does now, find a seam, then change it. Don't let an agent "tidy" old code with no tests around it.

## The rules

They're in each repo's `.github/copilot-instructions.md`, and `CODING_STANDARDS.md` holds the judgement calls. See [the harness](03-agent-harness.md) for how they're enforced.
