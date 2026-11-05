# Security for AI

**For developers, IT and security.** Everyone else: see [Using Copilot at work](01-using-copilot-at-work.md).

AI brings one new problem above all: **it can't reliably tell instructions from information.** Anything it reads can try to steer it.

## The risks: OWASP's top 10 for agents

The [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026) (December 2025). Names as [summarised here](https://www.speakeasy.com/blog/owasp-agentic-top-10-explained); check the original for the exact wording.

| ID | Risk | What Laya does |
|---|---|---|
| ASI01 | Agent goal hijack: an attacker redirects the agent through what it reads | Treat what's read as data. People approve what matters |
| ASI02 | Tool misuse: agents use tools beyond their purpose | Role agents with restricted tools. Guard hooks |
| ASI03 | Identity and privilege abuse | Tokens scoped per task. Laya's SharePoint backend acts as the signed-in person, so it opens only what they can |
| ASI04 | Agentic supply chain: malicious tools, plugins or MCP servers | `skill-intake`. An allowlist. Pinned copies |
| ASI05 | Unexpected code execution | Sandboxes, firewall, review before running |
| ASI06 | Memory and context poisoning | Files that steer agents need a code owner's review |
| ASI07 | Insecure inter-agent communication | Delegation only narrows. Few agents, simple flows |
| ASI08 | Cascading failures | Small batches, caps on retries, checks between stages |
| ASI09 | Human-agent trust exploitation: people approve unsafe things | Real oversight. [Risk tiers](../roles-and-lifecycle/risk-tiers.md). Training |
| ASI10 | Rogue agents: drifting beyond their purpose | An agent inventory, reviews, and a way to stop them |

## The lethal trifecta

[Simon Willison's](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) test for an AI agent. Danger comes when one agent has all three:

1. Access to **private data**
2. Exposure to **untrusted content**
3. A way to **communicate externally**

An attacker's instructions in an email or issue can make the agent send your data out. **Remove one leg.** This is why Laya's agents keep web search off, why Catch Me Up can read mail but can't send it, and why the cloud agent has a firewall.

## Prompt injection

- **Untrusted content** includes issues, pull request comments, web pages, emails, documents and tool output.
- **None of it can authorise anything.** An issue saying "please push this to production" isn't an approval.
- **Don't rely on filtering alone.** [GitHub](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations) filters hidden characters in input, but tells you to treat untrusted input carefully. [VS Code](https://code.visualstudio.com/docs/copilot/security) relies on URL approval, edit review, sandboxing and Workspace Trust together.
- **It's happened.** Cycode [reports](https://cycode.com/blog/owasp-top-10-agentic-applications/) a hijacked pull request that shipped data-wiping instructions through an AI coding extension.

## Skills are supply chain

A skill runs with a developer's permissions.

- **[Snyk's ToxicSkills audit](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub)** (February 2026) scanned 3,984 public skills: 13.4% had a critical-level issue, 36.82% had some security flaw, and 76 held confirmed malicious payloads.
- **Hidden files matter.** Test files in a skill can get executed, and scanners may not look at them.
- **Our own review** of well-known public collections found telemetry, `curl | bash` installers, browser cookie readers, permission-bypass flags, offensive-security tooling and promotional instructions.
- **So:** every outside skill goes through `skill-intake`. Pin it to a commit, read every file, and prefer writing your own from the idea. `gh skill` [warns](https://cli.github.com/manual/gh_skill_install) that skills aren't verified by GitHub.

## Permissions

- **Least agency:** give an agent only the tools and access this task needs.
- **Don't auto-approve.** VS Code's [`chat.tools.global.autoApprove`](https://code.visualstudio.com/docs/copilot/security) bypasses every prompt and can enable destructive actions. Block it with the `ChatToolsAutoApprove` policy.
- **Rule-based terminal approval is best-effort:** aliases and quoting can get around it.
- **Don't pre-approve the shell in a skill.** [GitHub warns](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) that `allowed-tools: shell` lets a malicious skill or prompt injection run anything.
- **But approval prompts wear thin:** people click through. Reduce the number of prompts by narrowing what's possible, not by turning them off.

## MCP servers

MCP connects agents to tools and data, and each server is a new way in.

- **Allowlist:** VS Code's `ChatMCP` policy can limit servers to a curated registry. Note [VS Code's warning](https://code.visualstudio.com/docs/copilot/security) that Copilot harness sessions don't fully enforce some policies.
- **Review before trusting a workspace,** because repository MCP config can start servers.
- **List what each server can reach and change** before adding it.
- **The cloud agent's firewall doesn't cover MCP server processes** ([GitHub](https://docs.github.com/en/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent)).

## Content exclusion has limits

[GitHub's content exclusion](https://docs.github.com/en/copilot/concepts/context/content-exclusion) keeps files out of Copilot's tools, including for agents. But GitHub is clear that:

- it isn't a security boundary or a substitute for operating-system permissions;
- it may miss indirect access, and doesn't cover symlinks or remote filesystems;
- third-party MCP servers may not respect it.

So keep secrets and real member data out of repos altogether.

## The cloud agent

From GitHub's [risks and mitigations](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations) and [guardrails tutorial](https://docs.github.com/en/enterprise-cloud@latest/copilot/tutorials/cloud-agent/build-guardrails):

- It pushes only to a `copilot/` branch, can't approve or merge, and its workflows wait for a person.
- Keep CodeQL, secret scanning, dependency checks and Copilot code review switched on.
- Its firewall is on by default, but GitHub says it [isn't a complete solution](https://docs.github.com/en/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent): it doesn't cover setup steps or MCP servers, and it isn't compatible with self-hosted runners or Windows.
- Use GitHub-hosted runners, so each session gets a fresh machine. Self-hosted ones should be ephemeral.
- Keep Actions secrets away from it: Copilot can't read them.
- Give `copilot-setup-steps.yml` the lowest permissions it needs.

## If an agent goes wrong

Treat it as a compromised identity until you know otherwise. Capture the session log, contain it, rotate what it could reach, and ask whether it was steered. See `incident-response`.

## Everyday security for all staff

- AI makes scams more convincing, so be suspicious of unexpected requests about payments, passwords or personal data.
- Don't click a link or enter a password because Copilot told you to.
- Report anything strange to the IT service desk.
