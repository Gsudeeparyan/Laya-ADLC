"""Compare two workbooks cell by cell (values and formulas).

Used to prove that a change touched only what it should: everything outside the changed
table must be identical before and after.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from .meta import META_SHEET
from .render import CHANGELOG_SHEET, README_SHEET

GENERATED = (META_SHEET, README_SHEET, CHANGELOG_SHEET)


def snapshot(wb, ignore=GENERATED) -> dict[str, dict[str, object]]:
    snap = {}
    for ws in wb.worksheets:
        if ws.title in ignore:
            continue
        snap[ws.title] = {
            cell.coordinate: cell.value
            for row in ws.iter_rows()
            for cell in row
            if cell.value not in (None, "")
        }
    return snap


def diff_snapshots(a: dict, b: dict) -> list[str]:
    lines = []
    for sheet in sorted(set(a) | set(b)):
        if sheet not in a:
            lines.append(f"+ sheet '{sheet}' added")
            continue
        if sheet not in b:
            lines.append(f"- sheet '{sheet}' removed")
            continue
        for coord in sorted(set(a[sheet]) | set(b[sheet])):
            va, vb = a[sheet].get(coord), b[sheet].get(coord)
            if va != vb:
                lines.append(f"~ {sheet}!{coord}: {va!r} -> {vb!r}")
    return lines


def diff_files(path_a: str | Path, path_b: str | Path, ignore=GENERATED) -> list[str]:
    return diff_snapshots(snapshot(load_workbook(path_a), ignore), snapshot(load_workbook(path_b), ignore))
