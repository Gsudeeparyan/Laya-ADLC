# The lifecycle

ADLC stands for **Agentic Development Life Cycle**: how work moves from an idea to something in use, with AI doing much of it and people answerable at each step. It runs at two speeds.

## For everyday work: draft, check, use

Most AI use at Laya is an email, a summary or a spreadsheet. This doesn't need stages.

1. **Ask.** Give Copilot the goal, the context, the source and what you expect.
2. **Check.** Read it and test the facts against the source. The more it matters, the harder you check.
3. **Decide.** You choose whether to use it. If it's your name on it, it's yours.

This covers T0 and T1 in the [risk tiers](risk-tiers.md). For T2, add a second person.

## For anything bigger: eight stages

For a new process, tool, system or anything built with AI.

| Stage | What happens | Non-technical tools | Technical tools | Gate: done when |
|---|---|---|---|---|
| **1. Idea** | Is it worth doing? | Laya Idea Refiner, Laya Privacy & AI Check | `/grill-with-docs`, `ai-feature-check` | Named owner; risk tier set; on the register if needed |
| **2. Spec** | What exactly do we need? | Laya Requirements Writer | `/to-spec`, `/to-tickets` | Testable requirements, agreed by the business owner |
| **3. Design** | How will it work, and what could go wrong? | Laya Process & SOP Builder | `bounded-contexts`, `data-design`, `member-data-safety` | Risks named; one-way decisions recorded and signed off; DPIA done if needed |
| **4. Build** | Make it, in small slices | Laya agents | `/implement`, `/tdd`, role agents | Small change, one ticket; tests written first |
| **5. Verify** | Does it really work? | Laya Second Check | `/code-review`, `test-strategy`, `security-review` | Someone other than the author checked it, against the spec |
| **6. Release** | Put it into use, with a way back | Laya Comms Writer, the staff guide | `release-change`, `/pr` | Approved by a named person; rollback ready; people told |
| **7. Operate** | Run it and watch it | Laya Project Planner | `production-ready`, `incident-response` | A named owner; signals watched; incidents have a route |
| **8. Learn** | Make it better | Laya Agile Coach | `/retro`, `harness-setup` | Lessons become checks or better instructions; register updated |

**Going round again is normal.** A small change returns to stage 2, not stage 1.

## What AI does and doesn't do at each stage

| Stage | AI can | A person must |
|---|---|---|
| Idea | Challenge the idea, ask questions, find facts | Decide whether it's worth doing |
| Spec | Draft requirements, spot gaps | Agree what's needed |
| Design | Offer options, find risks | Choose, and own decisions that are hard to undo |
| Build | Do the bulk of the work | Stay in charge of scope, and read what's produced |
| Verify | Run tests, review from a fresh start | Decide it's good enough, and approve it |
| Release | Prepare the evidence and the notes | Approve the release |
| Operate | Watch signals, draft updates | Decide what to do in an incident |
| Learn | Suggest what would have prevented it | Choose what changes |

## Three brakes

Every bit of automation speeds work up. It needs brakes that keep up, or you just produce mistakes faster. Matt Pocock describes three, and all of them are needed:

1. **Automated checks:** deterministic tests that every change must pass.
2. **Automated review:** a separate, fresh look at the change.
3. **Human review:** a person reads it before it takes effect. What they catch becomes new automated checks.

Add automation one step at a time, and let it earn more freedom as the brakes earn trust.

## Records to keep

| Record | Where | Who |
|---|---|---|
| AI use | The AI use register | The AI owner, with each use's owner |
| Decisions that are hard to undo | Decision records (ADRs), or the document's ADLC Record | The owner |
| What changed, and who approved it | Git history, pull requests, the change record | The author and the approver |
| Workbook changes | The workbook's own Change Log | Filled in by the Excel agents |
| Incidents | The incident log and review | The incident lead |

EIOPA expects records good enough for reproducibility and traceability, in proportion to the risk (paragraphs 3.22 to 3.24).
