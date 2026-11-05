"""Install Laya's GitHub Copilot harness into a repo, or skills into your own profile.

    python technical/harness/install_harness.py --target C:\\code\\claims-api
    python technical/harness/install_harness.py --personal

Replaced on every run, so re-running updates them:
    .github/skills/<library skills>, .github/agents/<role agents>, .github/hooks/laya-guard.*,
    .github/scripts/laya_scan.py and laya_pii_detectors.py

Created only if missing, because they belong to the repo once they exist:
    everything else in the kit, GLOSSARY.md and CODING_STANDARDS.md

Standard library only. Prints what it did.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TECHNICAL = HERE.parent
ROOT = TECHNICAL.parent
KIT = HERE / "repo-kit"
SKILLS = TECHNICAL / "skills-and-agents" / "skills"
AGENTS = TECHNICAL / "skills-and-agents" / "agents"
DETECTORS = TECHNICAL / "platform" / "src" / "adlc_pii" / "detectors.py"
GLOSSARY = ROOT / "GLOSSARY.md"
MANAGED = {".github/hooks/laya-guard.json", ".github/hooks/laya-guard.sh", ".github/hooks/laya-guard.ps1",
           ".github/hooks/laya-guard-patterns.txt", ".github/scripts/laya_scan.py"}


def copy(src: Path, dst: Path, log: list[str], replace: bool) -> None:
    if dst.exists() and not replace:
        log.append(f"keep    {dst}")
        return
    verb = "update " if dst.exists() else "new    "
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log.append(f"{verb} {dst}")


def copy_skills(dest: Path, log: list[str]) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for src in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists()):
        if (dest / src.name).exists():
            shutil.rmtree(dest / src.name)
        shutil.copytree(src, dest / src.name)
        count += 1
    log.append(f"skills  {count} -> {dest}")
    return count


def install_repo(target: Path) -> list[str]:
    if not target.is_dir():
        raise SystemExit(f"Repo not found: {target}")
    log: list[str] = []
    copy_skills(target / ".github" / "skills", log)
    for agent in sorted(AGENTS.glob("*.agent.md")):
        copy(agent, target / ".github" / "agents" / agent.name, log, replace=True)
    for src in sorted(p for p in KIT.rglob("*") if p.is_file()):
        rel = src.relative_to(KIT).as_posix()
        copy(src, target / rel, log, replace=rel in MANAGED)
    copy(DETECTORS, target / ".github" / "scripts" / "laya_pii_detectors.py", log, replace=True)
    copy(GLOSSARY, target / "GLOSSARY.md", log, replace=False)
    (target / ".github" / "LAYA-ADLC-VERSION.txt").write_text(
        f"Laya-ADLC harness installed {dt.date.today():%d/%m/%Y}. Re-run technical/harness/install_harness.py to update.\n",
        encoding="utf-8")
    return log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Install Laya's GitHub Copilot harness")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", type=Path, help="path to the repo")
    group.add_argument("--personal", action="store_true", help="install skills to ~/.copilot/skills")
    args = ap.parse_args(argv)
    if args.personal:
        log: list[str] = []
        copy_skills(Path.home() / ".copilot" / "skills", log)
        print("\n".join(log))
        return 0
    print("\n".join(install_repo(args.target)))
    print("\nNext: follow the harness-setup skill, or technical/harness/README.md, to fill in what only this repo knows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
