"""Adopt an existing (non-ADLC) workbook: work out its structure and make it AI-safe.

Adoption touches as little as possible. Each data block becomes an Excel Table (if it is
not one already). An ID column is added at the right-hand end when there is none, and
blank IDs are filled in. README, Change Log and the hidden _ADLC sheet are then added.
Existing values, formulas and formatting are left alone.
"""

from __future__ import annotations

import copy
import re
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo

from . import formulas
from .meta import is_adlc
from .spec import prepare_spec, slug, stored_spec

ID_HEADERS = {"id", "ref", "ref no", "ref.", "reference", "no", "no.", "#", "number", "item id", "case id"}
TOTAL_WORDS = ("total", "grand total", "sum")


@dataclass
class AdoptResult:
    spec: dict
    notes: list[str] = field(default_factory=list)
    awb: object = None


def risky_parts(path: str | Path) -> list[str]:
    """Things inside the file that openpyxl may not round-trip perfectly."""
    notes = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    if any(n.startswith("xl/pivotTables/") for n in names):
        notes.append("It contains pivot tables. They are kept, but refresh them in Excel after any change.")
    if any(n.startswith("xl/charts/") for n in names):
        notes.append("It contains charts. They are kept, but some chart formatting may be simplified.")
    if any(n.startswith("xl/drawings/") and "vmlDrawing" not in n for n in names) and not any(
        n.startswith("xl/charts/") for n in names
    ):
        notes.append("It contains shapes or pictures, which may be lost when the file is saved by the agent.")
    if any("vbaProject" in n for n in names):
        notes.append("It contains macros. Macros are not kept - use a copy, not the original.")
    if any(n.startswith("xl/externalLinks/") for n in names):
        notes.append("It links to other workbooks. Check those links still work after the change.")
    return notes


def _is_formula(v) -> bool:
    return isinstance(v, str) and v.startswith("=")


def _infer_type(values, number_formats, header):
    vals = [v for v in values if v not in (None, "")]
    if not vals:
        return {"type": "text"}
    if sum(_is_formula(v) for v in vals) >= max(1, len(vals) // 2):
        return {"type": "formula"}
    if all(isinstance(v, (datetime, date)) for v in vals):
        return {"type": "date"}
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        fmt = " ".join(number_formats)
        if "%" in fmt:
            return {"type": "percent"}
        if "€" in fmt or "$" in fmt or "£" in fmt:
            return {"type": "currency"}
        if all(float(v).is_integer() for v in vals):
            return {"type": "integer"}
        return {"type": "number"}
    texts = [str(v).strip() for v in vals]
    distinct = list(dict.fromkeys(texts))
    if {d.lower() for d in distinct} <= {"yes", "no"}:
        return {"type": "yes_no"}
    if len(distinct) <= 12 and len(texts) >= 2 * len(distinct) and max(len(d) for d in distinct) <= 30:
        return {"type": "choice", "choices": distinct}
    if sum(len(t) for t in texts) / len(texts) > 60:
        return {"type": "long_text"}
    return {"type": "text"}


def _dv_choices(wb, ws, col_idx, row):
    for dv in ws.data_validations.dataValidation:
        if dv.type != "list" or not dv.formula1:
            continue
        for rng in str(dv.sqref).split():
            c0, r0, c1, r1 = range_boundaries(rng)
            if not (c0 <= col_idx <= c1 and r0 <= row <= (r1 or row)):
                continue
            f = dv.formula1.strip()
            if f.startswith('"'):
                return [x.strip() for x in f.strip('"').split(",") if x.strip()]
            m = re.match(r"^=?'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+):\$?([A-Z]+)\$?(\d+)$", f)
            if m and m.group(1) in wb.sheetnames:
                src = wb[m.group(1)]
                cells = src[f"{m.group(2)}{m.group(3)}:{m.group(4)}{m.group(5)}"]
                return [str(c.value) for row_ in cells for c in row_ if c.value not in (None, "")]
    return None


def _detect_region(ws):
    """Find the first header row + data block on a sheet without Excel Tables."""
    max_r = min(ws.max_row, 30)
    for r in range(1, max_r + 1):
        cells = [(c, ws.cell(r, c).value) for c in range(1, ws.max_column + 1)]
        filled = [(c, v) for c, v in cells if v not in (None, "")]
        if len(filled) >= 2 and all(isinstance(v, str) for _, v in filled):
            c0 = filled[0][0]
            c1 = c0
            while c1 + 1 <= ws.max_column and ws.cell(r, c1 + 1).value not in (None, ""):
                c1 += 1
            if c1 == c0:
                continue
            last = r
            for rr in range(r + 1, ws.max_row + 1):
                if all(ws.cell(rr, c).value in (None, "") for c in range(c0, c1 + 1)):
                    break
                last = rr
            return c0, r, c1, last
    return None


def adopt(path: str | Path, *, title: str | None = None, owner: str = "", write: bool = True,
          requested_by: str = "ADLC engine", tool: str = "ADLC engine") -> AdoptResult:
    from .workbook import AdlcWorkbook, fill_ids, now_iso

    path = Path(path)
    wb = load_workbook(path)
    if is_adlc(wb):
        raise ValueError("This workbook is already an ADLC workbook - there is nothing to adopt.")
    notes = risky_parts(path)
    sheets_spec = []
    used_keys = set()
    plans = []

    for ws in wb.worksheets:
        if ws.sheet_state != "visible":
            continue
        existing = list(ws.tables.values())
        if existing:
            t = existing[0]
            box = range_boundaries(t.ref)
            if len(existing) > 1:
                notes.append(f"'{ws.title}' has {len(existing)} tables; only '{t.displayName}' was adopted.")
        else:
            box = _detect_region(ws)
            t = None
            if box is None:
                notes.append(f"'{ws.title}' has no table of data, so it was left as it is.")
                continue
        c0, r0, c1, r1 = box
        # Leave a totals row at the bottom outside the table.
        if t is None and r1 > r0:
            first = next((ws.cell(r1, c).value for c in range(c0, c1 + 1) if ws.cell(r1, c).value not in (None, "")), "")
            if str(first).strip().lower().startswith(TOTAL_WORDS):
                notes.append(
                    f"'{ws.title}': row {r1} looks like a totals row, so it was kept outside the table. "
                    "Before adding rows, move it above the table or to a summary sheet - otherwise there is no room to grow."
                )
                r1 -= 1
        merged = [m for m in ws.merged_cells.ranges if not (m.max_col < c0 or m.min_col > c1 or m.max_row < r0 or m.min_row > r1)]
        if merged:
            notes.append(f"'{ws.title}' has merged cells inside its data, so it was not adopted. Unmerge them and try again.")
            continue

        headers, seen = [], set()
        for c in range(c0, c1 + 1):
            h = re.sub(r"[\[\]#'\n\r\t]+", "-", str(ws.cell(r0, c).value or f"Column {c - c0 + 1}")).strip() or f"Column {c - c0 + 1}"
            base, n = h, 2
            while h.lower() in seen:
                h, n = f"{base} {n}", n + 1
            seen.add(h.lower())
            headers.append(h)

        tname = t.displayName if t is not None else "tbl" + "".join(p.capitalize() for p in re.split(r"[^A-Za-z0-9]+", ws.title) if p)
        if not re.match(r"^[A-Za-z_]", tname):
            tname = "tbl" + tname
        key = slug(ws.title)
        while key in used_keys:
            key += "_2"
        used_keys.add(key)

        columns = []
        id_index = None
        data_rows = range(r0 + 1, r1 + 1)
        for i, (c, h) in enumerate(zip(range(c0, c1 + 1), headers)):
            values = [ws.cell(r, c).value for r in data_rows]
            fmts = [ws.cell(r, c).number_format for r in data_rows[:20]]
            col = {"key": slug(h), "header": h, "description": ""}
            nonblank = [str(v) for v in values if v not in (None, "")]
            if id_index is None and h.lower() in ID_HEADERS and len(set(nonblank)) == len(nonblank):
                col["type"] = "id"
                id_index = i
            else:
                dv = _dv_choices(wb, ws, c, r0 + 1)
                col.update({"type": "choice", "choices": dv} if dv else _infer_type(values, fmts, h))
            if col["type"] == "formula":
                frow = next(r for r, v in zip(data_rows, values) if _is_formula(v))
                fval = ws.cell(frow, c).value
                if "[" in fval and t is not None:
                    col["formula"] = formulas.normalise(fval, tname)
                else:
                    col["formula_a1"], col["formula_row"] = fval, frow
            k, n = col["key"], 2
            while any(x["key"] == col["key"] for x in columns):
                col["key"], n = f"{k}_{n}", n + 1
            columns.append(col)

        add_id = id_index is None
        if add_id:
            free = all(ws.cell(r, c1 + 1).value in (None, "") for r in range(r0, r1 + 1))
            if not free:
                notes.append(f"'{ws.title}' has no ID column and no free column to the right for one, so it was not adopted.")
                continue
            columns.append({"key": "id" if "id" not in [x["key"] for x in columns] else "adlc_id", "header": "ID", "type": "id"})
            notes.append(f"'{ws.title}': added an 'ID' column at the right-hand end so rows can be found reliably.")
        id_col = next(x for x in columns if x["type"] == "id")
        ids = [str(ws.cell(r, c0 + columns.index(id_col)).value or "") for r in data_rows] if not add_id else []
        m = [re.match(r"^([A-Za-z]+[-_]?)\d+$", v) for v in ids if v]
        prefix = m[0].group(1) if m and all(x and x.group(1) == m[0].group(1) for x in m) else (re.sub(r"[^A-Z]", "", key.upper())[:3] or "ROW") + "-"

        table = {
            "key": key, "name": tname, "anchor": f"{get_column_letter(c0)}{r0}",
            "style": (t.tableStyleInfo.name if t is not None and t.tableStyleInfo else "TableStyleMedium2"),
            "id_prefix": prefix, "adopted": True, "preserve_styles": True, "columns": columns,
        }
        sheets_spec.append({"name": ws.title, "description": "", "tables": [table], "charts": []})
        plans.append((ws, t, box[0], r0, c1 + (1 if add_id else 0), r1, headers + (["ID"] if add_id else []), add_id))
        kinds = ", ".join(f"{x['header']} ({x['type']})" for x in columns)
        notes.append(f"'{ws.title}': adopted as table {tname} with columns {kinds}.")

    if not sheets_spec:
        raise ValueError("No table of data was found to adopt. " + " ".join(notes))
    spec = prepare_spec({
        "adlc_spec": 1,
        "workbook": {
            "title": title or path.stem.replace("_", " "),
            "purpose": f"Adopted from an existing workbook on {datetime.now():%d/%m/%Y}. Check that the column types and options are right.",
            "owner": owner,
        },
        "sheets": sheets_spec,
    })
    result = AdoptResult(stored_spec(spec), notes)
    if not write:
        return result

    for (ws, t, c0, r0, c1, r1, headers, add_id), (_, table) in zip(plans, [(s, s["tables"][0]) for s in spec["sheets"]]):
        for i, h in enumerate(headers):
            cell = ws.cell(r0, c0 + i)
            if cell.value != h:
                cell.value = h
            if add_id and i == len(headers) - 1:
                cell._style = copy.copy(ws.cell(r0, c1 - 1)._style)
        r1 = max(r1, r0 + 1)
        ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(c1)}{r1}"
        if t is not None:
            t.ref = ref
            t.autoFilter = AutoFilter(ref=ref)
        else:
            t = Table(displayName=table["name"], ref=ref)
            t.tableStyleInfo = TableStyleInfo(name=table["style"], showRowStripes=True)
            t.autoFilter = AutoFilter(ref=ref)
            ws.add_table(t)
        t.tableColumns = [TableColumn(id=i + 1, name=h) for i, h in enumerate(headers)]
        # Fill blank IDs in place, without touching any other cell.
        id_pos = next(i for i, c in enumerate(table["columns"]) if c["type"] == "id")
        rows = []
        for r in range(r0 + 1, r1 + 1):
            row_vals = [ws.cell(r, c0 + j).value for j in range(len(headers)) if j != id_pos]
            rows.append({"r": r, "id": ws.cell(r, c0 + id_pos).value, "has_data": any(v not in (None, "") for v in row_vals)})
        data = [{"id": x["id"]} for x in rows if x["has_data"]]
        fill_ids({"columns": [{"key": "id", "type": "id"}], "id_prefix": table["id_prefix"]}, data)
        for x, d in zip([x for x in rows if x["has_data"]], data):
            if x["id"] in (None, ""):
                cell = ws.cell(x["r"], c0 + id_pos, value=d["id"])
                if add_id:
                    cell._style = copy.copy(ws.cell(x["r"], c0 + id_pos - 1)._style)
                    cell.number_format = "@"

    stored = stored_spec(spec)
    now = now_iso()
    meta = {"format_version": 1, "workbook_id": str(uuid.uuid4()), "template": "adopted",
            "title": stored["workbook"]["title"], "owner": owner, "version": "1.0",
            "created": now, "updated": now, "updated_by": requested_by}
    awb = AdlcWorkbook(wb, stored, meta, path)
    awb._finish({
        "version": "1.0", "date": datetime.now().replace(microsecond=0), "requested_by": requested_by,
        "tool": tool, "summary": "Existing workbook adopted by ADLC",
        "changes": "\n".join(f"• {n}" for n in notes), "details": "",
    }, param_overrides=None)
    result.awb = awb
    return result
