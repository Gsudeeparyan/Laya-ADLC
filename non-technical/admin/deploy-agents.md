# Deploy the agents

**For:** IT, and licensed staff who build agents. Everyone else just uses them.

There are two ways. Choose by how much control you want.

| | **Agents Toolkit package (recommended)** | **Agent Builder** |
|---|---|---|
| Who | IT | Anyone with the paid licence |
| Time | One upload per agent | About 5 minutes per agent |
| Reaches | Everyone you assign it to | People you share it with |
| Updates | Re-upload; the app ID stays the same | Paste new instructions by hand |
| Good for | The company-wide rollout | Trying an agent, or a pilot |

Everything you need is in `ready-to-use/agents/`. Its README lists each agent and whether it needs anything set up first.

## Before you start

1. **Read [licences.md](licences.md).** The tenant check on Code Interpreter comes first.
2. Agree the tenant settings in [tenant-settings.md](tenant-settings.md).
3. Edit `non-technical/package.yaml`: point the `developer` links at your intranet, privacy notice and acceptable-use pages.
4. For the **Laya Policy Finder**, replace the example site in `non-technical/paid-licence/agents/laya-policy-finder/agent.yaml` with Laya's approved policy sites. Choose sites with current, properly shared documents: the agent is only as good as what's on them.
5. Rebuild, from `technical/platform`:
   ```text
   python tools/build_agents.py
   python tools/build_templates.py
   python tools/build_guides.py
   ```
6. Put the Word guides and templates from `ready-to-use/` in a SharePoint folder every member of staff can read, called **ADLC Templates**.

## Option A: Agents Toolkit package

Each `ready-to-use/agents/<tier>/<agent>/<agent>.zip` holds:

| File | Contents |
|---|---|
| `manifest.json` | App manifest. The `id` is derived from the agent's id, so re-deploying updates the agent and doesn't create a duplicate |
| `declarativeAgent.json` | Name, description, starters, capabilities; `instructions` points at `instruction.txt` |
| `instruction.txt` | The shared preamble, the PII guard where set, and the skill (8,000 characters or fewer) |
| `color.png`, `outline.png` | Icons |

1. Optional: validate a package with the Microsoft 365 Agents Toolkit in VS Code.
2. In the **Microsoft 365 admin center**, go to the agents area and choose to upload a custom agent. Upload the zip.
3. Assign it:
   - `everyone/` agents: all staff.
   - `paid-licence/` agents: a security group of licensed people.
4. Pin the **Laya AI Helper** for everyone, so it's the first thing people see.
5. Check it appears under **Agents** for a test user of each kind.

## Option B: Agent Builder (needs the paid licence)

Open `ready-to-use/agents/<tier>/<agent>/agent-builder.md`. It holds everything below, ready to copy.

1. In **Microsoft Copilot**, select **New agent**, then **Skip to configure**.
2. Copy in the **Name**, **Description** and the whole **Instructions** box.
3. Set **Knowledge** and **Capabilities** as the pack says. For free-tier agents, leave Knowledge empty.
4. Add each **starter prompt**.
5. Test it on the **Try it** tab with the [smoke test](smoke-test.md), then select **Create**.
6. Select **Share**, choose who, with **Can chat** access. To reach everyone, ask an admin to publish it to the catalog.

**Important:** an agent you build yourself shouldn't use your own licence's extras if it's for free users. If you add email or SharePoint as Knowledge, free users won't get what they expect. Keep Knowledge empty unless the pack says otherwise.

## The Laya Excel Expert for SharePoint

This agent needs a backend, so it can't be built in Agent Builder. See [deploy-sharepoint-backend.md](deploy-sharepoint-backend.md). Leave it until the rest is running.

## Suggested rollout

The company-wide plan is in [ROLLOUT.md](../../ROLLOUT.md). For the agents themselves:

| Wave | Agents | Who |
|---|---|---|
| 1 | Laya AI Helper, Prompt Coach, Second Check, Comms Writer, Document Summariser, PII Guard, Privacy & AI Check | 10-15 volunteers from 2-3 teams, including at least one unlicensed person in each |
| 2 | + the Excel agents | Same pilot group |
| 3 | + Document Co-author, Meeting Actions, Presentation Builder; + the three paid agents, for licensed people | Widen to the pilot teams |
| 4 | + Idea Refiner, Process & SOP Builder, Project Planner, Requirements Writer, Agile Coach | All staff |

## Keeping agents up to date

1. Change the skill, following [how to write skills](../../best-practices/04-writing-skills.md). Run `python tools/validate_skills.py` and `python -m pytest`.
2. Bump `adlc-version` in the skill, and `app_version` in `package.yaml`.
3. Rebuild, then re-upload the zip (the app ID stays the same), or paste the new instructions into Agent Builder.
4. Agents in the catalog may need resubmitting after a change.
