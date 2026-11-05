"""Fail CI if the repo holds what look like real personal data or secrets.

    python .github/scripts/laya_scan.py <folder or file> [...]

Uses Laya's detectors (copied here by the installer), which check PPSN, IBAN and card numbers
against their check digits, so a finding is rarely a false alarm. Standard library only.
To accept one synthetic value, add it to .github/scripts/laya_scan_allow.txt, one per line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from laya_pii_detectors import find_in_text  # noqa: E402

CHECKED = {"PPSN", "IBAN", "CARD"}
SECRET = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|gh[pousr]_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{22,}")
TEXT_SUFFIXES = {".py", ".sql", ".pls", ".pkb", ".pks", ".json", ".yaml", ".yml", ".csv", ".tsv", ".txt", ".md",
                 ".ts", ".tsx", ".js", ".jsx", ".cs", ".java", ".xml", ".html", ".env", ".ini", ".cfg", ".toml"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "bin", "obj"}
ALLOW_FILE = Path(__file__).resolve().parent / "laya_scan_allow.txt"


def files_under(roots: list[Path]):
    for root in roots:
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and not SKIP_DIRS & set(path.parts):
                yield path


def scan(path: Path, allow: set[str]) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    found = []
    for f in find_in_text(text):
        if f.type in CHECKED and f.value not in allow:
            found.append(f"{path}:{text.count(chr(10), 0, f.start) + 1}: looks like a real {f.type}")
    for m in SECRET.finditer(text):
        found.append(f"{path}:{text.count(chr(10), 0, m.start()) + 1}: looks like a secret")
    return found


def main(argv: list[str]) -> int:
    allow = set(ALLOW_FILE.read_text(encoding="utf-8").split()) if ALLOW_FILE.exists() else set()
    roots = [Path(a) for a in argv] or [Path(".")]
    problems = [line for path in files_under(roots) for line in scan(path, allow)]
    for line in problems:
        print(line)
    print(f"{len(problems)} finding(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
