"""ExpertWorkbook: change any Excel workbook safely, with a precise record of what changed.

    xw = ExpertWorkbook.open("Claims.xlsx")
    result = xw.apply([{"op": "insert_column", "sheet": "Claims", "header": "Priority", "after": "Status",
                        "choices": ["High", "Medium", "Low"]}], requested_by="Aoife")
    xw.save("Claims (updated).xlsx")
    print(result.text())

Every apply() is all-or-nothing: if one change fails, the workbook is reloaded as it was.
If the workbook is AI-safe (has an _ADLC sheet), its spec, version, README and Change Log
are brought up to date too, so the ADLC agents and engine keep working on it.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from . import ops as ops_mod
from .inspect import describe, inspect_workbook

VALUE_FIELDS = ("rows", "cells", "values", "fill", "find", "replace", "value", "value2")


def ops_for_log(ops) -> list[dict]:
    """Change Log 'Technical details': what was done and where - never the values typed in."""
    if isinstance(ops, dict):
        ops = ops.get("ops", [ops])
    out = []
    for op in ops:
        op = dict(op)
        for k in VALUE_FIELDS:
            if k in op:
                v = op[k]
                op[k] = f"{len(v)} item(s); values not logged" if isinstance(v, (list, dict)) else "(not logged)"
        if isinstance(op.get("set"), dict):
            op["set"] = sorted(op["set"])
        if isinstance(op.get("where"), (dict, list)):
            conds = op["where"] if isinstance(op["where"], list) else [op["where"]]
            op["where"] = [c.get("column", "?") if isinstance(c, dict) and "column" in c else "condition" for c in conds]
        out.append(op)
    return out


def _snapshot(wb) -> dict:
    return {(ws.title, c.row, c.column): c.value for ws in wb.worksheets for row in ws.iter_rows() for c in row
            if c.value is not None}


def changed_ranges(before: dict, after: dict, ignore=("_ADLC", "README", "Change Log")) -> list[str]:
    """Compress changed cells into ranges like 'Members!E1:E120'."""
    keys = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k[0] not in ignore}
    by_sheet: dict[str, dict[int, list[int]]] = {}
    for sheet, r, c in keys:
        by_sheet.setdefault(sheet, {}).setdefault(c, []).append(r)
    out = []
    for sheet, cols in sorted(by_sheet.items()):
        runs = []
        for c, rows in sorted(cols.items()):
            rows.sort()
            start = prev = rows[0]
            for r in rows[1:] + [None]:
                if r is not None and r == prev + 1:
                    prev = r
                    continue
                runs.append((c, start, prev))
                if r is not None:
                    start = prev = r
        merged = []
        for c, r0, r1 in runs:
            if merged and merged[-1][1] == c - 1 and merged[-1][2] == r0 and merged[-1][3] == r1:
                merged[-1] = (merged[-1][0], c, r0, r1)
            else:
                merged.append((c, c, r0, r1))
        for c0, c1, r0, r1 in merged:
            a, b = f"{get_column_letter(c0)}{r0}", f"{get_column_letter(c1)}{r1}"
            out.append(f"{sheet}!{a}" if a == b else f"{sheet}!{a}:{b}")
    return out


@dataclass
class ExpertResult:
    changes: list[str]
    warnings: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    version: str | None = None

    def text(self) -> str:
        head = f"Version {self.version} - here's what changed:" if self.version else "Here's what changed:"
        lines = [head] + [f"  - {c}" for c in self.changes]
        if self.warnings:
            lines += ["Worth knowing:"] + [f"  - {w}" for w in self.warnings]
        if self.changed:
            shown = ", ".join(self.changed[:8]) + (f" and {len(self.changed) - 8} more" if len(self.changed) > 8 else "")
            lines.append(f"Cells changed: {shown}")
        return "\n".join(lines)


class ExpertWorkbook:
    def __init__(self, data: bytes, path: str | Path | None = None):
        self._original = data
        self.path = Path(path) if path else None
        self.wb = load_workbook(io.BytesIO(data))

    @classmethod
    def open(cls, path: str | Path) -> "ExpertWorkbook":
        return cls(Path(path).read_bytes(), path)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ExpertWorkbook":
        return cls(data)

    @property
    def is_adlc(self) -> bool:
        return "_ADLC" in self.wb.sheetnames

    def inspect(self, sample_rows: int = 3) -> dict:
        return inspect_workbook(self.wb, self.path, sample_rows)

    def describe(self) -> str:
        return describe(self.inspect())

    def apply(self, ops, requested_by: str = "", tool: str = "ADLC Excel engine", summary: str | None = None) -> ExpertResult:
        before = _snapshot(self.wb)
        ctx = ops_mod.Ctx(self.wb)
        try:
            changes = ops_mod.run(ctx, ops)
            version = None
            if self.is_adlc:
                from .sync import sync_adlc

                version = sync_adlc(self.wb, ctx, changes, ops_for_log(ops), requested_by, tool, summary)
        except Exception:
            self.wb = load_workbook(io.BytesIO(self._original))  # all-or-nothing
            raise
        result = ExpertResult(changes, ctx.warnings, changed_ranges(before, _snapshot(self.wb)), version)
        return result

    def to_bytes(self) -> bytes:
        self.wb.calculation.fullCalcOnLoad = True
        buf = io.BytesIO()
        self.wb.save(buf)
        self._original = buf.getvalue()
        return self._original

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path or self.path)
        target.write_bytes(self.to_bytes())
        self.path = target
        return target
