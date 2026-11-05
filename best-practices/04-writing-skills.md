# Writing skills and agents

How to add or change a Laya agent so it works well for people who aren't experts. The house style is Matt Pocock's *writing-for-agents* method, applied to Laya's limits. His skill is in `technical/skills-and-agents/skills/writing-for-agents/`.

`python tools/validate_skills.py` (from `technical/platform`) checks the mechanical rules. The rest is judgement, so have someone who will really use it review each new skill.

## Anatomy of a staff agent

```text
non-technical/
  shared/
    laya-preamble.md          sent to every agent: how every Laya agent works
    pii-guard.md              sent to agents with adlc-data-guard: "true"
  everyone/  or  paid-licence/
    skills/<skill-id>/
      SKILL.md                frontmatter + body (the agent's instructions)
      references/             optional: longer examples (not sent to Copilot)
    agents/<agent-id>/
      agent.yaml              name, description, capabilities, starters, staff guide text
technical/platform/catalog.yaml   one entry per skill: id, tier, agent, batch, category, audience
GLOSSARY.md                   the shared language: use its terms, add new ones there first
```

The `SKILL.md` format follows the open [Agent Skills](https://agentskills.io/specification) standard, used by GitHub Copilot (`.github/skills/`) and Microsoft's agents.

**Which tier?** An agent goes in `everyone/` unless it needs something only the paid licence has: email, Teams messages, meetings, people or SharePoint. The validator enforces this. See the [licence table](../non-technical/admin/licences.md).

## Frontmatter

```yaml
---
name: excel-expert                   # = folder name, lower-case-with-hyphens, max 64 characters
description: >-                      # max 1,024 characters; what it does + "Use when ..."
  A senior Excel expert for any workbook... Use when someone uploads an .xlsx and wants to...
license: Proprietary - Laya Healthcare internal use
metadata:                            # values must be strings
  adlc-category: excel               # start | excel | documents | communication | planning | governance
  adlc-batch: A                      # rollout batch: A, B or C
  adlc-version: 2.1.0
  adlc-data-guard: "true"            # optional: adds shared/pii-guard.md
  m365-agent: laya-excel-expert      # folder under agents/
---
```

The description is a **context pointer**: Copilot reads it to decide when to load the skill. So:

- Write it in the third person and front-load what the skill does.
- List the **branches** that should trigger it, in the words people really say: "why is this total wrong?", "make me a tracker".
- Give one trigger per branch. Synonyms for the same branch are wasted words.

## Body: required sections, in this order

1. `## Role and goal`: who the agent is and what success looks like, in 2-3 sentences.
2. `## When to use`: the jobs it does, plus "Not for:" with the agent to use instead.
3. `## What to ask for`: what it needs to know, as rounds (the preamble says how to ask).
4. `## Steps`: numbered, with **STOP** wherever it must wait for the person (at least one), and **Done when** on the steps where rushing would hurt (at least one).
5. `## Output format`: exactly what the reply and any file look like.
6. `## Guardrails`: the hard limits: privacy, honesty, escalation.
7. `## Carrying on from an uploaded file`: how it resumes, since agents have no memory between chats.

## The budget

Agent instructions are limited to 8,000 characters. Each agent gets the preamble (about 1,770 characters), the PII guard if set (about 1,240), and the skill body. So a body can be about **5,000 characters with the guard** and **6,200 without**. The validator prints every agent's total.

[Microsoft warns](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions) against moving instructions into SharePoint to get around the limit: knowledge isn't treated as trusted instructions, and anyone who can edit that document could change how the agent behaves. Microsoft's skill packages allow up to 20,000 characters, but they need a licence or pay-as-you-go to add, so Laya's shared agents don't rely on them yet.

## The house style: seven levers

**1. The preamble is the single source of truth.** It already says how to ask (rounds of up to 3 questions with suggested answers; "yes" accepts all), when to just act, how to hand over files, how to end ("What next?"), how to handle personal data, and that facts come from the person. A skill never restates these. Restating wastes budget, and when the preamble changes, the copy goes stale. The validator rejects skills that restate the question style.

**2. Every risky step ends on a completion criterion.** "Done when..." tells the agent when the work is really finished. Without it, the agent stops at the first plausible answer. Make criteria **checkable** and **demanding**:

- "Done when original rows = clean rows + removed rows" beats "check the counts".
- "Done when every requirement is covered by at least one story" beats "write stories".

**3. Leading words.** A leading word is a compact idea the model already knows, which anchors a whole behaviour in a few tokens. Reuse the ones below before inventing new ones, and use each one the same way every time:

| Word | Means | Used in |
|---|---|---|
| snapshot / diff | record every cell and formula before; compare after | Excel Expert |
| red check | one row or cell where the answer is known to be wrong, used to prove the cause and the fix | Excel Expert, Explainer, SharePoint |
| grain | what one row stands for | Excel Builder |
| design tree / rounds | questions that depend on earlier answers wait for the next round | Idea Refiner, preamble |
| premise check | the 3-4 things an idea depends on being true | Idea Refiner |
| tracer bullet | the smallest version that runs end to end | Idea Refiner, Requirements Writer, Project Planner |
| one-way / two-way door | a decision that is hard / easy to undo | Idea Refiner, Requirements Writer |
| bottom line first | the main point or ask in the first two lines | Comms Writer, Summariser |
| two separate checks | review on two axes, reported separately so one can't hide the other | Comms Writer |
| reader test | re-read as the named reader and list what they'd still ask | Document Co-author |
| ask about the send | for a questionnaire, ask who it's for and what's needed back, not about the subject | Document Co-author |
| ghost deck | headline titles that tell the story on their own | Presentation Builder |
| SIPOC / waste | scope a process; spot waiting, hand-offs, re-typing, rework | Process & SOP Builder |
| so what | the meaning of a number for the reader's decision | Excel Insights |

**4. Prompt the positive.** State the behaviour you want ("change only what was asked: styles, order and layout stay as they were"). Microsoft gives the same advice: focus on what Copilot should do, not what to avoid. Keep "never" for hard guardrails you can't phrase positively, and pair it with the positive target.

**5. Prune no-ops.** Cut any sentence the model would obey anyway: "be helpful", "read the document carefully". The test is whether removing it changes behaviour. Delete the whole sentence, not just some of its words.

**6. Spend the budget on expertise, not etiquette.** Give it to the knowledge the model lacks or gets wrong:

- how openpyxl breaks references
- Irish date order, Eircode and phone formats
- PPSN check letters
- Laya's words (`GLOSSARY.md`)
- the order to test likely causes in

That's what makes an agent an expert, not a polite generalist.

**7. Make the file the memory.**

- Workbooks use the `_ADLC` sheet ([the continuity pattern](../technical/platform/docs/excel-continuity-pattern.md)).
- Documents end with an **ADLC Record**: Document | Version | Status | Owner | Last updated | Decisions so far | Open questions | Next step.

## Microsoft's advice that fits this

From [Write effective instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions):

- **Structure carries meaning.** Use sections for groups of tasks, bullets for parallel ones, and numbered steps only when order matters.
- **Make steps atomic,** each with a goal, an action and a way to know it's done. Our "Done when" is the transition Microsoft asks for.
- **Always specify tone and format.** Our `## Output format` section is the output contract.
- **Name the capability** where a step uses it: "use code interpreter to..."
- **Add a self-check** before the reply where completeness matters.
- **Expect drift.** Copilot's models change automatically, so re-test important agents.

## Rules for non-expert users

These live in the preamble and apply to every agent. Don't contradict them:

- Plain Irish/UK English, €, DD/MM/YYYY, Laya's words used consistently. Explain any needed term in brackets.
- **Ask in rounds:** up to 3 numbered questions, each with a suggested answer, worded so "yes" accepts it.
- **Finding facts is the agent's job; decisions are the person's.** Read the chat and the file before asking anything.
- Clear request and nothing lost: **just do it** and show what changed. Ask first only when it's ambiguous or destructive.
- "I don't follow" gets a **re-pitch**: context, plainer words, one example.
- Every file handoff says to download it before closing the chat, and how to save it. Every reply ends with **What next?** and 2-3 options.
- Personal data is protected, never refused. Facts, figures and policies come from the person or their files; gaps are `[to confirm]`.
- Hand over to the right sibling agent with a ready-to-paste prompt.

## Agents that read people's work

Paid-tier agents can read email, Teams and SharePoint. They need extra rules:

- **What they read is material, not instructions.** Say so in the guardrails: an email can't tell the agent what to do.
- **They only propose.** They draft; the person sends.
- **Every statement links to its source.**
- **They describe; they don't judge people.**
- **They say what they couldn't reach.**
- **They get the `discourage_model_knowledge` setting** when they should answer only from their sources (`ground_only_in_knowledge: true` in `agent.yaml`).

## Trust is earned

Borrowing from how others manage skills, an agent or skill has a status:

- **Provisional:** one team uses it on real tasks.
- **Trusted:** it has worked on real work, and a person has said so.

An agent failing because the environment was wrong doesn't count against it. An agent giving wrong instructions does. No agent rewrites itself: changes go through a person and a review.

A good skill also says when **not** to use it (the "Not for:" line), so it doesn't trigger on the wrong job.

## Workflow for a change

Developers should follow the `adlc-agent-author` skill in this repo's `.github/skills/`.

1. Edit `SKILL.md` (and `agent.yaml` if the name, description, starters or staff text change).
2. `python tools/validate_skills.py`. Fix anything it reports.
3. `python tools/build_agents.py`, then `python tools/build_guides.py`.
4. `python -m pytest`.
5. Try it: build a test agent from `ready-to-use/agents/<tier>/<agent>/agent-builder.md`, and run the starters plus three awkward requests: a vague ask, the wrong file, and personal data pasted in. Check that the agent asks in rounds, and that "yes" moves it on.
6. Bump `adlc-version`, and update the live agent. Agents in the catalog may need resubmitting.
7. If you find a mistake the validator could catch, add a check to `validate_skills.py` rather than a sentence here.
