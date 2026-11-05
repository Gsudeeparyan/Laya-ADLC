# GitHub organisation and enterprise checklist

**For GitHub admins.** These settings hold whatever anyone types. **Nothing here has been changed in Laya's GitHub:** it's a list of things to decide. GitHub changes menus and names often, so check against [its docs](https://docs.github.com/en/copilot).

**Assumption:** Laya is on GitHub with Copilot Business or Enterprise. Enterprise-level items need Enterprise. Tell the library owner if that's wrong: the repo-level parts still work.

## Copilot policies

- [ ] Decide who gets Copilot, and in which organisations.
- [ ] Set enterprise-wide baselines under **Enterprise managed settings**, which organisation owners can tighten ([guardrails tutorial](https://docs.github.com/en/enterprise-cloud@latest/copilot/tutorials/cloud-agent/build-guardrails)).
- [ ] **Models:** choose which are allowed. Each has its own data handling terms, so have the vendor owner and DPO check them.
- [ ] **Suggestions matching public code:** set a position. Check with Legal how this relates to any IP protection in the contract **[to confirm against Laya's contract]**.
- [ ] **Data use:** confirm from GitHub's Trust Center and your contract how Business or Enterprise data is handled, including retention. Our search found only community posts on retention, so don't rely on those.

## Copilot in the cloud (cloud agent)

- [ ] Decide which organisations and repositories can use it. Start small.
- [ ] Use **GitHub-hosted runners**, so each session gets a fresh machine. Self-hosted ones should be ephemeral.
- [ ] **Firewall:** on by default, and organisation owners can configure it. [It isn't a complete solution](https://docs.github.com/en/copilot/customizing-copilot/customizing-or-disabling-the-firewall-for-copilot-coding-agent): it doesn't cover setup steps or MCP servers, and isn't compatible with self-hosted runners or Windows.
- [ ] Keep its **validation tools on**: CodeQL, secret scanning, dependency checks, Copilot code review.
- [ ] Review default `GITHUB_TOKEN` permissions, because `copilot-setup-steps.yml` uses them.
- [ ] Keep Actions secrets away from it. Give it only the secrets it needs, in its own environment.
- [ ] Decide whether workflows on Copilot's pull requests need approval to run (on by default).

## Rulesets

- [ ] Apply a ruleset to agent-targeted repos: see `repo-kit/.github/rulesets/main-protection.json`.
- [ ] **Require review from Code Owners,** with CODEOWNERS protecting harness files.
- [ ] Require the `checks` and `dependencies` status checks.
- [ ] Confirm no ruleset blocks Copilot's commit metadata.
- [ ] Protect agent definition files. Note that an enterprise ruleset may also stop organisation owners editing organisation-level agents, so narrow its target if needed.

## Security features

- [ ] Secret scanning with **push protection**.
- [ ] CodeQL default setup.
- [ ] Dependabot alerts, and dependency review. On private repos these may need GitHub's security licence **[to confirm against Laya's plan]**.

## MCP servers

- [ ] Default to none. Add servers to an allowlist after `skill-intake` and a security review.
- [ ] In VS Code, use the `ChatMCP` policy to limit servers to a curated registry, and `McpGalleryServiceUrl` for a private one.

## VS Code policies

From [VS Code's security guide](https://code.visualstudio.com/docs/copilot/security). It warns that Copilot harness sessions don't fully enforce some of these (`ChatAgentMode`, `ChatMCP` and `ChatToolsEligibleForAutoApproval`), so check its notes before relying on them.

- [ ] `ChatToolsAutoApprove`: block global auto-approval.
- [ ] `ChatToolsTerminalEnableAutoApprove`: decide on terminal rules. Rule-based approval is best-effort.
- [ ] `ChatAgentExtensionTools`: decide whether to block tools from extensions.
- [ ] `ChatAgentMode`: only if you need to turn agent mode off.

## Content exclusion

- [ ] Set exclusions for sensitive paths, but **don't treat them as a boundary**. [GitHub says](https://docs.github.com/en/copilot/concepts/context/content-exclusion) they aren't a substitute for operating-system permissions, may miss indirect access, don't apply to symlinks or remote filesystems, and may not bind third-party MCP servers.
- [ ] Keep real member data and secrets out of repos altogether.

## Sharing skills and agents

- [ ] **Organisation instructions:** add a short set of Laya rules. They apply on GitHub.com and in code review, [not in local IDE sessions](https://docs.github.com/en/copilot/reference/custom-instructions-support), which is why each repo also has its own.
- [ ] **Organisation agents:** [`/agents` in the `.github-private` repo](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents) (public preview). Test in `.github/agents` first, then move to `/agents` to release.
- [ ] **Plugin marketplace:** with [managed settings](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/use-managed-settings/manage-plugin-marketplaces-and-plugins):

```json
{
  "extraKnownMarketplaces": {
    "laya-adlc": { "source": { "source": "github", "repo": "<laya-org>/laya-adlc" } }
  },
  "enabledPlugins": { "laya-engineering@laya-adlc": true }
}
```

`strictKnownMarketplaces` limits installs to listed sources, and also turns off the built-in marketplaces. Members need read access to the repo.

- [ ] **Skills:** decide whether developers may install from public sources. `gh skill` [warns](https://cli.github.com/manual/gh_skill_install) that skills aren't verified by GitHub.

## Monitoring

- [ ] **Audit logs:** under AI controls, review agentic activity. The log [doesn't include client session data](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-enterprise/review-audit-logs), such as prompts.
- [ ] Streaming agent session events: public preview, for Enterprise Managed Users or data residency.
- [ ] [Copilot usage metrics](https://docs.github.com/en/copilot/concepts/copilot-metrics): turn on the policy. Report by team, not by person.
- [ ] Review cloud agent session logs for T2 work.

## Compliance

- [ ] Add GitHub to the ICT third-party register, if it applies **[Compliance to confirm]**.
- [ ] Check the data residency option against Laya's requirements **[to confirm]**.
- [ ] Add GitHub Copilot to the [AI use register](../../roles-and-lifecycle/README.md#the-ai-use-register).

See the [platform admin role card](../../roles-and-lifecycle/cards/platform-admins.md).
