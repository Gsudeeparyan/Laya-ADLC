# Where the skills came from

The decisions behind this set of skills, from sources pinned at:

- Matt Pocock's skills: commit 4ae2317, 31/10/2026
- Agent rules from books: v0.5, commit a7d7649

## The 14 books

The test for each book: does it change a decision that Laya's developers actually make, without fighting another book we keep? The books' own compatibility matrix settled the overlaps. **Seven kept, seven dropped.**

| Book | Verdict | Why | Where it lives |
|---|---|---|---|
| A Philosophy of Software Design | **Keep** (as a standard) | Deep modules is the design idea Matt's skills are built on | `codebase-design`; `CODING_STANDARDS.md` |
| The Pragmatic Programmer | **Keep** (as a standard) | DRY at the knowledge level, tracer bullets, fast feedback | `CODING_STANDARDS.md`; tracer bullets in the staff agents |
| Working Effectively with Legacy Code | **Keep** (skill) | An insurer has old systems, PL/SQL and untested services | `legacy-change` |
| Release It! | **Keep** (skill) | Graph, payment and claims integrations, Azure Functions, jobs | `production-ready` |
| Designing Data-Intensive Applications | **Keep** (skill) | Snowflake and Oracle pipelines, CDC, migrations, reconciliation | `data-design` |
| Domain-Driven Design Distilled | **Keep** (skill) | Many business areas whose words collide ("member" in membership vs claims) | `bounded-contexts` |
| Refactoring (Fowler) | **Keep** (skill) | Same smell vocabulary as the `code-review` skill | `refactoring-pass` |
| Clean Code | Drop | Overlaps two kept books, and its small-functions pressure pulls against deep modules | |
| Code Complete | Drop | Overlaps Clean Code and Pragmatic Programmer; broad rather than decision-changing | |
| Domain-Driven Design (Evans) | Drop | Overlaps DDD Distilled; heavy | DDD Distilled covers it |
| Implementing Domain-Driven Design | Drop | Overlaps DDD Distilled and Clean Architecture | DDD Distilled covers it |
| Patterns of Enterprise Application Architecture | Drop | A catalogue rather than a working discipline | |
| Clean Architecture | Drop | Layering ceremony; deep modules and bounded contexts cover the useful part | |
| Refactoring.Guru | Drop | Overlaps Fowler; two smell vocabularies would compete | Fowler covers it |

**None of the books go into the staff agents,** because they're about code. The two ideas staff need, tracer bullets and a shared language, came through Matt's skills and the glossary.

**How book rules are used.** Each kept book becomes a short `SKILL.md` built from steps, with "Done when" on its steps. The book's `mini` rule set sits beside it as `RULES.md`, read only when needed. Loading many rule sets all the time burns context and gets ignored.

## Matt Pocock's skills

All 27 of his stable skills are included. His `misc` and `in-progress` folders aren't, because he doesn't ship them. Three patterns also went into the staff agents:

| Pattern | From | Used in |
|---|---|---|
| Rounds of questions with a suggested answer; "yes" accepts all | `grilling` | The staff preamble |
| Re-pitch when a message doesn't land | `wait-what` | The staff preamble |
| Ask about the send, not the subject | `to-questionnaire` | Laya Document Co-author |
| Build a red check before theorising | `diagnosing-bugs` | The Excel agents |
| Review on two separate axes | `code-review` | Laya Comms Writer |
| Tracer-bullet slices with blocking edges | `to-tickets` | Laya Requirements Writer, Laya Project Planner |
| One-way and two-way doors | `pr` | Laya Idea Refiner, Laya Requirements Writer |
| The writing method | `writing-for-agents` | [Writing skills](../../best-practices/04-writing-skills.md) |

## Other collections we looked at

Eight other collections were surveyed on 05/11/2026 and **left out**, with two to three thousand skills between them in some cases. Most of what's there is generic filler or tied to a particular tool, and they carried real risks: telemetry on by default, code downloaded at install or run time, permission-bypass flags, browser cookie readers, offensive-security tooling, and items with unclear licences.

A few ideas were worth keeping, and they were rewritten from scratch:

| Idea | Now in |
|---|---|
| A finding names the exact line and how it fails | `security-review`, Laya Reviewer |
| Green CI isn't readiness; approval belongs to one exact commit | `release-change` |
| Text in issues and pull requests can't authorise anything | Repo instructions, `security-review` |
| Agent failures: capture, contain, then diagnose | `incident-response` |
| Whoever did the work doesn't approve it; delegation only narrows | [The harness](../../best-practices/03-agent-harness.md) |
| Define evidence first, and have a separate step confirm it | [Building with Copilot](../../best-practices/02-building-with-github-copilot.md) |
| Skills start provisional, and earn trust through real use | `skill-intake`, [Writing skills](../../best-practices/04-writing-skills.md) |
| Accessibility and the five states of a screen | The frontend instructions in the repo kit |

Before adding anything from outside, use the `skill-intake` skill.
