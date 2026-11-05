"""Keep an AI-safe (ADLC) workbook's memory up to date after expert edits.

The expert engine can change anything; afterwards this reconciles the _ADLC spec with
what is really in the file (new or renamed columns, new tables, renamed sheets), bumps
the version, and adds a Change Log row - so ADLC agents and validation keep working.
"""

from __future__ import annotations

from datetime import datetime

from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

from .values import column_kind

ADLC_SHEETS = {"_ADLC", "_Lists", "README", "Settings", "Change Log"}


def _infer_column(ws, col, r0, r1, header, table_name, keys):
    from adlc_workbook.formulas import normalise
    from adlc_workbook.spec import slug

    from .ops import _dv_list

    cells = [ws.cell(r, col) for r in range(r0 + 1, r1 + 1)]
    kind = column_kind(cells)
    key, n = slug(header), 2
    while key in keys:
        key, n = f"{slug(header)}_{n}", n + 1
    spec = {"key": key, "header": header, "description": "", "required": False}
    if kind == "formula":
        formula_cells = [c for c in cells if isinstance(c.value, str) and c.value.startswith("=")]
        first = formula_cells[0]
        if len({c.value for c in formula_cells}) == 1 and len(formula_cells) == len(cells):
            spec.update(type="formula", formula=normalise(first.value, table_name))  # same on every row
        else:
            spec.update(type="formula", formula_a1=first.value, formula_row=first.row)  # row-relative A1
    elif kind == "date":
        spec["type"] = "date"
    elif kind == "number":
        nums = [c.value for c in cells if isinstance(c.value, (int, float))]
        spec["type"] = "integer" if all(float(v).is_integer() for v in nums) else "number"
    else:
        choices = _dv_list(ws, col, r0 + 1)
        values = {str(c.value).lower() for c in cells if c.value not in (None, "")}
        if choices and {c.lower() for c in choices} == {"yes", "no"}:
            spec["type"] = "yes_no"
        elif choices:
            spec.update(type="choice", choices=choices)
        else:
            spec["type"] = "long_text" if any(len(str(c.value or "")) > 60 for c in cells) else "text"
            if values and values <= {"yes", "no"}:
                spec["type"] = "yes_no"
    return spec


def _table_spec(ws, xl, existing=None):
    c0, r0, c1, r1 = range_boundaries(xl.ref)
    headers = [str(ws.cell(r0, c).value or "").strip() for c in range(c0, c1 + 1)]
    old = {c["header"].lower(): c for c in (existing or {}).get("columns", [])}
    cols, keys = [], set()
    for i, h in enumerate(headers):
        col = old.get(h.lower())
        if col is None:
            col = _infer_column(ws, c0 + i, r0, r1, h, xl.displayName, keys | {c["key"] for c in old.values()})
        else:
            col = dict(col, header=h)
        keys.add(col["key"])
        cols.append(col)
    return cols, f"{get_column_letter(c0)}{r0}"


def sync_adlc(wb, ctx, changes, logged_ops, requested_by, tool, summary) -> str:
    from adlc_workbook.meta import bump_version, read_meta
    from adlc_workbook.spec import slug, validate_spec
    from adlc_workbook.workbook import AdlcWorkbook, now_iso

    meta, spec = read_meta(wb)
    for old, new in ctx.sheet_renames.items():
        for s in spec["sheets"]:
            if s["name"] == old:
                s["name"] = new
    for sheet in list(spec["sheets"]):
        if sheet["name"] not in wb.sheetnames:
            spec["sheets"].remove(sheet)
            continue
        ws = wb[sheet["name"]]
        tables = {n.lower(): t for n, t in ((t.displayName, t) for t in ws.tables.values())}
        kept = []
        for t in sheet["tables"]:
            xl = tables.get(t["name"].lower())
            if xl is None:
                ctx.warnings.append(f"Table {t['name']} is no longer on '{ws.title}', so it was dropped from the workbook's record.")
                continue
            t["columns"], t["anchor"] = _table_spec(ws, xl, t)
            if "rows_from" not in t and not any(c["type"] == "id" for c in t["columns"]):
                t["static"] = True
            kept.append(t)
        sheet["tables"] = kept

    known = {t["name"].lower() for s in spec["sheets"] for t in s["tables"]}
    added = []
    for ws in wb.worksheets:
        if ws.title in ADLC_SHEETS:
            continue
        for name, xl in ((t.displayName, t) for t in ws.tables.values()):
            if name.lower() in known:
                continue
            cols, anchor = _table_spec(ws, xl)
            key, n = slug(name.removeprefix("tbl")), 2
            while any(t["key"] == key for s in spec["sheets"] for t in s["tables"]):
                key, n = f"{slug(name)}_{n}", n + 1
            table = {"key": key, "name": name, "anchor": anchor, "style": "TableStyleMedium2", "columns": cols}
            if not any(c["type"] == "id" for c in cols):
                table["static"] = True
            sheet = next((s for s in spec["sheets"] if s["name"] == ws.title), None)
            if sheet is None:
                sheet = {"name": ws.title, "description": "", "tables": [], "charts": []}
                spec["sheets"].append(sheet)
            sheet["tables"].append(table)
            added.append((sheet, table))

    errors = validate_spec(spec)
    if errors and added:
        for sheet, table in added:
            sheet["tables"].remove(table)
        spec["sheets"] = [s for s in spec["sheets"] if s["tables"] or s.get("charts")]
        errors = validate_spec(spec)
    if errors:
        ctx.warnings.append("The workbook's AI-safe record could not describe every change: " + "; ".join(errors[:3]))

    awb = AdlcWorkbook(wb, spec, meta)
    awb.meta["version"] = bump_version(meta.get("version"))
    awb.meta["updated"] = now_iso()
    awb.meta["updated_by"] = requested_by or "unknown"
    entry = {
        "version": awb.meta["version"],
        "date": datetime.now().replace(microsecond=0),
        "requested_by": requested_by or "unknown",
        "tool": tool,
        "summary": summary or "; ".join(changes)[:250],
        "changes": "\n".join(f"• {c}" for c in changes),
        "details": __import__("json").dumps(logged_ops, ensure_ascii=False, default=str)[:30_000],
    }
    awb._finish(entry, param_overrides=set())
    return awb.meta["version"]
