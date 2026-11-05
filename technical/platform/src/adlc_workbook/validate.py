"""Check that a workbook still matches its spec ("drift" detection).

Errors mean the engine cannot safely change the workbook until they are fixed. Warnings
are things a person should know about (blank required cells, duplicate-looking data).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

from . import meta as meta_mod
from .render import CHANGELOG_SHEET, README_SHEET, anchor_of
from .spec import iter_tables, validate_spec


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def text(self) -> str:
        lines = ["OK - the workbook matches its spec." if self.ok else "Problems found:"]
        lines += [f"  ERROR: {e}" for e in self.errors]
        lines += [f"  warning: {w}" for w in self.warnings]
        return "\n".join(lines)


def _dv_covers(ws, letter, row) -> bool:
    for dv in ws.data_validations.dataValidation:
        for rng in str(dv.sqref).split():
            c0, r0, c1, r1 = range_boundaries(rng)
            col = range_boundaries(f"{letter}1")[0]
            if c0 <= col <= c1 and r0 <= row <= r1:
                return True
    return False


def validate_workbook(wb) -> ValidationReport:
    rep = ValidationReport()
    try:
        meta, spec = meta_mod.read_meta(wb)
    except meta_mod.MetaError as exc:
        rep.errors.append(str(exc))
        return rep

    rep.errors += [f"spec: {e}" for e in validate_spec(spec)]
    if meta.get("integrity") == "mismatch":
        rep.warnings.append("The _ADLC checksum does not match its spec - it may have been edited by hand. "
                            "The next change by the engine re-writes it.")
    if wb[meta_mod.META_SHEET].sheet_state == "visible":
        rep.warnings.append("The _ADLC sheet is visible; it is normally hidden.")
    for name in (README_SHEET, CHANGELOG_SHEET):
        if name not in wb.sheetnames:
            rep.warnings.append(f"The '{name}' sheet is missing (it is re-created on the next change).")

    for sheet, table in iter_tables(spec):
        if sheet["name"] not in wb.sheetnames:
            rep.errors.append(f"Sheet '{sheet['name']}' is missing.")
            continue
        ws = wb[sheet["name"]]
        if table["name"] not in ws.tables:
            rep.errors.append(f"Table {table['name']} is missing from sheet '{sheet['name']}' (was it converted to a range or renamed?).")
            continue
        c0, r0, c1, r1 = range_boundaries(ws.tables[table["name"]].ref)
        a0, ar0 = anchor_of(table)
        if (c0, r0) != (a0, ar0):
            rep.errors.append(f"Table {table['name']} has moved from {table['anchor']} to {get_column_letter(c0)}{r0}.")
        headers = [str(ws.cell(r0, c).value or "").strip() for c in range(c0, c1 + 1)]
        expected = [str(c["header"]) for c in table["columns"]]
        if headers != expected:
            missing = [h for h in expected if h not in headers]
            extra = [h for h in headers if h not in expected]
            detail = []
            if missing:
                detail.append("missing: " + ", ".join(missing))
            if extra:
                detail.append("unexpected: " + ", ".join(extra))
            if not detail:
                detail.append("columns are in a different order")
            rep.errors.append(f"Columns of '{sheet['name']}' don't match the spec ({'; '.join(detail)}).")
            continue

        n_rows = r1 - r0
        data_rows = range(r0 + 1, r1 + 1)
        for i, col in enumerate(table["columns"]):
            letter = get_column_letter(c0 + i)
            values = [ws.cell(r, c0 + i).value for r in data_rows]
            if col["type"] == "formula" and col.get("formula"):
                broken = [r for r, v in zip(data_rows, values) if str(v or "") != col["formula"]]
                if broken:
                    rows_txt = ", ".join(str(r) for r in broken[:5]) + ("..." if len(broken) > 5 else "")
                    rep.errors.append(
                        f"'{col['header']}' on '{sheet['name']}' should be calculated, but row(s) {rows_txt} "
                        "hold a different formula or a typed value."
                    )
            elif col["type"] in ("choice", "yes_no"):
                if n_rows and not _dv_covers(ws, letter, r0 + 1):
                    rep.warnings.append(f"The dropdown for '{col['header']}' on '{sheet['name']}' is missing.")
                allowed = {str(c).lower() for c in col.get("choices", [])}
                odd = sorted({str(v) for v in values if v not in (None, "") and str(v).lower() not in allowed})
                if odd:
                    rep.warnings.append(f"'{col['header']}' on '{sheet['name']}' has values not in its list: {', '.join(odd[:5])}.")
            elif col["type"] == "id":
                has_data = [
                    r for r in data_rows
                    if any(ws.cell(r, c0 + j).value not in (None, "")
                           for j, c in enumerate(table["columns"]) if c["type"] not in ("id", "formula"))
                ]
                blanks = [r for r in has_data if ws.cell(r, c0 + i).value in (None, "")]
                if blanks:
                    rep.warnings.append(f"{len(blanks)} row(s) on '{sheet['name']}' have no ID yet (they get one on the next change).")
                ids = [str(v).lower() for v in values if v not in (None, "")]
                dupes = sorted({v for v in ids if ids.count(v) > 1})
                if dupes:
                    rep.errors.append(f"Duplicate IDs on '{sheet['name']}': {', '.join(d.upper() for d in dupes)}.")
            if col.get("required") and col["type"] not in ("formula", "id"):
                blank = 0
                for r in data_rows:
                    row_vals = [ws.cell(r, c0 + j).value for j, c in enumerate(table["columns"]) if c["type"] not in ("formula", "id")]
                    if any(v not in (None, "") for v in row_vals) and ws.cell(r, c0 + i).value in (None, ""):
                        blank += 1
                if blank:
                    rep.warnings.append(f"{blank} row(s) on '{sheet['name']}' are missing '{col['header']}', which should be filled in.")

    for p in spec.get("parameters", []):
        if f"p_{p['key']}" not in wb.defined_names:
            rep.errors.append(f"The setting '{p['label']}' (p_{p['key']}) is missing from the Settings sheet.")
    return rep
