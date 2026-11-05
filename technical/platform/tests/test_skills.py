import json
import shutil
import zipfile
from pathlib import Path

import pytest
import yaml

import build_agents
import validate_skills
from paths import PLATFORM, TIERS

SCHEMAS = PLATFORM / "tests" / "schemas"
TOTAL_AGENTS = 24
PAID_AGENTS = {"laya-catch-me-up", "laya-meeting-recap", "laya-policy-finder"}


def test_every_skill_passes_the_authoring_rules():
    errors, sizes = validate_skills.validate_all()
    assert errors == []
    assert len(sizes) == TOTAL_AGENTS
    assert all(size <= validate_skills.M365_LIMIT for _, size in sizes)


def test_preamble_carries_the_non_expert_rules():
    text = validate_skills.preamble()
    for rule in ("Ask in rounds", '"yes" accepts', "Finding facts is your job", "just do it",
                 "re-pitch", "What next?", "don't refuse", "SharePoint", "before you close this chat"):
        assert rule in text


@pytest.fixture(scope="module")
def built_agents(tmp_path_factory):
    out = tmp_path_factory.mktemp("agents")
    original = build_agents.DIST
    build_agents.DIST = out
    try:
        rows = build_agents.build()
    finally:
        build_agents.DIST = original
    return out, rows


def pkg_of(out: Path, aid: str) -> Path:
    return next(out.glob(f"*/{aid}")) / "appPackage"


def test_agent_packages_are_complete_and_valid(built_agents):
    out, rows = built_agents
    assert len(rows) == TOTAL_AGENTS
    for aid, size in rows:
        pkg = pkg_of(out, aid)
        has_actions = (pkg / "ai-plugin.json").exists()
        assert size <= 8000
        manifest = json.loads((pkg / "manifest.json").read_text(encoding="utf-8"))
        agent = json.loads((pkg / "declarativeAgent.json").read_text(encoding="utf-8"))
        assert manifest["copilotAgents"]["declarativeAgents"][0]["file"] == "declarativeAgent.json"
        assert len(manifest["name"]["short"]) <= 30 and len(manifest["description"]["short"]) <= 80
        assert agent["instructions"] == "$[file('instruction.txt')]"
        assert 1 <= len(agent["conversation_starters"]) <= 12
        assert len((pkg / "instruction.txt").read_text(encoding="utf-8")) == size
        with zipfile.ZipFile(pkg.parent / f"{aid}.zip") as z:
            expected = ["manifest.json", "declarativeAgent.json", "instruction.txt", "color.png", "outline.png"]
            if has_actions:
                expected += ["ai-plugin.json", "openapi.yaml"]
            assert sorted(z.namelist()) == sorted(expected)


def test_every_package_meets_microsofts_published_schema(built_agents):
    jsonschema = pytest.importorskip("jsonschema")
    agent_schema = json.loads((SCHEMAS / "declarative-agent-v1.9.schema.json").read_text(encoding="utf-8"))
    plugin_schema = json.loads((SCHEMAS / "plugin-v2.4.schema.json").read_text(encoding="utf-8"))
    out, rows = built_agents
    for aid, _ in rows:
        pkg = pkg_of(out, aid)
        document = json.loads((pkg / "declarativeAgent.json").read_text(encoding="utf-8"))
        document = {k: v for k, v in document.items() if k != "$schema"}
        jsonschema.validate(document, agent_schema)
        if (pkg / "ai-plugin.json").exists():
            plugin = json.loads((pkg / "ai-plugin.json").read_text(encoding="utf-8"))
            jsonschema.validate({k: v for k, v in plugin.items() if k != "$schema"}, plugin_schema)


def test_tiers_land_in_their_own_folders(built_agents):
    out, _ = built_agents
    assert {p.name for p in (out / "paid-licence").iterdir()} == PAID_AGENTS
    assert not PAID_AGENTS & {p.name for p in (out / "everyone").iterdir()}


def test_free_agents_use_only_what_free_copilot_chat_allows(built_agents):
    out, _ = built_agents
    allowed = {"CodeInterpreter", "WebSearch"}
    for pkg_dir in (out / "everyone").iterdir():
        agent = json.loads((pkg_dir / "appPackage" / "declarativeAgent.json").read_text(encoding="utf-8"))
        assert {c["name"] for c in agent["capabilities"]} <= allowed, pkg_dir.name


def test_paid_agents_declare_their_grounding(built_agents):
    out, _ = built_agents
    for aid in PAID_AGENTS:
        agent = json.loads((pkg_of(out, aid) / "declarativeAgent.json").read_text(encoding="utf-8"))
        assert {c["name"] for c in agent["capabilities"]} & {"Email", "TeamsMessages", "Meetings", "People", "OneDriveAndSharePoint"}


def test_policy_finder_answers_only_from_its_sources(built_agents):
    out, _ = built_agents
    agent = json.loads((pkg_of(out, "laya-policy-finder") / "declarativeAgent.json").read_text(encoding="utf-8"))
    assert agent["behavior_overrides"]["special_instructions"]["discourage_model_knowledge"] is True


def test_app_ids_are_stable_and_unique(built_agents):
    out, rows = built_agents
    ids = {aid: json.loads((pkg_of(out, aid) / "manifest.json").read_text(encoding="utf-8"))["id"] for aid, _ in rows}
    assert len(set(ids.values())) == len(ids)
    # The rename to "Privacy & AI Check" kept its id, so an update replaces the live agent instead of duplicating it.
    assert ids["laya-privacy-check"] == str(build_agents.uuid.uuid5(build_agents.NAMESPACE, "laya-privacy-check"))


def test_sharepoint_agent_plugin_confirms_before_saving(built_agents):
    out, _ = built_agents
    pkg = pkg_of(out, "laya-excel-expert-sharepoint")
    plugin = json.loads((pkg / "ai-plugin.json").read_text(encoding="utf-8"))
    confirm = {f["name"] for f in plugin["functions"] if "confirmation" in f.get("capabilities", {})}
    assert confirm == {"applyChanges", "createPiiFreeCopy", "restorePiiCopy"}
    assert len(plugin["name_for_human"]) <= 20
    spec = yaml.safe_load((pkg / "openapi.yaml").read_text(encoding="utf-8"))
    ops = {op["operationId"] for path in spec["paths"].values() for op in path.values()}
    assert ops == {f["name"] for f in plugin["functions"]}


def test_preamble_and_guard_shape_every_data_agent():
    guard = validate_skills.pii_guard()
    assert "never refuse" in guard and "PERSON_001" in guard
    _, sizes = validate_skills.validate_all()
    assert dict(sizes)["excel-expert"] > len(guard)


def test_agent_builder_pack_contains_full_instructions(built_agents):
    out, _ = built_agents
    pkg = pkg_of(out, "laya-excel-expert")
    pack = (pkg.parent / "agent-builder.md").read_text(encoding="utf-8")
    assert (pkg / "instruction.txt").read_text(encoding="utf-8") in pack
    assert "(code interpreter) **On**" in pack


def test_packs_warn_when_it_has_to_set_something_up(built_agents):
    out, _ = built_agents
    index = (out / "README.md").read_text(encoding="utf-8")
    assert "IT adds Laya's approved SharePoint sites first" in index
    assert "needs the SharePoint backend deployed first" in index
    pack = (pkg_of(out, "laya-excel-expert-sharepoint").parent / "agent-builder.md").read_text(encoding="utf-8")
    assert "can't be made in Agent Builder" in pack


def test_building_never_touches_the_rest_of_ready_to_use(tmp_path, monkeypatch):
    ready = tmp_path / "ready-to-use"
    (ready / "templates").mkdir(parents=True)
    (ready / "templates" / "keep.txt").write_text("keep", encoding="utf-8")
    monkeypatch.setattr(build_agents, "DIST", ready / "agents")
    build_agents.build()
    assert (ready / "templates" / "keep.txt").exists()


# ---------------------------------------------------------------- the validator's new rules go red when broken


@pytest.fixture
def broken_tier(tmp_path, monkeypatch):
    """A throwaway copy of the free tier, so a rule can be broken without touching the real files."""
    copy = tmp_path / "everyone"
    shutil.copytree(TIERS["everyone"], copy)
    monkeypatch.setitem(validate_skills.TIERS, "everyone", copy)
    return copy


def edit_yaml(path, change):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_licence_rule_goes_red_if_a_free_agent_reads_email(broken_tier):
    edit_yaml(broken_tier / "agents/laya-comms-writer/agent.yaml", lambda a: a["capabilities"].update(email=True))
    errors, _ = validate_skills.validate_all()
    assert any("comms-writer" in e and "needs the paid licence" in e for e in errors)


def test_unknown_capability_goes_red(broken_tier):
    edit_yaml(broken_tier / "agents/laya-comms-writer/agent.yaml", lambda a: a["capabilities"].update(dataverse=True))
    errors, _ = validate_skills.validate_all()
    assert any("unknown capability 'dataverse'" in e for e in errors)


def test_router_rule_goes_red_if_an_agent_is_missing_from_the_map(broken_tier):
    path = broken_tier / "skills/start-here/SKILL.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Laya Second Check", "Second Check"), encoding="utf-8")
    errors, _ = validate_skills.validate_all()
    assert any("can't route to Laya Second Check" in e for e in errors)


def test_stale_agent_name_goes_red(broken_tier):
    path = broken_tier / "skills/idea-refiner/SKILL.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Laya Privacy & AI Check", "Laya Privacy Checker"), encoding="utf-8")
    errors, _ = validate_skills.validate_all()
    assert any("names 'Laya Privacy Checker'" in e for e in errors)


def test_guard_without_code_interpreter_goes_red(broken_tier):
    edit_yaml(broken_tier / "agents/laya-second-check/agent.yaml", lambda a: a["capabilities"].update(code_interpreter=False))
    errors, _ = validate_skills.validate_all()
    assert any("second-check" in e and "adlc-data-guard needs code_interpreter" in e for e in errors)


def test_non_string_metadata_goes_red(broken_tier):
    path = broken_tier / "skills/second-check/SKILL.md"
    path.write_text(path.read_text(encoding="utf-8").replace('adlc-data-guard: "true"', "adlc-data-guard: true"), encoding="utf-8")
    errors, _ = validate_skills.validate_all()
    assert any("metadata.adlc-data-guard must be a string" in e for e in errors)
