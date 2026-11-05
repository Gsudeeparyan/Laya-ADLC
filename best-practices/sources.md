# Sources

Everything in this library's best practice comes from here. All were checked on **05/11/2026** unless it says otherwise. The library owner re-checks them each quarter, because Microsoft and GitHub change often.

**Type:** *Official* is the vendor's or regulator's own page. *Research* is a study or a recognised body. *Practitioner* is a respected individual or company's view: useful, but not authoritative. *Secondary* is someone's summary of an original, used where we couldn't read the original directly.

## Laya

| Source | Type | Used for |
|---|---|---|
| [Laya terms of business](https://layahealthcare.ie/termsconditions) | Official | Laya's regulatory position |

## Regulators and law

| Source | Type | Used for |
|---|---|---|
| [EIOPA Opinion on AI governance and risk management, EIOPA-BoS-25-360, 06/08/2025](https://www.eiopa.europa.eu/document/download/88342342-a17f-4f88-842f-bf62c93012d6_en) (read paragraphs 2.2 to 4.5) | Official | Roles, proportionality, the six areas, third parties |
| [Central Bank of Ireland, Insurance Quarterly, March 2026](https://www.centralbank.ie/docs/default-source/regulation/industry-market-sectors/insurance-reinsurance/solvency-ii/communications/insurance-quarterly-news/the-insurance-quarterly-march-2026.pdf?sfvrsn=ec8721a_4) (read pages 2 to 5) | Official | AI standards, survey, its role under the AI Act |
| [EU AI Act, Annex III](https://artificialintelligenceact.eu/annex/3/) | Secondary (text of the Act) | High-risk uses |
| [EU AI Act, Article 4](https://artificialintelligenceact.eu/article/4/) | Secondary (text of the Act) | AI literacy |
| [Digital Omnibus on AI, Regulation (EU) 2026/1744](https://artificialintelligenceact.eu/ai-act-explorer/digital-omnibus/) | Secondary (text of the regulation) | New dates. Compliance should check the Official Journal |
| [Data Protection Commission: AI, Large Language Models and Data Protection, 18/07/2024](https://www.dataprotection.ie/en/dpc-guidance/blogs/AI-LLMs-and-Data-Protection) | Official | What organisations should consider |
| [DORA Regulation, Article 2](https://www.springlex.eu/packages/dora/dora-regulation/article-2/) | Secondary (text of the regulation) | Scope, including intermediaries |
| [EIOPA Q&A on DORA](https://www.eiopa.europa.eu/qa-regulation/questions-and-answers-database/dora237-3350_en) | Official | Scope for intermediaries |

## Microsoft

| Source | Type | Used for |
|---|---|---|
| [Agent capabilities and licensing models](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/prerequisites) | Official | The free and paid boundary |
| [Agents admin guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-admin-guide) | Official | Who can build agents, sharing, publishing |
| [Agents checklist](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-checklist) | Official | Admin tasks, oversharing, audit, billing |
| [Licensing and cost for extensibility](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/cost-considerations) | Official | Usage costs |
| [Licence options](https://learn.microsoft.com/en-us/copilot/plan/copilot-license-options) | Official | Paid licence |
| [What Copilot licence do I have?](https://support.microsoft.com/en-us/microsoft-365-copilot/what-copilot-license-do-i-have) (updated April 2026) | Official | The label check |
| [Code interpreter](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/code-interpreter) | Official | Availability, temporary files |
| [Declarative agent schema 1.9](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-manifest-1.9) | Official | Agent packages; the note that conflicts on licensing |
| [Write effective instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions) | Official | How to write agents |
| [Skills in declarative agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-skills) and [adding them in Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-add-skills) | Official | Skill packages and their limits |
| [Build agents in Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-build-agents) | Official | Deployment steps |
| [Copilot Chat privacy and protections](https://learn.microsoft.com/en-us/copilot/plan/privacy-and-protections) | Official | Green shield, logging, Outlook, web search, EU Data Boundary |
| [Enterprise data protection](https://learn.microsoft.com/en-us/microsoft-365/copilot/enterprise-data-protection) | Official | Models outside the EU Data Boundary |
| [Great prompting](https://support.microsoft.com/en-us/microsoft-365-copilot/get-better-copilot-responses-with-great-prompting) and [writing prompts](https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-writing-prompts-in-microsoft-365-copilot) | Official | Goal, context, source, expectations |
| [How Copilot Chat works in Microsoft 365 apps](https://support.microsoft.com/en-us/microsoft-365-copilot/how-copilot-chat-works-in-microsoft-365-apps) | Official | In-app availability |
| [Discussion of notice MC1253863](https://techcommunity.microsoft.com/discussions/microsoft-copilot/removal-of-copilot-chat-availability-in-m365-apps/4502990) | Secondary | April 2026 change to in-app Copilot Chat |

## GitHub and VS Code

| Source | Type | Used for |
|---|---|---|
| [Customisation cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet) | Official | What goes where, and what reaches which surface |
| [Agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) and [adding skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) | Official | Skill locations; the warning on pre-approving the shell |
| [Custom instructions support](https://docs.github.com/en/copilot/reference/custom-instructions-support) | Official | Support matrix |
| [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) | Official | Agent format, tools |
| [Preparing for custom agents in an organisation](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents) | Official | Org-level agents |
| [Hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference) | Official | Hook format; fail-open and fail-closed |
| [Risks and mitigations for the cloud agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations) | Official | Cloud agent limits |
| [Building guardrails for the cloud agent](https://docs.github.com/en/enterprise-cloud@latest/copilot/tutorials/cloud-agent/build-guardrails) | Official | Rulesets, runners, secrets |
| [Best practices for tasks](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks) | Official | Giving tasks to the agent |
| [Customising the agent environment](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment) | Official | `copilot-setup-steps.yml` |
| [Agent firewall](https://docs.github.com/en/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent) | Official | Firewall limits |
| [Content exclusion](https://docs.github.com/en/copilot/concepts/context/content-exclusion) | Official | What it does and doesn't do. An older page still says agents aren't covered; we followed the main page |
| [Plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference), [marketplace](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace) and [managed settings](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/use-managed-settings/manage-plugin-marketplaces-and-plugins) | Official | Company-wide sharing |
| [Audit logs](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/review-audit-logs) and [usage metrics](https://docs.github.com/en/copilot/concepts/copilot-metrics) | Official | Monitoring |
| [`gh skill`](https://cli.github.com/manual/gh_skill_install) | Official | Validating skills; its warning that skills aren't verified |
| [VS Code: security](https://code.visualstudio.com/docs/copilot/security) | Official | Approvals, policies, sandbox |
| [VS Code: customisation](https://code.visualstudio.com/docs/copilot/customization/overview), [skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills), [hooks](https://code.visualstudio.com/docs/copilot/customization/hooks), [custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) and [plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins) | Official | Formats and settings |

## Research and practice

| Source | Type | Used for |
|---|---|---|
| [Google DORA: State of AI-assisted Software Development, 2025](https://dora.dev/dora-report-2025/) | Research | AI as an amplifier. Read through DORA's and Google's summaries |
| [DORA AI Capabilities Model](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model) | Research | The seven capabilities |
| [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026) | Research | The risk list. Names read through the summary below |
| [Speakeasy: the OWASP Agentic Top 10 explained](https://www.speakeasy.com/blog/owasp-agentic-top-10-explained) | Secondary | Names and mitigations |
| [Snyk: ToxicSkills, 05/02/2026](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub) | Research (vendor) | Numbers on malicious skills |
| [Cycode: OWASP Agentic Top 10](https://cycode.com/blog/owasp-top-10-agentic-applications/) | Practitioner (vendor) | Pull request hijack example |
| [FOSSA: slopsquatting](https://fossa.com/blog/slopsquatting-ai-hallucinations-new-software-supply-chain-risk/) | Practitioner (vendor) | Invented packages |
| [Birgitta Böckeler: Harness engineering, martinfowler.com, 02/04/2026](https://martinfowler.com/articles/harness-engineering.html) | Practitioner | Guides and sensors |
| [Simon Willison: The lethal trifecta, 16/06/2025](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | Practitioner | Private data, untrusted content, external communication |
| [Agent Skills specification](https://agentskills.io/specification) | Official (standard) | Skill format |
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | Practitioner | The developer flow and writing method. Pinned copy in this library |
| [Microsoft HVE Core](https://github.com/microsoft/hve-core) and [its role guides](https://github.com/microsoft/hve-core/tree/main/docs/hve-guide/roles) | Practitioner | Technical roles. Read for ideas, not copied |
| [GitHub awesome-copilot](https://github.com/github/awesome-copilot) | Practitioner | A community source to check when looking for skills. Not imported |
| [Agent rules from books](https://github.com/mattpocock/agent-rules-books) | Practitioner | The book-based skills. Pinned rules in this library |

## Where sources disagree

| Question | What we found | What we did |
|---|---|---|
| Do free users get Code Interpreter in agents? | Licensing table and Code Interpreter page: yes. Schema pages: no | Built on yes, as the newer and more specific. First item on the [smoke test](../non-technical/admin/smoke-test.md) |
| Do free users get Copilot in Word, Excel and PowerPoint? | April 2026 notice: being reserved for licensed users. Support page: a "Basic" label still has standard access | Told staff it depends on their label |
| Are Word, Excel and PowerPoint agents licensed only? | One page says they need the licence; another describes Copilot Chat using them | Didn't rely on them |
| Does content exclusion cover agents? | Main page: yes, with limits. An older page: no | Followed the main page, and told people not to rely on it as a boundary |
