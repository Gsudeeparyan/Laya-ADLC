# Measuring value

**For leaders and owners.** The Central Bank's survey found efficiency and cost reduction are the main reasons firms adopt AI, and its first standard is that AI should fit a specific business challenge. So: know what problem you're solving, and check that it's improving.

This page is mostly our own advice, except where it links to a source. Adapt it to Laya's goals.

## Start with one question

**What would be measurably better, and for whom?** Write it down before rolling something out. "Use more AI" isn't a goal. "Reduce the time to produce the monthly report from two days to one, with the same accuracy" is.

## For everyday work

| Measure | How | Watch out for |
|---|---|---|
| **Time on specific tasks,** before and after | Pick 3-5 tasks. Ask the people who do them | People overestimate. Include the time spent checking |
| **Quality** | Corrections, rework, complaints, errors found | Speed that creates rework is no gain |
| **Who's using it, by team** | [Copilot agent usage reports](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-checklist) | Use doesn't equal value |
| **Which agents get used** | Same | Unused agents are candidates for retiring |
| **Confidence** | A short survey: "I know what I can use it for", "I know how to check it" | Run it before and after training |
| **Mistakes reported** | Your incident log | **More reports early on is good news:** it means people feel safe to report |

## For software

[Google's DORA research](https://dora.dev/dora-report-2025/) (not the EU regulation of the same name) measures software delivery by both speed and stability, and found AI use now correlates with higher throughput. It also found teams can move faster without having the systems to handle that safely. So measure both:

| Measure | Why |
|---|---|
| Change lead time and deployment frequency | Are we delivering faster? |
| Change failure rate and time to restore | Are we breaking more? |
| Size of pull requests | Small batches are what keeps AI safe |
| Review time, and how long pull requests wait | Review is the new bottleneck |
| Rework: code changed again soon after merging | A sign that speed is costing quality |
| Mistakes turned into checks | Is the harness getting better? |

[GitHub's Copilot usage metrics](https://docs.github.com/en/copilot/concepts/copilot-metrics) show adoption, once the policy is turned on. They tell you who's using it, not whether it's working.

## What not to measure

- **Lines of code from AI, or suggestions accepted.** These reward more code, not better code.
- **Individuals.** Don't use usage data to rate people. It's unfair, and it may raise data protection and employment issues. Report by team, and leave out groups smaller than 5.
- **Time saved, by itself.** Ask where the time went.
- **Number of agents or prompts.** A small set of skills people trust beats a big catalogue.

## For governance

These show whether the system is under control:

| Measure | Target |
|---|---|
| AI uses on the register with a named owner | All |
| Reviews overdue | None |
| T3 uses with sign-offs recorded | All |
| People who've done the AI basics | Rising towards all, by team |
| Repos with the harness installed | Rising towards all active repos |
| Open `[to confirm]` items in this library | Falling |
| Time from an AI incident to it being reported | Falling |

## Review

- **Each quarter:** the library owner reports these to the AI owner.
- **Each year:** senior management reviews whether AI is delivering what was intended, and whether the [roles](../roles-and-lifecycle/README.md) and risk appetite still fit. EIOPA expects the approach to be reviewed regularly, especially as the number and importance of AI uses change (paragraph 3.9).
- **Licences:** review who has the paid licence each quarter. Give them to the people getting value from them.
