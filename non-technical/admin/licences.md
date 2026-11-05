# Microsoft Copilot licences: what works for whom

**For:** IT, AI champions and anyone building agents. Staff have their own version: [Which Copilot do I have?](../staff-guide/which-copilot-do-i-have.md)

Laya has two groups: most staff have **Copilot Chat** (free, included with Microsoft 365), and some have the paid **Microsoft Copilot** licence. Microsoft renamed these in 2026, so older pages say "Microsoft 365 Copilot" and "Microsoft 365 Copilot Chat". This library assumes pay-as-you-go billing is **off**.

Everything below comes from Microsoft Learn pages checked on 05/11/2026 (see [sources](../../best-practices/sources.md)). Microsoft changes these often, so re-check before relying on any detail.

## What agents can use

This is Microsoft's table, and `validate_skills.py` enforces the same boundary: an agent in `everyone/` can't use anything marked as needing more.

| Capability | Copilot Chat, no billing | Copilot Chat, pay-as-you-go | Paid licence |
|---|---|---|---|
| Custom instructions | Yes | Yes | Yes |
| Code interpreter | Yes | Yes | Yes |
| Custom actions | Yes | Yes | Yes |
| Image generator | Yes | Yes | Yes |
| Web search (including limited to chosen sites) | Yes | Yes | Yes |
| SharePoint data | No | Yes (metered) | Yes |
| Embedded file content | No | Yes (metered) | Yes |
| Copilot connectors, Dataverse | No | Yes (metered) | Yes |
| Email | No | No | Yes |
| Teams messages, Teams meetings | No | No | Yes |
| People | No | No | Yes |

## Using agents and building them are different

| Task | Who can do it |
|---|---|
| **Use** an agent built from instructions and code interpreter | Everyone with Copilot Chat |
| **Build** an agent in Agent Builder | People with the paid licence, or in a tenant with pay-as-you-go (Microsoft's admin guide) |
| **Deploy** a zip package to everyone | IT, in the Microsoft 365 admin center |
| **Add SKILL.md packages** to an agent | People with the paid licence, or pay-as-you-go |

So at Laya, licensed people or IT build the agents, and everyone uses them.

## What this means for the Laya agents

| Agents | Work for | Why |
|---|---|---|
| 21 agents in `everyone/` | Everyone | Instructions and code interpreter only; the SharePoint Excel agent adds custom actions |
| Laya Catch Me Up, Laya Meeting Recap | Paid licence only | They read email, Teams and meetings |
| Laya Policy Finder | Paid licence, or anyone if pay-as-you-go is turned on | It reads SharePoint |

**Share the paid agents only with a security group of licensed people.** Others would see an agent that can't do its job.

## Check this first in Laya's tenant

**Do free users really get Code Interpreter?** Microsoft's pages disagree:
- The licensing table and the Code Interpreter page (updated 22/10/2026) say yes, including for "Copilot Chat users without metered usage enabled".
- A note on the declarative agent schema pages (v1.7 and v1.9) says agents with any capability other than web search need metered usage or a licence.

The newer and more specific pages say yes, so the library is built that way. **Prove it with an unlicensed test account before you roll out**: it's step 1 in the [smoke test](smoke-test.md). If it fails, the Excel, PII Guard and file-producing agents need pay-as-you-go or a licence for those users.

## Other things worth knowing

- **Files are temporary.** Files from Code Interpreter last for the session only, so every agent tells people to download them before closing the chat.
- **Uploaded files** are stored in the user's OneDrive for Business.
- **Web search** queries go to Bing and are outside the EU Data Boundary. Laya's agents keep web search off.
- **Some models** are outside the EU Data Boundary. Microsoft's enterprise data protection page lists which, so check it before allowing them.
- **Copilot Chat in Outlook** works for everyone and can read that person's mail, calendar, meetings, chats and a limited set of files.
- **Copilot in Word, Excel, PowerPoint and OneNote** on the free version: Microsoft announced it was reserving this for licensed users from April 2026, while its support page still lists a "Basic" label with standard access. Check your tenant.
- **Word, Excel and PowerPoint agents:** Microsoft's pages also differ on whether these are licensed-only.
- **Instructions** are limited to 8,000 characters, and Microsoft warns against moving instructions into SharePoint to get around that: knowledge content isn't treated as trusted instructions.

## If Laya turns on pay-as-you-go later

Policy Finder could go to everyone. An admin creates a billing policy on an Azure subscription, connects it to the SharePoint agents service, and adds users to the security group assigned to it. Set a budget alert first: charges are metered in Copilot Credits.
