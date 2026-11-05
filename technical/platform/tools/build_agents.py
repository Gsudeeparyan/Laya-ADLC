"""Build Microsoft Copilot agent packs from the skills.

    python tools/build_agents.py

For every agent in non-technical/<tier>/agents/<id>/agent.yaml this writes
non-technical/ready-to-use/agents/<tier>/<id>/:
  agent-builder.md   copy-paste pack for Agent Builder
  appPackage/        Agents Toolkit package: manifest.json, declarativeAgent.json,
                     instruction.txt, color.png, outline.png
  <id>.zip           the zipped app package, ready for upload by IT
and ready-to-use/agents/README.md, an index of every agent.

Instructions = the shared preamble + (the PII guard) + the skill body (frontmatter removed),
and must fit Copilot's 8,000-character limit.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import BACKEND, PACKAGE_SETTINGS, READY_AGENTS, TIERS  # noqa: E402
from validate_skills import M365_LIMIT, instructions_for, parse_skill, uses_data_guard  # noqa: E402

DIST = READY_AGENTS  # only this folder is ever cleared; the rest of ready-to-use is left alone
NAMESPACE = uuid.UUID("6f1c2a52-3d0e-4c1b-9a51-0d7a1c0e5a11")
TIER_LABEL = {"everyone": "Everyone", "paid-licence": "Paid licence only"}
SWITCHED_ON_KNOWLEDGE = [("email", "My emails"), ("teams_messages", "Teams chats and channels"),
                         ("meetings", "Teams meetings"), ("people", "People in the organisation")]


def load_package_settings() -> dict:
    return yaml.safe_load(PACKAGE_SETTINGS.read_text(encoding="utf-8"))


def initials(name: str) -> str:
    words = [w for w in name.replace("Laya", "").replace("(Start Here)", "").replace("&", "").split() if w]
    return "".join(w[0] for w in words[:2]).upper() or "AI"


def make_icons(target: Path, label: str, colour: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    def font(size):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)

    img = Image.new("RGBA", (192, 192), colour)
    d = ImageDraw.Draw(img)
    d.text((96, 96), label, fill="white", font=font(84), anchor="mm")
    img.save(target / "color.png")

    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((1, 1, 30, 30), radius=6, outline="white", width=2)
    d.text((16, 16), label[:2], fill="white", font=font(13), anchor="mm")
    out.save(target / "outline.png")


def needs_it_setup(agent: dict) -> str | None:
    """Why this pack can't be used as it stands, if there's a reason."""
    if agent.get("actions"):
        return "needs the SharePoint backend deployed first"
    if agent["capabilities"].get("sharepoint_sites"):
        return "IT adds Laya's approved SharePoint sites first"
    return None


def intro(agent: dict) -> str:
    if agent.get("actions"):
        return ("**This agent uses actions (the SharePoint backend), so it can't be made in Agent Builder.** "
                f"IT deploys the app package `{agent['id']}.zip`: see `non-technical/admin/deploy-sharepoint-backend.md`. "
                "The steps below are for reference only.")
    return ("Build this agent in about 5 minutes. **To build it** you need the paid Microsoft Copilot licence, "
            "or IT can deploy the zip instead (`non-technical/admin/deploy-agents.md`). "
            f"**To use it**, people need: {TIER_LABEL_LONG[agent['_tier']]}.")


TIER_LABEL_LONG = {"everyone": "any Microsoft 365 account, including free Copilot Chat",
                   "paid-licence": "the paid Microsoft Copilot licence"}


def knowledge_line(agent: dict) -> str:
    caps = agent["capabilities"]
    picks = [label for key, label in SWITCHED_ON_KNOWLEDGE if caps.get(key)]
    picks += [f"SharePoint: {site}" for site in caps.get("sharepoint_sites") or []]
    if picks:
        return "add only these: " + "; ".join(picks) + "."
    return "leave empty. Free-tier agents work from what people upload (see `non-technical/admin/licences.md`)."


def agent_builder_pack(agent: dict, instructions: str, skill_desc: str) -> str:
    starters = "\n".join(
        f"| {i} | {s['title']} | {s['text']} |" for i, s in enumerate(agent["conversation_starters"], 1)
    )
    caps = agent["capabilities"]
    code = "On" if caps.get("code_interpreter") else "Off"
    web = "On" if caps.get("web_search") else "Off"
    audience = "people with the paid licence (a security group)" if agent["_tier"] == "paid-licence" else "anyone in your organisation"
    return f"""# {agent['name']} - Agent Builder pack

*What it does:* {skill_desc}

{intro(agent)}

1. Open **Microsoft Copilot** (https://m365.cloud.microsoft/chat), select **New agent**, then **Skip to configure**.
2. **Name:** `{agent['name']}`
3. **Description:** copy this:

   > {agent['description']}

4. **Instructions:** copy everything inside the box below ({len(instructions):,} of {M365_LIMIT:,} characters).
5. **Knowledge:** {knowledge_line(agent)}
6. **Capabilities:** Create documents, charts and code (code interpreter) **{code}**. Web search **{web}**. Create images **Off**.
7. **Starter prompts:** add each title and message:

| # | Title | Message |
|---|---|---|
{starters}

8. Test it on the **Try it** tab, using `non-technical/admin/smoke-test.md`, then select **Create**.
9. **Share** it with {audience}, with "Can chat" access. To list it for everyone to find, ask your Microsoft 365 admin to publish it to the organisation's catalog.

## Instructions

```text
{instructions}
```
"""


FUNCTIONS = [
    ("inspectWorkbook", "Map a workbook in SharePoint/OneDrive: sheets, tables, columns, formulas, dropdowns, which columns hold personal data. Call first, every time.", None),
    ("queryWorkbook", "Read or count rows matching conditions, to answer questions. Personal data comes back as tokens.", None),
    ("previewChanges", "Dry run: what a list of changes would do. Nothing is saved.", None),
    ("applyChanges", "Make the changes and save the workbook in place in SharePoint (version history keeps the old copy).",
     {"title": "Save these changes to the workbook?",
      "body": "**Change:** {{function.parameters.summary}}\n\nSharePoint version history keeps the previous copy."}),
    ("scanForPii", "Check a file for personal data. Changes nothing.", None),
    ("createPiiFreeCopy", "Save a copy of a file with personal data removed, next to the original.",
     {"title": "Create a PII-free copy?", "body": "A new file '(PII removed)' will be saved next to the original."}),
    ("restorePiiCopy", "Put real values back into a PII-free copy, saved as a new '(restored)' file.",
     {"title": "Restore real values?", "body": "A new file '(restored)' containing personal data will be saved next to the clean copy."}),
]


def plugin_manifest(agent: dict, oauth_reference_id: str) -> dict:
    functions = []
    for name, description, confirm in FUNCTIONS:
        fn = {"name": name, "description": description}
        if confirm:
            fn["capabilities"] = {"confirmation": {"type": "AdaptiveCard", **confirm}}
        functions.append(fn)
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.4/schema.json",
        "schema_version": "v2.4",
        "name_for_human": "Laya Excel Actions",  # max 20 characters
        "namespace": "layaexcel",
        "description_for_human": "Inspect, query and change Excel files in SharePoint in place; remove or restore personal data.",
        "description_for_model": (
            "Use for Excel workbooks in SharePoint or OneDrive given as a link. Always call inspectWorkbook first and use "
            "its exact sheet, table and column names. Answer questions with queryWorkbook. For changes, build the ops list, "
            "call previewChanges, tell the person the plan, then applyChanges. Values like PERSON_001 are privacy tokens: "
            "use them exactly as returned and never ask for or invent real personal details."
        ),
        "functions": functions,
        "runtimes": [{
            "type": "OpenApi",
            "auth": {"type": "OAuthPluginVault", "reference_id": oauth_reference_id},
            "spec": {"url": "openapi.yaml"},
            "run_for_functions": [f[0] for f in FUNCTIONS],
        }],
    }


def manifest_capabilities(caps: dict) -> list[dict]:
    """Copilot's capability objects, for the capabilities an agent.yaml turns on. An unknown one stops the build."""
    known = {"code_interpreter": "CodeInterpreter", "web_search": "WebSearch", "email": "Email",
             "teams_messages": "TeamsMessages", "meetings": "Meetings", "people": "People"}
    out = []
    for key, value in caps.items():
        if not value:
            continue
        if key == "sharepoint_sites":
            out.append({"name": "OneDriveAndSharePoint", "items_by_url": [{"url": site} for site in value]})
        elif key in known:
            out.append({"name": known[key]})
        else:
            raise SystemExit(f"Unknown capability in agent.yaml: {key}")
    return out


def all_agents() -> list[tuple[str, Path]]:
    return [(tier, f) for tier, base in TIERS.items() for f in sorted((base / "agents").glob("*/agent.yaml"))]


def build(function_host: str | None = None, oauth_reference_id: str | None = None) -> list[tuple[str, int]]:
    settings = load_package_settings()
    function_host = function_host or os.environ.get("ADLC_FUNCTION_HOST") or "${{FUNCTION_APP_HOST}}"
    oauth_reference_id = oauth_reference_id or os.environ.get("ADLC_OAUTH_REFERENCE_ID") or "${{OAUTH_REFERENCE_ID}}"
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    rows = []
    for tier, agent_file in all_agents():
        agent = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
        agent["_tier"] = tier
        fm, body = parse_skill(TIERS[tier] / "skills" / agent["skill"] / "SKILL.md")
        instructions = instructions_for(body, uses_data_guard(fm))
        if len(instructions) > M365_LIMIT:
            raise SystemExit(f"{agent['id']}: instructions are {len(instructions)} characters (limit {M365_LIMIT})")
        out = DIST / tier / agent["id"]
        pkg = out / "appPackage"
        pkg.mkdir(parents=True)

        (out / "agent-builder.md").write_text(
            agent_builder_pack(agent, instructions, " ".join(str(fm["description"]).split())), encoding="utf-8")
        (pkg / "instruction.txt").write_text(instructions, encoding="utf-8")

        actions = agent.get("actions")
        if actions:
            spec = (BACKEND / "openapi.yaml").read_text(encoding="utf-8").replace("${{FUNCTION_APP_HOST}}", function_host)
            (pkg / "openapi.yaml").write_text(spec, encoding="utf-8")
            (pkg / "ai-plugin.json").write_text(
                json.dumps(plugin_manifest(agent, oauth_reference_id), indent=2, ensure_ascii=False), encoding="utf-8")
        schema = settings["declarative_agent_schema"]
        declarative = {
            "$schema": f"https://developer.microsoft.com/json-schemas/copilot/declarative-agent/{schema}/schema.json",
            "version": schema,
            "name": agent["name"],
            "description": agent["description"],
            "instructions": "$[file('instruction.txt')]",
            "conversation_starters": agent["conversation_starters"],
            "capabilities": manifest_capabilities(agent["capabilities"]),
        }
        if agent.get("ground_only_in_knowledge"):
            declarative["behavior_overrides"] = {"special_instructions": {"discourage_model_knowledge": True}}
        if actions:
            declarative["actions"] = [{"id": "layaExcelActions", "file": "ai-plugin.json"}]
        (pkg / "declarativeAgent.json").write_text(json.dumps(declarative, indent=2, ensure_ascii=False), encoding="utf-8")

        mv = settings["teams_manifest_version"]
        manifest = {
            "$schema": f"https://developer.microsoft.com/json-schemas/teams/v{mv}/MicrosoftTeams.schema.json",
            "manifestVersion": mv,
            "version": settings["app_version"],
            "id": str(uuid.uuid5(NAMESPACE, agent["id"])),
            "developer": settings["developer"],
            "icons": {"color": "color.png", "outline": "outline.png"},
            "name": {"short": agent["name"][:30], "full": agent["name"]},
            "description": {
                "short": agent["description"].split(". ")[0][:80],
                "full": agent["description"],
            },
            "accentColor": settings["accent_color"],
            "copilotAgents": {"declarativeAgents": [{"id": "declarativeAgent", "file": "declarativeAgent.json"}]},
            "permissions": ["identity", "messageTeamMembers"],
            "validDomains": [function_host] if actions and not function_host.startswith("$") else [],
        }
        (pkg / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        make_icons(pkg, initials(agent["name"]), settings["accent_color"])

        with zipfile.ZipFile(out / f"{agent['id']}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(pkg.iterdir()):
                z.write(f, f.name)
        rows.append((agent, tier, len(instructions)))

    index = ["# Microsoft Copilot agent packs", "",
             "Generated by `python tools/build_agents.py`. Don't edit by hand: edit the skills instead.", "",
             "| Agent | Who can use it | Instructions | Agent Builder pack | IT package | Before use |", "|---|---|---|---|---|---|"]
    for agent, tier, size in rows:
        folder = f"{tier}/{agent['id']}"
        index.append(
            f"| {agent['name']} | {TIER_LABEL[tier]} | {size:,} chars | "
            f"[agent-builder.md]({folder}/agent-builder.md) | [{agent['id']}.zip]({folder}/{agent['id']}.zip) | "
            f"{needs_it_setup(agent) or 'ready'} |"
        )
    (DIST / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return [(a["id"], s) for a, _, s in rows]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build Copilot agent packs")
    ap.add_argument("--function-host", help="e.g. layaadlc-func.azurewebsites.net (for the SharePoint agent)")
    ap.add_argument("--oauth-reference-id", help="OAuth client registration ID from the Teams Developer Portal")
    args = ap.parse_args()
    for aid, size in build(args.function_host, args.oauth_reference_id):
        print(f"{aid:32} {size:5} chars")
