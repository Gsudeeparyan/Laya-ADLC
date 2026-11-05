"""A map of any workbook: what an agent needs to know before changing it."""

from __future__ import annotations

import zipfile
from pathlib import Path

from openpyxl.utils import get_column_letter

from .regions import GENERATED, all_regions
from .values import column_kind


def file_risks(path: str | Path | None) -> list[str]:
    if not path or not Path(path).exists():
        return []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    risks = []
    if any("pivotTable" in n for n in names):
        risks.append("pivot tables (they are kept; refresh them in Excel after a change)")
    if any("vbaProject" in n for n in names):
        risks.append("macros (not kept when saved as .xlsx)")
    if any(n.startswith("xl/externalLinks/") for n in names):
        risks.append("links to other workbooks")
    if any(n.startswith("xl/drawings/") and "vml" not in n for n in names) and not any(n.startswith("xl/charts/") for n in names):
        risks.append("shapes or pictures (may be lost)")
    return risks


def inspect_workbook(wb, path=None, sample_rows: int = 3) -> dict:
    regions = all_regions(wb)
    out = {"sheets": [], "named_ranges": sorted(wb.defined_names.keys()), "adlc": None, "risks": file_risks(path)}
    if "_ADLC" in wb.sheetnames:
        try:
            from adlc_workbook.meta import read_meta

            meta, _ = read_meta(wb)
            out["adlc"] = {"title": meta["title"], "version": meta["version"], "updated": meta["updated"]}
        except Exception:
            out["adlc"] = {"title": "", "version": "?", "updated": ""}
    for ws in wb.worksheets:
        if ws.title in GENERATED:
            continue
        sheet = {
            "name": ws.title, "visible": ws.sheet_state == "visible", "used_range": ws.dimensions,
            "tables": [], "charts": len(getattr(ws, "_charts", [])),
            "merged_cells": len(ws.merged_cells.ranges), "dropdowns": len(ws.data_validations.dataValidation),
            "highlight_rules": sum(len(cf.rules) for cf in ws.conditional_formatting),
            "freeze_panes": ws.freeze_panes,
        }
        for region in [r for r in regions if r.ws is ws]:
            cols = []
            for c in range(region.c0, region.c1 + 1):
                cells = [ws.cell(r, c) for r in region.data_rows]
                kind = column_kind(cells)
                info = {"header": region.headers[c - region.c0], "letter": get_column_letter(c), "kind": kind}
                if kind == "formula":
                    info["formula"] = next((x.value for x in cells if isinstance(x.value, str) and x.value.startswith("=")), None)
                from .ops import _dv_list

                choices = _dv_list(ws, c, region.header_row + 1)
                if choices:
                    info["dropdown"] = choices
                info["sample"] = [x.value if not hasattr(x.value, "isoformat") else x.value.strftime("%d/%m/%Y")
                                  for x in cells[:sample_rows] if x.value not in (None, "")]
                cols.append(info)
            sheet["tables"].append({
                "name": region.name, "is_excel_table": region.table is not None, "range": region.ref,
                "header_row": region.header_row, "rows": len(region.rows_with_data), "columns": cols,
            })
        out["sheets"].append(sheet)
    return out


def describe(info: dict) -> str:
    """Plain-English summary of inspect_workbook()."""
    lines = []
    if info.get("adlc"):
        lines.append(f"AI-safe workbook '{info['adlc']['title']}', version {info['adlc']['version']}.")
    for s in info["sheets"]:
        hidden = "" if s["visible"] else " (hidden)"
        lines.append(f"Sheet '{s['name']}'{hidden}:")
        for t in s["tables"]:
            kind = "Excel table" if t["is_excel_table"] else "data"
            lines.append(f"  {kind} {t['name']} - {t['rows']} rows")
            for c in t["columns"]:
                extra = f" = {c['formula']}" if c.get("formula") else (f" [{', '.join(map(str, c['dropdown']))}]" if c.get("dropdown") else "")
                lines.append(f"    {c['letter']}: {c['header']} ({c['kind']}){extra}")
        if s["charts"]:
            lines.append(f"  {s['charts']} chart(s)")
    if info.get("risks"):
        lines.append("Watch out: " + "; ".join(info["risks"]) + ".")
    return "\n".join(lines)
