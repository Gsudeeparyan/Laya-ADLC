"""Command line: python -m adlc_pii <command> ...

  scan    FILE                        report what PII is in a file (nothing is changed)
  clean   FILE [-o OUT] [--profile restore|anonymise] [--vault VAULT.json]
                                      write "<name> (PII removed)" + a vault to put values back
  restore FILE --vault VAULT.json [-o OUT]
                                      put the real values back into a file made from a cleaned copy
  text    "some text"                 clean a piece of text and show the tokens

The vault holds the real values. Keep it next to the original, never upload it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .policy import Policy
from .scrub import restore_file, scan_file, scrub_file, scrub_text
from .vault import Vault


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="adlc-pii", description="Find, remove and restore personal data (PII)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("file")
    s.add_argument("--json", action="store_true")
    s.add_argument("--policy")
    s = sub.add_parser("clean")
    s.add_argument("file")
    s.add_argument("-o", "--output")
    s.add_argument("--vault")
    s.add_argument("--profile", default="restore", choices=["restore", "anonymise"])
    s.add_argument("--policy")
    s = sub.add_parser("restore")
    s.add_argument("file")
    s.add_argument("--vault", required=True)
    s.add_argument("-o", "--output")
    s = sub.add_parser("text")
    s.add_argument("text")
    s.add_argument("--profile", default="restore", choices=["restore", "anonymise"])
    a = p.parse_args(argv)

    try:
        if a.cmd == "scan":
            report = scan_file(a.file, Policy.load(a.policy))
            print(json.dumps(report.to_dict(), indent=1, ensure_ascii=False) if a.json else report.text(cleaned=False))
            return 0
        if a.cmd == "clean":
            policy = Policy.load(a.policy, a.profile)
            out, report, vault = scrub_file(a.file, a.output, policy)
            print(report.text())
            print(f"\nCleaned copy: {out}")
            if len(vault) and policy.restorable:
                vpath = Path(a.vault) if a.vault else Path(a.file).with_suffix(".pii-vault.json")
                vault.save(vpath)
                print(f"Vault (keep private, never upload): {vpath}")
            return 0
        if a.cmd == "restore":
            out = restore_file(a.file, Vault.load(a.vault), a.output)
            print(f"Real values put back: {out}")
            return 0
        if a.cmd == "text":
            clean, vault = scrub_text(a.text, Policy(profile=a.profile))
            print(clean)
            for token, entry in vault.tokens.items():
                print(f"  {token} = {entry['value']}", file=sys.stderr)
            return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
