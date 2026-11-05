"""Library-wide checks. Run before sharing anything, and on any folder from outside Laya.

    python tools/check_library.py                # the whole library
    python tools/check_library.py --path <dir>   # a folder you're reviewing, such as an outside skill

Checks:
  other tools   no other AI coding tool is named: Laya uses Microsoft Copilot and GitHub Copilot only
  hidden text   no zero-width, bidirectional or tag characters that could hide instructions from a reader
  personal data no real-format PPSN, IBAN or card number (they're checked against their check digits)
  links         every relative link in every Markdown file resolves
  stale paths   no reference to the old layout

Exits 1 if it finds anything. Passing is necessary, not enough: a person still reads what comes in.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import ROOT, SRC  # noqa: E402

sys.path.insert(0, str(SRC))

from adlc_pii.detectors import find_in_text  # noqa: E402

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".txt", ".ps1", ".sh", ".toml", ".bicep", ".sql", ".html", ".csv"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "packages", "build", ".venv", "node_modules", "schemas"}

OTHER_TOOLS = re.compile(
    r"\bAntigravity\b|\bantigravity\b|\bGemini\b|\bCursor\b|\bWindsurf\b"
    r"|GEMINI\.md|\.cursor\b|openai\.yaml")
# Files that name other tools for a reason. Every entry needs one.
OTHER_TOOLS_ALLOWED = {
    "THIRD-PARTY-NOTICES.md",       # licence notices keep the upstream wording
    "vendor_matt_skills.py",        # it removes these names, so it has to know them
    "check_library.py",             # this file
    "test_library.py",              # it plants these names to prove the check works
    "RULES.md",                     # book rule sets, copied as they are under their licence
    "CHANGELOG.md",                 # records what was removed
}
HIDDEN = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\U000e0000-\U000e007f]")
REAL_FORMAT = {"PPSN", "IBAN", "CARD"}
LINK = re.compile(r"(?<!!)\[[^\]]*\]\((?!https?:|mailto:|#)([^)\s]+)\)")
# Upstream's illustrations of a format, not links to follow.
ILLUSTRATIVE = {"wayfinder/SKILL.md", "domain-modeling/GLOSSARY-FORMAT.md", "teach/GLOSSARY-FORMAT.md",
                "teach/MISSION-FORMAT.md", "teach/RESOURCES-FORMAT.md", "teach/LEARNING-RECORD-FORMAT.md"}
STALE = re.compile(r"ADLC-main|D:\\ADLC|docs/builder|docs/staff-guide|docs/laya-glossary|docs/skill-authoring-guide|"
                   r"dist/m365|dist/templates|agents/m365|skills/_shared|install-skills\.ps1|excel-workbook-editor|developer/skills")
STALE_ALLOWED = {"check_library.py", "test_library.py", "CHANGELOG.md"}
# Obviously fake values used in examples, with a reason. Everything else is a finding.
SYNTHETIC_ALLOWED = {"1234567T"}  # the made-up PPS number in the smoke test


def files_under(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and not SKIP_DIRS & set(path.parts):
            yield path


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return [f"{path}: can't be read as text; a person should look at it"]
    found: list[str] = []

    def where(offset: int) -> str:
        return f"{path}:{text.count(chr(10), 0, offset) + 1}"

    if path.name not in OTHER_TOOLS_ALLOWED:
        for m in OTHER_TOOLS.finditer(text):
            found.append(f"{where(m.start())}: other tools: names '{m.group(0)}'")
    for m in HIDDEN.finditer(text):
        found.append(f"{where(m.start())}: hidden text: U+{ord(m.group(0)):04X}")
    if path.name not in STALE_ALLOWED:
        for m in STALE.finditer(text):
            found.append(f"{where(m.start())}: stale path: '{m.group(0)}'")
    if "tests" not in path.parts:  # the engine's tests use synthetic values on purpose
        for f in find_in_text(text):
            if f.type in REAL_FORMAT and f.value not in SYNTHETIC_ALLOWED:
                found.append(f"{where(f.start)}: personal data: looks like a real {f.type}")
    if path.suffix.lower() == ".md" and "/".join(path.parts[-2:]) not in ILLUSTRATIVE:
        in_code = False
        offset = 0
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith("```"):
                in_code = not in_code
            elif not in_code:
                for m in LINK.finditer(re.sub(r"`[^`]*`", lambda c: " " * len(c.group(0)), line)):
                    target = m.group(1).split("#")[0]
                    if target and not (path.parent / target).exists():
                        found.append(f"{where(offset)}: broken link: {target}")
            offset += len(line)
    return found


def check_tree(root: Path) -> list[str]:
    return [line for path in files_under(root) for line in check_file(path)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Library-wide checks")
    ap.add_argument("--path", type=Path, default=ROOT, help="folder to check (default: the whole library)")
    args = ap.parse_args(argv)
    findings = check_tree(args.path)
    for line in findings:
        print(line)
    print(f"{len(findings)} finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
