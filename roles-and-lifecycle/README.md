# Roles and responsibilities when AI does the work

**AI does the work. A named person stays accountable.**

That one idea runs through this folder. As AI writes more of Laya's documents, spreadsheets and code, the question isn't "who typed it?" but "who answers for it?". The answer is always a person, and never a tool.

The Central Bank of Ireland has noted that some firms using AI don't have clearly defined roles and responsibilities. This folder is how Laya makes them clear.

**Status: draft for review by Compliance, the DPO and the AI owner.** Job titles and names are for Laya to fill in **[to confirm]**. If a card's role doesn't exist at Laya, give its duties to someone: the duty doesn't go away.

## Find your role

**Everyone**

| Card | Who it's for |
|---|---|
| [Every member of staff](cards/every-member-of-staff.md) | Anyone who uses Copilot, on free or paid |
| [Team lead or manager](cards/team-lead.md) | Anyone with people or a team's work to answer for |
| [Business owner](cards/business-owner.md) | Whoever owns a process, product or the outcome of a change |
| [AI champion](cards/ai-champion.md) | The person helping their team use AI well |
| [Agent owner](cards/agent-owner.md) | Whoever owns one Laya agent or skill |
| [Library owner](cards/library-owner.md) | Whoever owns this library |

**Technical**

| Card | Who it's for |
|---|---|
| [Developer](cards/developer.md) | Anyone writing code with GitHub Copilot |
| [Tech lead](cards/tech-lead.md) | Whoever sets standards and owns a system's design |
| [Test engineer](cards/test-engineer.md) | Whoever decides what proves it works |
| [Data engineer](cards/data-engineer.md) | Whoever changes Snowflake, Oracle or pipelines |
| [Platform engineer](cards/platform-engineer.md) | Whoever owns the GitHub Copilot harness |
| [Security engineer](cards/security-engineer.md) | Whoever reviews for security |
| [Service owner](cards/service-owner.md) | Whoever answers for a service in production |

**Governance**

| Card | Who it's for |
|---|---|
| [Board and senior management](cards/board-and-senior-management.md) | The people responsible for AI across Laya |
| [AI owner](cards/ai-owner.md) | The AI officer or committee |
| [Data Protection Officer](cards/data-protection-officer.md) | Personal data in AI |
| [Compliance and risk](cards/compliance-and-risk.md) | Whether AI use meets the rules |
| [Internal audit](cards/internal-audit.md) | Independent assurance |
| [Actuarial function](cards/actuarial-function.md) | AI touching reserving, underwriting or pricing |
| [Vendor owner](cards/vendor-owner.md) | Microsoft, GitHub and other AI suppliers |
| [Platform admins](cards/platform-admins.md) | Microsoft 365 and GitHub settings |

## How it fits together

1. **[Risk tiers](risk-tiers.md)** say how much human oversight a job needs. A personal email and a claims decision need very different care.
2. **[The lifecycle](lifecycle.md)** gives the stages work moves through, and the checks at each.
3. **[The RACI](raci.md)** says who does what at each stage.
4. **The role cards** say what each person owns, what AI can do for them, and what they can't hand over.

## Four rules for every role

1. **One named person is accountable for each piece of work.** An agent can do the work, but it can never be accountable.
2. **Whoever did the work doesn't approve it.** That holds for people and for agents: an agent never approves its own work, and a person reviews what agents produce.
3. **Oversight must be real.** The person checking needs the time, the skill and the authority to overrule the AI. A rubber stamp isn't oversight.
4. **More risk means more people.** See the [risk tiers](risk-tiers.md).

## The AI use register

Any AI use beyond personal drafting goes in the register: the use, its owner, its tier, the data, the oversight and a review date. It answers the first question anyone will ask: "Where is Laya using AI?" The Central Bank's survey found that most firms using AI (81%) keep such a register.

The template is **AI Use Register.xlsx** in `non-technical/ready-to-use/templates/`. The AI owner keeps it; each use's owner keeps their row current.

## Where this comes from

The governance roles follow the **EIOPA Opinion on AI governance and risk management** (August 2025, paragraphs 3.30 to 3.33), which names the board, the compliance and audit functions, the DPO and the actuarial function, and suggests an AI officer or committee. EIOPA also says firms stay responsible for AI systems they use, whether built in-house or bought (paragraph 3.11). The technical roles draw on Microsoft's HVE Core role guides and on how Matt Pocock's skills split up the work.

**Laya's position:** Laya Healthcare Limited is authorised by the Central Bank of Ireland and acts as an agent for AXA Insurance dac, which provides the health insurance. So some duties may sit with AXA Insurance dac or AXA Group, and group AI policies may apply. **[Compliance to map these]**

Sources are in [best-practices/sources.md](../best-practices/sources.md).
