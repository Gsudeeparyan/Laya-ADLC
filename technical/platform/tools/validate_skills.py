"""Check every skill against the ADLC authoring rules (best-practices/04-writing-skills.md).

    python tools/validate_skills.py

Checks: frontmatter fields, required sections, the 8,000-character Copilot limit
(shared preamble + skill body), a STOP point before any file is changed, at least one
"Done when" completion criterion, no restated question style (the preamble owns it),
catalog and agent.yaml consistency, relative links, the licence boundary (a free-tier
agent can use nothing that needs the paid licence), that the AI Helper can route to every
agent, and that every agent named in a skill exists. Exits 1 if anything fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import AGENTS, CATALOG, PII_GUARD, PREAMBLE, SKILLS, TIERS  # noqa: E402

M365_LIMIT = 8000
AGENT_BUILDER_NAME_LIMIT = 30
# From Microsoft's "Agent capabilities and licensing models" table (checked 05/11/2026).
FREE_CAPABILITIES = {"code_interpreter", "web_search"}
PAID_CAPABILITIES = {"sharepoint_sites", "email", "teams_messages", "meetings", "people"}
REQUIRED_SECTIONS = (
    "## Role and goal",
    "## When to use",
    "## What to ask for",
    "## Steps",
    "## Output format",
    "## Guardrails",
    "## Carrying on from an uploaded file",
)
REQUIRED_METADATA = ("adlc-category", "adlc-batch", "adlc-version", "m365-agent")
# The preamble is the single source of truth for how agents ask questions (rounds).
RESTATED_QUESTION_STYLE = re.compile(r"one question (at a time|per message)|\bone at a time\b", re.IGNORECASE)
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)
LINK = re.compile(r"\]\((?!https?:|mailto:|#)([^)]+)\)")
AGENT_MENTION = re.compile(r"\bLaya ((?:[A-Z][\w'-]*|&|for|\(Start|Here\))(?: (?:[A-Z][\w'-]*|&|for|\(Start|Here\)))*)")
NOT_AGENTS = ("Healthcare", "PowerPoint")


def parse_skill(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        raise ValueError("missing YAML frontmatter between --- lines")
    return yaml.safe_load(m.group(1)) or {}, m.group(2).strip()


def preamble() -> str:
    return PREAMBLE.read_text(encoding="utf-8").strip()


def pii_guard() -> str:
    return PII_GUARD.read_text(encoding="utf-8").strip()


def instructions_for(body: str, data_guard: bool = False) -> str:
    """What goes into the Copilot agent's Instructions box: preamble (+ data guard) + skill body."""
    parts = [preamble()] + ([pii_guard()] if data_guard else []) + [body.strip()]
    return "\n\n".join(parts)


def uses_data_guard(fm: dict) -> bool:
    return bool((fm.get("metadata") or {}).get("adlc-data-guard"))


def load_catalog() -> dict:
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


def validate_all() -> tuple[list[str], list[tuple[str, int]]]:
    errors: list[str] = []
    sizes: list[tuple[str, int]] = []
    catalog = load_catalog()
    entries = {e["id"]: e for e in catalog["skills"]}
    locations = {p.parent.name: (tier, p) for tier, base in TIERS.items() for p in (base / "skills").glob("*/SKILL.md")}
    folders = sorted(locations)
    agent_names = {e["name"] for e in catalog["skills"]}

    for missing in sorted(set(entries) - set(folders)):
        errors.append(f"{missing}: listed in catalog.yaml but skills/{missing}/SKILL.md does not exist")
    for extra in sorted(set(folders) - set(entries)):
        errors.append(f"{extra}: has a SKILL.md but is not listed in catalog.yaml")

    for sid in folders:
        tier, path = locations[sid]
        try:
            fm, body = parse_skill(path)
        except ValueError as exc:
            errors.append(f"{sid}: {exc}")
            continue
        err = lambda msg: errors.append(f"{sid}: {msg}")  # noqa: E731
        if fm.get("name") != sid:
            err(f"frontmatter name '{fm.get('name')}' must equal the folder name")
        desc = str(fm.get("description", ""))
        if not desc or len(desc) > 1024:
            err(f"description must be 1-1024 characters (is {len(desc)})")
        if "use when" not in desc.lower():
            err("description must say when to use it ('Use when ...')")
        if not fm.get("license"):
            err("license is required")
        meta = fm.get("metadata") or {}
        for k in REQUIRED_METADATA:
            if k not in meta:
                err(f"metadata.{k} is required")
        for k, v in meta.items():
            if not isinstance(v, str):
                err(f"metadata.{k} must be a string (Agent Skills spec); quote it")
        for section in REQUIRED_SECTIONS:
            if not re.search(rf"^{re.escape(section)}", body, re.MULTILINE):
                err(f"missing section '{section}'")
        if "STOP" not in body:
            err("needs at least one STOP point (wait for the person before acting)")
        if "Done when" not in body:
            err("needs at least one 'Done when' completion criterion on a step")
        if RESTATED_QUESTION_STYLE.search(body):
            err("restates the question style; the shared preamble owns it (ask in rounds)")
        size = len(instructions_for(body, uses_data_guard(fm)))
        sizes.append((sid, size))
        if size > M365_LIMIT:
            err(f"preamble + body is {size} characters; Copilot allows {M365_LIMIT}")
        for target in LINK.findall(body):
            if not (path.parent / target.split("#")[0]).exists():
                err(f"broken link to {target}")

        for mention in AGENT_MENTION.findall(body):
            if not mention.startswith(NOT_AGENTS) and not any(n.startswith(f"Laya {mention}") or f"Laya {mention}".startswith(n) for n in agent_names):
                err(f"names 'Laya {mention}', which isn't in the catalog")

        entry = entries.get(sid, {})
        if entry and entry.get("tier") != tier:
            err(f"catalog tier '{entry.get('tier')}' differs from its folder '{tier}'")
        agent_id = meta.get("m365-agent")
        if entry and entry.get("agent") != agent_id:
            err(f"catalog agent '{entry.get('agent')}' differs from metadata m365-agent '{agent_id}'")
        if entry and str(entry.get("batch")) != str(meta.get("adlc-batch")):
            err("catalog batch differs from metadata adlc-batch")
        agent_file = TIERS[tier] / "agents" / str(agent_id) / "agent.yaml"
        if not agent_file.exists():
            err(f"{tier}/agents/{agent_id}/agent.yaml is missing")
            continue
        agent = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
        if agent.get("skill") != sid:
            err(f"agent.yaml skill '{agent.get('skill')}' should be '{sid}'")
        if len(str(agent.get("name", ""))) > 100:
            err("agent name must be 100 characters or fewer")
        if entry and agent.get("name") != entry.get("name"):
            err(f"agent.yaml name '{agent.get('name')}' differs from the catalog's '{entry.get('name')}'")
        if not agent.get("actions") and len(str(agent.get("name", ""))) > AGENT_BUILDER_NAME_LIMIT:
            err(f"agent name must be {AGENT_BUILDER_NAME_LIMIT} characters or fewer for Agent Builder")
        caps = agent.get("capabilities") or {}
        in_use = {k for k, v in caps.items() if v}
        if uses_data_guard(fm) and "code_interpreter" not in in_use:
            err("adlc-data-guard needs code_interpreter: the guard's steps run in Code Interpreter")
        for unknown in sorted(set(caps) - FREE_CAPABILITIES - PAID_CAPABILITIES):
            err(f"unknown capability '{unknown}'; add it to the licence table in validate_skills.py first")
        if tier == "everyone":
            for paid in sorted(in_use & PAID_CAPABILITIES):
                err(f"'{paid}' needs the paid licence, so this agent can't be in everyone/")
        elif not in_use & PAID_CAPABILITIES:
            err("uses nothing that needs the paid licence, so it belongs in everyone/")
        if not 1 <= len(str(agent.get("description", ""))) <= 1000:
            err("agent description must be 1-1000 characters")
        starters = agent.get("conversation_starters") or []
        if not 1 <= len(starters) <= 12:
            err("agent needs 1-12 conversation starters")
        for s in starters:
            if not s.get("title") or not s.get("text"):
                err("every conversation starter needs a title and text")

    if "start-here" in locations:
        _, router_body = parse_skill(locations["start-here"][1])
        for name in sorted(agent_names - {"Laya AI Helper (Start Here)"}):
            if name not in router_body:
                errors.append(f"start-here: the AI Helper can't route to {name}; add it to the agent map")
    return errors, sizes


def main() -> int:
    errors, sizes = validate_all()
    for sid, size in sizes:
        bar = "#" * int(30 * size / M365_LIMIT)
        print(f"{sid:28} {size:5} / {M365_LIMIT}  {bar}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"\nAll {len(sizes)} skills pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
