# Regulation

**Status: draft for Compliance to review. This isn't legal advice.** It's a map of what we found on 05/11/2026, so that Compliance can correct it. Rules here are moving quickly. Anything marked **[to confirm]** needs a decision from Compliance or the DPO.

## Laya's position

From [Laya's terms of business](https://layahealthcare.ie/termsconditions):

- **Laya Healthcare Limited** is authorised by the Central Bank of Ireland, and registered as an insurance intermediary.
- It acts as an **agent for AXA Insurance dac**, which provides the health insurance, trading as laya healthcare.
- **Laya Life** is a separate line with its own provider, which the terms describe separately. **[Compliance to confirm]**

Why this matters: many duties below fall on "insurance undertakings". So some may sit with AXA Insurance dac or AXA Group, and group AI policies may apply here too. **[Compliance to map which duties sit where]**

## At a glance

| Rule | Why it matters | When |
|---|---|---|
| **EU AI Act** | Bans some uses; sets duties for high-risk AI, including health insurance pricing | In force in stages; see below |
| **EIOPA Opinion on AI** | How insurance rules apply to AI that isn't high-risk | Published August 2025 |
| **Central Bank of Ireland** | Laya's regulator, and the AI Act regulator for insurance | Now |
| **Consumer Protection Code 2025** | Requirements for firms using digital technology to provide financial services | Took effect March 2026 |
| **GDPR and Data Protection Act 2018** | Personal and health data | Now |
| **DORA (Digital Operational Resilience Act)** | ICT risk, incidents and third parties | Applies since January 2025 **[to confirm scope for Laya]** |

## EU AI Act

**Timing has changed.** The [Digital Omnibus on AI](https://artificialintelligenceact.eu/ai-act-explorer/digital-omnibus/), Regulation (EU) 2026/1744, entered into force on 27 July 2026.

| Date | What |
|---|---|
| 2 February 2025 | AI literacy (Article 4) and prohibited practices began to apply |
| 2 December 2026 | Providers of generative AI systems placed on the market before 2 August 2026 must meet the marking duty in Article 50(2) |
| **2 December 2027** | High-risk duties for Annex III systems. This used to be 2 August 2026 |

**Dates here come from the page above. Compliance should check them against the Official Journal.**

**High-risk for Laya's sector:** [Annex III, point 5(c)](https://artificialintelligenceact.eu/annex/3/) lists AI systems intended for "risk assessment and pricing in relation to natural persons in the case of life and health insurance". Annex III also lists AI in employment, such as recruitment and evaluating staff.

**How that applies in Ireland's community-rated health insurance market, and to Laya as an agent, needs a view from Compliance [to confirm].** Until then, Laya's [risk tiers](../roles-and-lifecycle/risk-tiers.md) treat any such use as T3.

**AI literacy:** [Article 4](https://artificialintelligenceact.eu/article/4/), as amended, requires providers and deployers to "take measures to support the development of AI literacy" of staff and others operating AI on their behalf. It doesn't require guaranteeing any particular level. [This training](../non-technical/training/README.md) supports that.

**Transparency:** people generally need to be told when they're dealing with AI. EIOPA notes this among the requirements for AI that isn't high-risk (paragraph 2.5). The details of Article 50 need Compliance's reading **[to confirm]**.

## EIOPA's Opinion on AI governance and risk management

[EIOPA-BoS-25-360](https://www.eiopa.europa.eu/document/download/88342342-a17f-4f88-842f-bf62c93012d6_en), 6 August 2025. It sets no new rules. It explains how existing insurance law (Solvency II, the Insurance Distribution Directive, DORA) applies to AI, for AI that isn't prohibited or high-risk.

**Proportionate:** assess each AI system's impact, then apply measures that fit (paragraphs 3.2 to 3.6). Impact depends on things like scale, data sensitivity, how many customers are affected, how autonomous it is, and whether it faces customers (3.3).

**Six areas to cover** (paragraph 3.7):

| Area | In short | Where in this library |
|---|---|---|
| Fairness and ethics | Treat customers fairly; remove bias, including proxy variables; monitor outcomes; offer redress (3.12-3.16) | [Risk tiers](../roles-and-lifecycle/risk-tiers.md), `ai-feature-check` |
| Data governance | Complete, accurate, appropriate data, with limitations recorded (3.17-3.21) | `data-design`, `member-data-safety` |
| Documentation and record keeping | Enough for reproducibility and traceability (3.22-3.24) | [Lifecycle records](../roles-and-lifecycle/lifecycle.md), the AI use register |
| Transparency and explainability | Meaningful explanations, adapted to the audience (3.25-3.28) | `ai-feature-check` |
| Human oversight | Clear roles, escalation, training, guardrails (3.29-3.33) | [Roles](../roles-and-lifecycle/README.md) |
| Accuracy, robustness, cybersecurity | Defined levels, metrics, resilience to attack, fall-back plans (3.34-3.38) | `production-ready`, `security-review` |

**Roles** (paragraph 3.30): the board is responsible for overall use; compliance and audit verify; the DPO verifies data protection; the actuarial function is responsible for controls in its area. Firms may appoint an AI officer or committee (3.31).

**Third parties:** firms stay responsible for AI they use, whether built in-house or bought, and should get adequate information and assurance from suppliers (3.11). That covers Microsoft and GitHub.

## Central Bank of Ireland

From the [Insurance Quarterly, March 2026](https://www.centralbank.ie/docs/default-source/regulation/industry-market-sectors/insurance-reinsurance/solvency-ii/communications/insurance-quarterly-news/the-insurance-quarterly-march-2026.pdf?sfvrsn=ec8721a_4):

**Its role:** the Irish government has designated the Central Bank as a regulator under the AI Act for financial services within its remit, including insurance. Digitalisation and AI are a focus area for its supervision.

**Four standards when deploying AI:**

1. **Strategic alignment:** the use of AI is appropriate for the specific business challenge.
2. **Accountability and explainability:** clear accountabilities and responsibility, human oversight of decisions, and explainability.
3. **Proportionate governance:** risk management in line with the scale, scope and sensitivity of the deployment.
4. **Compliance:** processes to make sure regulatory obligations are met.

It also says firms should integrate AI into mainstream prudential and conduct risk frameworks, and that technical competence and ethical behaviour are required of those using AI tools.

**What its survey found** (53 firms):

- 85% are using AI to some extent; 81% have adopted generative AI.
- Use is mostly internal, and none reported fully autonomous AI.
- 81% of those using AI have a register of use cases, and 70% address it in a policy.
- **Some firms don't have clearly defined roles and responsibilities.**
- IT and cyber security are the top concerns, followed by data protection and ethics.

**Consumer Protection Code 2025:** the Bulletin notes it contains specific requirements for in-scope firms using digital technology to provide financial services. **[Compliance to confirm what this means for Laya's AI use]**

## GDPR

See [Data protection](06-data-protection.md). In particular:

- Health data is special category data.
- A DPIA may be needed for new technologies or large-scale processing.
- People have rights around solely automated decisions with significant effects.
- A notifiable personal data breach must go to the Data Protection Commission within 72 hours of becoming aware of it (Article 33).

The [DPC's July 2024 guidance](https://www.dataprotection.ie/en/dpc-guidance/blogs/AI-LLMs-and-Data-Protection) covers what organisations should consider when staff use AI tools.

## DORA

The Digital Operational Resilience Act sets rules on ICT risk, incident reporting and third-party risk for financial entities, and EIOPA links it to AI governance (paragraphs 3.1, 3.7, 3.34).

**Does it apply to Laya directly?** [Article 2](https://www.springlex.eu/packages/dora/dora-regulation/article-2/) covers insurance undertakings and intermediaries, but excludes intermediaries that are micro, small or medium-sized enterprises. **Compliance should confirm Laya's position**, and how AXA's obligations reach it.

If it applies:

- Microsoft and GitHub are likely ICT third-party providers, relevant to the register of information.
- Major ICT incidents have reporting deadlines.
- Changes need managed, auditable processes.

The `release-change` and `incident-response` skills are built with this in mind.

## What Laya should do next

| Action | Owner |
|---|---|
| Review this document and correct it | Compliance |
| Map duties between Laya, AXA Insurance dac and AXA Group; check group AI policy | Compliance |
| Decide how Annex III 5(c) applies in community rating | Compliance, actuarial function |
| Name an AI owner; approve the [roles](../roles-and-lifecycle/README.md) | Senior management |
| Start the AI use register | AI owner |
| Agree what staff may put into Copilot, and retention | DPO |
| Record training for AI literacy | HR, Compliance |
| Assess Microsoft and GitHub as AI suppliers | Vendor owner |
