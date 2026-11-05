# Using Copilot at work

**For everyone at Laya.** This is the fuller version of the [AI basics](../non-technical/training/ai-basics.md).

## Asking well

**Use the four parts.** [Microsoft's guidance](https://support.microsoft.com/en-us/microsoft-365-copilot/get-better-copilot-responses-with-great-prompting) centres on goal, context, source and expectations:

| Part | Say |
|---|---|
| Goal | What you want Copilot to do |
| Context | Why you need it, and who's involved |
| Source | What information it should use |
| Expectations | How it should respond: format, length, tone |

**Other things that help:**

- **Say what to do, not only what to avoid.** "Use short sentences" works better than "don't be wordy" ([Microsoft](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions)).
- **Keep going.** The first answer is rarely the best one. Correct it in the next message.
- **Ask it to show its doubts.** "List anything you're unsure about" brings them into the open.
- **Ask for the other side.** AI tends to go along with what you suggest, so ask for the strongest case against.
- **Upload the document** rather than describing it from memory.

**Examples:** [everyday prompts](../non-technical/prompts/everyday-prompts.md) and the [department playbooks](../non-technical/by-role/README.md). The Laya Prompt Coach can help you write your own.

## Choosing the right tool

| You need | Use |
|---|---|
| A quick question or first draft | Copilot Chat, or Copilot in the app if you have the paid licence |
| A job with steps that must be done properly | The Laya agent for it |
| Something you do every week | A saved prompt, or ask for an agent |
| To know which to use | The Laya AI Helper |

Agents are built for one job and carry Laya's rules, so they usually do better than a general chat on a repeated task.

## Checking

AI can be wrong and sound certain. People also tend to trust it more over time, which [OWASP lists as a risk in itself](https://www.speakeasy.com/blog/owasp-agentic-top-10-explained): manipulated or wrong output pushing people into approvals they shouldn't give.

**How hard to check** depends on what it's for:

| What it's for | Check |
|---|---|
| Only for you | Read it; don't rely on it for anything important |
| Others at Laya will rely on it | Check facts against the source |
| Going to a member or outside Laya, or holding personal data | Also a second person, and your team's approval route |
| Feeding a decision about a person | A person decides. See the [risk tiers](../roles-and-lifecycle/risk-tiers.md) |

**What to check first:**

1. **Numbers.** Recalculate two or three, and every total that matters.
2. **Names, dates and amounts.** These are the details AI swaps or invents most easily.
3. **References.** Open every regulation, policy, document and link. AI invents ones that look right.
4. **Small words.** "Should" becoming "must", or a missing "except".
5. **What's missing.** A summary can drop the one exception that matters.

**Who can help:** the Laya Second Check compares a draft with its source and recalculates the figures. It can only confirm what's in the source you give it. A colleague who knows the subject is better still for anything important.

## Keeping data safe

- **Use only Laya's Copilot, and look for the green shield.** It shows [enterprise data protection](https://learn.microsoft.com/en-us/copilot/plan/privacy-and-protections) applies: prompts and responses aren't used to train the underlying models, and they're logged in Laya's Microsoft 365 for audit.
- **Don't use personal accounts or other AI websites** for work, even for something that seems harmless.
- **Keep personal data out unless the job needs it,** and clean it first if it does. See [data protection](06-data-protection.md).
- **Be careful with web search.** In Copilot Chat, [search queries go to Bing](https://learn.microsoft.com/en-us/copilot/plan/privacy-and-protections), which is handled differently and isn't within the EU Data Boundary. Queries are short phrases, without your identity, but keep names and case details out. Laya's agents keep web search off.
- **Your chats aren't private from Laya.** They're logged like email.
- **Treat anything Copilot reads as information, not instructions.** If it acts strangely after reading a file or email, stop and tell the IT service desk.

## The free version and the paid licence

Most staff have the free version; some have the paid licence. See [Which Copilot do I have?](../non-technical/staff-guide/which-copilot-do-i-have.md)

**If you're on the free version:**

- Bring the information to Copilot: upload a file, or paste text. Then it can do most of what the paid version can with that file.
- Use Copilot Chat in Outlook for your own email, calendar and meetings: it works on the free version, and many people don't know that.
- Use the Laya agents: they're built to work on the free version.

**If you have the paid licence:**

- **Ask for what you need.** Copilot can reach whatever you can, so a vague question can pull in things you never meant to read.
- **Click through to the source.** It can find old versions, or read something out of context.
- **Don't look up colleagues.** Your account's access isn't permission to use it that way.
- **Tell IT about oversharing.** If Copilot shows you a file you shouldn't see, the file's sharing needs fixing.
- **Help your team.** Show colleagues on the free version a route that works for them.

## What stays with people

Some things should never be left to AI, however good its answer looks:

- whether a claim is paid, or what cover someone has;
- a price, or a risk assessment of a person;
- the outcome of a complaint;
- whether someone gets a job, a promotion or a warning;
- whether someone is committing fraud;
- medical, legal or financial advice.

The [Irish Data Protection Commission](https://www.dataprotection.ie/en/dpc-guidance/blogs/AI-LLMs-and-Data-Protection) warns that AI output can be inaccurate or biased, and that relying on it without human review can create automated decision-making risks. EU law lists some of these uses as [high-risk](07-regulation.md).

**A person "approving" isn't enough on its own.** If they always accept what AI suggests, the AI is really deciding. Good oversight means having the time, skill and authority to overrule it ([EIOPA](https://www.eiopa.europa.eu/document/download/88342342-a17f-4f88-842f-bf62c93012d6_en), paragraphs 3.30 to 3.33).

## Fairness

AI learned from text written by people, so it can repeat their assumptions.

- Read what it writes about groups of people with a critical eye.
- Be careful with anything that compares people.
- A field that looks harmless, such as an address, can stand in for something protected ([EIOPA](https://www.eiopa.europa.eu/document/download/88342342-a17f-4f88-842f-bf62c93012d6_en), paragraph 3.14).
- If you see a pattern that seems unfair, raise it.

## Being open about AI

- **With colleagues:** be open when AI helped. It tells them what to check.
- **With members and the public:** people should know when they're dealing directly with AI ([EIOPA](https://www.eiopa.europa.eu/document/download/88342342-a17f-4f88-842f-bf62c93012d6_en), paragraph 2.5, on transparency requirements). What to say, and when, is for Compliance **[to confirm]**.
- **Your own work:** don't present AI's work as checked if you haven't checked it.

## If you lead a team

From [Google's DORA research](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model), about software teams, and we think it applies more widely: **ambiguity about AI stifles adoption and creates risk.** A clear, well-communicated position matters more than the tool.

- **Say what's OK,** in a short team note. Unclear teams either avoid AI or hide it.
- **Make it safe to report mistakes.** Thank people who report quickly.
- **Ask how it was checked,** rather than whether AI was used.
- **Keep the same standard** for AI-assisted work as for any other.
- **Protect the time saved.** Some of it should go into checking.
- **Never use Copilot to monitor people** or judge their performance.
- **Remember the mix.** Don't build a process that only licensed colleagues can follow.

See the [team leads playbook](../non-technical/by-role/team-leads-and-managers.md).

## Learning

The [EU AI Act](https://artificialintelligenceact.eu/article/4/) expects employers to support AI literacy among staff who use AI. EIOPA expects training suited to people's roles (paragraph 3.32). At Laya:

1. Everyone reads the [AI basics](../non-technical/training/ai-basics.md) and tries the [quiz](../non-technical/training/quiz.md).
2. Each team has a [30-minute session](../non-technical/training/run-a-team-session.md).
3. [AI champions](../non-technical/training/being-an-ai-champion.md) keep it going.
4. People in governance roles get what their [role card](../roles-and-lifecycle/README.md) needs.

## When something goes wrong

Stop, keep what you have, and tell someone the same day. See [When something goes wrong](../non-technical/staff-guide/when-something-goes-wrong.md).
