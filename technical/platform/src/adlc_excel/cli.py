"""Command line: python -m adlc_excel <command> ...

  inspect  book.xlsx [--json]                    map of sheets, tables, columns, formulas, risks
  apply    book.xlsx ops.yaml [-o out.xlsx] --by NAME [--summary TEXT]
  ops                                            list the available operations

ops.yaml holds a list of operations, for example:
  - op: insert_column
    sheet: Claims
    header: Priority
    after: Status
    choices: [High, Medium, Low]
  - op: update_rows
    sheet: Claims
    where: {Status: Closed}
    set: {Priority: Low}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .ops import OPS, OpError
from .regions import TargetError
from .workbook import ExpertWorkbook


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="adlc-excel", description="Expert Excel engine")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("inspect")
    s.add_argument("book")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("apply")
    s.add_argument("book")
    s.add_argument("ops")
    s.add_argument("-o", "--output")
    s.add_argument("--by", required=True)
    s.add_argument("--summary")
    sub.add_parser("ops")
    a = p.parse_args(argv)
    try:
        if a.cmd == "ops":
            print("\n".join(sorted(OPS)))
            return 0
        xw = ExpertWorkbook.open(a.book)
        if a.cmd == "inspect":
            print(json.dumps(xw.inspect(), indent=1, default=str, ensure_ascii=False) if a.json else xw.describe())
            return 0
        text = Path(a.ops).read_text(encoding="utf-8")
        ops = json.loads(text) if a.ops.endswith(".json") else yaml.safe_load(text)
        result = xw.apply(ops, requested_by=a.by, tool="adlc-excel CLI", summary=a.summary)
        out = xw.save(a.output or a.book)
        print(result.text())
        print(f"Saved {out}")
        return 0
    except (OpError, TargetError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
