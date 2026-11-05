"""Find PII in text, Excel, Word and CSV files; replace it; put it back later.

    clean, report, vault = scrub_file("Claims.xlsx")      # -> "Claims (PII removed).xlsx"
    restore_file("Claims (PII removed) - edited.xlsx", vault)

Formulas are never changed by scrubbing. Cells in columns whose heading says what they
hold (Name, PPS number, Email...) are replaced as a whole. All other text is scanned
for patterns, Irish names and names already seen elsewhere in the same file.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from pathlib import Path

from .detectors import (
    FIRST_NAMES, PATTERNS, classify_header, find_in_text, iban_valid, looks_like_person_name, luhn_valid, ppsn_valid,
)
from .policy import Policy
from .report import PiiReport
from .vault import TOKEN_RE, Vault, display

SKIP_SHEETS = {"_ADLC", "_Lists"}
_FULL = {ptype: rx for ptype, rx, _ in PATTERNS}


# --------------------------------------------------------------------------- core


def apply_action(ptype: str, value, action: str, vault: Vault):
    if action == "keep":
        return value
    if action == "pseudonymise":
        return vault.token_for(ptype, value)
    if action == "generalise":
        if ptype == "DATE_OF_BIRTH":
            if isinstance(value, (date, datetime)):
                return f"born {value.year}"
            m = re.search(r"(19|20)\d{2}", str(value))
            return f"born {m.group(0)}" if m else "[DATE_OF_BIRTH]"
        if ptype == "EIRCODE":
            return re.sub(r"\s", "", str(value)).upper()[:3] + " area"
    return f"[{ptype}]"


def scrub_text(text: str, policy: Policy | None = None, vault: Vault | None = None,
               known: dict[str, str] | None = None, report: PiiReport | None = None,
               where: str = "text") -> tuple[str, Vault]:
    """Replace PII in a piece of text. Returns (clean text, vault)."""
    policy = policy or Policy()
    vault = vault if vault is not None else Vault()
    if not isinstance(text, str) or not text:
        return text, vault
    # Names already seen (earlier in this text, file or chat) are matched in any letter case.
    known = dict(known or {})
    for token, entry in vault.tokens.items():
        if entry["type"] in ("PERSON", "STAFF_NAME") and isinstance(entry["value"], str):
            known.setdefault(entry["value"], entry["type"])
    findings = find_in_text(text, policy.member_patterns, known, allow=policy.allow)
    names = {f.value: f.type for f in findings if f.type in ("PERSON", "STAFF_NAME") and f.value not in known}
    if names:
        known.update(names)
        findings = find_in_text(text, policy.member_patterns, known, allow=policy.allow)
    replacements = []
    for f in findings:  # in reading order, so tokens are numbered as they appear
        action = policy.action(f.type)
        if report is not None:
            report.add(where, f.type, f.method, f.value, action)
        if action != "keep":
            replacements.append((f, str(apply_action(f.type, f.value, action, vault))))
    out = text
    for f, new in reversed(replacements):
        out = out[:f.start] + new + out[f.end:]
    return out, vault


def _value_matches(ptype: str, s: str) -> bool:
    s = s.strip()
    if ptype == "PPSN":
        return ppsn_valid(s)
    if ptype == "IBAN":
        return iban_valid(s)
    if ptype == "CARD":
        return bool(re.fullmatch(r"[\d -]{13,23}", s)) and luhn_valid(s)
    rx = _FULL.get(ptype)
    return bool(rx and rx.fullmatch(s))


def classify_column(header, values) -> tuple[str | None, str]:
    """Decide what a column holds, from its heading first and then from its values."""
    ptype = classify_header(header)
    if ptype:
        return ptype, "header"
    sample = [display(v) for v in values if v not in (None, "") and not (isinstance(v, str) and v.startswith("="))][:200]
    if len(sample) < 3:
        return None, ""
    for candidate in ("PPSN", "IBAN", "CARD", "EMAIL", "PHONE", "EIRCODE"):
        if sum(_value_matches(candidate, s) for s in sample) / len(sample) >= 0.6:
            return candidate, "values"
    if sum(looks_like_person_name(s) for s in sample) / len(sample) >= 0.6:
        return "PERSON", "values"
    return None, ""


def _staff_name_like(value: str) -> bool:
    """Only real-looking names from Owner-type columns count ('Aoife', 'Liam Ryan' - not 'ADLC engine')."""
    words = value.split()
    if not 1 <= len(words) <= 3 or not all(w[:1].isupper() and w.replace("'", "").replace("-", "").isalpha() for w in words):
        return False
    return len(words) > 1 or words[0] in FIRST_NAMES


def _known_names(columns: dict[int, tuple[str, str]], rows: list[list], headers: list) -> dict[str, str]:
    """Names seen in name columns, including 'First Last' built from split name columns."""
    known: dict[str, str] = {}
    first_idx = [i for i, h in enumerate(headers) if re.search(r"first|forename|given", str(h or ""), re.I)]
    last_idx = [i for i, h in enumerate(headers) if re.search(r"surname|last name|family", str(h or ""), re.I)]
    for row in rows:
        for i, (ptype, _) in columns.items():
            if ptype not in ("PERSON", "STAFF_NAME") or i >= len(row) or not isinstance(row[i], str):
                continue
            value = row[i].strip()
            if len(value) <= 2 or TOKEN_RE.fullmatch(value):
                continue
            if ptype == "STAFF_NAME" and not _staff_name_like(value):
                continue
            known[value] = ptype
        for fi in first_idx:
            for li in last_idx:
                if fi < len(row) and li < len(row) and row[fi] and row[li]:
                    known[f"{str(row[fi]).strip()} {str(row[li]).strip()}"] = "PERSON"
    return known


def scrub_table(headers: list, rows: list[list], policy: Policy | None = None, vault: Vault | None = None,
                report: PiiReport | None = None, where: str = "table") -> tuple[list[list], dict[int, str]]:
    """Tokenise a table of values (e.g. rows about to be shown to an AI). Returns (rows, column types)."""
    policy = policy or Policy()
    vault = vault if vault is not None else Vault()
    report = report if report is not None else PiiReport(where)
    columns = {}
    for i, h in enumerate(headers):
        ptype, method = classify_column(h, [r[i] for r in rows if i < len(r)])
        if ptype:
            columns[i] = (ptype, method)
    known = _known_names(columns, rows, headers)
    out = []
    for row in rows:
        new = []
        for i, v in enumerate(row):
            if v in (None, "") or (isinstance(v, str) and (v.startswith("=") or TOKEN_RE.fullmatch(v.strip()))):
                new.append(v)
            elif i in columns:
                ptype, method = columns[i]
                action = policy.action(ptype)
                report.add(f"{where} ({headers[i]})", ptype, method, v, action)
                new.append(apply_action(ptype, v, action, vault) if action != "keep" else v)
            elif isinstance(v, str):
                new.append(scrub_text(v, policy, vault, known, report, where=f"{where} ({headers[i] if i < len(headers) else i})")[0])
            else:
                new.append(v)
        out.append(new)
    return out, {i: t for i, (t, _) in columns.items()}


# --------------------------------------------------------------------------- Excel


def _regions(ws):
    """(header_row, first_col, last_col, last_row) for each data block on a sheet."""
    regions = []
    from openpyxl.utils.cell import range_boundaries

    for t in ws.tables.values():
        c0, r0, c1, r1 = range_boundaries(t.ref)
        regions.append((r0, c0, c1, r1))
    if regions:
        return regions
    for r in range(1, min(ws.max_row, 20) + 1):
        cells = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
        filled = [(c, v) for c, v in enumerate(cells, start=1) if v not in (None, "")]
        if len(filled) >= 2 and all(isinstance(v, str) for _, v in filled):
            return [(r, filled[0][0], filled[-1][0], ws.max_row)]
    return []


def scrub_workbook(wb, policy: Policy, vault: Vault, report: PiiReport, write: bool = True):
    from openpyxl.utils import get_column_letter

    plans = []
    known: dict[str, str] = {}
    for ws in wb.worksheets:
        if ws.title in SKIP_SHEETS or ws.title.startswith("_PII"):
            continue
        for (r0, c0, c1, r1) in _regions(ws):
            headers = [ws.cell(r0, c).value for c in range(c0, c1 + 1)]
            rows = [[ws.cell(r, c).value for c in range(c0, c1 + 1)] for r in range(r0 + 1, r1 + 1)]
            columns = {}
            for i, h in enumerate(headers):
                ptype, method = classify_column(h, [row[i] for row in rows])
                if ptype:
                    columns[i] = (ptype, method)
            known.update(_known_names(columns, rows, headers))
            plans.append((ws, r0, c0, r1, headers, columns))

    handled = set()
    for ws, r0, c0, r1, headers, columns in plans:
        for i, (ptype, method) in columns.items():
            col = c0 + i
            where = f"{ws.title}!{get_column_letter(col)} ({headers[i]})"
            action = policy.action(ptype)
            for r in range(r0 + 1, r1 + 1):
                cell = ws.cell(r, col)
                handled.add((ws.title, r, col))
                v = cell.value
                if v in (None, "") or (isinstance(v, str) and (v.startswith("=") or TOKEN_RE.fullmatch(v.strip()))):
                    continue
                report.add(where, ptype, method, v, action)
                if write and action != "keep":
                    cell.value = apply_action(ptype, v, action, vault)
                    if not isinstance(cell.value, (int, float, date, datetime)):
                        cell.number_format = "@"
                        cell.data_type = "s"

    for ws in wb.worksheets:
        if ws.title in SKIP_SHEETS or ws.title.startswith("_PII"):
            continue
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if (ws.title, cell.row, cell.column) in handled or not isinstance(v, str) or v.startswith("="):
                    continue
                clean, _ = scrub_text(v, policy, vault, known, report, where=f"{ws.title}!{cell.column_letter} (text)")
                if write and clean != v:
                    cell.value = clean
                    cell.data_type = "s"
    return wb


def restore_workbook(wb, vault: Vault):
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, str):
                    new = vault.restore_value(v)
                    if new != v:
                        cell.value = new
                        if isinstance(new, (date, datetime)):
                            cell.number_format = "dd/mm/yyyy"
                        elif isinstance(new, (int, float)):
                            cell.number_format = "General"
    return wb


# --------------------------------------------------------------------------- Word


def _set_paragraph_text(p, text: str):
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r.text = ""


def _docx_paragraphs(doc):
    """(label, paragraph) for body, tables, headers and footers."""
    for i, p in enumerate(doc.paragraphs, start=1):
        yield "Body text", p
    for ti, table in enumerate(doc.tables, start=1):
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield f"Table {ti}", p
    for section in doc.sections:
        for part in (section.header, section.footer):
            for p in part.paragraphs:
                yield "Header/footer", p


def scrub_docx(doc, policy: Policy, vault: Vault, report: PiiReport, write: bool = True):
    known: dict[str, str] = {}
    whole_cells = set()   # cell elements replaced as a whole (kept referenced so identity is stable)
    for ti, table in enumerate(doc.tables, start=1):
        if len(table.rows) < 2:
            continue
        headers = [c.text.strip() for c in table.rows[0].cells]
        rows = [[c.text.strip() for c in r.cells] for r in table.rows[1:]]
        columns = {}
        for i, h in enumerate(headers):
            ptype, method = classify_column(h, [row[i] for row in rows if i < len(row)])
            if ptype:
                columns[i] = (ptype, method)
        known.update(_known_names(columns, rows, headers))
        for r in table.rows[1:]:
            for i, (ptype, method) in columns.items():
                if i >= len(r.cells):
                    continue
                cell = r.cells[i]
                text = cell.text.strip()
                whole_cells.add(cell._tc)
                if not text or TOKEN_RE.fullmatch(text):
                    continue
                action = policy.action(ptype)
                report.add(f"Table {ti} ({headers[i]})", ptype, method, text, action)
                if write and action != "keep":
                    _set_paragraph_text(cell.paragraphs[0], str(apply_action(ptype, text, action, vault)))
                    for extra in cell.paragraphs[1:]:
                        _set_paragraph_text(extra, "")
    for label, p in _docx_paragraphs(doc):
        if p._p.getparent() in whole_cells:
            continue
        text = p.text
        clean, _ = scrub_text(text, policy, vault, known, report, where=label)
        if write and clean != text:
            _set_paragraph_text(p, clean)
    return doc


def restore_docx(doc, vault: Vault):
    for _, p in _docx_paragraphs(doc):
        text = p.text
        new = vault.restore_text(text)
        if new != text:
            _set_paragraph_text(p, new)
    return doc


# --------------------------------------------------------------------------- CSV / text


def scrub_csv_text(text: str, policy: Policy, vault: Vault, report: PiiReport, where: str = "CSV") -> str:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return text
    headers, body = rows[0], rows[1:]
    columns = {}
    for i, h in enumerate(headers):
        ptype, method = classify_column(h, [r[i] for r in body if i < len(r)])
        if ptype:
            columns[i] = (ptype, method)
    known = _known_names(columns, body, headers)
    for r in body:
        for i, value in enumerate(r):
            if not value:
                continue
            if i in columns and not TOKEN_RE.fullmatch(value.strip()):
                ptype, method = columns[i]
                action = policy.action(ptype)
                report.add(f"{where} column '{headers[i]}'", ptype, method, value, action)
                if action != "keep":
                    r[i] = str(apply_action(ptype, value, action, vault))
            else:
                r[i], _ = scrub_text(value, policy, vault, known, report, where=f"{where} column '{headers[i] if i < len(headers) else i + 1}'")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows([headers] + body)
    return buf.getvalue()


# --------------------------------------------------------------------------- files


def cleaned_name(path: Path) -> Path:
    return path.with_name(f"{path.stem} (PII removed){path.suffix}")


def scrub_file(path, out=None, policy: Policy | None = None, vault: Vault | None = None,
               write: bool = True) -> tuple[Path | None, PiiReport, Vault]:
    """Clean a file. Returns (cleaned file path or None for a scan, report, vault)."""
    path = Path(path)
    policy = policy or Policy.load()
    vault = vault if vault is not None else Vault(path.name)
    report = PiiReport(path.name)
    ext = path.suffix.lower()
    target = Path(out) if out else cleaned_name(path)
    if ext == ".xlsx":
        from openpyxl import load_workbook

        wb = load_workbook(path)
        scrub_workbook(wb, policy, vault, report, write)
        if write:
            wb.save(target)
    elif ext == ".docx":
        from docx import Document

        doc = Document(str(path))
        scrub_docx(doc, policy, vault, report, write)
        if write:
            doc.save(str(target))
    elif ext == ".csv":
        clean = scrub_csv_text(path.read_text(encoding="utf-8-sig"), policy, vault, report, where=path.name)
        if write:
            target.write_text(clean, encoding="utf-8-sig")
    elif ext in (".txt", ".md", ".vtt", ".json"):
        clean, _ = scrub_text(path.read_text(encoding="utf-8"), policy, vault, report=report, where=path.name)
        if write:
            target.write_text(clean, encoding="utf-8")
    else:
        raise ValueError(f"Can't clean {ext} files yet. Supported: .xlsx, .docx, .csv, .txt, .md, .vtt (save PDFs as Word first).")
    return (target if write else None), report, vault


def scan_file(path, policy: Policy | None = None) -> PiiReport:
    return scrub_file(path, policy=policy, write=False)[1]


def restore_file(path, vault: Vault, out=None) -> Path:
    path = Path(path)
    stem = path.stem.replace(" (PII removed)", "")
    target = Path(out) if out else path.with_name(f"{stem} (restored){path.suffix}")
    ext = path.suffix.lower()
    if ext == ".xlsx":
        from openpyxl import load_workbook

        wb = load_workbook(path)
        restore_workbook(wb, vault)
        wb.save(target)
    elif ext == ".docx":
        from docx import Document

        doc = Document(str(path))
        restore_docx(doc, vault)
        doc.save(str(target))
    else:
        target.write_text(vault.restore_text(path.read_text(encoding="utf-8-sig")), encoding="utf-8")
    return target
