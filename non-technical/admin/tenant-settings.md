# Microsoft 365 tenant settings for AI

**For:** Microsoft 365, Purview and Power Platform admins. This is the Microsoft side of Laya's agent harness: the settings that hold however people use Copilot. Instructions in an agent can be ignored, but these can't.

Menu names change often, and Microsoft uses several names for the same admin area: "Copilot controls", "Copilot Control System" and "Agent Registry". Check against the [Agents admin guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-admin-guide) and the [Agents checklist](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-checklist).

**This is a checklist of things to decide.** Nothing here has been changed in Laya's tenant.

## 1. Who can get and share agents

| Setting | Recommended | Why |
|---|---|---|
| Agent access: who can use agents | All staff | The free-tier agents are for everyone |
| Agent types allowed | Microsoft's and Laya's. External publishers only after review | Non-Microsoft agents aren't covered by Microsoft's agreements, so review their terms first |
| Agent sharing | A named group of builders, not everyone | Stops many unreviewed copies appearing |
| Publishing to the organisation's catalog | Admin approval | The review step before something reaches all staff |
| Sideloading ("Upload custom apps" in Teams setup policies) | Off for most; on for a pilot group | Packages are code-like, so keep this controlled |
| Agent Registry | Review monthly; block anything unsafe or non-compliant | The single inventory of what's in use |

## 2. Data protection

| Control | Why |
|---|---|
| Check for oversharing first, with SharePoint Advanced Management and Purview DSPM for AI | Licensed Copilot surfaces whatever a person can reach. A file shared with "everyone" becomes easy to find |
| Sensitivity labels, with Purview Data Loss Prevention for Copilot | Keeps selected files away from Copilot and agents |
| Restrict web search if Compliance prefers | Web queries go to Bing, outside the EU Data Boundary |
| Check the model list against the EU Data Boundary | Some models are excluded from the boundary and from in-country processing commitments |

## 3. Keeping a record

| Control | Why |
|---|---|
| Purview audit for Copilot | Prompts and responses are logged for audit and eDiscovery |
| A retention policy for Copilot interactions | The DPC expects a retention schedule. Agree the period with the DPO and Compliance **[to confirm]** |
| Copilot agent usage reports | Show adoption, without tracking individuals' content |

Tell staff that chats are logged and how they may be reviewed. HR and the DPO should agree the wording **[to confirm]**.

## 4. Cost

| Control | Why |
|---|---|
| Keep pay-as-you-go off unless agreed | Metered agents are off by default. Turning it on starts charges for anything grounded in tenant data |
| If it's on: budget alerts, and a security group for who's covered | Prevents surprise bills |
| Review who holds the paid licence each quarter | Give them to people who use them |

## 5. Getting the agents out

Follow [Deploy the agents](deploy-agents.md). In short:
1. IT uploads the packages, or licensed makers build from the packs.
2. Assign `everyone/` agents to all staff, and pin the Laya AI Helper for everyone.
3. Assign `paid-licence/` agents to a security group of licensed people.

## 6. Who owns what

| Area | Owner |
|---|---|
| Tenant settings for Copilot and agents | Microsoft 365 admin |
| Copilot Studio settings, connectors | Power Platform admin |
| Labels, DLP, audit, retention | Purview or Compliance admin |
| Billing | Global or billing admin |
| What's allowed | The AI owner, DPO and Compliance decide; admins implement |

See the [platform admin role card](../../roles-and-lifecycle/cards/platform-admins.md).
