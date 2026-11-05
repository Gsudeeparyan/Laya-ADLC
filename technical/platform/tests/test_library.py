"""The library as a whole: staff-facing content stays complete and honest, and the build tools really run."""

import re

import pytest
import yaml

import build_guides
import build_staff_guide
import build_templates
import check_library
from paths import BEST_PRACTICES, BY_ROLE, CATALOG, NON_TECHNICAL, PROMPTS, ROLES, ROOT, STAFF_GUIDE, TRAINING

CATALOG_NAMES = {e["name"] for e in yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["skills"]}
PLAYBOOK_SECTIONS = ("**Where AI helps:**", "**What stays with you:**", "## Jobs AI can help with",
                     "## If you have the paid licence", "## Check before you use it", "## Never hand these to AI")
CARD_SECTIONS = ("## What you own", "## What AI can do for you", "## What you must not hand over", "## Your tools", "## The evidence you leave")
AGENT_MENTION = re.compile(r"\bLaya ((?:[A-Z][\w'-]*|&|for|\(Start|Here\))(?: (?:[A-Z][\w'-]*|&|for|\(Start|Here\)))*)")
# "Laya" followed by words that aren't an agent's name.
NOT_AGENTS = ("Healthcare", "AI-safe", "PowerPoint", "Life", "Technical", "Reviewer", "Planner", "Implementer", "Security Reviewer",
              "Test Engineer", "Data Engineer", "Release Manager", "Incident Responder")


def staff_docs():
    folders = [NON_TECHNICAL / "by-role", NON_TECHNICAL / "prompts", NON_TECHNICAL / "paid-licence", TRAINING, STAFF_GUIDE,
               NON_TECHNICAL / "admin", ROLES, BEST_PRACTICES]
    docs = [NON_TECHNICAL / "README.md", ROOT / "README.md", ROOT / "ROLLOUT.md"]
    for folder in folders:
        docs += [p for p in folder.rglob("*.md") if "skills" not in p.parts]
    return docs


# ---------------------------------------------------------------- the library-wide check


def test_the_whole_library_is_clean():
    assert check_library.check_tree(ROOT) == []


@pytest.mark.parametrize("content, finding", [
    ("Use Cursor for this.", "other tools"),
    ("Put it in .cursor/config.json", "other tools"),
    ("See .cursor/skills", "other tools"),
    ("hidden" + chr(0x200B) + "word", "hidden text"),
    ("tag" + chr(0xE0041) + "char", "hidden text"),
    ("See [this](missing.md)", "broken link"),
    ("See docs/builder/deploy.md", "stale path"),
    ("A real-format IBAN IE29 AIBK 9311 5212 3456 78", "personal data"),
])
def test_library_check_goes_red_when_broken(tmp_path, content, finding):
    (tmp_path / "x.md").write_text(content, encoding="utf-8")
    assert any(finding in line for line in check_library.check_tree(tmp_path)), finding


def test_library_check_ignores_code_and_ordinary_words(tmp_path):
    (tmp_path / "ok.md").write_text("A database cursor is fine. `[not a link](x.md)`\n\n```text\n[nor this](y.md)\n```\n", encoding="utf-8")
    assert check_library.check_tree(tmp_path) == []


# ---------------------------------------------------------------- what non-technical staff rely on


def test_every_agent_named_in_staff_docs_exists():
    unknown = set()
    for doc in staff_docs():
        for mention in AGENT_MENTION.findall(doc.read_text(encoding="utf-8")):
            mention = mention.removesuffix(" for")  # "the Laya AI Helper for everyone" isn't part of the name
            known = any(n.startswith(f"Laya {mention}") or f"Laya {mention}".startswith(n) for n in CATALOG_NAMES)
            if not known and not mention.startswith(NOT_AGENTS):
                unknown.add(f"{doc.name}: Laya {mention}")
    assert not unknown, sorted(unknown)


def test_the_getting_started_guide_lists_every_agent():
    text = (STAFF_GUIDE / "getting-started.md").read_text(encoding="utf-8")
    for name in CATALOG_NAMES:
        assert name in text, name


def test_every_department_has_a_complete_playbook():
    assert len(build_guides.PLAYBOOK_ORDER) == 12
    index = (BY_ROLE / "README.md").read_text(encoding="utf-8")
    front_door = (NON_TECHNICAL / "README.md").read_text(encoding="utf-8")
    for slug in build_guides.PLAYBOOK_ORDER:
        text = (BY_ROLE / f"{slug}.md").read_text(encoding="utf-8")
        for section in PLAYBOOK_SECTIONS:
            assert section in text, f"{slug} is missing {section}"
        assert f"({slug}.md)" in index and f"by-role/{slug}.md" in front_door, slug


@pytest.mark.parametrize("slug", ["pricing-and-underwriting", "hr-and-people", "claims"])
def test_the_highest_risk_playbooks_say_what_ai_must_not_do(slug):
    never = (BY_ROLE / f"{slug}.md").read_text(encoding="utf-8").split("## Never hand these to AI")[1]
    assert re.search(r"Deciding|Screening|Risk assessment", never), slug


def test_free_staff_are_never_sent_only_to_a_paid_agent():
    """A job table in a playbook is the free route, so it can't rely on an agent that needs the licence."""
    paid = ("Laya Catch Me Up", "Laya Meeting Recap", "Laya Policy Finder")
    for slug in build_guides.PLAYBOOK_ORDER:
        jobs = (BY_ROLE / f"{slug}.md").read_text(encoding="utf-8").split("## Jobs AI can help with")[1].split("## If you have the paid licence")[0]
        for name in paid:
            assert name not in jobs, f"{slug}: {name} is in the free table"


def test_everyday_prompts_leave_out_paid_only_features():
    text = (PROMPTS / "everyday-prompts.md").read_text(encoding="utf-8")
    assert "Laya Catch Me Up" not in text and "Copilot in Word" not in text


def test_the_quiz_has_an_answer_for_every_question():
    text = (TRAINING / "quiz.md").read_text(encoding="utf-8")
    questions = re.findall(r"^\*\*(\d+)\.", text, re.MULTILINE)
    answers = re.findall(r"^(\d+)\. \*\*[abc]\.\*\*", text.split("## Answers")[1], re.MULTILINE)
    assert questions == answers and len(questions) == 10


def test_staff_know_who_to_tell_when_something_goes_wrong():
    text = (STAFF_GUIDE / "when-something-goes-wrong.md").read_text(encoding="utf-8")
    for needed in ("Data Protection Officer", "IT service desk", "72 hours", "Stop"):
        assert needed in text


# ---------------------------------------------------------------- roles


def test_every_role_card_is_complete_and_listed():
    cards = {p.stem for p in (ROLES / "cards").glob("*.md")}
    assert cards == set(build_guides.CARD_ORDER)
    index = (ROLES / "README.md").read_text(encoding="utf-8")
    for slug in cards:
        text = (ROLES / "cards" / f"{slug}.md").read_text(encoding="utf-8")
        for section in CARD_SECTIONS:
            assert section in text, f"{slug} is missing {section}"
        assert f"cards/{slug}.md" in index, slug


def test_raci_has_one_accountable_person_per_row_and_never_an_agent():
    text = (ROLES / "raci.md").read_text(encoding="utf-8")
    tables = [block for block in re.split(r"\n\n", text) if block.startswith("|")]
    assert len(tables) == 3
    rows_checked = 0
    for table in tables:
        lines = table.strip().splitlines()
        header = [c.strip() for c in lines[0].strip("|").split("|")]
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) == len(header), line
            assert cells.count("A") == 1, f"needs exactly one A: {line}"
            if "AI agent" in header:
                assert cells[header.index("AI agent")] != "A", line
            rows_checked += 1
    assert rows_checked >= 25


def test_governance_roles_follow_the_regulators_list():
    index = (ROLES / "README.md").read_text(encoding="utf-8")
    for role in ("Board and senior management", "Compliance and risk", "Internal audit", "Data Protection Officer", "Actuarial function", "AI owner"):
        assert role in index


# ---------------------------------------------------------------- the tools that have no other test


def test_templates_build_and_validate_including_the_register(tmp_path, monkeypatch):
    monkeypatch.setattr(build_templates, "OUT", tmp_path)
    monkeypatch.setattr(build_templates, "ROOT", tmp_path)
    built = {p.name for p in build_templates.build()}
    assert {"AI Use Register.xlsx", "Action Tracker.xlsx", "RAID Log.xlsx", "Project Plan.xlsx", "Simple Register.xlsx"} == built
    assert len(build_templates.build_documents()) == 4


def test_staff_guide_pages_show_who_can_use_each_agent():
    paid = build_staff_guide.agent_page({"name": "X", "description": "d", "conversation_starters": [],
                                         "staff_guide": {"upload": "u", "you_get": "y", "example": "e", "tips": []}}, "paid-licence")
    assert "paid Microsoft Copilot licence" in paid


def test_every_word_guide_builds_and_has_content(tmp_path):
    docx = pytest.importorskip("docx")
    built = build_guides.build_all(tmp_path)
    assert len(built) == 5
    assert (tmp_path / "README.md").exists()
    for path in built:
        document = docx.Document(path)
        assert len(document.paragraphs) > 10, path.name


def test_word_renderer_handles_links_code_and_uneven_tables(tmp_path):
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    build_staff_guide.render_markdown(doc, """# Title
A [public page](https://example.test/a) and [a local page](other.md), **bold with a [link](x.md)**.

| A | B |
|---|---|
| one column |
| three | col | umns |

```text
code here
```

1. first
2. second
""")
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "a local page" in text and "other.md" not in text and "[" not in text
    assert "code here" in text and "```" not in text
    assert "1. first" in text
    assert len(doc.tables[0].columns) == 2
    assert 'w:hyperlink' in doc.element.xml
