import json
import re

import pytest
import yaml

from paths import DEV_AGENTS, DEV_SKILLS, ROOT, SKILLS_AND_AGENTS

SKILLS = sorted(DEV_SKILLS.glob("*/SKILL.md"))
AGENTS = sorted(DEV_AGENTS.glob("*.agent.md"))
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)
SIBLING_REF = re.compile(r"`\.\./([a-z0-9-]+)/SKILL\.md`")
LINK = re.compile(r"\]\((?!https?:|#)([^)]+)\)")
LAYA_SKILLS = {
    "ask-laya", "member-data-safety", "legacy-change", "production-ready", "data-design", "bounded-contexts",
    "refactoring-pass", "security-review", "test-strategy", "release-change", "incident-response",
    "ai-feature-check", "harness-setup", "skill-intake",
}
ROLE_AGENTS = {
    "laya-planner", "laya-implementer", "laya-reviewer", "laya-security-reviewer", "laya-test-engineer",
    "laya-data-engineer", "laya-release-manager", "laya-incident-responder",
}
READ_ONLY_AGENTS = {"laya-planner", "laya-reviewer", "laya-security-reviewer"}
# Upstream's illustrations of a format, not links to follow.
ILLUSTRATIVE_LINKS = {"wayfinder", "domain-modeling", "teach"}


def parse(path):
    m = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m.group(1)), m.group(2)


def test_library_has_the_laya_skills_and_all_27_of_matts():
    names = {p.parent.name for p in SKILLS}
    assert LAYA_SKILLS <= names
    assert len(names - LAYA_SKILLS) == 27


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_every_skill_meets_the_agent_skills_spec(path):
    fm, _ = parse(path)
    assert fm["name"] == path.parent.name
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"])
    assert 1 <= len(fm["description"]) <= 1024
    assert fm.get("license"), "the licence must travel with the skill"


@pytest.mark.parametrize("name", sorted(LAYA_SKILLS))
def test_laya_skills_follow_the_invocation_rules(name):
    fm, body = parse(DEV_SKILLS / name / "SKILL.md")
    if fm.get("disable-model-invocation"):
        assert "use when" not in fm["description"].lower(), "user-invoked descriptions are human-facing"
    else:
        assert "Use when" in fm["description"], "model-invoked descriptions carry their triggers"
        assert "Done when" in body, "steps need a completion criterion"


def test_matts_skills_record_their_pinned_source():
    for path in SKILLS:
        if path.parent.name not in LAYA_SKILLS:
            fm, _ = parse(path)
            assert fm["metadata"]["source"].startswith("mattpocock/skills@"), path


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_links_and_sibling_skill_references_resolve(path):
    _, body = parse(path)
    for name in SIBLING_REF.findall(body):
        assert (DEV_SKILLS / name / "SKILL.md").exists(), f"refers to '{name}', which isn't in the library"
    if path.parent.name not in ILLUSTRATIVE_LINKS:
        for target in LINK.findall(body):
            assert (path.parent / target).exists(), f"broken link {target}"


def test_sibling_reference_check_is_not_vacuous():
    bodies = "".join(path.read_text(encoding="utf-8") for path in SKILLS)
    assert len(SIBLING_REF.findall(bodies)) >= 25


def test_book_rules_keep_their_attribution():
    rules = list(DEV_SKILLS.glob("*/RULES.md"))
    assert len(rules) == 5
    for path in rules:
        head = path.read_text(encoding="utf-8")[:400]
        assert "agent-rules-books" in head and "MIT License" in head, path


def test_role_agents_are_complete():
    assert {p.name.removesuffix(".agent.md") for p in AGENTS} == ROLE_AGENTS
    for path in AGENTS:
        fm, body = parse(path)
        assert fm["name"].startswith("Laya ") and fm["description"]
        assert "Done when" in body, path
        assert len(body) < 30000, "GitHub's limit for an agent prompt"


def test_review_agents_cannot_edit_or_run_anything():
    for name in READ_ONLY_AGENTS:
        fm, _ = parse(DEV_AGENTS / f"{name}.agent.md")
        assert set(fm["tools"]) == {"read", "search"}, name


def test_agents_only_name_skills_that_exist():
    skills = {p.parent.name for p in SKILLS}
    for path in AGENTS:
        _, body = parse(path)
        for word in re.findall(r"`([a-z]+(?:-[a-z]+)+|tdd|retro)`", body):
            if word not in {"to-do"}:
                assert word in skills, f"{path.name} names `{word}`"


def test_handoffs_point_at_real_agents():
    for path in AGENTS:
        fm, _ = parse(path)
        for handoff in fm.get("handoffs", []):
            assert handoff["agent"] in ROLE_AGENTS


def test_plugin_and_marketplace_agree():
    plugin = json.loads((SKILLS_AND_AGENTS / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".github" / "plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert market["owner"]["name"] and re.fullmatch(r"[a-z0-9-]{1,64}", market["name"])
    entry = market["plugins"][0]
    assert entry["name"] == plugin["name"] and entry["version"] == plugin["version"]
    assert (ROOT / entry["source"]).resolve() == SKILLS_AND_AGENTS.resolve()
