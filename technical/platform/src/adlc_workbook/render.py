"""Write a spec (plus data rows) into an openpyxl workbook.

Every data table is an Excel Table. A table is always re-written as a whole block, which
keeps it consistent with the spec and leaves everything outside the table untouched.
"""

from __future__ import annotations

from datetime import date, datetime, time

from openpyxl.comments import Comment
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.formula.translate import Translator
from openpyxl.styles import Alignment, Border, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string, range_boundaries
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableFormula, TableStyleInfo

from . import formulas
from .meta import META_SHEET
from .spec import iter_tables

BUFFER_ROWS = 500
README_SHEET = "README"
SETTINGS_SHEET = "Settings"
CHANGELOG_SHEET = "Change Log"
LISTS_SHEET = "_Lists"

NUMBER_FORMATS = {
    "id": "@", "text": "@", "long_text": "@", "choice": "@", "yes_no": "@",
    "number": "#,##0.00", "integer": "#,##0", "currency": '"€"#,##0.00',
    "percent": "0%", "date": "dd/mm/yyyy", "formula": "General",
}
DEFAULT_WIDTHS = {
    "id": 11, "text": 24, "long_text": 48, "number": 13, "integer": 11, "currency": 14,
    "percent": 11, "date": 13, "choice": 17, "yes_no": 10, "formula": 15,
}
TYPE_LABELS = {
    "id": "Automatic ID - leave blank, it is filled in for you",
    "text": "Text",
    "long_text": "Longer text",
    "number": "Number",
    "integer": "Whole number",
    "currency": "Amount in euro",
    "percent": "Percentage (type 50% or 0.5)",
    "date": "Date (DD/MM/YYYY)",
    "choice": "Pick from the dropdown list",
    "yes_no": "Yes or No",
    "formula": "Calculated automatically - please don't type here",
}
COLOUR_STYLES = {
    "green": ("C6EFCE", "006100"),
    "amber": ("FFEB9C", "9C5700"),
    "red": ("FFC7CE", "9C0006"),
    "grey": ("EDEDED", "595959"),
    "blue": ("DDEBF7", "1F4E78"),
}
CALC_FILL = PatternFill(fill_type="solid", start_color="F2F2F2", end_color="F2F2F2")
CALC_FONT = Font(color="595959", italic=True)

CHANGELOG_TABLE = {
    "key": "change_log",
    "name": "tblChangeLog",
    "anchor": "A1",
    "style": "TableStyleLight9",
    "columns": [
        {"key": "version", "header": "Version", "type": "text", "width": 9},
        {"key": "date", "header": "Date", "type": "date", "number_format": "dd/mm/yyyy hh:mm", "width": 17},
        {"key": "requested_by", "header": "Requested by", "type": "text", "width": 20},
        {"key": "tool", "header": "Tool", "type": "text", "width": 20},
        {"key": "summary", "header": "Summary", "type": "long_text", "width": 45},
        {"key": "changes", "header": "Changes", "type": "long_text", "width": 60},
        {"key": "details", "header": "Technical details", "type": "long_text", "width": 40},
    ],
}


class DriftError(ValueError):
    """The workbook no longer matches its spec in a way the engine cannot repair safely."""


# --------------------------------------------------------------------------- helpers


def anchor_of(table: dict) -> tuple[int, int]:
    letters, row = coordinate_from_string(table.get("anchor", "A1"))
    return column_index_from_string(letters), row


def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def set_text(cell, value):
    """Write ``value``; text that starts with '=' is stored as text, never as a formula."""
    cell.value = value
    if isinstance(value, str) and value.startswith("="):
        cell.data_type = "s"
    return cell


def table_box(ws, table: dict):
    """Current (min_col, min_row, max_col, max_row) of a table in ``ws``, or None."""
    t = ws.tables.get(table["name"]) if table["name"] in ws.tables else None
    return range_boundaries(t.ref) if t is not None else None


def coerce(value, col: dict):
    """Turn a user-supplied value into the right Python type for its column."""
    t = col["type"]
    if _blank(value):
        return None
    if t in ("choice", "yes_no"):
        choices = col.get("choices", [])
        for c in choices:
            if str(value).strip().lower() == str(c).lower():
                return c
        raise ValueError(f"'{value}' is not one of the choices for '{col['header']}': {', '.join(map(str, choices))}")
    if t == "date":
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time())
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        raise ValueError(f"'{value}' is not a date I recognise for '{col['header']}' (use DD/MM/YYYY)")
    if t in ("number", "integer", "currency", "percent"):
        if isinstance(value, bool):
            raise ValueError(f"'{value}' is not a number for '{col['header']}'")
        if isinstance(value, (int, float)):
            num = value
        else:
            # Typed text: "1,250", "€40", "50%" or "50" (a percentage given in points).
            text = str(value).strip().replace(",", "").replace("€", "")
            pct = text.endswith("%")
            try:
                num = float(text.rstrip("%"))
            except ValueError:
                raise ValueError(f"'{value}' is not a number for '{col['header']}'") from None
            if pct or (t == "percent" and num > 1):
                num /= 100
        if t == "integer":
            return int(round(num))
        return num
    return str(value) if not isinstance(value, (int, float, datetime)) else value


# --------------------------------------------------------------------------- reading


def read_rows(ws, table: dict) -> list[dict]:
    """Read the input values of every non-empty row of ``table`` (formula columns skipped)."""
    box = table_box(ws, table)
    if box is None:
        raise DriftError(f"Table {table['name']} is missing from sheet '{ws.title}'.")
    c0, r0, c1, r1 = box
    headers = [str(ws.cell(r0, c).value or "").strip().lower() for c in range(c0, c1 + 1)]
    index = {}
    for i, col in enumerate(table["columns"]):
        h = str(col["header"]).strip().lower()
        if h in headers:
            index[col["key"]] = c0 + headers.index(h)
        elif len(headers) == len(table["columns"]):
            index[col["key"]] = c0 + i
        else:
            raise DriftError(
                f"Column '{col['header']}' is missing from table {table['name']} on sheet '{ws.title}'."
            )
    keep = [c for c in table["columns"] if c["type"] != "formula"]
    rows = []
    for r in range(r0 + 1, r1 + 1):
        row = {c["key"]: ws.cell(r, index[c["key"]]).value for c in keep}
        if all(_blank(row.get(c["key"])) for c in keep if c["type"] != "id"):
            continue
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- writing


def _clear_box(ws, c0, r0, c1, r1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            cell = ws.cell(r, c)
            cell.value = None
            cell.comment = None
            cell.font = Font()
            cell.fill = PatternFill()
            cell.border = Border()
            cell.alignment = Alignment()
            cell.number_format = "General"


def _intersects(sqref, c0, c1, first_row) -> bool:
    for rng in str(sqref).split():
        try:
            a, b, c, d = range_boundaries(rng)
        except ValueError:
            continue
        if a is None:
            continue
        if not (c < c0 or a > c1) and (d is None or d >= first_row):
            return True
    return False


def _clear_rules(ws, c0, c1, first_row):
    dvs = ws.data_validations.dataValidation
    ws.data_validations.dataValidation = [
        dv for dv in dvs if not _intersects(dv.sqref, c0, c1, first_row)
    ]
    keep = ConditionalFormattingList()
    for cf in ws.conditional_formatting:
        if _intersects(cf.sqref, c0, c1, first_row):
            continue
        for rule in cf.rules:
            keep.add(str(cf.sqref), rule)
    ws.conditional_formatting = keep


def _capture_styles(ws, box, table):
    """Remember header and first-data-row styles per column (used for adopted workbooks)."""
    c0, r0, c1, r1 = box
    headers = [str(ws.cell(r0, c).value or "").strip().lower() for c in range(c0, c1 + 1)]
    styles = {}
    for col in table["columns"]:
        h = str(col["header"]).lower()
        if h in headers:
            c = c0 + headers.index(h)
            styles[col["key"]] = (ws.cell(r0, c)._style, ws.cell(min(r0 + 1, r1), c)._style)
    return styles


def _formula_for(col, table, row, col_idx):
    if col.get("formula"):
        return col["formula"]
    if col.get("formula_a1"):
        letter = get_column_letter(col_idx)
        origin = f"{letter}{col.get('formula_row', 2)}"
        return Translator(col["formula_a1"], origin=origin).translate_formula(f"{letter}{row}")
    return None


def _style_data_cell(cell, col, preserved):
    if preserved is not None:
        cell._style = preserved
        return
    cell.number_format = col.get("number_format") or NUMBER_FORMATS.get(col["type"], "General")
    wrap = col["type"] == "long_text"
    cell.alignment = Alignment(vertical="top", wrap_text=wrap)
    if col["type"] == "formula":
        cell.fill = CALC_FILL
        cell.font = CALC_FONT


def check_room(ws, table: dict, n_rows: int) -> None:
    """Refuse to grow a table over cells that already hold something (e.g. a totals row)."""
    c0, r0 = anchor_of(table)
    c1, r1 = c0 + len(table["columns"]) - 1, r0 + max(1, n_rows)
    old = table_box(ws, table)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if old and old[0] <= c <= old[2] and old[1] <= r <= old[3]:
                continue
            cell = ws._cells.get((r, c))
            if cell is not None and cell.value not in (None, ""):
                raise DriftError(
                    f"There is something in {cell.coordinate} on '{ws.title}' ({str(cell.value)[:40]!r}) where the "
                    "table needs to grow. Move it further away from the table (or to another sheet) and try again, "
                    "so nothing gets overwritten."
                )


def _free_rows_end(ws, c0, c1, r1) -> int:
    """Last row below a table that dropdowns and highlights may cover without touching other content."""
    for r in range(r1 + 1, r1 + BUFFER_ROWS + 1):
        if any(ws._cells.get((r, c)) is not None and ws._cells[(r, c)].value not in (None, "") for c in range(c0, c1 + 1)):
            return r - 1
    return r1 + BUFFER_ROWS


def write_table(wb, ws, table: dict, rows: list[dict], *, validations: bool = True, freeze: bool = True):
    """(Re)write ``table`` with ``rows`` as an Excel Table on ``ws``."""
    cols = table["columns"]
    c0, r0 = anchor_of(table)
    n = max(1, len(rows))
    c1, r1 = c0 + len(cols) - 1, r0 + n
    check_room(ws, table, len(rows))

    old_box = table_box(ws, table)
    preserve = bool(table.get("preserve_styles")) and old_box is not None
    styles = _capture_styles(ws, old_box, table) if preserve else {}
    old_style_name = None
    if old_box is not None:
        old_style_name = ws.tables[table["name"]].tableStyleInfo.name if ws.tables[table["name"]].tableStyleInfo else None
        _clear_box(ws, *old_box)
        del ws.tables[table["name"]]
        band = (min(old_box[0], c0), max(old_box[2], c1))
    else:
        band = (c0, c1)
    _clear_rules(ws, band[0], band[1], r0 + 1)

    for i, col in enumerate(cols):
        cell = ws.cell(r0, c0 + i, value=str(col["header"]))
        if col.get("description"):
            note = Comment(str(col["description"]), "ADLC")
            note.width, note.height = 220, 90
            cell.comment = note
        if col["key"] in styles:
            cell._style = styles[col["key"]][0]

    for ri in range(n):
        row = rows[ri] if ri < len(rows) else {}
        r = r0 + 1 + ri
        for i, col in enumerate(cols):
            cell = ws.cell(r, c0 + i)
            if col["type"] == "formula":
                cell.value = _formula_for(col, table, r, c0 + i)
            else:
                # Values are written as they are: new input is coerced by the caller.
                if col["type"] in ("text", "long_text", "id", "choice", "yes_no"):
                    set_text(cell, row.get(col["key"]))
                else:
                    cell.value = row.get(col["key"])
            _style_data_cell(cell, col, styles[col["key"]][1] if col["key"] in styles else None)

    ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(c1)}{r1}"
    t = Table(displayName=table["name"], ref=ref)
    t.tableStyleInfo = TableStyleInfo(
        name=table.get("style") or old_style_name or "TableStyleMedium2", showRowStripes=True
    )
    t.autoFilter = AutoFilter(ref=ref)
    t.tableColumns = []
    for i, col in enumerate(cols):
        tc = TableColumn(id=i + 1, name=str(col["header"]))
        if col["type"] == "formula" and col.get("formula"):
            tc.calculatedColumnFormula = TableFormula(attr_text=col["formula"][1:])
        t.tableColumns.append(tc)
    ws.add_table(t)

    if not preserve:
        for i, col in enumerate(cols):
            width = col.get("width") or max(DEFAULT_WIDTHS.get(col["type"], 15), min(len(str(col["header"])) + 4, 40))
            ws.column_dimensions[get_column_letter(c0 + i)].width = width
    if freeze and table.get("anchor", "A1") == "A1":
        ws.freeze_panes = "A2"
    if validations:
        last = _free_rows_end(ws, c0, c1, r1)
        _add_validations(wb, ws, table, r0 + 1, last)
        _add_formatting(ws, table, r0 + 1, last)


def list_name(table: dict, col: dict) -> str:
    return f"lst_{table['key']}_{col['key']}"


def _inline_list_ok(choices) -> bool:
    joined = ",".join(str(c) for c in choices)
    return len(joined) <= 250 and not any("," in str(c) or '"' in str(c) for c in choices)


def _add_validations(wb, ws, table, first, last):
    c0, _ = anchor_of(table)
    for i, col in enumerate(table["columns"]):
        letter = get_column_letter(c0 + i)
        t = col["type"]
        dv = None
        if t in ("choice", "yes_no"):
            choices = col.get("choices", [])
            formula1 = (
                '"' + ",".join(str(c) for c in choices) + '"'
                if _inline_list_ok(choices) else f"={list_name(table, col)}"
            )
            dv = DataValidation(type="list", formula1=formula1, allow_blank=True)
            dv.errorTitle = "Please pick from the list"
            dv.error = (
                f"'{col['header']}' must be one of the options in the dropdown. "
                "To add a new option, ask the Excel Expert agent."
            )[:225]
        elif t == "date":
            dv = DataValidation(type="date", operator="greaterThan", formula1="36526", allow_blank=True)
            dv.errorTitle = "Please type a date"
            dv.error = f"'{col['header']}' needs a date, for example 31/12/2026."
        elif t in ("integer", "number", "currency", "percent"):
            lo = col.get("min", -1_000_000_000_000)
            hi = col.get("max", 1_000_000_000_000)
            dv = DataValidation(
                type="whole" if t == "integer" else "decimal", operator="between",
                formula1=str(lo), formula2=str(hi), allow_blank=True,
            )
            dv.errorTitle = "Please type a number"
            rng_text = f" between {lo} and {hi}" if "min" in col or "max" in col else ""
            dv.error = f"'{col['header']}' needs a number{rng_text}."
        if dv is not None:
            dv.showErrorMessage = True
            dv.errorStyle = "stop"
            dv.add(f"{letter}{first}:{letter}{last}")
            ws.add_data_validation(dv)


def _literal(v) -> str:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return '"' + str(v).replace('"', '""') + '"'


def _row_has_data(table, c0, first) -> str:
    parts = [
        f"LEN(${get_column_letter(c0 + i)}{first})"
        for i, col in enumerate(table["columns"])
        if col["type"] not in ("formula", "id")
    ]
    return "(" + "+".join(parts) + ")>0" if parts else "FALSE"


def _condition(hl, cell, has_data) -> str:
    when = hl["when"]
    v = hl.get("value_formula") or (_literal(hl.get("value")) if "value" in hl else '""')
    return {
        "equals": f"{cell}={v}",
        "not_equals": f"AND(LEN({cell})>0,{cell}<>{v})",
        "less_than": f"AND(ISNUMBER({cell}),{cell}<{v})",
        "greater_than": f"AND(ISNUMBER({cell}),{cell}>{v})",
        "less_or_equal": f"AND(ISNUMBER({cell}),{cell}<={v})",
        "greater_or_equal": f"AND(ISNUMBER({cell}),{cell}>={v})",
        "blank": f"AND({has_data},LEN({cell})=0)",
        "not_blank": f"LEN({cell})>0",
        "contains": f"ISNUMBER(SEARCH({v},{cell}))",
    }[when]


def _rule(expr, colour):
    bg, fg = COLOUR_STYLES[colour]
    return FormulaRule(
        formula=[expr],
        fill=PatternFill(start_color=bg, end_color=bg, fill_type="solid"),
        font=Font(color=fg),
    )


def _add_formatting(ws, table, first, last):
    c0, _ = anchor_of(table)
    c1 = c0 + len(table["columns"]) - 1
    has_data = _row_has_data(table, c0, first)
    for i, col in enumerate(table["columns"]):
        letter = get_column_letter(c0 + i)
        cell = f"${letter}{first}"
        col_rng = f"{letter}{first}:{letter}{last}"
        if col.get("required") and col["type"] not in ("formula", "id"):
            ws.conditional_formatting.add(col_rng, _rule(f"AND({has_data},LEN(TRIM({cell}))=0)", "red"))
        for hl in col.get("highlights", []):
            rng = (
                f"{get_column_letter(c0)}{first}:{get_column_letter(c1)}{last}"
                if hl.get("whole_row") else col_rng
            )
            ws.conditional_formatting.add(rng, _rule(_condition(hl, cell, has_data), hl.get("color", "green")))


# --------------------------------------------------------------------------- rows_from


def summary_rows(spec, table, existing: list[dict]) -> list[dict]:
    """Rows of a summary table: one per choice of the source column, keeping typed inputs."""
    from .spec import find_column, find_table

    _, src = find_table(spec, table["rows_from"]["table"])
    src_col = find_column(src, table["rows_from"]["column"])
    cat_key = table["columns"][0]["key"]
    by_cat = {str(r.get(cat_key)): r for r in existing}
    rows = []
    for choice in src_col.get("choices", []):
        row = dict(by_cat.get(str(choice), {}))
        row[cat_key] = choice
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- lists, settings


def _fresh_sheet(wb, name, index=None):
    if name in wb.sheetnames:
        del wb[name]
    return wb.create_sheet(name, index) if index is not None else wb.create_sheet(name)


def _drop_names(wb, prefix):
    for name in [n for n in list(wb.defined_names.keys()) if n.startswith(prefix)]:
        del wb.defined_names[name]


def render_lists(wb, spec):
    """Long dropdown lists live on a hidden _Lists sheet behind named ranges."""
    _drop_names(wb, "lst_")
    long_lists = [
        (table, col) for _, table in iter_tables(spec) for col in table["columns"]
        if col["type"] in ("choice", "yes_no") and not _inline_list_ok(col.get("choices", []))
    ]
    if not long_lists:
        if LISTS_SHEET in wb.sheetnames:
            del wb[LISTS_SHEET]
        return
    ws = _fresh_sheet(wb, LISTS_SHEET)
    ws.sheet_state = "hidden"
    for i, (table, col) in enumerate(long_lists, start=1):
        letter = get_column_letter(i)
        ws.cell(1, i, value=list_name(table, col))
        for r, choice in enumerate(col["choices"], start=2):
            ws.cell(r, i, value=str(choice))
        last = len(col["choices"]) + 1
        ref = f"'{LISTS_SHEET}'!${letter}$2:${letter}${last}"
        wb.defined_names[list_name(table, col)] = DefinedName(list_name(table, col), attr_text=ref)


PARAM_FORMATS = {
    "number": "#,##0.00", "integer": "0", "currency": '"€"#,##0.00',
    "percent": "0%", "date": "dd/mm/yyyy", "text": "@",
}


def render_settings(wb, spec, overrides: set[str] | None = None):
    """Settings sheet: one row per parameter, each value cell has a name like p_due_soon_days.

    Values people typed in Excel are kept unless the parameter is in ``overrides``.
    """
    _drop_names(wb, "p_")
    params = spec.get("parameters", [])
    current = {}
    if SETTINGS_SHEET in wb.sheetnames:
        ws_old = wb[SETTINGS_SHEET]
        for r in range(2, ws_old.max_row + 1):
            name = ws_old.cell(r, 3).value
            if name:
                current[str(name)] = ws_old.cell(r, 2).value
    if not params:
        if SETTINGS_SHEET in wb.sheetnames:
            del wb[SETTINGS_SHEET]
        return
    ws = _fresh_sheet(wb, SETTINGS_SHEET)
    headers = ["Setting", "Value", "Name used in formulas", "What it does"]
    for i, h in enumerate(headers, start=1):
        ws.cell(1, i, value=h)
    for r, p in enumerate(params, start=2):
        pname = f"p_{p['key']}"
        value = p.get("value")
        if pname in current and (overrides is None or p["key"] not in overrides):
            value = current[pname]
        if p["type"] == "date" and value is not None:
            value = coerce(value, {"type": "date", "header": p["label"]})
        ws.cell(r, 1, value=p["label"])
        vcell = ws.cell(r, 2, value=value)
        vcell.number_format = PARAM_FORMATS.get(p["type"], "General")
        vcell.fill = PatternFill(fill_type="solid", start_color="FFF2CC", end_color="FFF2CC")
        ws.cell(r, 3, value=pname)
        ws.cell(r, 4, value=p.get("description", "")).alignment = Alignment(wrap_text=True, vertical="top")
        wb.defined_names[pname] = DefinedName(pname, attr_text=f"'{SETTINGS_SHEET}'!$B${r}")
    ref = f"A1:D{len(params) + 1}"
    t = Table(displayName="tblSettings", ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    t.autoFilter = AutoFilter(ref=ref)
    ws.add_table(t)
    for letter, width in zip("ABCD", (40, 16, 26, 70)):
        ws.column_dimensions[letter].width = width
    ws.freeze_panes = "A2"


# --------------------------------------------------------------------------- change log


def changelog_rows(wb) -> list[dict]:
    if CHANGELOG_SHEET not in wb.sheetnames:
        return []
    ws = wb[CHANGELOG_SHEET]
    if CHANGELOG_TABLE["name"] not in ws.tables:
        return []
    return read_rows(ws, CHANGELOG_TABLE)


def render_changelog(wb, rows: list[dict]):
    ws = wb[CHANGELOG_SHEET] if CHANGELOG_SHEET in wb.sheetnames else wb.create_sheet(CHANGELOG_SHEET)
    write_table(wb, ws, CHANGELOG_TABLE, rows, validations=False)


# --------------------------------------------------------------------------- README


H1 = Font(bold=True, size=16, color="1F4E78")
H2 = Font(bold=True, size=12, color="1F4E78")
BOLD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")


def render_readme(wb, spec, meta, editor_agent: str = "Laya Excel Expert"):
    ws = _fresh_sheet(wb, README_SHEET, 0)
    info = spec["workbook"]
    r = 1

    def put(text, font=None, col=1):
        nonlocal r
        cell = set_text(ws.cell(r, col), text)
        cell.alignment = WRAP
        if font:
            cell.font = font
        return cell

    def line(*values, font=None):
        nonlocal r
        for i, v in enumerate(values, start=1):
            cell = set_text(ws.cell(r, i), v)
            cell.alignment = WRAP
            if font:
                cell.font = font
        r += 1

    put(info["title"], H1)
    r += 1
    if info.get("purpose"):
        put(info["purpose"])
        r += 1
    r += 1
    put("About this workbook", H2)
    r += 1
    for label, key in (("Owner", "owner"), ("Version", "version"), ("Last updated", "updated"),
                       ("Updated by", "updated_by"), ("Workbook ID", "workbook_id")):
        value = meta.get(key) or info.get(key, "")
        if key == "updated" and value:
            value = str(value)[:16].replace("T", " ")
        line(label, value)
    r += 1

    if info.get("how_to_use"):
        put("How to use it", H2)
        r += 1
        for i, step in enumerate(info["how_to_use"], start=1):
            line(f"{i}.", step)
        r += 1

    put("What's in this workbook", H2)
    r += 1
    line("Sheet", "What it holds", font=BOLD)
    line(README_SHEET, "This page.")
    for sheet in spec["sheets"]:
        line(sheet["name"], sheet.get("description", ""))
    if spec.get("parameters"):
        line(SETTINGS_SHEET, "Numbers the formulas use (for example, how many days count as 'due soon'). You can change the yellow cells.")
    line(CHANGELOG_SHEET, "A record of every change made to this workbook's structure or data by the AI agents.")
    r += 1

    for sheet in spec["sheets"]:
        for table in sheet["tables"]:
            put(f"Columns in '{sheet['name']}'", H2)
            r += 1
            line("Column", "What to enter", "Type", "Must fill in?", "Options / how it's worked out", font=BOLD)
            for col in table["columns"]:
                if col["type"] == "formula":
                    detail = "Formula: " + formulas.display(
                        col.get("formula") or col.get("formula_a1", ""), table["name"]
                    ).lstrip("=")
                elif col["type"] in ("choice", "yes_no"):
                    detail = ", ".join(str(c) for c in col.get("choices", []))
                else:
                    detail = ""
                line(col["header"], col.get("description", ""), TYPE_LABELS.get(col["type"], col["type"]),
                     "Yes" if col.get("required") else "", detail)
            r += 1

    put("Changing this workbook with AI", H2)
    r += 1
    steps = [
        f"Open Microsoft Copilot and choose the '{editor_agent}' agent.",
        "Upload this file and say what you want to change, in your own words.",
        "Check the list of changes it proposes, then reply OK.",
        "Download the new file and save it over this one in SharePoint. SharePoint keeps the old version, so nothing is lost.",
    ]
    for i, step in enumerate(steps, start=1):
        line(f"{i}.", step)
    r += 1
    put("Please don't rename or delete the hidden '_ADLC' sheet, and don't rename the tables. "
        "That is how the agents remember this workbook's structure. Typing, editing or deleting rows yourself is fine.")
    ws.cell(r, 1).font = Font(italic=True, color="9C0006")

    for letter, width in zip("ABCDE", (26, 60, 30, 14, 50)):
        ws.column_dimensions[letter].width = width
    ws.sheet_view.showGridLines = False


# --------------------------------------------------------------------------- order


def order_sheets(wb, spec):
    spec_names = [s["name"] for s in spec["sheets"]]
    fixed_tail = [SETTINGS_SHEET, CHANGELOG_SHEET, LISTS_SHEET, META_SHEET]
    by_name = {ws.title: ws for ws in wb._sheets}
    ordered = [by_name[README_SHEET]] if README_SHEET in by_name else []
    ordered += [by_name[n] for n in spec_names if n in by_name]
    ordered += [ws for ws in wb._sheets if ws.title not in spec_names + fixed_tail + [README_SHEET]]
    ordered += [by_name[n] for n in fixed_tail if n in by_name]
    wb._sheets = ordered
    for ws in wb.worksheets:
        ws.sheet_view.tabSelected = False
    wb.active = 0
    wb.worksheets[0].sheet_view.tabSelected = True
