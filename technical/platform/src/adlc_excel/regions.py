"""Find the data people mean: a sheet, an Excel Table, or a header row + block of rows."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.cell import range_boundaries

GENERATED = {"_ADLC", "_Lists"}
TOTAL_WORDS = ("total", "grand total", "sum", "subtotal")


class TargetError(ValueError):
    """The sheet, table or column could not be found. Message is written for non-experts."""


@dataclass
class Region:
    ws: object
    header_row: int
    c0: int
    c1: int
    last_row: int
    table: object = None

    @property
    def name(self) -> str:
        return self.table.displayName if self.table is not None else f"{self.ws.title}!{self.ref}"

    @property
    def ref(self) -> str:
        return f"{get_column_letter(self.c0)}{self.header_row}:{get_column_letter(self.c1)}{self.last_row}"

    @property
    def headers(self) -> list[str]:
        return [str(self.ws.cell(self.header_row, c).value or "").strip() for c in range(self.c0, self.c1 + 1)]

    @property
    def data_rows(self) -> range:
        return range(self.header_row + 1, self.last_row + 1)

    def is_blank_row(self, r: int) -> bool:
        return all(self.ws.cell(r, c).value in (None, "") for c in range(self.c0, self.c1 + 1))

    @property
    def rows_with_data(self) -> list[int]:
        return [r for r in self.data_rows if not self.is_blank_row(r)]

    def col(self, ref) -> int:
        """Absolute column index for a header (any case), a column letter, or a 1-based position."""
        if isinstance(ref, int):
            return self.c0 + ref - 1
        text = str(ref).strip()
        headers = self.headers
        lowered = [h.lower() for h in headers]
        if text.lower() in lowered:
            return self.c0 + lowered.index(text.lower())
        if re.fullmatch(r"[A-Za-z]{1,3}", text):
            idx = column_index_from_string(text.upper())
            if self.c0 <= idx <= self.c1:
                return idx
        close = difflib.get_close_matches(text, headers, n=2, cutoff=0.6)
        hint = f" Did you mean {' or '.join(repr(c) for c in close)}?" if close else ""
        raise TargetError(f"I can't find a column called '{text}' in {self.name}.{hint} Columns are: {', '.join(h for h in headers if h)}.")

    def has_col(self, ref) -> bool:
        try:
            self.col(ref)
            return True
        except TargetError:
            return False

    def refresh_table(self):
        if self.table is not None:
            self.c0, self.header_row, self.c1, self.last_row = range_boundaries(self.table.ref)


def find_sheet(wb, name):
    if name is None:
        return None
    for ws in wb.worksheets:
        if ws.title.lower() == str(name).strip().lower():
            return ws
    close = difflib.get_close_matches(str(name), wb.sheetnames, n=2, cutoff=0.5)
    hint = f" Did you mean {' or '.join(repr(c) for c in close)}?" if close else ""
    visible = [ws.title for ws in wb.worksheets if ws.sheet_state == "visible"]
    raise TargetError(f"There is no sheet called '{name}'.{hint} Sheets: {', '.join(visible)}.")


def detect_block(ws) -> Region | None:
    """The first header row (2+ text cells) in the top 30 rows and the rows under it."""
    for r in range(1, min(ws.max_row, 30) + 1):
        filled = [(c, ws.cell(r, c).value) for c in range(1, ws.max_column + 1) if ws.cell(r, c).value not in (None, "")]
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
                first = next((ws.cell(rr, c).value for c in range(c0, c1 + 1) if ws.cell(rr, c).value not in (None, "")), "")
                if str(first).strip().lower().startswith(TOTAL_WORDS):
                    break
                last = rr
            return Region(ws, r, c0, c1, last)
    return None


def table_region(ws, t) -> Region:
    c0, r0, c1, r1 = range_boundaries(t.ref)
    return Region(ws, r0, c0, c1, r1, t)


def all_regions(wb) -> list[Region]:
    out = []
    for ws in wb.worksheets:
        if ws.title in GENERATED:
            continue
        if ws.tables:
            out += [table_region(ws, t) for t in ws.tables.values()]
        else:
            block = detect_block(ws)
            if block:
                out.append(block)
    return out


def find_region(wb, sheet=None, table=None, column=None) -> Region:
    """Resolve what the person is talking about: a table name, a sheet, or a column heading."""
    if table:
        for ws in wb.worksheets:
            for name, t in ((t.displayName, t) for t in ws.tables.values()):
                if name.lower() == str(table).lower():
                    return table_region(ws, t)
        if not sheet:
            sheet = table  # people often give the sheet name as "the table"
    candidates = []
    if sheet:
        ws = find_sheet(wb, sheet)
        candidates = [table_region(ws, t) for t in ws.tables.values()] or ([b] if (b := detect_block(ws)) else [])
        if not candidates:
            raise TargetError(f"I can't find a header row with data on '{ws.title}'.")
    else:
        candidates = all_regions(wb)
        if not candidates:
            raise TargetError("I can't find any table of data in this workbook.")
    if column:
        with_col = [r for r in candidates if r.has_col(column)]
        if len(with_col) == 1 or (with_col and sheet):
            return with_col[0]
        if len(with_col) > 1:
            raise TargetError(
                f"More than one table has a column '{column}': {', '.join(r.name for r in with_col)}. Which one?"
            )
    if len(candidates) == 1 or sheet:
        return candidates[0]
    raise TargetError("Which table do you mean? This workbook has: " + ", ".join(r.name for r in candidates) + ".")
