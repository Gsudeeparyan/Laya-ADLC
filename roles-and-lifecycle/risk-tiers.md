# Risk tiers: how much oversight does this need?

Not all AI use needs the same care. Rewording your own email and supporting a claims decision are very different. EIOPA calls this proportionality: simple checks where the impact is small, and much more where it could harm people or the business.

**Pick the highest tier that fits. If you're unsure, go one higher and ask.**

**Status: draft for Compliance, DPO and AI owner review [to confirm].** The tiers are Laya's own scheme, not a legal classification.

## The four tiers

| Tier | What it is | Everyday examples | Technical examples |
|---|---|---|---|
| **T0: Just for me** | Only you see it, and you use it as a starting point | Summarise a public article; brainstorm; explain a formula | Explain unfamiliar code; a throwaway prototype on your machine |
| **T1: Inside Laya, no personal data** | Others at Laya rely on it, and no one's personal data is involved | An internal update; a process guide; a report with no personal data | An internal tool with no personal data; a test; a refactor with tests |
| **T2: People or the outside world** | It uses personal data, goes outside Laya, or could affect members or the business | A member letter; anything with personal data; a marketing piece; a figure for a board paper | Code that handles member data; anything in production; a data pipeline |
| **T3: Decisions about people, or critical to the business** | It affects what happens to a person, or Laya's finances or legal position | AI feeding into a claim, complaint, job or performance decision; a regulatory submission | AI features that assess or decide; pricing; reserving; a service whose failure would stop the business |

## What each tier needs

| | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| **Accountable person** | You | You | Named owner | Named owner, with the business owner |
| **Check the output** | You | You, against the source | You, plus a second person | Independent validation by someone who didn't build it |
| **Personal data** | Avoid | None, by definition | Cleaned first where you can. New uses go through the Laya Privacy & AI Check | DPO involved; DPIA likely |
| **AI use register** | No | If it's a regular team use | Yes | Yes, before work starts |
| **Sign-off before use** | None | None | Your manager or code owner, plus your team's normal approval | AI owner, Compliance and DPO, plus the actuarial function if it touches pricing or reserving |
| **Can AI act by itself?** | Fine, it's only you | Fine, if a person reviews before others rely on it | No. A person reviews everything before it takes effect | No. A person decides, and can explain the decision |
| **Cloud agent for code** | Yes | Yes | Only with tests and code-owner review | Not for the sensitive part |

## How to tell T2 from T3

Ask: **"Could this change what happens to a particular person, or materially affect Laya's finances or legal position?"**

- A claims team uses AI to *rewrite a letter* after a person has decided. **T2.**
- A claims team uses AI to *suggest whether to pay*. **T3,** even if a person clicks approve at the end, because people tend to go along with what AI suggests.

## What the EU AI Act says

Some uses are defined by law, and they're at least T3:

- **AI for risk assessment and pricing of people in life and health insurance** is listed as high-risk (Annex III, point 5(c)).
- **AI in hiring, promotion and evaluating staff** is listed as high-risk too (Annex III).

The high-risk duties now apply from **2 December 2027**, after the Digital Omnibus (Regulation (EU) 2026/1744). Other duties already apply, including AI literacy (Article 4), since 2 February 2025. How these apply to Laya is for Compliance to confirm. See [regulation](../best-practices/07-regulation.md).

## The factors that raise a tier

These come from EIOPA's paragraphs on assessing impact (3.3 and 3.4):

- Large-scale processing, or sensitive data such as health data
- Many people affected, especially vulnerable people
- How autonomously the AI acts
- Customer-facing, rather than purely internal
- Possible harm to someone, including discrimination
- Importance to business continuity or Laya's finances
- Reputational risk

## Not sure?

Use the **Laya Privacy & AI Check**, or the `ai-feature-check` skill if you're a developer, or ask the AI owner.
