"""Copy Matt Pocock's stable skills into the library and adapt them for GitHub Copilot.

    python tools/vendor_matt_skills.py --from D:\\ADLC\\skills

Third-party prompts are code, so they change only on review:
  1. git pull in the clone and read the upstream diff.
  2. Run this script.
  3. Review the changes it makes under technical/skills-and-agents/skills/.

The rewrites below are the only edits made to his text. They are listed in
technical/skills-and-agents/MATT-POCOCK-SKILLS.md. Never hand-edit the vendored copies:
the next run would undo it. Add a rewrite here instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import DEV_SKILLS, SKILLS_AND_AGENTS  # noqa: E402

BUCKETS = ("engineering", "productivity")
MANIFEST = SKILLS_AND_AGENTS / "MATT-POCOCK-SKILLS.md"
UPSTREAM = "mattpocock/skills"
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
NAME = r'[`"]([a-z0-9-]+)[`"]'
HIDDEN = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\U000e0000-\U000e007f]")
LEFTOVER = re.compile(r"Skill tool", re.IGNORECASE)


def ref(name: str) -> str:
    return f"`{name}` skill (`../{name}/SKILL.md`)"


def _both(verb: str):
    return lambda m: f"{verb} the {ref(m.group(1))} and the {ref(m.group(2))}"


def _one(verb: str):
    return lambda m: f"{verb} the {ref(m.group(1))}"


# Copilot's docs describe skills being matched and loaded, not a callable "Skill tool", so
# these say what the agent actually does: open the sibling skill and follow it.
TEXT_REWRITES: list[tuple[re.Pattern, object]] = [
    (re.compile(rf"\bCall the Skill tool twice, for {NAME} and {NAME}"), _both("Read and follow")),
    (re.compile(rf"\bcall the Skill tool twice, for {NAME} and {NAME}"), _both("read and follow")),
    (re.compile(rf"\bcalling the Skill tool with {NAME}"), _one("reading and following")),
    (re.compile(rf"\bcalls the Skill tool with {NAME}"), _one("reads and follows")),
    (re.compile(rf"\bCall the Skill tool with {NAME}"), _one("Read and follow")),
    (re.compile(rf"\bcall the Skill tool with {NAME}"), _one("read and follow")),
    (re.compile(r"\bcall the Skill tool for whichever skills"), "read and follow whichever skills"),
    (re.compile(r"should call the Skill tool for\."), "should read and follow."),
]


def rewrite_text(text: str) -> str:
    for pattern, replacement in TEXT_REWRITES:
        text = pattern.sub(replacement, text)
    return text


def add_provenance(text: str, commit: str) -> str:
    """State the licence and source in the frontmatter, so they travel with the skill."""
    m = FRONTMATTER.match(text)
    if not m:
        raise ValueError("no frontmatter")
    head = m.group(1)
    if not re.search(r"^license:", head, re.MULTILINE):
        head += "\nlicense: MIT"
    source = f"  source: {UPSTREAM}@{commit}"
    if re.search(r"^metadata:\s*$", head, re.MULTILINE):
        head = re.sub(r"^metadata:\s*$", lambda _: f"metadata:\n{source}", head, count=1, flags=re.MULTILINE)
    else:
        head += f"\nmetadata:\n{source}"
    return f"---\n{head}\n---\n" + text[m.end():]


def upstream_skills(clone: Path) -> list[Path]:
    found = []
    for bucket in BUCKETS:
        found += sorted(p.parent for p in (clone / "skills" / bucket).glob("*/SKILL.md"))
    return found


def vendor(clone: Path, target: Path = DEV_SKILLS, manifest: Path = MANIFEST) -> list[str]:
    commit = subprocess.run(["git", "-C", str(clone), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    skills = upstream_skills(clone)
    if not skills:
        raise SystemExit(f"Not a clone of {UPSTREAM}: {clone}")
    target.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    names: list[str] = []
    for src in skills:
        dst = target / src.name
        if dst.exists():
            shutil.rmtree(dst)
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            rel = f.relative_to(src)
            if rel.parts[0] == "agents":  # another tool's metadata
                continue
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            text = rewrite_text(f.read_text(encoding="utf-8"))
            if rel.as_posix() == "SKILL.md":
                text = add_provenance(text, commit)
            if HIDDEN.search(text):
                problems.append(f"{src.name}/{rel}: contains hidden characters")
            for hit in LEFTOVER.findall(text):
                problems.append(f"{src.name}/{rel}: still mentions '{hit}'")
            out.write_text(text, encoding="utf-8", newline="\n")
        names.append(src.name)
    if problems:
        raise SystemExit("Stopped: review these before using the update:\n  " + "\n  ".join(problems))
    write_manifest(manifest, commit, names)
    return names


def write_manifest(path: Path, commit: str, names: list[str]) -> None:
    listing = ", ".join(f"`{n}`" for n in names)
    path.write_text(f"""# Matt Pocock's skills in this library

Copied from [{UPSTREAM}](https://github.com/{UPSTREAM}) (MIT licence) by `technical/platform/tools/vendor_matt_skills.py`.

- **Pinned commit:** `{commit}`
- **Copied:** {dt.date.today():%d/%m/%Y}
- **Skills ({len(names)}):** {listing}

His `misc` and `in-progress` folders are left out, because he doesn't ship them.

## What we changed, and why

Only these edits are made to his text. They come from the script, so they repeat on every update.

| Change | Why |
|---|---|
| "Call the Skill tool with X" becomes "Read and follow the X skill (`../X/SKILL.md`)" | GitHub's docs describe Copilot matching and loading skills, not a callable skill tool |
| Another tool's instruction file name becomes `.github/copilot-instructions.md` | It's the instruction file every Copilot surface reads |
| Each skill's `agents/` metadata file is removed | It's for another tool. Copilot uses `disable-model-invocation` in `SKILL.md` instead |
| `license` and `metadata.source` are added to the frontmatter | So the licence and pinned source travel with each skill |

## Where they work

- **Everywhere skills are supported:** the single-session skills.
- **VS Code and Copilot CLI only:** `implement-spec` and `wayfinder`, which start subagents. GitHub's cheat sheet doesn't list subagents for Visual Studio or GitHub.com.
- **Git Bash, WSL or Linux needed:** `wizard`, and the reproduction script in `diagnosing-bugs`.

## Updating

1. `git pull` in your clone and read the upstream diff.
2. `python tools/vendor_matt_skills.py --from <clone>` from `technical/platform`.
3. Review the changes, then run `python -m pytest`.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Copy Matt Pocock's skills into the library")
    ap.add_argument("--from", dest="clone", required=True, type=Path, help="path to a clone of mattpocock/skills")
    args = ap.parse_args()
    done = vendor(args.clone)
    print(f"Vendored {len(done)} skills into {DEV_SKILLS}")
