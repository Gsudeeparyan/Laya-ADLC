"""Command line: python -m adlc_workbook <command> ...

  build    spec.yaml out.xlsx [--owner NAME]        build a workbook from a spec
  apply    book.xlsx ops.yaml [-o out.xlsx] --by NAME [--summary TEXT]
  validate book.xlsx                                check the workbook still matches its spec
  inspect  book.xlsx                                show version, sheets, tables and columns
  spec     book.xlsx                                print the stored spec as YAML
  adopt    book.xlsx [-o out.xlsx] [--dry-run]      make an existing workbook AI-safe
  diff     before.xlsx after.xlsx                   list every cell that changed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .adopt import adopt
from .diff import diff_files
from .meta import MetaError
from .ops import OpError
from .render import DriftError
from .spec import SpecError, dump_yaml, iter_tables, load_spec
from .workbook import AdlcWorkbook


def _load_ops(path: str):
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text) if path.endswith(".json") else yaml.safe_load(text)
    return data.get("ops", data) if isinstance(data, dict) else data


def cmd_build(a):
    awb = AdlcWorkbook.build(load_spec(a.spec), owner=a.owner, requested_by=a.by)
    out = awb.save(a.out)
    print(f"Built {out} (version {awb.meta['version']})")
    return 0


def cmd_apply(a):
    awb = AdlcWorkbook.open(a.book)
    data = _load_ops(a.ops)
    res = awb.apply(data, requested_by=a.by, tool="adlc-wb CLI", summary=a.summary)
    out = awb.save(a.output or a.book)
    print(f"Saved {out} as version {res.version}:")
    for c in res.changes:
        print(f"  - {c}")
    for w in res.warnings:
        print(f"  ! {w}")
    rep = awb.validate()
    print(rep.text())
    return 0 if rep.ok else 1


def cmd_validate(a):
    from openpyxl import load_workbook

    from .validate import validate_workbook

    rep = validate_workbook(load_workbook(a.book))
    print(rep.text())
    return 0 if rep.ok else 1


def cmd_inspect(a):
    awb = AdlcWorkbook.open(a.book)
    m = awb.meta
    print(f"{m['title']}  (version {m['version']}, owner: {m['owner'] or '-'}, updated {m['updated']} by {m['updated_by']})")
    for sheet, table in iter_tables(awb.spec):
        print(f"\nSheet '{sheet['name']}' - table {table['name']} (key: {table['key']})")
        for c in table["columns"]:
            extra = ""
            if c.get("choices"):
                extra = " [" + ", ".join(map(str, c["choices"])) + "]"
            if c.get("formula"):
                extra = f" = {c['formula']}"
            print(f"  - {c['header']} ({c['key']}, {c['type']}){extra}")
    for p in awb.spec.get("parameters", []):
        print(f"\nSetting p_{p['key']}: {p['label']} = {p.get('value')}")
    return 0


def cmd_spec(a):
    print(dump_yaml(AdlcWorkbook.open(a.book).spec))
    return 0


def cmd_adopt(a):
    res = adopt(a.book, title=a.title, owner=a.owner or "", write=not a.dry_run, requested_by=a.by)
    for n in res.notes:
        print(f"- {n}")
    if a.dry_run:
        print("\nDraft spec:\n" + dump_yaml(res.spec))
        return 0
    out = res.awb.save(a.output or a.book)
    print(f"\nSaved {out}")
    return 0


def cmd_diff(a):
    lines = diff_files(a.before, a.after)
    print("\n".join(lines) if lines else "No differences outside README, Change Log and _ADLC.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="adlc-wb", description="ADLC self-describing Excel workbooks")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("build", help="build a workbook from a spec")
    s.add_argument("spec")
    s.add_argument("out")
    s.add_argument("--owner")
    s.add_argument("--by", default="ADLC engine")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("apply", help="apply change operations")
    s.add_argument("book")
    s.add_argument("ops")
    s.add_argument("-o", "--output")
    s.add_argument("--by", required=True, help="who asked for the change")
    s.add_argument("--summary")
    s.set_defaults(fn=cmd_apply)

    for name, fn in (("validate", cmd_validate), ("inspect", cmd_inspect), ("spec", cmd_spec)):
        s = sub.add_parser(name)
        s.add_argument("book")
        s.set_defaults(fn=fn)

    s = sub.add_parser("adopt", help="make an existing workbook AI-safe")
    s.add_argument("book")
    s.add_argument("-o", "--output")
    s.add_argument("--title")
    s.add_argument("--owner")
    s.add_argument("--by", default="ADLC engine")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_adopt)

    s = sub.add_parser("diff", help="list cells that changed")
    s.add_argument("before")
    s.add_argument("after")
    s.set_defaults(fn=cmd_diff)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except (SpecError, OpError, MetaError, DriftError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
